from __future__ import annotations

import functools
import inspect
import random
import uuid
from dataclasses import asdict
from typing import Any, Callable, Dict, List, Optional, TypeVar

from azure.kusto.data import (
    ClientRequestProperties,
    KustoConnectionStringBuilder,
)

from fabric_rti_mcp import __version__  # type: ignore
from fabric_rti_mcp.kusto.kusto_config import KustoConfig
from fabric_rti_mcp.kusto.kusto_connection import KustoConnection, sanitize_uri
from fabric_rti_mcp.kusto.kusto_response_formatter import format_results

_DEFAULT_DB_NAME = KustoConnectionStringBuilder.DEFAULT_DATABASE_NAME
CONFIG = KustoConfig.from_env()


class KustoElicitationError(Exception):
    """Exception raised when user interaction is needed to resolve missing parameters."""

    def __init__(self, message: str, available_options: List[Dict[str, Any]], parameter_type: str):
        super().__init__(message)
        self.available_options = available_options
        self.parameter_type = parameter_type


class KustoSamplingError(Exception):
    """Exception raised when automatic sampling fails and fallback is needed."""

    def __init__(self, message: str, attempted_sample: Optional[str] = None):
        super().__init__(message)
        self.attempted_sample = attempted_sample


def _sample_cluster_from_known_services(context_query: Optional[str] = None) -> Optional[str]:
    """
    Sample a cluster URI from known services based on context.

    :param context_query: Optional query text to help with selection
    :return: Selected cluster URI or None if no services available
    """
    known_services = KustoConfig.get_known_services()
    if not known_services:
        return None

    services_list = list(known_services.values())

    # If only one service, return it
    if len(services_list) == 1:
        return services_list[0].service_uri

    # For multiple services, try context-based selection
    if context_query and "sample" in context_query.lower():
        # Prefer services with "samples" or "demo" in description
        for service in services_list:
            if service.description and any(
                keyword in service.description.lower() for keyword in ["sample", "demo", "test", "example"]
            ):
                return service.service_uri

    # Fallback to default service if available
    if CONFIG.default_service:
        return CONFIG.default_service.service_uri

    # Random sampling as last resort
    return random.choice(services_list).service_uri


def _elicit_cluster_selection() -> str:
    """
    Elicit cluster selection from user when no cluster_uri is provided.

    :return: Never returns, always raises KustoElicitationError
    :raises KustoElicitationError: Always raised to prompt user for cluster selection
    """
    known_services = KustoConfig.get_known_services()

    if not known_services:
        available_options = []
        message = (
            "No Kusto cluster URI provided and no known services are configured. "
            "Please provide a cluster_uri parameter (e.g., 'https://mycluster.kusto.windows.net') "
            "or configure known services via KUSTO_KNOWN_SERVICES environment variable."
        )
    else:
        available_options = [
            {
                "service_uri": service.service_uri,
                "description": service.description or "No description",
                "default_database": service.default_database or _DEFAULT_DB_NAME,
            }
            for service in known_services.values()
        ]

        service_list = ", ".join([f"'{s['service_uri']}'" for s in available_options])
        message = (
            f"No Kusto cluster URI provided. Please specify one of the available clusters: {service_list}. "
            "Or provide a custom cluster_uri parameter."
        )

    raise KustoElicitationError(message, available_options, "cluster_uri")


def _sample_database_from_cluster(cluster_uri: str, context_query: Optional[str] = None) -> Optional[str]:
    """
    Sample a database from available databases in the cluster.

    :param cluster_uri: The cluster to query for databases
    :param context_query: Optional query text to help with selection
    :return: Selected database name or None if sampling fails
    """
    try:
        # Get list of databases from cluster
        databases = _execute(".show databases", cluster_uri)

        if not databases:
            return None

        # Extract database names and ensure they are strings
        db_names: List[str] = []
        for db in databases:
            db_name = db.get("DatabaseName")
            if isinstance(db_name, str) and db_name.strip():
                db_names.append(db_name)

        if not db_names:
            return None

        # If only one database, return it
        if len(db_names) == 1:
            return db_names[0]

        # Context-based selection
        if context_query:
            query_lower = context_query.lower()

            # Look for database hints in the query
            for db_name in db_names:
                if db_name.lower() in query_lower:
                    return db_name

            # Prefer common database names for samples/demos
            if any(keyword in query_lower for keyword in ["sample", "demo", "test", "example"]):
                for db_name in db_names:
                    if any(keyword in db_name.lower() for keyword in ["sample", "demo", "test", "example"]):
                        return db_name

        # Random sampling as fallback
        return random.choice(db_names)

    except Exception:
        # If we can't query databases, return None to trigger elicitation
        return None


