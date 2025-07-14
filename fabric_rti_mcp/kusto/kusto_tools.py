from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from fabric_rti_mcp.kusto import kusto_service


def register_tools(mcp: FastMCP) -> None:
    mcp.add_tool(
        kusto_service.kusto_get_clusters,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
    mcp.add_tool(
        kusto_service.add_kusto_cluster,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
    )
    mcp.add_tool(
        kusto_service.kusto_query,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
    mcp.add_tool(
        kusto_service.kusto_command,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
    )
    mcp.add_tool(
        kusto_service.kusto_list_databases,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
    mcp.add_tool(
        kusto_service.kusto_list_tables,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
    mcp.add_tool(
        kusto_service.kusto_get_entities_schema,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
    mcp.add_tool(
        kusto_service.kusto_get_table_schema,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
    mcp.add_tool(
        kusto_service.kusto_get_function_schema,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
    mcp.add_tool(
        kusto_service.kusto_sample_table_data,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
    mcp.add_tool(
        kusto_service.kusto_sample_function_data,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
    mcp.add_tool(
        kusto_service.kusto_ingest_inline_into_table,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
    )
    mcp.add_tool(
        kusto_service.kusto_list_graph_models,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
    mcp.add_tool(
        kusto_service.kusto_get_graph_model,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
    mcp.add_tool(
        kusto_service.kusto_show_graph_snapshots,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
    mcp.add_tool(
        kusto_service.kusto_show_graph_snapshot,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
    mcp.add_tool(
        kusto_service.kusto_sample_graph_nodes_smart,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
    mcp.add_tool(
        kusto_service.kusto_sample_graph_edges_smart,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
    mcp.add_tool(
        kusto_service.kusto_query_graph_smart,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
    mcp.add_tool(
        kusto_service.kusto_graph_match,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
