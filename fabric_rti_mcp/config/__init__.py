from __future__ import annotations

import argparse
import logging
import os
from dataclasses import dataclass

logger = logging.getLogger("fabric-rti-mcp")


class GlobalFabricRTIEnvVarNames:
    default_fabric_api_base = "FABRIC_API_BASE"
    fabric_base_url = "FABRIC_BASE_URL"
    http_host = "FABRIC_RTI_HTTP_HOST"
    transport = "FABRIC_RTI_TRANSPORT"
    http_port = "FABRIC_RTI_HTTP_PORT"  # default port name used by RTI MCP
    azure_service_deployment_default_port = "PORT"  # Azure App Services or Azure Container Apps uses this port name
    functions_deployment_default_port = "FUNCTIONS_CUSTOMHANDLER_PORT"  # Azure Functions uses this port name
    http_path = "FABRIC_RTI_HTTP_PATH"
    stateless_http = "FABRIC_RTI_STATELESS_HTTP"
    use_obo_flow = "USE_OBO_FLOW"
    use_ai_foundry_compat = "FABRIC_RTI_AI_FOUNDRY_COMPATIBILITY_SCHEMA"
    enable_kusto = "FABRIC_RTI_ENABLE_KUSTO"
    enable_eventstream = "FABRIC_RTI_ENABLE_EVENTSTREAM"
    enable_activator = "FABRIC_RTI_ENABLE_ACTIVATOR"
    enable_map = "FABRIC_RTI_ENABLE_MAP"


DEFAULT_FABRIC_API_BASE = "https://api.fabric.microsoft.com/v1"
DEFAULT_FABRIC_BASE_URL = "https://fabric.microsoft.com"
DEFAULT_FABRIC_RTI_TRANSPORT = "stdio"
DEFAULT_FABRIC_RTI_HTTP_PORT = 3000
DEFAULT_FABRIC_RTI_HTTP_PATH = "/mcp"
DEFAULT_FABRIC_RTI_HTTP_HOST = "127.0.0.1"
DEFAULT_FABRIC_RTI_STATELESS_HTTP = False
DEFAULT_USE_OBO_FLOW = False
DEFAULT_FABRIC_RTI_AI_FOUNDRY_COMPATIBILITY_SCHEMA = False
DEFAULT_FABRIC_RTI_ENABLE_KUSTO = True
DEFAULT_FABRIC_RTI_ENABLE_EVENTSTREAM = True
DEFAULT_FABRIC_RTI_ENABLE_ACTIVATOR = True
DEFAULT_FABRIC_RTI_ENABLE_MAP = True


@dataclass(slots=True, frozen=True)
class GlobalFabricRTIConfig:
    fabric_api_base: str
    fabric_base_url: str
    transport: str
    http_host: str
    http_port: int
    http_path: str
    stateless_http: bool
    use_obo_flow: bool
    use_ai_foundry_compat: bool
    enable_kusto: bool
    enable_eventstream: bool
    enable_activator: bool
    enable_map: bool

    @staticmethod
    def from_env() -> GlobalFabricRTIConfig:
        return GlobalFabricRTIConfig(
            fabric_api_base=os.getenv(GlobalFabricRTIEnvVarNames.default_fabric_api_base, DEFAULT_FABRIC_API_BASE),
            fabric_base_url=os.getenv(GlobalFabricRTIEnvVarNames.fabric_base_url, DEFAULT_FABRIC_BASE_URL),
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
            stateless_http=os.getenv(GlobalFabricRTIEnvVarNames.stateless_http, str(DEFAULT_FABRIC_RTI_STATELESS_HTTP)).lower() in ("true", "1", "yes"),
            use_obo_flow=os.getenv(GlobalFabricRTIEnvVarNames.use_obo_flow, str(DEFAULT_USE_OBO_FLOW)).lower() in ("true", "1", "yes"),
            use_ai_foundry_compat=os.getenv(
                GlobalFabricRTIEnvVarNames.use_ai_foundry_compat, str(DEFAULT_FABRIC_RTI_AI_FOUNDRY_COMPATIBILITY_SCHEMA)
            ).lower() in ("true", "1", "yes"),
            enable_kusto=os.getenv(GlobalFabricRTIEnvVarNames.enable_kusto, str(DEFAULT_FABRIC_RTI_ENABLE_KUSTO)).lower() in ("true", "1", "yes"),
            enable_eventstream=os.getenv(GlobalFabricRTIEnvVarNames.enable_eventstream, str(DEFAULT_FABRIC_RTI_ENABLE_EVENTSTREAM)).lower() in ("true", "1", "yes"),
            enable_activator=os.getenv(GlobalFabricRTIEnvVarNames.enable_activator, str(DEFAULT_FABRIC_RTI_ENABLE_ACTIVATOR)).lower() in ("true", "1", "yes"),
            enable_map=os.getenv(GlobalFabricRTIEnvVarNames.enable_map, str(DEFAULT_FABRIC_RTI_ENABLE_MAP)).lower() in ("true", "1", "yes"),
        )

    @staticmethod
    def existing_env_vars() -> list[str]:
        """Return a list of environment variable names that are currently set."""
        result: list[str] = []
        env_vars = [
            GlobalFabricRTIEnvVarNames.default_fabric_api_base,
            GlobalFabricRTIEnvVarNames.fabric_base_url,
            GlobalFabricRTIEnvVarNames.transport,
            GlobalFabricRTIEnvVarNames.http_host,
            GlobalFabricRTIEnvVarNames.http_port,
            GlobalFabricRTIEnvVarNames.http_path,
            GlobalFabricRTIEnvVarNames.stateless_http,
            GlobalFabricRTIEnvVarNames.use_obo_flow,
            GlobalFabricRTIEnvVarNames.use_ai_foundry_compat,
            GlobalFabricRTIEnvVarNames.enable_kusto,
            GlobalFabricRTIEnvVarNames.enable_eventstream,
            GlobalFabricRTIEnvVarNames.enable_activator,
            GlobalFabricRTIEnvVarNames.enable_map,
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
        parser.add_argument(
            "--use-ai-foundry-compat", action="store_true", help="Enable or disable AI Foundry compatibility mode"
        )
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
        use_ai_foundry_compat = (
            args.use_ai_foundry_compat if args.use_ai_foundry_compat is not None else base_config.use_ai_foundry_compat
        )

        return GlobalFabricRTIConfig(
            fabric_api_base=base_config.fabric_api_base,
            fabric_base_url=base_config.fabric_base_url,
            transport=transport,
            http_host=http_host,
            http_port=http_port,
            http_path=base_config.http_path,
            stateless_http=stateless_http,
            use_obo_flow=use_obo_flow,
            use_ai_foundry_compat=use_ai_foundry_compat,
            enable_kusto=base_config.enable_kusto,
            enable_eventstream=base_config.enable_eventstream,
            enable_activator=base_config.enable_activator,
            enable_map=base_config.enable_map,
        )


# Global configuration instance
global_config = GlobalFabricRTIConfig.with_args()
