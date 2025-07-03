import os
import sys

from mcp.server.fastmcp import FastMCP

from fabric_rti_mcp import __version__
from fabric_rti_mcp.common import logger
from fabric_rti_mcp.kusto import kusto_tools
from fabric_rti_mcp.eventstream import eventstream_tools


def register_tools(mcp: FastMCP) -> None:
    """Register all available tools with the MCP server."""
    # Register Kusto tools
    kusto_tools.register_tools(mcp)
    
    # Register Eventstream tools
    eventstream_tools.register_tools(mcp)
    
    logger.error("Registered tools from Kusto and Eventstream modules")


def main() -> None:
    # writing to stderr because stdout is used for the transport
    # and we want to see the logs in the console
    logger.error("Starting Fabric RTI MCP server")
    logger.error(f"Version: {__version__}")
    logger.error(f"Python version: {sys.version}")
    logger.error(f"Platform: {sys.platform}")
    # print pid
    logger.error(f"PID: {os.getpid()}")
    # import later to allow for environment variables to be set from command line
    mcp = FastMCP("fabric-rti-mcp-server")
    register_tools(mcp)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