def _elicit_database_selection(cluster_uri: str) -> str:
    """
    Elicit database selection from user when no database is specified.

    :param cluster_uri: The cluster URI to get database list from
    :return: Never returns, always raises KustoElicitationError
    :raises KustoElicitationError: Always raised to prompt user for database selection
    """
    try:
        # Try to get available databases
        databases = _execute(".show databases", cluster_uri)
        available_options = [
            {
                "database_name": db.get("DatabaseName", ""),
                "size_mb": db.get("TotalExtentSize", 0),
                "description": f"Database on {cluster_uri}",
            }
            for db in databases
            if db.get("DatabaseName")
        ]

        if available_options:
            db_list = ", ".join([f"'{db['database_name']}'" for db in available_options])
            message = (
                f"No database specified and no default configured for cluster {cluster_uri}. "
                f"Available databases: {db_list}. Please specify a database parameter."
            )
        else:
            available_options = []
            message = (
                f"No database specified and unable to list databases for cluster {cluster_uri}. "
                "Please specify a database parameter."
            )

    except Exception:
        available_options = []
        message = (
            f"No database specified and unable to connect to cluster {cluster_uri} to list databases. "
            "Please specify a database parameter."
        )

    raise KustoElicitationError(message, available_options, "database")


class KustoConnectionManager:
    def __init__(self) -> None:
        self._cache: Dict[str, KustoConnection] = {}

    def connect_to_all_known_services(self) -> None:
        """
        Use at your own risk. Connecting takes time and might make the server unresponsive.
        """
        if CONFIG.eager_connect:
            known_services = KustoConfig.get_known_services().values()
            for known_service in known_services:
                self.get(known_service.service_uri)

    def get(self, cluster_uri: str) -> KustoConnection:
        """
        Retrieves a cached or new KustoConnection for the given URI.
        This method is the single entry point for accessing connections.
        """
        sanitized_uri = sanitize_uri(cluster_uri)

        if sanitized_uri in self._cache:
            return self._cache[sanitized_uri]

        # Connection not found, create a new one.
        known_services = KustoConfig.get_known_services()
        default_database = _DEFAULT_DB_NAME

        if sanitized_uri in known_services:
            default_database = known_services[sanitized_uri].default_database or _DEFAULT_DB_NAME
        elif not CONFIG.allow_unknown_services:
            raise ValueError(
                f"Service URI '{sanitized_uri}' is not in the list of approved services, "
                "and unknown connections are not permitted by the administrator."
            )

        connection = KustoConnection(sanitized_uri, default_database=default_database)
        self._cache[sanitized_uri] = connection
        return connection


# --- In the main module scope ---
# Instantiate it once to be used as a singleton throughout the module.
_CONNECTION_MANAGER = KustoConnectionManager()
# Not recommended for production use, but useful for testing and development.
if CONFIG.eager_connect:
    _CONNECTION_MANAGER.connect_to_all_known_services()


def get_kusto_connection(cluster_uri: str) -> KustoConnection:
    # Nicety to allow for easier mocking in tests.
    return _CONNECTION_MANAGER.get(cluster_uri)


def get_kusto_connection_with_elicitation(
    cluster_uri: Optional[str] = None, context_query: Optional[str] = None
) -> KustoConnection:
    """
    Get a Kusto connection with elicitation and sampling support.

    :param cluster_uri: Optional cluster URI. If None, will attempt sampling or elicitation
    :param context_query: Optional query context to help with intelligent sampling
    :return: KustoConnection instance
    :raises KustoElicitationError: When user input is needed for cluster selection
    """
    if cluster_uri is None:
        # Try sampling from known services first
        sampled_uri = _sample_cluster_from_known_services(context_query)
        if sampled_uri:
            cluster_uri = sampled_uri
        else:
            # No sampling possible, elicit user choice
            _elicit_cluster_selection()  # This will always raise KustoElicitationError
            # This line should never be reached due to the exception above
            raise RuntimeError("Elicitation should have raised KustoElicitationError")

    return get_kusto_connection(cluster_uri)


F = TypeVar("F", bound=Callable[..., Any])


