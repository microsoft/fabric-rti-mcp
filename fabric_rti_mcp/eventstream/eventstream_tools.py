"""
Eventstream tools registration for Microsoft Fabric RTI MCP
Registers Eventstream-related tools with the MCP server
"""

from fastmcp import FastMCP
from fabric_rti_mcp.eventstream import eventstream_service
from fabric_rti_mcp.eventstream import eventstream_builder_tools


def register_tools(mcp: FastMCP) -> None:
    """Register all Eventstream tools with the MCP server."""
    
    # Read-only tools (queries, list operations)
    mcp.add_tool(eventstream_service.eventstream_list)
    mcp.add_tool(eventstream_service.eventstream_get)
    mcp.add_tool(eventstream_service.eventstream_get_definition)
    
    # Destructive tools (create, update, delete operations)
    mcp.add_tool(eventstream_service.eventstream_create)
    mcp.add_tool(eventstream_service.eventstream_update)
    mcp.add_tool(eventstream_service.eventstream_delete)
    
    # Register builder tools
    eventstream_builder_tools.register_tools(mcp)
