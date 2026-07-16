from mcp.types import ToolAnnotations

from fabric_rti_mcp.services import AddTool
from fabric_rti_mcp.services.eventstream import eventstream_builder_service


def register_tools(add_tool: AddTool) -> None:
    # Session management tools (read-only for getting, potentially destructive for clearing)
    add_tool(
        eventstream_builder_service.eventstream_start_definition,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
    )
    add_tool(
        eventstream_builder_service.eventstream_get_current_definition,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
    add_tool(
        eventstream_builder_service.eventstream_clear_definition,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
    )

    # Data source tools (modify definition - potentially destructive)
    add_tool(
        eventstream_builder_service.eventstream_add_sample_data_source,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
    )
    add_tool(
        eventstream_builder_service.eventstream_add_custom_endpoint_source,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
    )

    # Stream tools (modify definition - potentially destructive)
    add_tool(
        eventstream_builder_service.eventstream_add_derived_stream,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
    )

    # Destination tools (modify definition - potentially destructive)
    add_tool(
        eventstream_builder_service.eventstream_add_eventhouse_destination,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
    )
    add_tool(
        eventstream_builder_service.eventstream_add_custom_endpoint_destination,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
    )

    # Validation and creation tools
    add_tool(
        eventstream_builder_service.eventstream_validate_definition,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
    add_tool(
        eventstream_builder_service.eventstream_create_from_definition,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
    )
    add_tool(
        eventstream_builder_service.eventstream_list_available_components,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
