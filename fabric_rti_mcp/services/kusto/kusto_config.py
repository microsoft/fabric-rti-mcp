from __future__ import annotations

import json
import os
from dataclasses import dataclass

from azure.kusto.data import KustoConnectionStringBuilder

from fabric_rti_mcp.config import logger


@dataclass(slots=True, frozen=True)
class KustoServiceConfig:
    service_uri: str
    default_database: str | None = None
    description: str | None = None


class KustoEnvVarNames:
    default_service_uri = "KUSTO_SERVICE_URI"
    default_service_default_db = "KUSTO_SERVICE_DEFAULT_DB"
    open_ai_embedding_endpoint = "AZ_OPENAI_EMBEDDING_ENDPOINT"
    known_services = "KUSTO_KNOWN_SERVICES"
    eager_connect = "KUSTO_EAGER_CONNECT"
    allow_unknown_services = "KUSTO_ALLOW_UNKNOWN_SERVICES"
    timeout = "FABRIC_RTI_KUSTO_TIMEOUT"
    schema_cache_enabled = "FABRIC_RTI_KUSTO_SCHEMA_CACHE_ENABLED"
    schema_cache_path = "FABRIC_RTI_KUSTO_SCHEMA_CACHE_PATH"
    schema_cache_ttl = "FABRIC_RTI_KUSTO_SCHEMA_CACHE_TTL"

    @staticmethod
    def all() -> list[str]:
        """Return a list of all environment variable names used by KustoConfig."""
        return [
            KustoEnvVarNames.default_service_uri,
            KustoEnvVarNames.default_service_default_db,
            KustoEnvVarNames.open_ai_embedding_endpoint,
            KustoEnvVarNames.known_services,
            KustoEnvVarNames.eager_connect,
            KustoEnvVarNames.allow_unknown_services,
            KustoEnvVarNames.timeout,
            KustoEnvVarNames.schema_cache_enabled,
            KustoEnvVarNames.schema_cache_path,
            KustoEnvVarNames.schema_cache_ttl,
        ]


DEFAULT_SCHEMA_CACHE_TTL_SECONDS = 86400  # 1 day


@dataclass(slots=True, frozen=True)
class KustoConfig:
    # Default service. Will be used if no specific service is provided.
    default_service: KustoServiceConfig | None = None
    # Optional OpenAI embedding endpoint to be used for embeddings where applicable.
    open_ai_embedding_endpoint: str | None = None
    # List of known Kusto services. If empty, no services are configured.
    known_services: list[KustoServiceConfig] | None = None
    # Whether to eagerly connect to the default service on startup.
    # This can slow startup and is not recommended.
    eager_connect: bool = False
    # Security setting to allow unknown services. If this is set to False,
    # only services in known_services will be allowed.
    allow_unknown_services: bool = True
    # Global timeout for all Kusto operations in seconds
    timeout_seconds: int | None = None
    # Whether schema caching is enabled
    schema_cache_enabled: bool = False
    # Path for storing schema cache files (defaults to user app data)
    schema_cache_path: str | None = None
    # Schema cache TTL in seconds (default: 1 day)
    schema_cache_ttl_seconds: int = DEFAULT_SCHEMA_CACHE_TTL_SECONDS

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
        known_services: list[KustoServiceConfig] | None = None
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

        # Parse schema cache configuration
        schema_cache_enabled = os.getenv(KustoEnvVarNames.schema_cache_enabled, "false").lower() in ("true", "1")
        schema_cache_path = os.getenv(KustoEnvVarNames.schema_cache_path, None)
        schema_cache_ttl_seconds = DEFAULT_SCHEMA_CACHE_TTL_SECONDS
        ttl_env = os.getenv(KustoEnvVarNames.schema_cache_ttl)
        if ttl_env:
            try:
                schema_cache_ttl_seconds = int(ttl_env)
            except ValueError:
                pass

        return KustoConfig(
            default_service,
            open_ai_embedding_endpoint,
            known_services,
            eager_connect,
            allow_unknown_services,
            timeout_seconds,
            schema_cache_enabled,
            schema_cache_path,
            schema_cache_ttl_seconds,
        )

    @staticmethod
    def existing_env_vars() -> list[str]:
        """Return a lit of environment variables that are used by KustoConfig, and are present in the environment."""
        collected: list[str] = []
        for env_var in KustoEnvVarNames.all():
            if os.getenv(env_var) is not None:
                collected.append(env_var)
        return collected

    @staticmethod
    def get_known_services() -> dict[str, KustoServiceConfig]:
        config = KustoConfig.from_env()
        result: dict[str, KustoServiceConfig] = {}
        if config.default_service:
            result[config.default_service.service_uri] = config.default_service
        if config.known_services is not None:
            for known_service in config.known_services:
                result[known_service.service_uri] = known_service
        return result
