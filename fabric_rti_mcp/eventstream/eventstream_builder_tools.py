"""
Eventstream Builder Tools Registration for Microsoft Fabric RTI MCP
Registers all builder-related tools with the MCP server
"""

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from fabric_rti_mcp.eventstream import eventstream_builder_service


def register_tools(mcp: FastMCP) -> None:
    """Register all Eventstream Builder tools with the MCP server."""
    
    # Session management tools (non-destructive)
    mcp.add_tool(
        eventstream_builder_service.eventstream_start_definition,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
    )
    
    mcp.add_tool(
        eventstream_builder_service.eventstream_get_current_definition,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
    
    mcp.add_tool(
        eventstream_builder_service.eventstream_clear_definition,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
    )
    
    mcp.add_tool(
        eventstream_builder_service.eventstream_validate_definition,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
    
    mcp.add_tool(
        eventstream_builder_service.eventstream_list_available_components,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
    
    # Source management tools (non-destructive definition building)
    mcp.add_tool(
        eventstream_builder_service.eventstream_add_sample_data_source,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
    )
    
    mcp.add_tool(
        eventstream_builder_service.eventstream_add_custom_endpoint_source,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
    )
    
    # Stream management tools (non-destructive definition building)
    mcp.add_tool(
        eventstream_builder_service.eventstream_add_default_stream,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
    )
    
    mcp.add_tool(
        eventstream_builder_service.eventstream_add_derived_stream,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
    )
    
    # Destination management tools (non-destructive definition building)
    mcp.add_tool(
        eventstream_builder_service.eventstream_add_eventhouse_destination,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
    )
    
    mcp.add_tool(
        eventstream_builder_service.eventstream_add_custom_endpoint_destination,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
    )
    
    # Creation tool (destructive - creates actual resources in Fabric)
    mcp.add_tool(
        eventstream_builder_service.eventstream_create_from_definition,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
    )