def destructive_operation(func: F) -> F:
    """
    Decorator to mark a Kusto operation as 'destructive' (e.g., ingest, drop).
    This is a robust way to manage the 'request_readonly' property, preventing
    accidental data modification from read-only functions.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):  # type: ignore
        return func(*args, **kwargs)

    setattr(wrapper, "_is_destructive", True)  # type: ignore
    return wrapper  # type: ignore


def _crp(action: str, is_destructive: bool, ignore_readonly: bool) -> ClientRequestProperties:
    crp: ClientRequestProperties = ClientRequestProperties()
    crp.application = f"fabric-rti-mcp{{{__version__}}}"  # type: ignore
    crp.client_request_id = f"KFRTI_MCP.{action}:{str(uuid.uuid4())}"  # type: ignore
    if not is_destructive and not ignore_readonly:
        crp.set_option("request_readonly", True)

    # Set global timeout if configured
    if CONFIG.timeout_seconds is not None:
        # Convert seconds to timespan format (HH:MM:SS)
        hours, remainder = divmod(CONFIG.timeout_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        timeout_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        crp.set_option("servertimeout", timeout_str)

    return crp


def _execute(
    query: str,
    cluster_uri: str,
    readonly_override: bool = False,
    database: Optional[str] = None,
) -> List[Dict[str, Any]]:
    caller_frame = inspect.currentframe().f_back  # type: ignore
    action_name = caller_frame.f_code.co_name  # type: ignore
    caller_func = caller_frame.f_globals.get(action_name)  # type: ignore
    is_destructive = hasattr(caller_func, "_is_destructive")

    connection = get_kusto_connection(cluster_uri)
    client = connection.query_client

    # agents can send messy inputs
    query = query.strip()

    database = database or connection.default_database
    database = database.strip()

    crp = _crp(action_name, is_destructive, readonly_override)
    result_set = client.execute(database, query, crp)
    return format_results(result_set)


def _execute_with_elicitation(
    query: str,
    cluster_uri: Optional[str] = None,
    readonly_override: bool = False,
    database: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Execute a query with elicitation and sampling support for missing parameters.

    :param query: The KQL query to execute
    :param cluster_uri: Optional cluster URI. If None, will attempt sampling or elicitation
    :param readonly_override: Whether to override read-only settings
    :param database: Optional database name. If None, will attempt sampling or elicitation
    :return: Query results
    :raises KustoElicitationError: When user input is needed for parameter resolution
    """
    caller_frame = inspect.currentframe().f_back  # type: ignore
    action_name = caller_frame.f_code.co_name  # type: ignore
    caller_func = caller_frame.f_globals.get(action_name)  # type: ignore
    is_destructive = hasattr(caller_func, "_is_destructive")

    # Handle cluster_uri elicitation/sampling
    if cluster_uri is None:
        sampled_uri = _sample_cluster_from_known_services(query)
        if sampled_uri:
            cluster_uri = sampled_uri
        else:
            _elicit_cluster_selection()  # This will always raise KustoElicitationError
            # This line should never be reached due to the exception above
            raise RuntimeError("Elicitation should have raised KustoElicitationError")

    # At this point cluster_uri is guaranteed to be a string
    connection = get_kusto_connection(cluster_uri)
    client = connection.query_client

    # agents can send messy inputs
    query = query.strip()

    # Handle database elicitation/sampling
    if database is None:
        database = connection.default_database
        if not database or database == _DEFAULT_DB_NAME:
            # Try sampling from available databases
            sampled_db = _sample_database_from_cluster(cluster_uri, query)
            if sampled_db:
                database = sampled_db
            else:
                # No sampling possible, elicit user choice
                _elicit_database_selection(cluster_uri)  # This will always raise KustoElicitationError
                # This line should never be reached due to the exception above
                raise RuntimeError("Elicitation should have raised KustoElicitationError")

    database = database.strip()

    crp = _crp(action_name, is_destructive, readonly_override)
    result_set = client.execute(database, query, crp)
    return format_results(result_set)


# NOTE: This is temporary. The intent is to not use environment variables for persistency.
def kusto_known_services() -> List[Dict[str, str]]:
    """
    Retrieves a list of all Kusto services known to the MCP.
    Could be null if no services are configured.

    :return: List of objects, {"service": str, "description": str, "default_database": str}
    """
    services = KustoConfig.get_known_services().values()
    return [asdict(service) for service in services]


