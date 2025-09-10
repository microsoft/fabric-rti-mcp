from __future__ import annotations

import functools
import inspect
import uuid
from dataclasses import asdict
from typing import Any, Callable, Dict, List, Optional, TypeVar

from azure.kusto.data import (
    ClientRequestProperties,
    KustoConnectionStringBuilder,
)

from fabric_rti_mcp import __version__  # type: ignore
from fabric_rti_mcp.common import logger
from fabric_rti_mcp.kusto.kusto_config import KustoConfig
from fabric_rti_mcp.kusto.kusto_connection import KustoConnection, sanitize_uri
from fabric_rti_mcp.kusto.kusto_formatter import KustoFormatter

_DEFAULT_DB_NAME = KustoConnectionStringBuilder.DEFAULT_DATABASE_NAME
CONFIG = KustoConfig.from_env()


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


def _crp(
    action: str, is_destructive: bool, ignore_readonly: bool, additional_properties: Optional[Dict[str, Any]] = None
) -> ClientRequestProperties:
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

    # Apply any additional properties provided by the user (can override global settings)
    if additional_properties:
        for key, value in additional_properties.items():
            crp.set_option(key, value)

    return crp


def _execute(
    query: str,
    cluster_uri: str,
    readonly_override: bool = False,
    database: Optional[str] = None,
    client_request_properties: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    caller_frame = inspect.currentframe().f_back  # type: ignore
    action_name = caller_frame.f_code.co_name  # type: ignore
    caller_func = caller_frame.f_globals.get(action_name)  # type: ignore
    is_destructive = hasattr(caller_func, "_is_destructive")

    # Generate correlation ID for tracing
    crp = _crp(action_name, is_destructive, readonly_override, client_request_properties)
    correlation_id = crp.client_request_id  # type: ignore

    try:
        connection = get_kusto_connection(cluster_uri)
        client = connection.query_client

        # agents can send messy inputs
        query = query.strip()

        database = database or connection.default_database
        database = database.strip()

        result_set = client.execute(database, query, crp)
        return asdict(KustoFormatter.to_columnar(result_set))

    except Exception as e:
        error_msg = f"Error executing Kusto operation '{action_name}' (correlation ID: {correlation_id}): {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e


# NOTE: This is temporary. The intent is to not use environment variables for persistency.
def kusto_known_services() -> List[Dict[str, str]]:
    """
    Retrieves a list of all Kusto services known to the MCP.
    Could be null if no services are configured.

    :return: List of objects, {"service": str, "description": str, "default_database": str}
    """
    services = KustoConfig.get_known_services().values()
    return [asdict(service) for service in services]


def kusto_kql_query(query: str, cluster_uri: str, database: Optional[str] = None) -> Dict[str, Any]:
    """
    Executes a KQL query on the specified database. If no database is provided,
    it will use the default database.

    :param query: The KQL query to execute.
    :param cluster_uri: The URI of the Kusto cluster.
    :param database: Optional database name. If not provided, uses the default database.
    :return: The result of the query execution as a list of dictionaries (json).
    """
    return _execute(query, cluster_uri, database=database)


def kusto_tsql_query(query: str, cluster_uri: str, database: Optional[str] = None) -> Dict[str, Any]:
    """
    Executes a T-SQL query on the specified database. If no database is provided,
    it will use the default database.

    :param query: The T-SQL query to execute.
    :param cluster_uri: The URI of the Kusto cluster.
    :param database: Optional database name. If not provided, uses the default database.
    :return: The result of the query execution as a list of dictionaries (json).
    """
    client_request_properties = {"query_language": "sql"}
    return _execute(query, cluster_uri, database=database, client_request_properties=client_request_properties)


@destructive_operation
def kusto_command(command: str, cluster_uri: str, database: Optional[str] = None) -> Dict[str, Any]:
    """
    Executes a kusto management command on the specified database. If no database is provided,
    it will use the default database.

    :param command: The kusto management command to execute.
    :param cluster_uri: The URI of the Kusto cluster.
    :param database: Optional database name. If not provided, uses the default database.
    :return: The result of the command execution as a list of dictionaries (json).
    """
    return _execute(command, cluster_uri, database=database)


def kusto_list_databases(cluster_uri: str) -> Dict[str, Any]:
    """
    Retrieves a list of all databases in the Kusto cluster.

    :param cluster_uri: The URI of the Kusto cluster.
    :return: List of dictionaries containing database information.
    """
    return _execute(".show databases", cluster_uri)


def kusto_list_tables(cluster_uri: str, database: str) -> Dict[str, Any]:
    """
    Retrieves a list of all tables in the specified database.

    :param cluster_uri: The URI of the Kusto cluster.
    :param database: The name of the database to list tables from.
    :return: List of dictionaries containing table names, cslschema and a docstring.
    """
    return _execute(".show database cslschema | project-away DatabaseName", cluster_uri, database=database)


def kusto_get_entities_schema(cluster_uri: str, database: Optional[str] = None) -> Dict[str, Any]:
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


def kusto_get_table_schema(table_name: str, cluster_uri: str, database: Optional[str] = None) -> Dict[str, Any]:
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
) -> Dict[str, Any]:
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
) -> Dict[str, Any]:
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
) -> Dict[str, Any]:
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
) -> Dict[str, Any]:
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
) -> Dict[str, Any]:
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
