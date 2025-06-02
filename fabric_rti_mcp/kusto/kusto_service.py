import inspect
import uuid
from collections import defaultdict
from typing import Any, Dict, List, Optional

from azure.kusto.data import (
    ClientRequestProperties,
    KustoClient,
    KustoConnectionStringBuilder,
)

from fabric_rti_mcp import __version__  # type: ignore
from fabric_rti_mcp.kusto.kusto_connection import KustoConnection
from fabric_rti_mcp.kusto.kusto_response_formatter import format_results


class KustoConnectionCache(defaultdict[str, KustoConnection]):
    def __missing__(self, key: str) -> KustoConnection:
        client = KustoConnection(key)
        self[key] = client
        return client


KUSTO_CONNECTION_CACHE: Dict[str, KustoConnection] = KustoConnectionCache()
DEFAULT_DB = KustoConnectionStringBuilder.DEFAULT_DATABASE_NAME


def get_kusto_connection(cluster_uri: str) -> KustoConnection:
    # clean uo the cluster URI since agents can send messy inputs
    cluster_uri = cluster_uri.strip()
    if cluster_uri.endswith("/"):
        cluster_uri = cluster_uri[:-1]
    return KUSTO_CONNECTION_CACHE[cluster_uri]


def get_kusto_query_client(cluster_uri: str) -> KustoClient:
    return get_kusto_connection(cluster_uri).query_client


def _execute(
    query: str,
    cluster_uri: str,
    readonly_override: bool = False,
    database: Optional[str] = None,
) -> List[Dict[str, Any]]:
    caller_frame = inspect.currentframe().f_back  # type: ignore
    # Get the name of the caller function
    action = caller_frame.f_code.co_name  # type: ignore

    database = database or DEFAULT_DB
    # agents can send messy inputs
    database = database.strip()
    query = query.strip()

    client = get_kusto_query_client(cluster_uri)
    crp: ClientRequestProperties = ClientRequestProperties()
    crp.application = f"fabric-rti-mcp{{{__version__}}}"  # type: ignore
    crp.client_request_id = f"KFRTI_MCP.{action}:{str(uuid.uuid4())}"  # type: ignore
    if action not in DESTRUCTIVE_TOOLS and not readonly_override:
        crp.set_option("request_readonly", True)
    result_set = client.execute(database, query, crp)
    return format_results(result_set)


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


DESTRUCTIVE_TOOLS = {
    kusto_command.__name__,
    kusto_ingest_inline_into_table.__name__,
}
