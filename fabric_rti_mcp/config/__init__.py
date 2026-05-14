from __future__ import annotations

import argparse
import logging
import os
import sys
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
    cors_allowed_origins = "FABRIC_RTI_CORS_ORIGINS"


DEFAULT_FABRIC_API_BASE = "https://api.fabric.microsoft.com/v1"
DEFAULT_FABRIC_BASE_URL = "https://fabric.microsoft.com"
DEFAULT_FABRIC_RTI_TRANSPORT = "stdio"
DEFAULT_FABRIC_RTI_HTTP_PORT = 3000
DEFAULT_FABRIC_RTI_HTTP_PATH = "/mcp"
DEFAULT_FABRIC_RTI_HTTP_HOST = "127.0.0.1"
DEFAULT_FABRIC_RTI_STATELESS_HTTP = False
DEFAULT_USE_OBO_FLOW = False
DEFAULT_FABRIC_RTI_AI_FOUNDRY_COMPATIBILITY_SCHEMA = False
DEFAULT_FABRIC_RTI_CORS_ORIGINS = "*"


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
    cors_allowed_origins: str

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
            stateless_http=os.getenv(GlobalFabricRTIEnvVarNames.stateless_http, "false").lower() in ("true", "1"),
            use_obo_flow=os.getenv(GlobalFabricRTIEnvVarNames.use_obo_flow, "false").lower() in ("true", "1"),
            use_ai_foundry_compat=os.getenv(GlobalFabricRTIEnvVarNames.use_ai_foundry_compat, "false").lower()
            in ("true", "1"),
            cors_allowed_origins=os.getenv(
                GlobalFabricRTIEnvVarNames.cors_allowed_origins, DEFAULT_FABRIC_RTI_CORS_ORIGINS
            ),
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
            GlobalFabricRTIEnvVarNames.cors_allowed_origins,
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
        parser.add_argument(
            "--custom-watermark",
            type=str,
            help='JSON object for custom query watermark, e.g. \'{"team": "my-team", "app_id": "env:MY_APP_ID"}\''
            " (FABRIC_RTI_KUSTO_CUSTOM_WATERMARK)",
        )
        args, _ = parser.parse_known_args()

        transport = base_config.transport
        if args.stdio:
            transport = "stdio"
        elif args.http or os.getenv("PORT"):  # if it is running in Azure (Port is set), use HTTP transport
            transport = "http"

        stateless_http = args.stateless_http if "--stateless-http" in sys.argv else base_config.stateless_http
        http_host = args.host if args.host is not None else base_config.http_host
        http_port = args.port if args.port is not None else base_config.http_port
        use_obo_flow = args.use_obo_flow if "--use-obo-flow" in sys.argv else base_config.use_obo_flow
        use_ai_foundry_compat = (
            args.use_ai_foundry_compat if "--use-ai-foundry-compat" in sys.argv else base_config.use_ai_foundry_compat
        )

        # CLI --custom-watermark takes priority over env var
        if args.custom_watermark is not None:
            os.environ["FABRIC_RTI_KUSTO_CUSTOM_WATERMARK"] = args.custom_watermark

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
            cors_allowed_origins=base_config.cors_allowed_origins,
        )


# Global configuration instance
global_config = GlobalFabricRTIConfig.with_args()
