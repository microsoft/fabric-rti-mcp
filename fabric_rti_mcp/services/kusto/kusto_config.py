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
    shots_table = "KUSTO_SHOTS_TABLE"
    known_services = "KUSTO_KNOWN_SERVICES"
    eager_connect = "KUSTO_EAGER_CONNECT"
    allow_unknown_services = "KUSTO_ALLOW_UNKNOWN_SERVICES"
    timeout = "FABRIC_RTI_KUSTO_TIMEOUT"
    deeplink_style = "FABRIC_RTI_KUSTO_DEEPLINK_STYLE"
    response_format = "FABRIC_RTI_KUSTO_RESPONSE_FORMAT"

    @staticmethod
    def all() -> list[str]:
        """Return a list of all environment variable names used by KustoConfig."""
        return [
            KustoEnvVarNames.default_service_uri,
            KustoEnvVarNames.default_service_default_db,
            KustoEnvVarNames.open_ai_embedding_endpoint,
            KustoEnvVarNames.shots_table,
            KustoEnvVarNames.known_services,
            KustoEnvVarNames.eager_connect,
            KustoEnvVarNames.allow_unknown_services,
            KustoEnvVarNames.timeout,
            KustoEnvVarNames.deeplink_style,
            KustoEnvVarNames.response_format,
        ]


@dataclass(slots=True, frozen=True)
class KustoConfig:
    # Default service. Will be used if no specific service is provided.
    default_service: KustoServiceConfig | None = None
    # Optional OpenAI embedding endpoint to be used for embeddings where applicable.
    open_ai_embedding_endpoint: str | None = None
    # Default shots table name for the kusto_get_shots tool.
    shots_table: str | None = None
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
    # Override deeplink style detection. Valid values: "adx", "fabric".
    deeplink_style: str | None = None
    # Response format for Kusto query results. Default: "kusto_response".
    response_format: str = "kusto_response"

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
        shots_table = os.getenv(KustoEnvVarNames.shots_table, None)
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

        deeplink_style = None
        deeplink_style_env = os.getenv(KustoEnvVarNames.deeplink_style)
        if deeplink_style_env:
            normalized = deeplink_style_env.strip().lower()
            if normalized in ("adx", "fabric"):
                deeplink_style = normalized
            else:
                logger.warning(
                    f"Invalid {KustoEnvVarNames.deeplink_style}='{deeplink_style_env}'. "
                    "Expected 'adx' or 'fabric'. Ignoring override."
                )

        valid_formats = ("columnar", "json", "csv", "tsv", "header_arrays", "kusto_response")
        response_format = "kusto_response"
        response_format_env = os.getenv(KustoEnvVarNames.response_format)
        if response_format_env:
            normalized_fmt = response_format_env.strip().lower()
            if normalized_fmt in valid_formats:
                response_format = normalized_fmt
            else:
                logger.warning(
                    f"Invalid {KustoEnvVarNames.response_format}='{response_format_env}'. "
                    f"Expected one of: {', '.join(valid_formats)}. Using default 'kusto_response'."
                )

        return KustoConfig(
            default_service,
            open_ai_embedding_endpoint,
            shots_table,
            known_services,
            eager_connect,
            allow_unknown_services,
            timeout_seconds,
            deeplink_style,
            response_format,
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
