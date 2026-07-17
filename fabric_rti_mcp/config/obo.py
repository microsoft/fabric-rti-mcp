import argparse
import os
from dataclasses import dataclass


class FabricRtiMcpOBOFlowEnvVarNames:
    """Environment variable names for OBO Flow configuration."""

    azure_tenant_id = "FABRIC_RTI_MCP_AZURE_TENANT_ID"
    # client id for the AAD App which is used to authenticate the user from gateway (APIM)
    entra_app_client_id = "FABRIC_RTI_MCP_ENTRA_APP_CLIENT_ID"
    # user assigned managed identity client id used as Federated credentials on the Entra App (entra_app_client_id)
    umi_client_id = "FABRIC_RTI_MCP_USER_MANAGED_IDENTITY_CLIENT_ID"
    kusto_audience = "FABRIC_RTI_MCP_KUSTO_AUDIENCE"  # Kusto audience, ex: https://<clustername>.kusto.windows.net
    fabric_audience = "FABRIC_RTI_MCP_FABRIC_AUDIENCE"  # Fabric REST audience
    allowed_obo_audiences = "FABRIC_RTI_MCP_ALLOWED_OBO_AUDIENCES"


# Default values for OBO Flow configuration
DEFAULT_FABRIC_RTI_MCP_AZURE_TENANT_ID = "72f988bf-86f1-41af-91ab-2d7cd011db47"  # MS tenant id
DEFAULT_FABRIC_RTI_MCP_ENTRA_APP_CLIENT_ID = ""
DEFAULT_FABRIC_RTI_MCP_USER_MANAGED_IDENTITY_CLIENT_ID = ""
DEFAULT_FABRIC_RTI_MCP_KUSTO_AUDIENCE = "https://kusto.kusto.windows.net"
DEFAULT_FABRIC_RTI_MCP_FABRIC_AUDIENCE = "https://api.fabric.microsoft.com"


def normalize_obo_audience(audience: str) -> str:
    """Normalize an OBO resource URI or .default scope to its resource URI."""
    normalized = audience.strip()
    if normalized.endswith("/.default"):
        normalized = normalized[: -len("/.default")]
    normalized = normalized.rstrip("/")
    if not normalized:
        raise ValueError("OBO audience cannot be empty")
    return normalized


def parse_obo_audiences(raw_audiences: str) -> tuple[str, ...]:
    """Parse a comma-separated OBO audience allow-list."""
    audiences = [normalize_obo_audience(audience) for audience in raw_audiences.split(",") if audience.strip()]
    unique_audiences = tuple(dict.fromkeys(audiences))
    if not unique_audiences:
        raise ValueError(f"{FabricRtiMcpOBOFlowEnvVarNames.allowed_obo_audiences} cannot be empty")
    return unique_audiences


@dataclass(slots=True, frozen=True)
class FabricRtiMcpOBOFlowAuthConfig:
    """Configuration for OBO (On-Behalf-Of) Flow authentication."""

    azure_tenant_id: str
    entra_app_client_id: str
    umi_client_id: str
    kusto_audience: str
    fabric_audience: str
    allowed_obo_audiences: tuple[str, ...]

    @staticmethod
    def from_env() -> "FabricRtiMcpOBOFlowAuthConfig":
        """Load OBO Flow configuration from environment variables."""
        kusto_audience = normalize_obo_audience(
            os.getenv(FabricRtiMcpOBOFlowEnvVarNames.kusto_audience, DEFAULT_FABRIC_RTI_MCP_KUSTO_AUDIENCE)
        )
        fabric_audience = normalize_obo_audience(
            os.getenv(FabricRtiMcpOBOFlowEnvVarNames.fabric_audience, DEFAULT_FABRIC_RTI_MCP_FABRIC_AUDIENCE)
        )
        allowed_obo_audiences_env = os.getenv(FabricRtiMcpOBOFlowEnvVarNames.allowed_obo_audiences)
        allowed_obo_audiences = (
            parse_obo_audiences(allowed_obo_audiences_env)
            if allowed_obo_audiences_env is not None
            else tuple(dict.fromkeys([kusto_audience, fabric_audience]))
        )

        return FabricRtiMcpOBOFlowAuthConfig(
            azure_tenant_id=os.getenv(
                FabricRtiMcpOBOFlowEnvVarNames.azure_tenant_id, DEFAULT_FABRIC_RTI_MCP_AZURE_TENANT_ID
            ),
            entra_app_client_id=os.getenv(
                FabricRtiMcpOBOFlowEnvVarNames.entra_app_client_id, DEFAULT_FABRIC_RTI_MCP_ENTRA_APP_CLIENT_ID
            ),
            umi_client_id=os.getenv(
                FabricRtiMcpOBOFlowEnvVarNames.umi_client_id, DEFAULT_FABRIC_RTI_MCP_USER_MANAGED_IDENTITY_CLIENT_ID
            ),
            kusto_audience=kusto_audience,
            fabric_audience=fabric_audience,
            allowed_obo_audiences=allowed_obo_audiences,
        )

    def require_allowed_audience(self, audience: str) -> str:
        """Return a normalized audience if it is allowed; otherwise raise."""
        normalized_audience = normalize_obo_audience(audience)
        if normalized_audience not in self.allowed_obo_audiences:
            allowed = ", ".join(self.allowed_obo_audiences)
            raise ValueError(f"OBO audience '{normalized_audience}' is not in the allowed audience list: {allowed}")
        return normalized_audience

    @staticmethod
    def existing_env_vars() -> list[str]:
        """Return a list of environment variable names that are currently set."""
        result: list[str] = []
        env_vars = [
            FabricRtiMcpOBOFlowEnvVarNames.azure_tenant_id,
            FabricRtiMcpOBOFlowEnvVarNames.entra_app_client_id,
            FabricRtiMcpOBOFlowEnvVarNames.umi_client_id,
            FabricRtiMcpOBOFlowEnvVarNames.kusto_audience,
            FabricRtiMcpOBOFlowEnvVarNames.fabric_audience,
            FabricRtiMcpOBOFlowEnvVarNames.allowed_obo_audiences,
        ]
        for env_var in env_vars:
            if os.getenv(env_var) is not None:
                result.append(env_var)
        return result

    @staticmethod
    def with_args() -> "FabricRtiMcpOBOFlowAuthConfig":
        """Load OBO Flow configuration from environment variables and command line arguments."""
        obo_config = FabricRtiMcpOBOFlowAuthConfig.from_env()

        parser = argparse.ArgumentParser(description="Fabric RTI MCP Server OBO Flow Configuration")
        parser.add_argument("--entra-app-client-id", type=str, help="Azure AAD App Client ID")
        parser.add_argument("--umi-client-id", type=str, help="User Managed Identity Client ID")
        args, _ = parser.parse_known_args()

        entra_app_client_id = (
            args.entra_app_client_id if args.entra_app_client_id is not None else obo_config.entra_app_client_id
        )
        umi_client_id = args.umi_client_id if args.umi_client_id is not None else obo_config.umi_client_id

        return FabricRtiMcpOBOFlowAuthConfig(
            azure_tenant_id=obo_config.azure_tenant_id,
            entra_app_client_id=entra_app_client_id,
            umi_client_id=umi_client_id,
            kusto_audience=obo_config.kusto_audience,
            fabric_audience=obo_config.fabric_audience,
            allowed_obo_audiences=obo_config.allowed_obo_audiences,
        )


obo_config = FabricRtiMcpOBOFlowAuthConfig.with_args()
