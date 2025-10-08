from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from fabric_rti_mcp.activator.activator_service import DEFAULT_ACTIVATOR_SERVICE


def register_tools(mcp: FastMCP) -> None:
    """Register all Activator tools with the MCP server."""

    # Read-only tools (queries, list operations)
    mcp.add_tool(
        DEFAULT_ACTIVATOR_SERVICE.activator_list_artifacts,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )

    # Destructive tools (create, update, delete operations)
    mcp.add_tool(
        DEFAULT_ACTIVATOR_SERVICE.activator_create_trigger,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
    )
