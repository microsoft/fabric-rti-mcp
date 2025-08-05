from __future__ import annotations

import logging
import os
from dataclasses import dataclass

logger = logging.getLogger("fabric-rti-mcp")


class GlobalFabricRTIEnvVarNames:
    default_fabric_api_base = "FABRIC_API_BASE"


DEFAULT_FABRIC_API_BASE = "https://api.fabric.microsoft.com/v1"


@dataclass(slots=True, frozen=True)
class GlobalFabricRTIConfig:
    fabric_api_base: str

    @staticmethod
    def from_env() -> GlobalFabricRTIConfig:
        return GlobalFabricRTIConfig(
            fabric_api_base=os.getenv(GlobalFabricRTIEnvVarNames.default_fabric_api_base, DEFAULT_FABRIC_API_BASE)
        )

    @staticmethod
    def existing_env_vars() -> list[str]:
        """Return a list of environment variable names that are currently set."""
        return [GlobalFabricRTIEnvVarNames.default_fabric_api_base]
