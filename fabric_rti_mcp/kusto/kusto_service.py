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

def kusto_list_graph_models(
    cluster_uri: str, 
    database: Optional[str] = None, 
    show_all: bool = False,
    show_details: bool = False
) -> List[Dict[str, Any]]:
    """
    Lists all graph models in the database. By default, shows only the latest version of each model.
    If no database is provided, uses the default database.

    :param cluster_uri: The URI of the Kusto cluster.
    :param database: Optional database name. If not provided, uses the default database.
    :param show_all: If True, shows all versions of every graph model. If False, shows only the latest version.
    :param show_details: If True, returns detailed information including model definition and metadata.
    :return: List of dictionaries containing graph model information.
    """
    command = ".show graph_models"
    
    if show_details:
        command += " details"
    
    if show_all:
        if show_details:
            command += " with (showAll = true)"
        else:
            command += " with (showAll = true)"
    
    return _execute(command, cluster_uri, database=database)


def kusto_get_graph_model(
    graph_model_name: str,
    cluster_uri: str,
    database: Optional[str] = None,
    model_id: Optional[str] = None,
    show_details: bool = False
) -> List[Dict[str, Any]]:
    """
    Shows the details of a specific graph model, including its versions.
    If no database is provided, uses the default database.

    :param graph_model_name: The name of the graph model to show.
    :param cluster_uri: The URI of the Kusto cluster.
    :param database: Optional database name. If not provided, uses the default database.
    :param model_id: Optional specific version identifier (GUID) of the graph model. Use '*' to show all versions.
    :param show_details: If True, returns detailed information including model definition and metadata.
    :return: List of dictionaries containing graph model information.
    """
    command = f".show graph_model {graph_model_name}"
    
    if show_details:
        command += " details"
    elif model_id:
        command += f" with (id = \"{model_id}\")"
    
    return _execute(command, cluster_uri, database=database)


def kusto_sample_graph_nodes(
    graph_name: str,
    cluster_uri: str,
    sample_size: int = 50,
    database: Optional[str] = None,
    snapshot_name: Optional[str] = None,
    transient: bool = False,
) -> List[Dict[str, Any]]:
    """
    Retrieves a random sample of nodes from the specified graph.
    If no database is provided, uses the default database.

    :param graph_name: Name of the graph to sample nodes from.
    :param cluster_uri: The URI of the Kusto cluster.
    :param sample_size: Number of nodes to sample. Defaults to 50.
    :param database: Optional database name. If not provided, uses the default database.
    :param snapshot_name: Optional snapshot name to use. If not provided, uses the latest snapshot.
    :param transient: If True, creates a transient graph from the model. If False, uses snapshots.
    :return: List of dictionaries containing sampled node records.
    """
    # Build the graph function call
    if transient:
        graph_func = f'graph("{graph_name}", true)'
    elif snapshot_name:
        graph_func = f'graph("{graph_name}", "{snapshot_name}")'
    else:
        graph_func = f'graph("{graph_name}")'
    
    # Build the complete query
    query = f"{graph_func} | graph-to-table nodes | sample {sample_size}"
    
    return _execute(query, cluster_uri, database=database)


def kusto_sample_graph_edges(
    graph_name: str,
    cluster_uri: str,
    sample_size: int = 50,
    database: Optional[str] = None,
    snapshot_name: Optional[str] = None,
    transient: bool = False,
) -> List[Dict[str, Any]]:
    """
    Retrieves a random sample of edges from the specified graph.
    If no database is provided, uses the default database.

    :param graph_name: Name of the graph to sample edges from.
    :param cluster_uri: The URI of the Kusto cluster.
    :param sample_size: Number of edges to sample. Defaults to 50.
    :param database: Optional database name. If not provided, uses the default database.
    :param snapshot_name: Optional snapshot name to use. If not provided, uses the latest snapshot.
    :param transient: If True, creates a transient graph from the model. If False, uses snapshots.
    :return: List of dictionaries containing sampled edge records.
    """
    # Build the graph function call
    if transient:
        graph_func = f'graph("{graph_name}", true)'
    elif snapshot_name:
        graph_func = f'graph("{graph_name}", "{snapshot_name}")'
    else:
        graph_func = f'graph("{graph_name}")'
    
    # Build the complete query
    query = f"{graph_func} | graph-to-table edges | sample {sample_size}"
    
    return _execute(query, cluster_uri, database=database)


