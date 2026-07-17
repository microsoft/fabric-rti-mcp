from mcp.types import ToolAnnotations

from fabric_rti_mcp.services import AddTool
from fabric_rti_mcp.services.eventstream import eventstream_builder_tools, eventstream_service


def register_tools(add_tool: AddTool) -> None:
    """Register all Eventstream tools with the MCP server using ToolAnnotations pattern."""

    # Read-only tools (queries, list operations)
    add_tool(
        eventstream_service.eventstream_list,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
    add_tool(
        eventstream_service.eventstream_get,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
    add_tool(
        eventstream_service.eventstream_get_definition,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )

    # Destructive tools (create, update, delete operations)
    add_tool(
        eventstream_service.eventstream_create,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
    )
    add_tool(
        eventstream_service.eventstream_update,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
    )
    add_tool(
        eventstream_service.eventstream_delete,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
    )

    # Register builder tools
    eventstream_builder_tools.register_tools(add_tool)
