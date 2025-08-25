"""
Eventstream tools registration for Microsoft Fabric RTI MCP
Registers Eventstream-related tools with the MCP server
"""

from fastmcp import FastMCP
from fabric_rti_mcp.eventstream import eventstream_service
from fabric_rti_mcp.eventstream import eventstream_builder_tools


def register_tools(mcp: FastMCP) -> None:
    """Register all Eventstream tools with the MCP server using modern decorator pattern."""
    
    # Read-only tools (queries, list operations)
    @mcp.tool()
    def eventstream_list(workspace_id: str):
        """List all Eventstreams in your Fabric workspace."""
        return eventstream_service.eventstream_list(workspace_id)
    
    @mcp.tool()
    def eventstream_get(workspace_id: str, item_id: str):
        """Get detailed information about a specific Eventstream."""
        return eventstream_service.eventstream_get(workspace_id, item_id)
    
    @mcp.tool()
    def eventstream_get_definition(workspace_id: str, item_id: str):
        """Retrieve complete JSON definition of an Eventstream."""
        return eventstream_service.eventstream_get_definition(workspace_id, item_id)
    
    # Destructive tools (create, update, delete operations)
    @mcp.tool()
    def eventstream_create(workspace_id: str, eventstream_name: str = None, eventstream_id: str = None, definition: dict = None, description: str = None):
        """Create new Eventstreams with custom configuration (auto-includes default stream)."""
        return eventstream_service.eventstream_create(workspace_id, eventstream_name, eventstream_id, definition, description)
    
    @mcp.tool()
    def eventstream_update(workspace_id: str, item_id: str, definition: dict):
        """Modify existing Eventstream settings and destinations."""
        return eventstream_service.eventstream_update(workspace_id, item_id, definition)
    
    @mcp.tool()
    def eventstream_delete(workspace_id: str, item_id: str):
        """Remove Eventstreams and associated resources."""
        return eventstream_service.eventstream_delete(workspace_id, item_id)
    
    # Register builder tools
    eventstream_builder_tools.register_tools(mcp)
