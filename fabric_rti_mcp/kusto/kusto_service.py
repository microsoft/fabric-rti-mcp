from __future__ import annotations

import functools
import inspect
import uuid
from dataclasses import asdict
from typing import Any, Callable, Dict, List, Optional, TypeVar

from azure.kusto.data import ClientRequestProperties, KustoConnectionStringBuilder

from fabric_rti_mcp import __version__  # type: ignore
from fabric_rti_mcp.common import logger
from fabric_rti_mcp.kusto.kusto_config import KustoConfig
from fabric_rti_mcp.kusto.kusto_connection import KustoConnection, sanitize_uri
from fabric_rti_mcp.kusto.kusto_formatter import KustoFormatter


def canonical_entity_type(entity_type: str) -> str:
    """
    Converts various entity type inputs to a canonical form.
    For example, "materialized-view" and "materialized view" both map to "materialized-view".
    """
    entity_type = entity_type.strip().lower()
    if entity_type in ["materialized view", "materialized-view", "mv"]:
        return "materialized-view"
    elif entity_type in ["table", "tables"]:
        return "table"
    elif entity_type in ["function", "functions"]:
        return "function"
    elif entity_type in ["graph", "graphs", "graph model", "graph-model"]:
        return "graph"
    elif entity_type in ["database", "databases"]:
        return "database"
    else:
        raise ValueError(
            f"Unknown entity type '{entity_type}'. "
            "Supported types: table, materialized-view, function, graph, database."
        )


CONFIG = KustoConfig.from_env()
_DEFAULT_DB_NAME = (
    CONFIG.default_service.default_database
    if CONFIG.default_service
    else KustoConnectionStringBuilder.DEFAULT_DATABASE_NAME
)


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
    action: str, is_destructive: bool, ignore_readonly: bool, client_request_properties: Optional[Dict[str, Any]] = None
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

    # Apply any additional client request properties provided by the user
    # User properties can override global settings
    if client_request_properties:
        for key, value in client_request_properties.items():
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

    # Generate correlation ID for tracing and merge with any custom properties
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


