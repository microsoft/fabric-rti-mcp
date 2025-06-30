import os
import sys

from mcp.server.fastmcp import FastMCP

from fabric_rti_mcp import __version__
from fabric_rti_mcp.common import logger
from fabric_rti_mcp.kusto import kusto_tools
from fabric_rti_mcp.extensions import ExtensionRegistry


def register_tools(mcp: FastMCP) -> None:
    # Register core Kusto tools
    kusto_tools.register_tools(mcp)
    
    # Register extension tools
    extension_registry = ExtensionRegistry()
    extension_registry.discover_extensions()
    extension_registry.register_all_tools(mcp)
    
    # Log registered extensions
    extensions = extension_registry.list_extensions()
    if extensions:
        logger.info(f"Registered extensions: {', '.join(extensions)}")
    else:
        logger.info("No extensions registered")


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
    mcp = FastMCP("kusto-mcp-server")
    register_tools(mcp)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
