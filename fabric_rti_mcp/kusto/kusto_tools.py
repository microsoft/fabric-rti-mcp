from typing import Dict, List, Optional

from fastmcp import FastMCP

from fabric_rti_mcp.kusto import kusto_service


def register_tools(mcp: FastMCP) -> None:
    """Register all Kusto tools with the MCP server using modern decorator pattern."""

    @mcp.tool()
    def kusto_known_services() -> List[Dict]:
        return kusto_service.kusto_known_services()

    @mcp.tool()
    def kusto_query(query: str, cluster_uri: str, database: Optional[str] = None) -> List[Dict]:
        return kusto_service.kusto_query(query, cluster_uri, database)

    @mcp.tool()
    def kusto_command(command: str, cluster_uri: str, database: Optional[str] = None) -> List[Dict]:
        return kusto_service.kusto_command(command, cluster_uri, database)

    @mcp.tool()
    def kusto_list_databases(cluster_uri: str) -> List[Dict]:
        return kusto_service.kusto_list_databases(cluster_uri)

    @mcp.tool()
    def kusto_list_tables(cluster_uri: str, database: str) -> List[Dict]:
        return kusto_service.kusto_list_tables(cluster_uri, database)

    @mcp.tool()
    def kusto_get_entities_schema(cluster_uri: str, database: Optional[str] = None) -> List[Dict]:
        return kusto_service.kusto_get_entities_schema(cluster_uri, database)

    @mcp.tool()
    def kusto_get_table_schema(table_name: str, cluster_uri: str, database: Optional[str] = None) -> List[Dict]:
        return kusto_service.kusto_get_table_schema(table_name, cluster_uri, database)

    @mcp.tool()
    def kusto_get_function_schema(function_name: str, cluster_uri: str, database: Optional[str] = None) -> List[Dict]:
        return kusto_service.kusto_get_function_schema(function_name, cluster_uri, database)

    @mcp.tool()
    def kusto_sample_table_data(
        table_name: str, cluster_uri: str, sample_size: int = 10, database: Optional[str] = None
    ) -> List[Dict]:
        return kusto_service.kusto_sample_table_data(table_name, cluster_uri, sample_size, database)

    @mcp.tool()
    def kusto_sample_function_data(
        function_call_with_params: str, cluster_uri: str, sample_size: int = 10, database: Optional[str] = None
    ) -> List[Dict]:
        return kusto_service.kusto_sample_function_data(function_call_with_params, cluster_uri, sample_size, database)

    @mcp.tool()
    def kusto_ingest_inline_into_table(
        table_name: str, data_comma_separator: str, cluster_uri: str, database: Optional[str] = None
    ) -> List[Dict]:
        return kusto_service.kusto_ingest_inline_into_table(table_name, data_comma_separator, cluster_uri, database)

    @mcp.tool()
    def kusto_get_shots(
        prompt: str,
        shots_table_name: str,
        cluster_uri: str,
        sample_size: int = 3,
        database: Optional[str] = None,
        embedding_endpoint: Optional[str] = None,
    ) -> List[Dict]:
        return kusto_service.kusto_get_shots(
            prompt, shots_table_name, cluster_uri, sample_size, database, embedding_endpoint
        )