def kusto_query(
    query: str,
    cluster_uri: str,
    database: Optional[str] = None,
    client_request_properties: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Executes a KQL query on the specified database. If no database is provided,
    it will use the default database.

    :param query: The KQL query to execute.
    :param cluster_uri: The URI of the Kusto cluster.
    :param database: Optional database name. If not provided, uses the default database.
    :param client_request_properties: Optional dictionary of additional client request properties.
    :return: The result of the query execution as a list of dictionaries (json).
    """
    return _execute(query, cluster_uri, database=database, client_request_properties=client_request_properties)


def kusto_graph_query(
    graph_name: str,
    query: str,
    cluster_uri: str,
    database: str | None,
    client_request_properties: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Intelligently executes a graph query using snapshots if they exist,
    otherwise falls back to transient graphs.
    If no database is provided, uses the default database.

    :param graph_name: Name of the graph to query.
    :param query: The KQL query to execute after the graph() function.
    Must include proper project clause for graph-match queries.
    :param cluster_uri: The URI of the Kusto cluster.
    :param database: Optional database name. If not provided, uses the default database.
    :param client_request_properties: Optional dictionary of additional client request properties.
    :return: List of dictionaries containing query results.

    Critical:
    * Graph queries must have a graph-match clause and a projection clause.
    Optionally they may contain a where clause.
    * Graph entities are only accessible in the graph-match scope.
        When leaving that scope (sub-sequent '|'), the data is treated as a table,
        and graph-specific functions (like labels()) will not be available.
    * Always prefer expressing everything with graph patterns.
      Avoid using graph-to-table operator unless you have no other way around it.
    * There is no id() function on graph entities. If you need a unique identifier,
      make sure to check the schema and use an appropriate property.
    * There is no `type` property on graph entities.
      Use `labels()` function to get the list of labels for a node or edge.
    * Properties that are used outside the graph-match context are renamed to `_` instead of `.`.
      For example, `node.name` becomes `node_name`.
    * For variable length paths, you can use `all` or `any` to enforce conditions on all/any edges
      in variable path length elements (e.g. `()-[e*1..3]->() where all(e, labels() has 'Label')`).

    Examples:

    # Basic node counting with graph-match (MUST include project clause):
    kusto_graph_query(
        "MyGraph",
        "| graph-match (node) project labels=labels(node)
         | mv-expand label = labels
         | summarize count() by tostring(label)",
        cluster_uri
    )

    # Relationship matching:
    kusto_graph_query(
        "MyGraph",
        "| graph-match (house)-[relationship]->(character)
            where labels(house) has 'House' and labels(character) has 'Character'
            project house.name, character.firstName, character.lastName
        | project house_name=house_name, character_full_name=character_firstName + ' ' + character_lastName
        | limit 10",
        cluster_uri
    )

    # Variable length path matching:
    kusto_graph_query(
        "MyGraph",
        "| graph-match (source)-[path*1..3]->(m)-[e]->(target)
            where all(path, labels() has 'Label')
            project source, destination, path, m, e, target
        | take 100",
        cluster_uri
    )
    """
    query = (
        f"graph('{graph_name}') {query}"  # todo: this should properly choose between graph() and make-graph operator
    )
    return _execute(query, cluster_uri, database=database, client_request_properties=client_request_properties)


@destructive_operation
def kusto_command(
    command: str,
    cluster_uri: str,
    database: Optional[str] = None,
    client_request_properties: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Executes a kusto management command on the specified database. If no database is provided,
    it will use the default database.

    :param command: The kusto management command to execute.
    :param cluster_uri: The URI of the Kusto cluster.
    :param database: Optional database name. If not provided, uses the default database.
    :param client_request_properties: Optional dictionary of additional client request properties.
    :return: The result of the command execution as a list of dictionaries (json).
    """
    return _execute(command, cluster_uri, database=database, client_request_properties=client_request_properties)


def kusto_list_entities(
    cluster_uri: str,
    entity_type: str,
    database: Optional[str] = None,
    client_request_properties: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Retrieves a list of all entities (databases, tables, materialized views, functions, graphs) in the Kusto cluster.

    :param entity_type: Type of entities to list: "databases", "tables", "materialized-views", "functions", "graphs".
    :param database: The name of the database to list entities from.
    Required for all types except "databases" (which are top-level).
    :param cluster_uri: The URI of the Kusto cluster.
    :param client_request_properties: Optional dictionary of additional client request properties.

    :return: List of dictionaries containing entity information.
    """

    entity_type = canonical_entity_type(entity_type)
    if entity_type == "database":
        return _execute(
            ".show databases | project DatabaseName, DatabaseAccessMode, PrettyName, DatabaseId",
            cluster_uri,
            database=KustoConnectionStringBuilder.DEFAULT_DATABASE_NAME,
            client_request_properties=client_request_properties,
        )
    elif entity_type == "table":
        return _execute(
            ".show tables | project-away DatabaseName",
            cluster_uri,
            database=database,
            client_request_properties=client_request_properties,
        )
    elif entity_type == "materialized-view":
        return _execute(
            ".show materialized-views",
            cluster_uri,
            database=database,
            client_request_properties=client_request_properties,
        )
    elif entity_type == "function":
        return _execute(
            ".show functions", cluster_uri, database=database, client_request_properties=client_request_properties
        )
    elif entity_type == "graph":
        return _execute(
            ".show graph_models | project-away DatabaseName",
            cluster_uri,
            database=database,
            client_request_properties=client_request_properties,
        )
    return {}


def kusto_describe_database(
    cluster_uri: str, database: str | None, client_request_properties: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Retrieves schema information for all entities (tables, materialized views, functions, graphs)
    in the specified database.

    In most cases, it would be useful to call kusto_sample_entity() to see *actual* data samples,
    since schema information alone may not provide a complete picture of the data (e.g. dynamic columns, etc...)

    :param cluster_uri: The URI of the Kusto cluster.
    :param database: The name of the database to get schema for.
    :param client_request_properties: Optional dictionary of additional client request properties.
    :return: List of dictionaries containing entity schema information.
    """
    return _execute(
        ".show databases entities with (showObfuscatedStrings=true) "
        f"| where DatabaseName == '{database or _DEFAULT_DB_NAME}' "
        "| project EntityName, EntityType, Folder, DocString, CslInputSchema, Content, CslOutputSchema",
        cluster_uri,
        database=database,
        client_request_properties=client_request_properties,
    )


def kusto_describe_database_entity(
    entity_name: str,
    entity_type: str,
    cluster_uri: str,
    database: Optional[str] = None,
    client_request_properties: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Retrieves the schema information for a specific entity (table, materialized view, function, graph)
    in the specified database. If no database is provided, uses the default database.

    :param entity_name: Name of the entity to get schema for.
    :param entity_type: Type of the entity (table, materialized view, function, graph).
    :param cluster_uri: The URI of the Kusto cluster.
    :param database: Optional database name. If not provided, uses the default database.
    :param client_request_properties: Optional dictionary of additional client request properties.
    :return: List of dictionaries containing entity schema information.
    """

    entity_type = canonical_entity_type(entity_type)
    if entity_type.lower() == "table":
        return _execute(
            f".show table {entity_name} cslschema",
            cluster_uri,
            database=database,
            client_request_properties=client_request_properties,
        )
    elif entity_type.lower() == "function":
        return _execute(
            f".show function {entity_name}",
            cluster_uri,
            database=database,
            client_request_properties=client_request_properties,
        )
    elif entity_type.lower() == "materialized-view":
        return _execute(
            f".show materialized-view {entity_name} "
            "| project Name, SourceTable, Query, LastRun, LastRunResult, IsHealthy, IsEnabled, DocString",
            cluster_uri,
            database=database,
            client_request_properties=client_request_properties,
        )
    elif entity_type.lower() == "graph":
        return _execute(
            f".show graph_model {entity_name} details | project Name, Model",
            cluster_uri,
            database=database,
            client_request_properties=client_request_properties,
        )
    # Add more entity types as needed
    return {}


def kusto_sample_entity(
    entity_name: str,
    entity_type: str,
    cluster_uri: str,
    sample_size: int = 10,
    database: Optional[str] = None,
    client_request_properties: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Retrieves a data sample from the specified entity.
    If no database is provided, uses the default database.

    :param entity_name: Name of the entity to sample data from.
    :param entity_type: Type of the entity (table, materialized-view, function, graph).
    :param cluster_uri: The URI of the Kusto cluster.
    :param sample_size: Number of records to sample. Defaults to 10.
    :param database: Optional database name. If not provided, uses the default database.
    :param client_request_properties: Optional dictionary of additional client request properties.
    :return: List of dictionaries containing sampled records.
    """
    entity_type = canonical_entity_type(entity_type)
    if entity_type.lower() in ["table", "materialized-view", "function"]:
        return _execute(
            f"{entity_name} | sample {sample_size}",
            cluster_uri,
            database=database,
            client_request_properties=client_request_properties,
        )
    if entity_type.lower() == "graph":
        # TODO: handle transient graphs properly
        sample_size_node = max(1, sample_size // 2)  # at least 5 of each
        sample_size_edge = max(1, sample_size - sample_size_node)  # at least 5 of each
        return _execute(
            f"""let NodeSample = graph('{entity_name}')
| graph-to-table nodes
| take {sample_size_node}
| project PackedEntity=pack_all(), EntityType='Node';
let EdgeSample = graph('{entity_name}')
| graph-to-table edges
| take {sample_size_edge}
| project PackedEntity=pack_all(), EntityType='Edge';
NodeSample
| union EdgeSample
""",
            cluster_uri,
            database=database,
            client_request_properties=client_request_properties,
        )

    raise ValueError(f"Sampling not supported for entity type '{entity_type}'.")


@destructive_operation
def kusto_ingest_inline_into_table(
    table_name: str,
    data_comma_separator: str,
    cluster_uri: str,
    database: Optional[str] = None,
    client_request_properties: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Ingests inline CSV data into a specified table. The data should be provided as a comma-separated string.
    If no database is provided, uses the default database.

    :param table_name: Name of the table to ingest data into.
    :param data_comma_separator: Comma-separated data string to ingest.
    :param cluster_uri: The URI of the Kusto cluster.
    :param database: Optional database name. If not provided, uses the default database.
    :param client_request_properties: Optional dictionary of additional client request properties.
    :return: List of dictionaries containing the ingestion result.
    """
    return _execute(
        f".ingest inline into table {table_name} <| {data_comma_separator}",
        cluster_uri,
        database=database,
        client_request_properties=client_request_properties,
    )


def kusto_get_shots(
    prompt: str,
    shots_table_name: str,
    cluster_uri: str,
    sample_size: int = 3,
    database: Optional[str] = None,
    embedding_endpoint: Optional[str] = None,
    client_request_properties: Optional[Dict[str, Any]] = None,
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
    :param client_request_properties: Optional dictionary of additional client request properties.
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

    return _execute(kql_query, cluster_uri, database=database, client_request_properties=client_request_properties)

def anomaly_diffpatterns_query(
    cluster_uri: str,
    table_name: str,
    first_set_condition: str,
    second_set_condition: str,
    threshold: str = "~", # "~" means use default (0.05). Otherwise a string representing a float between 0.015 and 1.0
    project_columns: Optional[List[str]] = None,  # New optional parameter
    database: Optional[str] = None,
    client_request_properties: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Executes a KQL query that compares first data set vs. second data set patterns
    using the diffpatterns operator.

    :param cluster_uri: The URI of the Kusto cluster.
    :param table_name: The Kusto table to query.    
    :param first_set_condition: A KQL filter expression defining the first dataset 
        (e.g., "Timestamp between (datetime(2025-01-01) .. datetime(2025-01-07))").
    :param second_set_condition: A KQL filter expression defining the second dataset
        (e.g., "Timestamp between (datetime(2025-02-01) .. datetime(2025-02-07))").
    :param threshold: A real between 0.015–1.0, or "~" to use the default (0.05). 
        Controls the sensitivity of the diffpatterns operator.
    :param project_columns: Optional list of column names to include in the query. 
        If provided, only these columns plus the extended 'AB' column are used in diffpatterns.        
    :param database: Optional database name. If not provided, uses the default database.
    :param client_request_properties: Optional dictionary of additional client request properties.
    :return: The result of the query execution as a list of dictionaries (json).
    """

    if threshold == "~":
        threshold = "'~'"

    query = f"""
    {table_name}
    | where ({first_set_condition}) or ({second_set_condition})
    | extend AB = iff({second_set_condition}, 'Anomaly', 'Baseline')
    """

    if project_columns:
        # Ensure 'AB' is always included
        columns = ", ".join(project_columns + ["AB"])
        query += f"\n| project {columns}"

    query += f"\n| evaluate diffpatterns(AB, 'Anomaly', 'Baseline', '~', {threshold})"

    return _execute(
        query,
        cluster_uri,
        database=database,
        client_request_properties=client_request_properties,
    )
