import os
import sys

from mcp.server.fastmcp import FastMCP

from fabric_rti_mcp import __version__
from fabric_rti_mcp.common import logger
from fabric_rti_mcp.kusto import kusto_tools


def register_tools(mcp: FastMCP) -> None:
    kusto_tools.register_tools(mcp)


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
