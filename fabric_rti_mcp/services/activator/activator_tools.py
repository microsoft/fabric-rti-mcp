from mcp.types import ToolAnnotations

from fabric_rti_mcp.services import AddTool
from fabric_rti_mcp.services.activator.activator_service import DEFAULT_ACTIVATOR_SERVICE


def register_tools(add_tool: AddTool) -> None:
    """Register all Activator tools with the MCP server."""

    # Read-only tools (queries, list operations)
    add_tool(
        DEFAULT_ACTIVATOR_SERVICE.activator_list_artifacts,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )

    # Destructive tools (create, update, delete operations)
    add_tool(
        DEFAULT_ACTIVATOR_SERVICE.activator_create_trigger,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
    )
