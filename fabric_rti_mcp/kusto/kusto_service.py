import inspect
import os
import uuid
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from azure.kusto.data import (
    ClientRequestProperties,
    KustoConnectionStringBuilder,
)

from fabric_rti_mcp import __version__  # type: ignore
from fabric_rti_mcp.kusto.kusto_connection import KustoConnection
from fabric_rti_mcp.kusto.kusto_response_formatter import format_results


class KustoConnectionWrapper(KustoConnection):
    def __init__(
        self, cluster_uri: str, default_database: str, description: Optional[str] = None
    ):
        super().__init__(cluster_uri)
        self.default_database = default_database
        self.description = description or cluster_uri


class KustoConnectionCache(defaultdict[str, KustoConnectionWrapper]):
    def __init__(self) -> None:
        super().__init__()
        default_cluster = os.getenv("KUSTO_SERVICE_URI")
        default_db = os.getenv(
            "KUSTO_SERVICE_DEFAULT_DB",
            KustoConnectionStringBuilder.DEFAULT_DATABASE_NAME,
        )
        if default_cluster:
            self.add_cluster_internal(default_cluster, default_db, "default cluster")

    def __missing__(self, key: str) -> KustoConnectionWrapper:
        client = KustoConnectionWrapper(key, DEFAULT_DB)
        self[key] = client
        return client

    def add_cluster_internal(
        self,
        cluster_uri: str,
        default_database: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        """Internal method to add a cluster during cache initialization."""
        cluster_uri = cluster_uri.strip()
        if cluster_uri.endswith("/"):
            cluster_uri = cluster_uri[:-1]

        if cluster_uri in self:
            return
        self[cluster_uri] = KustoConnectionWrapper(
            cluster_uri, default_database or DEFAULT_DB, description
        )


def add_kusto_cluster(
    cluster_uri: str,
    default_database: Optional[str] = None,
    description: Optional[str] = None,
) -> None:
    KUSTO_CONNECTION_CACHE.add_cluster_internal(
        cluster_uri, default_database, description
    )


def get_kusto_connection(cluster_uri: str) -> KustoConnectionWrapper:
    # clean uo the cluster URI since agents can send messy inputs
    cluster_uri = cluster_uri.strip()
    if cluster_uri.endswith("/"):
        cluster_uri = cluster_uri[:-1]
    return KUSTO_CONNECTION_CACHE[cluster_uri]


def _execute(
    query: str,
    cluster_uri: str,
    readonly_override: bool = False,
    database: Optional[str] = None,
) -> List[Dict[str, Any]]:
    caller_frame = inspect.currentframe().f_back  # type: ignore
    # Get the name of the caller function
    action = caller_frame.f_code.co_name  # type: ignore

    connection = get_kusto_connection(cluster_uri)
    client = connection.query_client

    # agents can send messy inputs
    query = query.strip()

    database = database or connection.default_database
    database = database.strip()

    crp: ClientRequestProperties = ClientRequestProperties()
    crp.application = f"fabric-rti-mcp{{{__version__}}}"  # type: ignore
    crp.client_request_id = f"KFRTI_MCP.{action}:{str(uuid.uuid4())}"  # type: ignore
    if action not in DESTRUCTIVE_TOOLS and not readonly_override:
        crp.set_option("request_readonly", True)
    result_set = client.execute(database, query, crp)
    return format_results(result_set)


def kusto_get_clusters() -> List[Tuple[str, str]]:
    """
    Retrieves a list of all Kusto clusters in the cache.

    :return: List of tuples containing cluster URI and description. When selecting a cluster,
             the URI must be used, the description is used only for additional information.
    """
    return [(uri, client.description) for uri, client in KUSTO_CONNECTION_CACHE.items()]


def kusto_connect(
    cluster_uri: str, default_database: str, description: Optional[str] = None
) -> None:
    """
    Connects to a Kusto cluster and adds it to the cache.

    :param cluster_uri: The URI of the Kusto cluster.
    :param default_database: The default database to use for queries on this cluster.
    :param description: Optional description for the cluster. Cannot be used to retrieve the cluster,
                       but can be used to provide additional information about the cluster.
    """
    add_kusto_cluster(
        cluster_uri, default_database=default_database, description=description
    )


def kusto_query(
    query: str, cluster_uri: str, database: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Executes a KQL query on the specified database. If no database is provided,
    it will use the default database.

    :param query: The KQL query to execute.
    :param cluster_uri: The URI of the Kusto cluster.
    :param database: Optional database name. If not provided, uses the default database.
    :return: The result of the query execution as a list of dictionaries (json).
    """
    return _execute(query, cluster_uri, database=database)


def kusto_command(
    command: str, cluster_uri: str, database: Optional[str] = None
) -> List[Dict[str, Any]]:
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


def kusto_get_entities_schema(
    cluster_uri: str, database: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retrieves schema information for all entities (tables, materialized views, functions)
    in the specified database. If no database is provided, uses the default database.

    :param cluster_uri: The URI of the Kusto cluster.
    :param database: Optional database name. If not provided, uses the default database.
    :return: List of dictionaries containing entity schema information.
    """
    return _execute(
        ".show databases entities with (showObfuscatedStrings=true) "
        f"| where DatabaseName == '{database or DEFAULT_DB}' "
        "| project EntityName, EntityType, Folder, DocString",
        cluster_uri,
        database=database,
    )


def kusto_get_table_schema(
    table_name: str, cluster_uri: str, database: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retrieves the schema information for a specific table in the specified database.
    If no database is provided, uses the default database.

    :param table_name: Name of the table to get schema for.
    :param cluster_uri: The URI of the Kusto cluster.
    :param database: Optional database name. If not provided, uses the default database.
    :return: List of dictionaries containing table schema information.
    """
    return _execute(
        f".show table {table_name} cslschema", cluster_uri, database=database
    )


def kusto_get_function_schema(
    function_name: str, cluster_uri: str, database: Optional[str] = None
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
    return _execute(
        f"{table_name} | sample {sample_size}", cluster_uri, database=database
    )


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


def kusto_get_shots(prompt: str,
    shots_table_name: str,
    cluster_uri: str,
    sample_size: int = 3,
    database: Optional[str] = None,
    embedding_endpoint: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieves shots that are most semantic similar to the supplied prompt from the specified shots table.

    :param prompt: The user prompt to find similar shots for.
    :param shots_table_name: Name of the table containing the shots. The table should have "EmbeddingText" (string) column
                             containing the natural language prompt, "AugmentedText" (string) column containing the respective KQL,
                             and "EmbeddingVector" (dynamic) column containing the embedding vector for the NL.
    :param cluster_uri: The URI of the Kusto cluster.
    :param sample_size: Number of most similar shots to retrieve. Defaults to 3.
    :param database: Optional database name. If not provided, uses the "AI" database or the default database.
    :param embedding_endpoint: Optional endpoint for the embedding model to use. 
                             If not provided, uses the AZ_OPENAI_EMBEDDING_ENDPOINT environment variable.
                             If no valid endpoint is set, this function should not be called.
    :return: List of dictionaries containing the shots records.
    """
    
    # Use provided endpoint, or fall back to environment variable, or use default
    endpoint = embedding_endpoint or DEFAULT_EMBEDDING_ENDPOINT

    kql_query = f"""
        let model_endpoint = '{endpoint}';
        let embedded_term = toscalar(evaluate ai_embeddings('{prompt}', model_endpoint));
        {shots_table_name}
        | extend similarity = series_cosine_similarity(embedded_term, EmbeddingVector)
        | top {sample_size} by similarity
        | project similarity, EmbeddingText, AugmentedText
    """

    return _execute(kql_query, cluster_uri, database=database)


def kusto_explain_kql_results(
    kql_query: str,
    completion_endpoint: Optional[str] = None,
) -> str:
    """
    Takes a KQL query and modifies it to add natural language explanations for each row using Kusto plugin completion.
    Each row is packed into JSON format using pack_all() and sent to the completion API for explanation.
    
    :param kql_query: The KQL query to modify for adding natural language explanations.
    :param completion_endpoint: Optional endpoint for the text completion model to use.
                               If not provided, uses the AZ_OPENAI_COMPLETION_ENDPOINT environment variable.
                               If no valid endpoint is set, this function should not be called.
    :return: Modified KQL query string that includes natural language descriptions for each row.
    """
    
    if not kql_query or not kql_query.strip():
        raise ValueError("KQL query cannot be empty")
    
    # Use provided endpoint, or fall back to environment variable, or use default
    endpoint = completion_endpoint or DEFAULT_COMPLETION_ENDPOINT
    
    if not endpoint:
        raise ValueError("No completion endpoint provided. Set AZ_OPENAI_COMPLETION_ENDPOINT environment variable or provide completion_endpoint parameter.")
    
    # Clean up the input query
    cleaned_query = kql_query.strip()
    
    # Create the modified query that adds natural language explanations
    modified_query = f"""let model_endpoint = '{endpoint}';
{cleaned_query}
| extend RowData = tostring(pack_all())
| extend NaturalLanguageDescription = toscalar(evaluate ai_completion(strcat('Explain this data row in natural language: ', RowData), model_endpoint))
| project-away RowData"""
    
    return modified_query


KUSTO_CONNECTION_CACHE: KustoConnectionCache = KustoConnectionCache()
DEFAULT_DB = KustoConnectionStringBuilder.DEFAULT_DATABASE_NAME
DEFAULT_EMBEDDING_ENDPOINT = os.getenv("AZ_OPENAI_EMBEDDING_ENDPOINT")
DEFAULT_COMPLETION_ENDPOINT = os.getenv("AZ_OPENAI_COMPLETION_ENDPOINT")

DESTRUCTIVE_TOOLS = {
    kusto_command.__name__,
    kusto_ingest_inline_into_table.__name__,
}
