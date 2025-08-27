from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

from dotenv import load_dotenv

logger = logging.getLogger("fabric-rti-mcp")


class GlobalFabricRTIEnvVarNames:
    default_fabric_api_base = "FABRIC_API_BASE"
    transport = "FABRIC_RTI_TRANSPORT"
    http_host = "FABRIC_RTI_HTTP_HOST"
    http_port = "FABRIC_RTI_HTTP_PORT"
    debug_mode = "FABRIC_RTI_DEBUG_MODE"


DEFAULT_FABRIC_API_BASE = "https://api.fabric.microsoft.com/v1"


@dataclass(slots=True, frozen=True)
class GlobalFabricRTIConfig:
    fabric_api_base: str
    transport: str
    http_host: str
    http_port: int
    debug_mode: bool

    @staticmethod
    def from_env() -> GlobalFabricRTIConfig:
        # Load .env file if it exists
        env_file = Path.cwd() / ".env"
        if env_file.exists():
            load_dotenv(env_file)

        return GlobalFabricRTIConfig(
            fabric_api_base=os.getenv(GlobalFabricRTIEnvVarNames.default_fabric_api_base, DEFAULT_FABRIC_API_BASE),
            transport=os.getenv(GlobalFabricRTIEnvVarNames.transport, "stdio"),
            http_host=os.getenv(GlobalFabricRTIEnvVarNames.http_host, "0.0.0.0"),
            http_port=int(os.getenv(GlobalFabricRTIEnvVarNames.http_port, "8000")),
            debug_mode=os.getenv(GlobalFabricRTIEnvVarNames.debug_mode, "false").lower() in ("true", "1"),
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
        ]
        for env_var in env_vars:
            if os.getenv(env_var) is not None:
                result.append(env_var)
        return result


# Global configuration instance
config = GlobalFabricRTIConfig.from_env()