def kusto_sample_graph_nodes_and_edges(
    graph_name: str,
    cluster_uri: str,
    nodes_sample_size: int = 50,
    edges_sample_size: int = 50,
    database: Optional[str] = None,
    snapshot_name: Optional[str] = None,
    transient: bool = False,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Retrieves random samples of both nodes and edges from the specified graph.
    If no database is provided, uses the default database.

    :param graph_name: Name of the graph to sample from.
    :param cluster_uri: The URI of the Kusto cluster.
    :param nodes_sample_size: Number of nodes to sample. Defaults to 50.
    :param edges_sample_size: Number of edges to sample. Defaults to 50.
    :param database: Optional database name. If not provided, uses the default database.
    :param snapshot_name: Optional snapshot name to use. If not provided, uses the latest snapshot.
    :param transient: If True, creates a transient graph from the model. If False, uses snapshots.
    :return: Dictionary with 'nodes' and 'edges' keys containing sampled records.
    """
    # Sample nodes
    nodes_result = kusto_sample_graph_nodes(
        graph_name=graph_name,
        cluster_uri=cluster_uri,
        sample_size=nodes_sample_size,
        database=database,
        snapshot_name=snapshot_name,
        transient=transient,
    )
    
    # Sample edges
    edges_result = kusto_sample_graph_edges(
        graph_name=graph_name,
        cluster_uri=cluster_uri,
        sample_size=edges_sample_size,
        database=database,
        snapshot_name=snapshot_name,
        transient=transient,
    )
    
    return {
        "nodes": nodes_result,
        "edges": edges_result,
    }


def kusto_show_graph_snapshots(
    cluster_uri: str,
    database: Optional[str] = None,
    graph_model_name: Optional[str] = None,
    show_all: bool = False
) -> List[Dict[str, Any]]:
    """
    Lists all graph snapshots for a specific graph model or for all graph models.
    If no database is provided, uses the default database.

    :param cluster_uri: The URI of the Kusto cluster.
    :param database: Optional database name. If not provided, uses the default database.
    :param graph_model_name: Optional graph model name to filter snapshots. If not provided, shows snapshots for all models.
    :param show_all: If True, shows all snapshots. If False, shows only the latest snapshots.
    :return: List of dictionaries containing graph snapshot information.
    """
    if graph_model_name:
        command = f".show graph_snapshots {graph_model_name}"
    else:
        command = ".show graph_snapshots *"
    
    if show_all:
        command += " with (showAll = true)"
    
    return _execute(command, cluster_uri, database=database)


def kusto_show_graph_snapshot(
    graph_model_name: str,
    snapshot_name: str,
    cluster_uri: str,
    database: Optional[str] = None,
    show_details: bool = False
) -> List[Dict[str, Any]]:
    """
    Shows detailed information about a specific graph snapshot.
    If no database is provided, uses the default database.

    :param graph_model_name: The name of the graph model that the snapshot belongs to.
    :param snapshot_name: The name of the graph snapshot to show.
    :param cluster_uri: The URI of the Kusto cluster.
    :param database: Optional database name. If not provided, uses the default database.
    :param show_details: If True, returns detailed information including node count, edge count, and retention policy.
    :return: List of dictionaries containing graph snapshot information.
    """
    command = f".show graph_snapshot {graph_model_name}.{snapshot_name}"
    
    if show_details:
        command += " details"
    
    return _execute(command, cluster_uri, database=database)


def kusto_check_graph_snapshots_exist(
    graph_model_name: str,
    cluster_uri: str,
    database: Optional[str] = None,
) -> bool:
    """
    Checks if any snapshots exist for the specified graph model.
    
    :param graph_model_name: The name of the graph model to check.
    :param cluster_uri: The URI of the Kusto cluster.
    :param database: Optional database name. If not provided, uses the default database.
    :return: True if snapshots exist, False otherwise.
    """
    try:
        snapshots = kusto_show_graph_snapshots(
            cluster_uri=cluster_uri,
            database=database,
            graph_model_name=graph_model_name
        )
        return len(snapshots) > 0
    except Exception:
        # If we can't check snapshots, assume they don't exist and use transient
        return False


def kusto_sample_graph_nodes_smart(
    graph_name: str,
    cluster_uri: str,
    sample_size: int = 50,
    database: Optional[str] = None,
    snapshot_name: Optional[str] = None,
    prefer_snapshots: bool = True,
) -> List[Dict[str, Any]]:
    """
    Intelligently retrieves a random sample of nodes from the specified graph.
    Automatically uses snapshots if they exist, otherwise falls back to transient graphs.
    If no database is provided, uses the default database.

    :param graph_name: Name of the graph to sample nodes from.
    :param cluster_uri: The URI of the Kusto cluster.
    :param sample_size: Number of nodes to sample. Defaults to 50.
    :param database: Optional database name. If not provided, uses the default database.
    :param snapshot_name: Optional specific snapshot name to use. If provided, will use this snapshot.
    :param prefer_snapshots: If True, prefers snapshots over transient graphs when snapshots exist.
    :return: List of dictionaries containing sampled node records.
    """
    # If a specific snapshot is requested, use it
    if snapshot_name:
        return kusto_sample_graph_nodes(
            graph_name=graph_name,
            cluster_uri=cluster_uri,
            sample_size=sample_size,
            database=database,
            snapshot_name=snapshot_name,
            transient=False,
        )
    
    # Check if snapshots exist for the model
    if prefer_snapshots and kusto_check_graph_snapshots_exist(graph_name, cluster_uri, database):
        # Use snapshots (latest)
        return kusto_sample_graph_nodes(
            graph_name=graph_name,
            cluster_uri=cluster_uri,
            sample_size=sample_size,
            database=database,
            snapshot_name=None,
            transient=False,
        )
    else:
        # Use transient graph
        return kusto_sample_graph_nodes(
            graph_name=graph_name,
            cluster_uri=cluster_uri,
            sample_size=sample_size,
            database=database,
            snapshot_name=None,
            transient=True,
        )


def kusto_sample_graph_edges_smart(
    graph_name: str,
    cluster_uri: str,
    sample_size: int = 50,
    database: Optional[str] = None,
    snapshot_name: Optional[str] = None,
    prefer_snapshots: bool = True,
) -> List[Dict[str, Any]]:
    """
    Intelligently retrieves a random sample of edges from the specified graph.
    Automatically uses snapshots if they exist, otherwise falls back to transient graphs.
    If no database is provided, uses the default database.

    :param graph_name: Name of the graph to sample edges from.
    :param cluster_uri: The URI of the Kusto cluster.
    :param sample_size: Number of edges to sample. Defaults to 50.
    :param database: Optional database name. If not provided, uses the default database.
    :param snapshot_name: Optional specific snapshot name to use. If provided, will use this snapshot.
    :param prefer_snapshots: If True, prefers snapshots over transient graphs when snapshots exist.
    :return: List of dictionaries containing sampled edge records.
    """
    # If a specific snapshot is requested, use it
    if snapshot_name:
        return kusto_sample_graph_edges(
            graph_name=graph_name,
            cluster_uri=cluster_uri,
            sample_size=sample_size,
            database=database,
            snapshot_name=snapshot_name,
            transient=False,
        )
    
    # Check if snapshots exist for the model
    if prefer_snapshots and kusto_check_graph_snapshots_exist(graph_name, cluster_uri, database):
        # Use snapshots (latest)
        return kusto_sample_graph_edges(
            graph_name=graph_name,
            cluster_uri=cluster_uri,
            sample_size=sample_size,
            database=database,
            snapshot_name=None,
            transient=False,
        )
    else:
        # Use transient graph
        return kusto_sample_graph_edges(
            graph_name=graph_name,
            cluster_uri=cluster_uri,
            sample_size=sample_size,
            database=database,
            snapshot_name=None,
            transient=True,
        )

def kusto_query_graph_smart(
    graph_name: str,
    query_suffix: str,
    cluster_uri: str,
    database: Optional[str] = None,
    snapshot_name: Optional[str] = None,
    prefer_snapshots: bool = True,
) -> List[Dict[str, Any]]:
    """
    Intelligently executes a graph query using snapshots if they exist, otherwise falls back to transient graphs.
    If no database is provided, uses the default database.

    :param graph_name: Name of the graph to query.
    :param query_suffix: The KQL query to execute after the graph() function. Must include proper project clause for graph-match queries.
    :param cluster_uri: The URI of the Kusto cluster.
    :param database: Optional database name. If not provided, uses the default database.
    :param snapshot_name: Optional specific snapshot name to use. If provided, will use this snapshot.
    :param prefer_snapshots: If True, prefers snapshots over transient graphs when snapshots exist.
    :return: List of dictionaries containing query results.
    
    Examples:
    
    # Basic node counting with graph-match (MUST include project clause):
    kusto_query_graph_smart(
        "MyGraph", 
        "| graph-match (node) project labels=labels(node) | mv-expand label = labels | summarize count() by tostring(label)",
        cluster_uri
    )
    
    # Complex relationship matching:
    kusto_query_graph_smart(
        "MyGraph", 
        "| graph-match (house)-[relationship]->(character) where labels(house) has 'House' and labels(character) has 'Character' project house.name, character.name | limit 10",
        cluster_uri
    )
    
    # Variable length path matching:
    kusto_query_graph_smart(
        "MyGraph", 
        "| graph-match (source)-[path*1..3]->(destination) project source, destination, path | take 100",
        cluster_uri
    )
    
    # Advanced security analysis - compromised user to sensitive resource:
    kusto_query_graph_smart(
        "SecurityGraph",
        '''| graph-match (compromisedUser)-->(initialDevice)-[hop*0..3]->(sensitiveResource)
        where 
            // Connect with our identity analysis
            compromisedUser.id in (CompromisedAccounts)
            // Connect with our asset analysis
            and sensitiveResource.id in (SensitiveResources)
        project
            CompromisedUser = compromisedUser,
            InitialDevice = initialDevice,
            SensitiveResourceAccessed = sensitiveResource,
            Path = hop,
            // Report if user has legitimate permissions (additional context)
            HasLegitimateAccess = compromisedUser in 
                (PermissionChains | where ResourceId == sensitiveResource | project UserId)''',
        cluster_uri
    )
    
    # Complex permission analysis with group membership chains:
    kusto_query_graph_smart(
        "IdentityGraph",
        '''| graph-match (resource)<-[authorized_on*1..4]-(group)-[hasMember*1..255]->(user)
        where user.NodeId == interestingUser and user.NodeType == "User" and hasMember.EdgeType == "has_member" and group.NodeType == "Group" and
            authorized_on.EdgeType in ("authorized_on", "contains_resource")
        project Username=user.NodeId, userFQDN=user.FQDN, resourceTenantId=resource.TenantId, resourceType=resource.NodeType, resourceName=resource.NodeId''',
        cluster_uri
    )
    
     # Complex permission analysis with group membership chains:
    kusto_query_graph_smart(
        "IdentityGraph",
        '''| graph-match (resource)<-[authorized_on*1..4]-(group)-[hasMember*1..255]->(user)
        where user.NodeId == interestingUser and user.NodeType == "User" and hasMember.EdgeType == "has_member" and group.NodeType == "Group" and
            authorized_on.EdgeType in ("authorized_on", "contains_resource")
        project Username=user.NodeId, userFQDN=user.FQDN, resourceTenantId=resource.TenantId, resourceType=resource.NodeType, resourceName=resource.NodeId''',
        cluster_uri
    )
    
	# Complex pattern with variable length edges amd filtering
    kusto_query_graph_smart("NetworkGraph", 
    		"| graph-match (source)-[path*1..5]->(destination) where_clause='all(path, bandwidth > 100) project user.name, resource.name, path_length = array_length(access) | limit 10",
            cluster_uri
	)
    
    Important: 
    - graph-match queries MUST include a project clause
    - Use graph-to-table for simple node/edge exploration
    - Use labels() function in WHERE clauses of graph-match, not in the path pattern
    """
    # Build the graph function call
    if snapshot_name:
        # Use specific snapshot
        graph_func = f'graph("{graph_name}", "{snapshot_name}")'
    elif prefer_snapshots and kusto_check_graph_snapshots_exist(graph_name, cluster_uri, database):
        # Use latest snapshot
        graph_func = f'graph("{graph_name}")'
    else:
        # Use transient graph
        graph_func = f'graph("{graph_name}", true)'
    
    # Build the complete query
    query = f"{graph_func} {query_suffix}"
    
    return _execute(query, cluster_uri, database=database)


def kusto_graph_match(
    graph_name: str,
    pattern: str,
    cluster_uri: str,
    project_clause: str,
    database: Optional[str] = None,
    snapshot_name: Optional[str] = None,
    transient: bool = False,
    where_clause: Optional[str] = None,
    cycles: Optional[str] = None,
    take: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Executes a graph-match query on the specified graph to find patterns in nodes and edges.
    This function enables pattern matching in graph data, including filtering by labels and using
    graph functions like all(), any(), labels(), etc.

    :param graph_name: Name of the graph to query.
    :param pattern: Graph pattern to match (e.g., "(user)-[permission]->(resource)")
    :param cluster_uri: The URI of the Kusto cluster.
    :param project_clause: PROJECT clause for output formatting (without the 'project' keyword).
    :param database: Optional database name. If not provided, uses the default database.
    :param snapshot_name: Optional snapshot name to use. If not provided, uses the latest snapshot.
    :param transient: If True, creates a transient graph from the model. If False, uses snapshots.
    :param where_clause: Optional WHERE clause for filtering matches (without the 'where' keyword).
    :param cycles: Optional cycle handling parameter (currently not used in graph-match syntax).
    :param take: Optional number of results to return (uses 'take' operator).
    :return: List of dictionaries containing matched patterns.
    
    Examples:
    
    # Basic pattern matching
    kusto_graph_match("SecurityGraph", "(user)-[permission]->(resource)", 
                     cluster_uri, "user.name, resource.name")
    
    # With WHERE clause
    kusto_graph_match("SecurityGraph", "(alice)<-[reports*1..5]-(employee)", 
                     cluster_uri, "employee = employee.name, age = employee.age",
                     where_clause='alice.name == "Alice" and employee.age < 30')
    
    # Complex pattern with variable length edges
    kusto_graph_match("NetworkGraph", "(source)-[path*1..5]->(destination)", 
                     cluster_uri, "source.name, destination.name, path_length = array_length(path)",
                     where_clause='all(path, bandwidth > 100)')
    
    # Using graph functions
    kusto_graph_match("SecurityGraph", "(user)-[access*1..3]->(resource)", 
                     cluster_uri, "user.name, resource.name, path_length = array_length(access)",
                     where_clause='labels(user) has "Employee"')
    """
    # Build the graph function call
    if transient:
        graph_func = f'graph("{graph_name}", true)'
    elif snapshot_name:
        graph_func = f'graph("{graph_name}", "{snapshot_name}")'
    else:
        graph_func = f'graph("{graph_name}")'
    
    # Build the graph-match query components
    graph_match_parts = ["| graph-match", pattern]
    
    # Add optional WHERE clause (part of graph-match, no pipe)
    if where_clause:
        graph_match_parts.append(f"where {where_clause}")
    
    # Add mandatory PROJECT clause (part of graph-match, no pipe) - comes after WHERE
    graph_match_parts.append(f"project {project_clause}")
    
    # Combine graph function with graph-match (join with newlines and spaces for readability)
    graph_match_query = "\n   ".join(graph_match_parts)
    query_parts = [graph_func, graph_match_query]
    
    # Add optional TAKE (this goes after graph-match with pipe)
    if take:
        query_parts.append(f"| take {take}")
    
    query = " ".join(query_parts)
    
    return _execute(query, cluster_uri, database=database)



KUSTO_CONNECTION_CACHE: KustoConnectionCache = KustoConnectionCache()
DEFAULT_DB = KustoConnectionStringBuilder.DEFAULT_DATABASE_NAME

DESTRUCTIVE_TOOLS = {
    kusto_command.__name__,
    kusto_ingest_inline_into_table.__name__,
}
