import os
import signal
import sys
import types
from datetime import datetime, timezone
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse

from fabric_rti_mcp import __version__
from fabric_rti_mcp.auth.auth_middleware import add_auth_middleware
from fabric_rti_mcp.compat.ms_foundry import SchemaCompatibleMCP
from fabric_rti_mcp.config import global_config as config
from fabric_rti_mcp.config import logger
from fabric_rti_mcp.config.obo import obo_config
from fabric_rti_mcp.services import AddTool
from fabric_rti_mcp.services.activator import activator_tools
from fabric_rti_mcp.services.eventstream import eventstream_tools
from fabric_rti_mcp.services.kusto import kusto_config, kusto_tools
from fabric_rti_mcp.services.map import map_tools

# Global variable to store server start time
server_start_time = datetime.now(timezone.utc)


def setup_shutdown_handler(sig: int, frame: types.FrameType | None) -> None:
    """Handle process termination signals."""
    signal_name = signal.Signals(sig).name
    logger.info(f"Received signal {sig} ({signal_name}), shutting down...")

    # Exit the process
    sys.exit(0)


def add_allowed_tools(service_tool_modules: tuple[Any, ...], allowed_tools: set[str], add_tool: AddTool) -> None:
    known_services = {
        service_tools.__name__.rsplit(".", 1)[-1].removesuffix("_tools"): service_tools
        for service_tools in service_tool_modules
    }
    allowed_service_names = (
        set(known_services)
        if not allowed_tools
        else {tool if tool in known_services else tool.split("_", 1)[0] for tool in allowed_tools}
    )
    unknown_services = allowed_service_names - set(known_services)
    if unknown_services:
        unknown = ", ".join(sorted(unknown_services))
        raise ValueError(f"Unknown entries in FABRIC_RTI_ALLOWED_TOOLS: {unknown}")

    known_tool_names: set[str] = set()

    def filtered_add_tool(tool: Any, **kwargs: Any) -> None:
        tool_name = tool.__name__.lower()
        known_tool_names.add(tool_name)
        service_name = tool_name.split("_", 1)[0]
        if not allowed_tools or service_name in allowed_tools or tool_name in allowed_tools:
            add_tool(tool, **kwargs)

    for service_name, service_tools in known_services.items():
        if service_name in allowed_service_names:
            service_tools.register_tools(filtered_add_tool)

    unknown_entries = allowed_tools - set(known_services) - known_tool_names
    if unknown_entries:
        unknown = ", ".join(sorted(unknown_entries))
        raise ValueError(f"Unknown entries in FABRIC_RTI_ALLOWED_TOOLS: {unknown}")


def register_tools(mcp: FastMCP) -> None:
    """Register all tools with the MCP server."""
    logger.info("Kusto configuration keys found in environment:")
    logger.info(", ".join(kusto_config.KustoConfig.existing_env_vars()))

    service_tool_modules = (kusto_tools, eventstream_tools, activator_tools, map_tools)
    allowed_tools = {tool.lower() for tool in _split_comma_separated(os.getenv("FABRIC_RTI_ALLOWED_TOOLS", ""))}
    add_allowed_tools(service_tool_modules, allowed_tools, mcp.add_tool)


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


def _split_comma_separated(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _is_loopback_host(host: str) -> bool:
    return host in ("127.0.0.1", "localhost", "::1")


def build_transport_security_settings() -> TransportSecuritySettings | None:
    """Build explicit DNS-rebinding protection when configured, otherwise let FastMCP handle loopback defaults."""
    allowed_hosts = _split_comma_separated(config.http_allowed_hosts)
    allowed_origins = _split_comma_separated(config.http_allowed_origins)

    if allowed_hosts or allowed_origins:
        if not allowed_hosts:
            raise ValueError("FABRIC_RTI_HTTP_ALLOWED_HOSTS must be set when configuring HTTP transport security")
        return TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=allowed_hosts,
            allowed_origins=allowed_origins,
        )

    if not _is_loopback_host(config.http_host):
        if not config.http_debug_mode:
            raise ValueError(
                "HTTP host is non-loopback. Configure FABRIC_RTI_HTTP_ALLOWED_HOSTS "
                "or set FABRIC_RTI_HTTP_DEBUG_MODE=true for local testing only."
            )
        logger.warning(
            "HTTP host is non-loopback and no explicit Host/Origin allow-list is configured. "
            "This is allowed only because FABRIC_RTI_HTTP_DEBUG_MODE=true. Do not use this configuration in production."
        )

    return None


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
            logger.info(f"Use OBO flow: {config.use_obo_flow}")

        # TODO: Add telemetry configuration here

        if config.use_obo_flow and (not obo_config.entra_app_client_id or not obo_config.umi_client_id):
            raise ValueError("OBO flow is enabled but required client IDs are missing")

        if config.use_ai_foundry_compat:
            logger.info("AI Foundry compatibility mode enabled - schemas will be simplified")

        name = "fabric-rti-mcp-server"
        fastmcp_class = SchemaCompatibleMCP if config.use_ai_foundry_compat else FastMCP

        if config.transport == "http":
            fastmcp_server = fastmcp_class(
                name,
                host=config.http_host,
                port=config.http_port,
                streamable_http_path=config.http_path,
                stateless_http=config.stateless_http,
                transport_security=build_transport_security_settings(),
            )
        else:
            fastmcp_server = fastmcp_class(name)

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
