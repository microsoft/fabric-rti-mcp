from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from fabric_rti_mcp.eventstream import eventstream_service


def register_tools(mcp: FastMCP) -> None:
    """Register all Eventstream tools with the MCP server."""

    # Read-only tools (queries, list operations)
    mcp.add_tool(
        eventstream_service.eventstream_list,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )

    mcp.add_tool(
        eventstream_service.eventstream_get,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )

    mcp.add_tool(
        eventstream_service.eventstream_get_definition,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )

    # Destructive tools (create, update, delete operations)
    mcp.add_tool(
        eventstream_service.eventstream_create,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
    )

    mcp.add_tool(
        eventstream_service.eventstream_create_simple,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
    )

    mcp.add_tool(
        eventstream_service.eventstream_update,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
    )

    mcp.add_tool(
        eventstream_service.eventstream_delete,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
    )
