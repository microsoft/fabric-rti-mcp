import os
import signal
import sys
import types
from datetime import datetime, timezone
from typing import Optional

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from fabric_rti_mcp import __version__
from fabric_rti_mcp.authentication.auth_middleware import add_auth_middleware
from fabric_rti_mcp.common import config, logger
from fabric_rti_mcp.eventstream import eventstream_tools
from fabric_rti_mcp.kusto import kusto_config, kusto_tools
# Global variable to store server start time
server_start_time = datetime.now(timezone.utc)

KUSTO_INSTRUCTIONS = """
- Kusto
    - Description: Kusto service for querying and managing data.
    - Guideline:
        - Clearly distinguish between different parts of queries (e.g. relational, graph, semantic similarity).
          Although they can be mixed, they have different semantics:
            - Relational queries focus on structured data and relationships.
            - Graph queries explore connections between entities. To use them you must have:
                - A graph reference (e.g. graph('name'))
                - A graph-match clause with a graph pattern (e.g. | graph-match (node)-[edge]->(target) project node, edge)
                - The graph-match node must have a projection clause to be valid
            - Semantic similarity queries assess the meaning and context of data.
                - Use series_cosine_similarity(vector_a, vector_b)
        - Don't guess schema / values. Always execute `kusto_get_entity_schema()` first,
            and if still unsure, use a simple query like `take 1` to understand the data.
"""

def setup_shutdown_handler(sig: int, frame: Optional[types.FrameType]) -> None:
    """Handle process termination signals."""
    signal_name = signal.Signals(sig).name
    logger.info(f"Received signal {sig} ({signal_name}), shutting down...")

    # Exit the process
    sys.exit(0)


def register_tools(mcp: FastMCP) -> None:
    """Register all tools with the MCP server."""
    logger.info("Kusto configuration keys found in environment:")
    logger.info(", ".join(kusto_config.KustoConfig.existing_env_vars()))

    kusto_tools.register_tools(mcp)
    eventstream_tools.register_tools(mcp)


# Health check function defined at module level
async def health_check(request: Request) -> JSONResponse:
    """Health check endpoint."""
    current_time = datetime.now(timezone.utc)
    logger.info(f"Server health check at {current_time}")
    return JSONResponse(
        {
            "status": "healthy",
            "current_time_utc": current_time.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "server": "fabric-rti-mcp",
            "start_time_utc": server_start_time.strftime("%Y-%m-%d %H:%M:%S UTC"),
        }
    )


def add_health_endpoint(mcp: FastMCP) -> None:
    """Add health endpoint for Kubernetes liveness probes."""
    # Register the pre-defined health check function
    mcp.custom_route("/health", methods=["GET"])(health_check)


def main() -> None:
    """Main entry point for the server."""
    try:
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, setup_shutdown_handler)  # Signal Interrupt)
        signal.signal(signal.SIGTERM, setup_shutdown_handler)  # Signal Terminate

        # Set up logging to stderr because stdout is used for stdio transport
        # writing to stderr because stdout is used for the transport
        # and we want to see the logs in the console
        logger.info("Starting Fabric RTI MCP server")
        logger.info(f"Version: {__version__}")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Platform: {sys.platform}")
        logger.info(f"PID: {os.getpid()}")
        logger.info(f"Transport: {config.transport}")

        if config.transport == "http":
            logger.info(f"Host: {config.http_host}")
            logger.info(f"Port: {config.http_port}")
            logger.info(f"Path: {config.http_path}")
            logger.info(f"Stateless HTTP: {config.stateless_http}")

        # TODO: Add telemetry configuration here

        name = "fabric-rti-mcp-server"
        if config.transport == "http":
            fastmcp_server = FastMCP(
                name,
                host=config.http_host,
                port=config.http_port,
                streamable_http_path=config.http_path,
                stateless_http=config.stateless_http,
            )
        else:
            fastmcp_server = FastMCP(name, instructions="""
This server has the following services:
{ki}
- EventStream
    - Description: EventStream service for processing and managing events.
    - Guideline: ``
                                     """.format(ki=KUSTO_INSTRUCTIONS))

        # 1. Register tools
        register_tools(fastmcp_server)

        # 2. Add HTTP-specific features if in HTTP mode
        if config.transport == "http":
            add_health_endpoint(fastmcp_server)
            logger.info("Adding authorization middleware")
            add_auth_middleware(fastmcp_server)

        # TBD - Add telemetry

        # 3. Run the server with the specified transport
        if config.transport == "http":
            logger.info(f"Starting {name} (HTTP) on {config.http_host}:{config.http_port} with /health endpoint")
            fastmcp_server.run(transport="streamable-http")
        else:
            logger.info(f"Starting {name} (stdio)")
            fastmcp_server.run(transport="stdio")

    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as error:
        logger.error(f"Server error: {error}")
        raise


if __name__ == "__main__":
    main()
