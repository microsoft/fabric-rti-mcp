from fastmcp import FastMCP
from fabric_rti_mcp.kusto import kusto_service


def register_tools(mcp: FastMCP) -> None:
    mcp.add_tool(kusto_service.kusto_get_clusters)
    mcp.add_tool(kusto_service.add_kusto_cluster)
    mcp.add_tool(kusto_service.kusto_query)
    mcp.add_tool(kusto_service.kusto_command)
    mcp.add_tool(kusto_service.kusto_list_databases)
    mcp.add_tool(kusto_service.kusto_list_tables)
    mcp.add_tool(kusto_service.kusto_get_entities_schema)
    mcp.add_tool(kusto_service.kusto_get_table_schema)
    mcp.add_tool(kusto_service.kusto_get_function_schema)
    mcp.add_tool(kusto_service.kusto_sample_table_data)
    mcp.add_tool(kusto_service.kusto_sample_function_data)
    mcp.add_tool(kusto_service.kusto_ingest_inline_into_table)
