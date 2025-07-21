# Template for new module tools registration
# Replace <MODULE_NAME> with the actual module name

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

# TODO: Import the actual service module
# from fabric_rti_mcp.<module_name> import <module_name>_service


def register_tools(mcp: FastMCP) -> None:
    """Register all tools for this module with the MCP server."""
    
    # TODO: Add tool registrations following the kusto_tools.py pattern
    # Example:
    
    # Read-only tools (queries, list operations, etc.)
    # mcp.add_tool(
    #     <module_name>_service.module_query,
    #     annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    # )
    
    # mcp.add_tool(
    #     <module_name>_service.module_list_resources,
    #     annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    # )
    
    # Destructive tools (create, update, delete operations)
    # mcp.add_tool(
    #     <module_name>_service.module_create_resource,
    #     annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
    # )
    
    pass  # Remove this when you add actual tool registrations
