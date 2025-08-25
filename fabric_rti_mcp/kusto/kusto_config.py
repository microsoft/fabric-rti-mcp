from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional

from azure.kusto.data import KustoConnectionStringBuilder

from fabric_rti_mcp.common import logger


@dataclass(slots=True, frozen=True)
class KustoServiceConfig:
    service_uri: str
    default_database: Optional[str] = None
    description: Optional[str] = None


class KustoEnvVarNames:
    default_service_uri = "KUSTO_SERVICE_URI"
    default_service_default_db = "KUSTO_SERVICE_DEFAULT_DB"
    open_ai_embedding_endpoint = "AZ_OPENAI_EMBEDDING_ENDPOINT"
    known_services = "KUSTO_KNOWN_SERVICES"
    eager_connect = "KUSTO_EAGER_CONNECT"
    allow_unknown_services = "KUSTO_ALLOW_UNKNOWN_SERVICES"
    timeout = "FABRIC_RTI_KUSTO_TIMEOUT"

    @staticmethod
    def all() -> List[str]:
        """Return a list of all environment variable names used by KustoConfig."""
        return [
            KustoEnvVarNames.default_service_uri,
            KustoEnvVarNames.default_service_default_db,
            KustoEnvVarNames.open_ai_embedding_endpoint,
            KustoEnvVarNames.known_services,
            KustoEnvVarNames.eager_connect,
            KustoEnvVarNames.allow_unknown_services,
            KustoEnvVarNames.timeout,
        ]


@dataclass(slots=True, frozen=True)
class KustoConfig:
    # Default service. Will be used if no specific service is provided.
    default_service: Optional[KustoServiceConfig] = None
    # Optional OpenAI embedding endpoint to be used for embeddings where applicable.
    open_ai_embedding_endpoint: Optional[str] = None
    # List of known Kusto services. If empty, no services are configured.
    known_services: Optional[List[KustoServiceConfig]] = None
    # Whether to eagerly connect to the default service on startup.
    # This can slow startup and is not recommended.
    eager_connect: bool = False
    # Security setting to allow unknown services. If this is set to False,
    # only services in known_services will be allowed.
    allow_unknown_services: bool = True
    # Global timeout for all Kusto operations in seconds
    timeout_seconds: Optional[int] = None

    @staticmethod
    def from_env() -> KustoConfig:
        """Create a KustoConfig instance from environment variables."""
        default_service_uri = os.getenv(KustoEnvVarNames.default_service_uri)
        default_db = os.getenv(
            KustoEnvVarNames.default_service_default_db, KustoConnectionStringBuilder.DEFAULT_DATABASE_NAME
        )
        default_service = None
        if default_service_uri:
            default_service = KustoServiceConfig(
                service_uri=default_service_uri, default_database=default_db, description="Default"
            )

        open_ai_embedding_endpoint = os.getenv(KustoEnvVarNames.open_ai_embedding_endpoint, None)
        known_services_string = os.getenv(KustoEnvVarNames.known_services, None)
        known_services: List[KustoServiceConfig] | None = None
        eager_connect = os.getenv(KustoEnvVarNames.eager_connect, "false").lower() in ("true", "1")
        allow_unknown_services = os.getenv(KustoEnvVarNames.allow_unknown_services, "true").lower() in ("true", "1")

        # Parse timeout configuration
        timeout_seconds = None
        timeout_env = os.getenv(KustoEnvVarNames.timeout)
        if timeout_env:
            try:
                timeout_seconds = int(timeout_env)
            except ValueError:
                # Ignore invalid timeout values
                pass

        if known_services_string:
            try:
                known_services_json = json.loads(known_services_string)
                known_services = [KustoServiceConfig(**service) for service in known_services_json]
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse {KustoEnvVarNames.known_services}: {e}. Skipping known services.")

        return KustoConfig(
            default_service,
            open_ai_embedding_endpoint,
            known_services,
            eager_connect,
            allow_unknown_services,
            timeout_seconds,
        )

    @staticmethod
    def existing_env_vars() -> List[str]:
        """Return a lit of environment variables that are used by KustoConfig, and are present in the environment."""
        collected: List[str] = []
        for env_var in KustoEnvVarNames.all():
            if os.getenv(env_var) is not None:
                collected.append(env_var)
        return collected

    @staticmethod
    def get_known_services() -> Dict[str, KustoServiceConfig]:
        config = KustoConfig.from_env()
        result: Dict[str, KustoServiceConfig] = {}
        if config.default_service:
            result[config.default_service.service_uri] = config.default_service
        if config.known_services is not None:
            for known_service in config.known_services:
                result[known_service.service_uri] = known_service
        return result
