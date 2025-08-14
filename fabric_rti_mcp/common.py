from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger("fabric-rti-mcp")


class GlobalFabricRTIEnvVarNames:
    default_fabric_api_base = "FABRIC_API_BASE"
    kusto_timeout = "FABRIC_RTI_KUSTO_TIMEOUT"


DEFAULT_FABRIC_API_BASE = "https://api.fabric.microsoft.com/v1"


@dataclass(slots=True, frozen=True)
class GlobalFabricRTIConfig:
    fabric_api_base: str
    kusto_timeout_seconds: Optional[int]

    @staticmethod
    def from_env() -> GlobalFabricRTIConfig:
        kusto_timeout_seconds = None
        timeout_env = os.getenv(GlobalFabricRTIEnvVarNames.kusto_timeout)
        if timeout_env:
            try:
                kusto_timeout_seconds = int(timeout_env)
            except ValueError:
                # Ignore invalid timeout values
                pass

        return GlobalFabricRTIConfig(
            fabric_api_base=os.getenv(GlobalFabricRTIEnvVarNames.default_fabric_api_base, DEFAULT_FABRIC_API_BASE),
            kusto_timeout_seconds=kusto_timeout_seconds,
        )

    @staticmethod
    def existing_env_vars() -> list[str]:
        """Return a list of environment variable names that are currently set."""
        return [GlobalFabricRTIEnvVarNames.default_fabric_api_base, GlobalFabricRTIEnvVarNames.kusto_timeout]


# Global configuration instance
config = GlobalFabricRTIConfig.from_env()
