"""
Eventstream Builder Tools Registration for Microsoft Fabric RTI MCP
Registers all builder-related tools with the MCP server
"""

from fastmcp import FastMCP
# Use full builder service with all tools
from fabric_rti_mcp.eventstream import eventstream_builder_service


def register_tools(mcp: FastMCP) -> None:
    """Register all available Eventstream Builder tools with the MCP server."""
    
    # Session management tools
    mcp.add_tool(eventstream_builder_service.eventstream_start_definition)
    mcp.add_tool(eventstream_builder_service.eventstream_get_current_definition)
    mcp.add_tool(eventstream_builder_service.eventstream_clear_definition)
    
    # Data source tools
    mcp.add_tool(eventstream_builder_service.eventstream_add_sample_data_source)
    mcp.add_tool(eventstream_builder_service.eventstream_add_custom_endpoint_source)
    
    # Stream tools
    mcp.add_tool(eventstream_builder_service.eventstream_add_default_stream)
    mcp.add_tool(eventstream_builder_service.eventstream_add_derived_stream)
    
    # Destination tools
    mcp.add_tool(eventstream_builder_service.eventstream_add_eventhouse_destination)
    mcp.add_tool(eventstream_builder_service.eventstream_add_custom_endpoint_destination)
    
    # Validation and creation tools
    mcp.add_tool(eventstream_builder_service.eventstream_validate_definition)
    mcp.add_tool(eventstream_builder_service.eventstream_create_from_definition)
    mcp.add_tool(eventstream_builder_service.eventstream_list_available_components)
