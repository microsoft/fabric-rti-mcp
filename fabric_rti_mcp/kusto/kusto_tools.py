from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from fabric_rti_mcp.kusto import kusto_service


def register_tools(mcp: FastMCP) -> None:
    mcp.add_tool(
        kusto_service.kusto_known_services,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
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
        kusto_service.kusto_list_entities,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
    mcp.add_tool(
        kusto_service.kusto_describe_database,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
    mcp.add_tool(
        kusto_service.kusto_describe_database_entity,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
    mcp.add_tool(
        kusto_service.kusto_graph_query,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
    mcp.add_tool(
        kusto_service.kusto_sample_entity,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
    mcp.add_tool(
        kusto_service.kusto_ingest_inline_into_table,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
    )
    mcp.add_tool(
        kusto_service.kusto_get_shots,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
    )

    mcp.add_tool(
        kusto_service.anomaly_diffpatterns_query,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
