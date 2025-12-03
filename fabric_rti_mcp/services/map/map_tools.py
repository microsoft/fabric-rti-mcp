from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from fabric_rti_mcp.services.map import map_service


def register_tools(mcp: FastMCP) -> None:
    """Register all Map tools with the MCP server."""

    # Read-only tools (queries, list operations)
    mcp.add_tool(
        map_service.map_list,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )

    mcp.add_tool(
        map_service.map_get,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )

    mcp.add_tool(
        map_service.map_get_definition,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )

    # Destructive tools (create, update, delete operations)
    mcp.add_tool(
        map_service.map_create,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
    )

    mcp.add_tool(
        map_service.map_update_definition,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
    )

    mcp.add_tool(
        map_service.map_update,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
    )

    mcp.add_tool(
        map_service.map_delete,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
    )
