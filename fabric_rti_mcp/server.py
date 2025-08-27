import os
import subprocess
import sys
import threading
import time

from mcp.server.fastmcp import FastMCP

from fabric_rti_mcp import __version__
from fabric_rti_mcp.common import config, logger
from fabric_rti_mcp.eventstream import eventstream_tools
from fabric_rti_mcp.kusto import kusto_config, kusto_tools


def launch_mcp_inspector() -> None:
    """Launch MCP Inspector in a separate process if debug mode is enabled."""
    if not config.debug_mode:
        return

    def start_inspector():
        try:
            logger.error("Debug mode enabled - launching MCP Inspector...")
            # Give the main server a moment to start
            time.sleep(2)

            # Try to launch npx with shell=True for better PATH resolution
            cmd = "npx @modelcontextprotocol/inspector"
            try:
                logger.error(f"Trying to launch MCP Inspector with command: {cmd}")
                subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                logger.error("MCP Inspector launched successfully")
            except Exception as ex:
                logger.error(f"Failed to launch MCP Inspector: {ex}")
                logger.error("Please ensure Node.js is installed and run manually: npx @modelcontextprotocol/inspector")

        except Exception as e:
            logger.error(f"Failed to launch MCP Inspector: {e}")

    # Start inspector in a separate thread to not block the main server
    inspector_thread = threading.Thread(target=start_inspector, daemon=True)
    inspector_thread.start()


def register_tools(mcp: FastMCP) -> None:
    logger.info("Kusto configuration keys found in environment:")
    logger.info(", ".join(kusto_config.KustoConfig.existing_env_vars()))
    kusto_tools.register_tools(mcp)
    eventstream_tools.register_tools(mcp)


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
    mcp = FastMCP("fabric-rti-mcp-server", host=config.http_host, port=config.http_port)
    register_tools(mcp)

    if config.transport == "http":
        logger.warning(f"Starting HTTP server on {config.http_host}:{config.http_port}")

        # Launch MCP Inspector if debug mode is enabled
        if config.debug_mode:
            launch_mcp_inspector()

        # Note: FastMCP uses "streamable-http" transport, host/port are set via environment
        mcp.run(transport="streamable-http")
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