def kusto_query(query: str, cluster_uri: str, database: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Executes a KQL query on the specified database. If no database is provided,
    it will use the default database.

    :param query: The KQL query to execute.
    :param cluster_uri: The URI of the Kusto cluster.
    :param database: Optional database name. If not provided, uses the default database.
    :return: The result of the query execution as a list of dictionaries (json).
    """
    return _execute(query, cluster_uri, database=database)


@destructive_operation
def kusto_command(command: str, cluster_uri: str, database: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Executes a kusto management command on the specified database. If no database is provided,
    it will use the default database.

    :param command: The kusto management command to execute.
    :param cluster_uri: The URI of the Kusto cluster.
    :param database: Optional database name. If not provided, uses the default database.
    :return: The result of the command execution as a list of dictionaries (json).
    """
    return _execute(command, cluster_uri, database=database)


def kusto_list_databases(cluster_uri: str) -> List[Dict[str, Any]]:
    """
    Retrieves a list of all databases in the Kusto cluster.

    :param cluster_uri: The URI of the Kusto cluster.
    :return: List of dictionaries containing database information.
    """
    return _execute(".show databases", cluster_uri)


def kusto_list_tables(cluster_uri: str, database: str) -> List[Dict[str, Any]]:
    """
    Retrieves a list of all tables in the specified database.

    :param cluster_uri: The URI of the Kusto cluster.
    :param database: The name of the database to list tables from.
    :return: List of dictionaries containing table information.
    """
    return _execute(".show tables", cluster_uri, database=database)


def kusto_get_entities_schema(cluster_uri: str, database: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieves schema information for all entities (tables, materialized views, functions)
    in the specified database. If no database is provided, uses the default database.

    :param cluster_uri: The URI of the Kusto cluster.
    :param database: Optional database name. If not provided, uses the default database.
    :return: List of dictionaries containing entity schema information.
    """
    return _execute(
        ".show databases entities with (showObfuscatedStrings=true) "
        f"| where DatabaseName == '{database or _DEFAULT_DB_NAME}' "
        "| project EntityName, EntityType, Folder, DocString",
        cluster_uri,
        database=database,
    )


def kusto_get_table_schema(table_name: str, cluster_uri: str, database: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieves the schema information for a specific table in the specified database.
    If no database is provided, uses the default database.

    :param table_name: Name of the table to get schema for.
    :param cluster_uri: The URI of the Kusto cluster.
    :param database: Optional database name. If not provided, uses the default database.
    :return: List of dictionaries containing table schema information.
    """
    return _execute(f".show table {table_name} cslschema", cluster_uri, database=database)


def kusto_get_function_schema(
    function_name: str,
    cluster_uri: str,
    database: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieves schema information for a specific function, including parameters and output schema.
    If no database is provided, uses the default database.

    :param function_name: Name of the function to get schema for.
    :param cluster_uri: The URI of the Kusto cluster.
    :param database: Optional database name. If not provided, uses the default database.
    :return: List of dictionaries containing function schema information.
    """
    return _execute(f".show function {function_name}", cluster_uri, database=database)


def kusto_sample_table_data(
    table_name: str,
    cluster_uri: str,
    sample_size: int = 10,
    database: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieves a random sample of records from the specified table.
    If no database is provided, uses the default database.

    :param table_name: Name of the table to sample data from.
    :param cluster_uri: The URI of the Kusto cluster.
    :param sample_size: Number of records to sample. Defaults to 10.
    :param database: Optional database name. If not provided, uses the default database.
    :return: List of dictionaries containing sampled records.
    """
    return _execute(f"{table_name} | sample {sample_size}", cluster_uri, database=database)


def kusto_sample_function_data(
    function_call_with_params: str,
    cluster_uri: str,
    sample_size: int = 10,
    database: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieves a random sample of records from the result of a function call.
    If no database is provided, uses the default database.

    :param function_call_with_params: Function call string with parameters.
    :param cluster_uri: The URI of the Kusto cluster.
    :param sample_size: Number of records to sample. Defaults to 10.
    :param database: Optional database name. If not provided, uses the default database.
    :return: List of dictionaries containing sampled records.
    """
    return _execute(
        f"{function_call_with_params} | sample {sample_size}",
        cluster_uri,
        database=database,
    )


@destructive_operation
def kusto_ingest_inline_into_table(
    table_name: str,
    data_comma_separator: str,
    cluster_uri: str,
    database: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Ingests inline CSV data into a specified table. The data should be provided as a comma-separated string.
    If no database is provided, uses the default database.

    :param table_name: Name of the table to ingest data into.
    :param data_comma_separator: Comma-separated data string to ingest.
    :param cluster_uri: The URI of the Kusto cluster.
    :param database: Optional database name. If not provided, uses the default database.
    :return: List of dictionaries containing the ingestion result.
    """
    return _execute(
        f".ingest inline into table {table_name} <| {data_comma_separator}",
        cluster_uri,
        database=database,
    )


def kusto_get_shots(
    prompt: str,
    shots_table_name: str,
    cluster_uri: str,
    sample_size: int = 3,
    database: Optional[str] = None,
    embedding_endpoint: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieves shots that are most semantic similar to the supplied prompt from the specified shots table.

    :param prompt: The user prompt to find similar shots for.
    :param shots_table_name: Name of the table containing the shots. The table should have "EmbeddingText" (string)
                             column containing the natural language prompt, "AugmentedText" (string) column containing
                             the respective KQL, and "EmbeddingVector" (dynamic) column containing the embedding vector
                             for the NL.
    :param cluster_uri: The URI of the Kusto cluster.
    :param sample_size: Number of most similar shots to retrieve. Defaults to 3.
    :param database: Optional database name. If not provided, uses the "AI" database or the default database.
    :param embedding_endpoint: Optional endpoint for the embedding model to use. If not provided, uses the
                             AZ_OPENAI_EMBEDDING_ENDPOINT environment variable. If no valid endpoint is set,
                             this function should not be called.
    :return: List of dictionaries containing the shots records.
    """
    # Use provided endpoint, or fall back to environment variable, or use default
    endpoint = embedding_endpoint or CONFIG.open_ai_embedding_endpoint

    kql_query = f"""
        let model_endpoint = '{endpoint}';
        let embedded_term = toscalar(evaluate ai_embeddings('{prompt}', model_endpoint));
        {shots_table_name}
        | extend similarity = series_cosine_similarity(embedded_term, EmbeddingVector)
        | top {sample_size} by similarity
        | project similarity, EmbeddingText, AugmentedText
    """

    return _execute(kql_query, cluster_uri, database=database)


def kusto_query_with_elicitation(
    query: str, cluster_uri: Optional[str] = None, database: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Executes a KQL query with elicitation and sampling support for missing parameters.
    If cluster_uri or database are not provided, the system will attempt to sample
    from available options or elicit user choice.

    :param query: The KQL query to execute.
    :param cluster_uri: Optional URI of the Kusto cluster. If not provided, will attempt
                       sampling from known services or elicit user choice.
    :param database: Optional database name. If not provided, will attempt sampling
                    from available databases or elicit user choice.
    :return: The result of the query execution as a list of dictionaries (json).
    :raises KustoElicitationError: When user input is needed to resolve missing parameters.
    """
    return _execute_with_elicitation(query, cluster_uri, database=database)


def kusto_sample_data_with_elicitation(
    table_name: str,
    cluster_uri: Optional[str] = None,
    sample_size: int = 10,
    database: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieves a random sample of records from the specified table with elicitation support.
    If cluster_uri or database are not provided, the system will attempt to sample
    from available options or elicit user choice.

    :param table_name: Name of the table to sample data from.
    :param cluster_uri: Optional URI of the Kusto cluster. If not provided, will attempt
                       sampling from known services or elicit user choice.
    :param sample_size: Number of records to sample. Defaults to 10.
    :param database: Optional database name. If not provided, will attempt sampling
                    from available databases or elicit user choice.
    :return: List of dictionaries containing sampled records.
    :raises KustoElicitationError: When user input is needed to resolve missing parameters.
    """
    return _execute_with_elicitation(f"{table_name} | sample {sample_size}", cluster_uri, database=database)


def kusto_explore_with_elicitation(
    cluster_uri: Optional[str] = None,
    database: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Explores available tables in a database with elicitation support.
    If cluster_uri or database are not provided, the system will attempt to sample
    from available options or elicit user choice.

    :param cluster_uri: Optional URI of the Kusto cluster. If not provided, will attempt
                       sampling from known services or elicit user choice.
    :param database: Optional database name. If not provided, will attempt sampling
                    from available databases or elicit user choice.
    :return: List of dictionaries containing table information.
    :raises KustoElicitationError: When user input is needed to resolve missing parameters.
    """
    return _execute_with_elicitation(".show tables", cluster_uri, database=database)
