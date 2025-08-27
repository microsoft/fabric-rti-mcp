"""
Fabric RTI MCP Server

This module provides the main entry point for the server, supporting both stdio
and HTTP transport modes with authentication.
"""

import argparse
import os
import signal
import sys
import types
from datetime import datetime
from typing import Dict, Any, Optional

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from fabric_rti_mcp import __version__
from fabric_rti_mcp.authentication.auth_middleware import add_auth_middleware
from fabric_rti_mcp.common import logger
from fabric_rti_mcp.eventstream import eventstream_tools
from fabric_rti_mcp.kusto import kusto_config, kusto_tools


def setup_shutdown_handler(sig: int, frame: Optional[types.FrameType]) -> None:
    """Handle process termination signals."""
    signal_name = signal.Signals(sig).name
    logger.info(f"Received signal {sig} ({signal_name}), shutting down...")
    
    # Exit the process
    sys.exit(0)


def parse_args() -> Dict[str, Any]:
    """
    Parse command line arguments with environment variable support.
    
    Returns:
        Dict[str, Any]: Dictionary of parsed arguments
    """
    # Environment defaults
    env_host = os.getenv("FASTMCP_HOST", os.getenv("MCP_HTTP_HOST", "0.0.0.0" if os.getenv("PORT") else "127.0.0.1"))
    env_port = int(os.getenv("PORT", os.getenv("FUNCTIONS_CUSTOMHANDLER_PORT", os.getenv("FASTMCP_PORT", os.getenv("MCP_HTTP_PORT", "3000")))))
    env_path = os.getenv("FASTMCP_PATH", os.getenv("MCP_HTTP_PATH", "/mcp"))
    
    parser = argparse.ArgumentParser(description="Fabric RTI MCP Server")
    transport_group = parser.add_mutually_exclusive_group()
    transport_group.add_argument("--stdio", action="store_true", help="Use stdio transport (default)")
    transport_group.add_argument("--http", action="store_true", help="Use HTTP transport")
    
    parser.add_argument("--host", default=env_host,help="Host to bind to when running in HTTP mode")
    parser.add_argument("--port", type=int, default=env_port, help="Port to use when running in HTTP mode")
    parser.add_argument("--streamable-http-path", default=env_path, help="Path for HTTP transport")
    
    args = parser.parse_args()
    
    # Determine transport mode from arguments
    # for Azure (PORT env variable is set)
    if args.http or os.getenv("PORT"):
        mode = "http"
    elif args.stdio:
        mode = "stdio"
    else:
        mode = "stdio"  # Default
    
    return {
        "mode": mode,
        "host": args.host,
        "port": args.port,
        "streamable_http_path": getattr(args, 'streamable_http_path')
    }


def register_tools(mcp: FastMCP) -> None:
    """Register all tools with the MCP server."""
    logger.info("Kusto configuration keys found in environment:")
    logger.info(", ".join(kusto_config.KustoConfig.existing_env_vars()))
    
    kusto_tools.register_tools(mcp)
    eventstream_tools.register_tools(mcp)
    
from datetime import datetime

# Health check function defined at module level
async def health_check(request: Request) -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "server": "fabric-rti-mcp"
    })

def add_health_endpoint(mcp: FastMCP) -> None:
    """Add health endpoint for Kubernetes liveness probes."""
    # Register the pre-defined health check function
    mcp.custom_route("/health", methods=["GET"])(health_check)
    
def main() -> None:
    """Main entry point for the server."""
    try:
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, setup_shutdown_handler) # Signal Interrupt)
        signal.signal(signal.SIGTERM, setup_shutdown_handler) # Signal Terminate
        
        # Parse command line arguments
        args = parse_args()
        
        # Set up logging to stderr because stdout is used for stdio transport
        # writing to stderr because stdout is used for the transport
        # and we want to see the logs in the console
        logger.info("Starting Fabric RTI MCP server")
        logger.info(f"Version: {__version__}")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Platform: {sys.platform}")
        logger.info(f"PID: {os.getpid()}")
        logger.info(f"Transport: {args['mode']}")
        
        if args["mode"] == "http":
            logger.info(f"Host: {args['host']}")
            logger.info(f"Port: {args['port']}")
            logger.info(f"Path: {args['streamable_http_path']}")
        
        # TODO: Add telemetry configuration here
        
        name = "fabric-rti-mcp-server"
        # Create FabricRTIMCP instance
        if args["mode"] == "http":
            fastmcp_server = FastMCP(
                name,
                host=args["host"],
                port=args["port"],
                streamable_http_path=args["streamable_http_path"],
                stateless_http=True
            )
        else:
            fastmcp_server = FastMCP(name)

        # 1. Register tools
        register_tools(fastmcp_server)

        # 2. Add HTTP-specific features if in HTTP mode
        if args["mode"] == "http":
            add_health_endpoint(fastmcp_server)
            logger.info("Adding authorization middleware")
            add_auth_middleware(fastmcp_server)

        # TBD - Add telemetry 

        # 3. Run the server with the specified transport
        if args["mode"] == "http":
            logger.info(f"Starting {name} (HTTP) on {args['host']}:{args['port']} with /health endpoint")
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
