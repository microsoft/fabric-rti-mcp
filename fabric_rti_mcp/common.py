from __future__ import annotations

import argparse
import logging
import os
from dataclasses import dataclass
from typing import List

logger = logging.getLogger("fabric-rti-mcp")


class GlobalFabricRTIEnvVarNames:
    default_fabric_api_base = "FABRIC_API_BASE"
    http_host = "FABRIC_RTI_HTTP_HOST"
    transport = "FABRIC_RTI_TRANSPORT"
    http_port = "FABRIC_RTI_HTTP_PORT"  # default port name used by RTI MCP
    azure_service_deployment_default_port = "PORT"  # Azure App Services or Azure Container Apps uses this port name
    functions_deployment_default_port = "FUNCTIONS_CUSTOMHANDLER_PORT"  # Azure Functions uses this port name
    http_path = "FABRIC_RTI_HTTP_PATH"
    stateless_http = "FABRIC_RTI_STATELESS_HTTP"
    use_obo_flow = "USE_OBO_FLOW"


DEFAULT_FABRIC_API_BASE = "https://api.fabric.microsoft.com/v1"
DEFAULT_FABRIC_RTI_TRANSPORT = "stdio"
DEFAULT_FABRIC_RTI_HTTP_PORT = 3000
DEFAULT_FABRIC_RTI_HTTP_PATH = "/mcp"
DEFAULT_FABRIC_RTI_HTTP_HOST = "127.0.0.1"
DEFAULT_FABRIC_RTI_STATELESS_HTTP = False
DEFAULT_USE_OBO_FLOW = False


@dataclass(slots=True, frozen=True)
class GlobalFabricRTIConfig:
    fabric_api_base: str
    transport: str
    http_host: str
    http_port: int
    http_path: str
    stateless_http: bool
    use_obo_flow: bool

    @staticmethod
    def from_env() -> GlobalFabricRTIConfig:
        return GlobalFabricRTIConfig(
            fabric_api_base=os.getenv(GlobalFabricRTIEnvVarNames.default_fabric_api_base, DEFAULT_FABRIC_API_BASE),
            transport=os.getenv(GlobalFabricRTIEnvVarNames.transport, DEFAULT_FABRIC_RTI_TRANSPORT),
            http_host=os.getenv(GlobalFabricRTIEnvVarNames.http_host, DEFAULT_FABRIC_RTI_HTTP_HOST),
            http_port=int(
                os.getenv(
                    "PORT",
                    os.getenv(
                        "FUNCTIONS_CUSTOMHANDLER_PORT",
                        os.getenv(GlobalFabricRTIEnvVarNames.http_port, DEFAULT_FABRIC_RTI_HTTP_PORT),
                    ),
                )
            ),
            http_path=os.getenv(GlobalFabricRTIEnvVarNames.http_path, DEFAULT_FABRIC_RTI_HTTP_PATH),
            stateless_http=bool(
                os.getenv(GlobalFabricRTIEnvVarNames.stateless_http, DEFAULT_FABRIC_RTI_STATELESS_HTTP)
            ),
            use_obo_flow=bool(os.getenv(GlobalFabricRTIEnvVarNames.use_obo_flow, DEFAULT_USE_OBO_FLOW)),
        )

    @staticmethod
    def existing_env_vars() -> List[str]:
        """Return a list of environment variable names that are currently set."""
        result: List[str] = []
        env_vars = [
            GlobalFabricRTIEnvVarNames.default_fabric_api_base,
            GlobalFabricRTIEnvVarNames.transport,
            GlobalFabricRTIEnvVarNames.http_host,
            GlobalFabricRTIEnvVarNames.http_port,
            GlobalFabricRTIEnvVarNames.http_path,
            GlobalFabricRTIEnvVarNames.stateless_http,
            GlobalFabricRTIEnvVarNames.use_obo_flow,
        ]
        for env_var in env_vars:
            if os.getenv(env_var) is not None:
                result.append(env_var)
        return result

    @staticmethod
    def with_args() -> GlobalFabricRTIConfig:
        base_config = GlobalFabricRTIConfig.from_env()

        # see if the client is passing these (ex: local debug / test client)
        parser = argparse.ArgumentParser(description="Fabric RTI MCP Server")
        parser.add_argument("--stdio", action="store_true", help="Use stdio transport")
        parser.add_argument("--http", action="store_true", help="Use HTTP transport")
        parser.add_argument("--host", type=str, help="HTTP host to listen on")
        parser.add_argument("--port", type=int, help="HTTP port to listen on")
        parser.add_argument("--stateless-http", action="store_true", help="Enable or disable stateless HTTP")
        parser.add_argument("--use-obo-flow", action="store_true", help="Enable or disable OBO flow")
        args, _ = parser.parse_known_args()

        transport = base_config.transport
        if args.stdio:
            transport = "stdio"
        elif args.http or os.getenv("PORT"):  # if it is running in Azure (Port is set), use HTTP transport
            transport = "http"

        stateless_http = args.stateless_http if args.stateless_http is not None else base_config.stateless_http
        http_host = args.host if args.host is not None else base_config.http_host
        http_port = args.port if args.port is not None else base_config.http_port
        use_obo_flow = args.use_obo_flow if args.use_obo_flow is not None else base_config.use_obo_flow

        return GlobalFabricRTIConfig(
            fabric_api_base=base_config.fabric_api_base,
            transport=transport,
            http_host=http_host,
            http_port=http_port,
            http_path=base_config.http_path,
            stateless_http=stateless_http,
            use_obo_flow=use_obo_flow,
        )


# Global configuration instance
global_config = GlobalFabricRTIConfig.with_args()
