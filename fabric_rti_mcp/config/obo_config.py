import argparse
import os
from dataclasses import dataclass
from typing import List


class FabricRtiMcpOBOFlowEnvVarNames:
    """Environment variable names for OBO Flow configuration."""

    azure_tenant_id = "FABRIC_RTI_MCP_AZURE_TENANT_ID"
    # client id for the AAD App which is used to authenticate the user from gateway (APIM)
    entra_app_client_id = "FABRIC_RTI_MCP_ENTRA_APP_CLIENT_ID"
    # user assigned managed identity client id used as Federated credentials on the Entra App (entra_app_client_id)
    umi_client_id = "FABRIC_RTI_MCP_USER_MANAGED_IDENTITY_CLIENT_ID"
    kusto_audience = "FABRIC_RTI_MCP_KUSTO_AUDIENCE"  # Kusto audience, ex: https://<clustername>.kusto.windows.net


# Default values for OBO Flow configuration
DEFAULT_FABRIC_RTI_MCP_AZURE_TENANT_ID = "72f988bf-86f1-41af-91ab-2d7cd011db47"  # MS tenant id
DEFAULT_FABRIC_RTI_MCP_ENTRA_APP_CLIENT_ID = ""
DEFAULT_FABRIC_RTI_MCP_USER_MANAGED_IDENTITY_CLIENT_ID = ""
DEFAULT_FABRIC_RTI_MCP_KUSTO_AUDIENCE = "https://kusto.kusto.windows.net"


@dataclass(slots=True, frozen=True)
class FabricRtiMcpOBOFlowAuthConfig:
    """Configuration for OBO (On-Behalf-Of) Flow authentication."""

    azure_tenant_id: str
    entra_app_client_id: str
    umi_client_id: str
    kusto_audience: str

    @staticmethod
    def from_env() -> "FabricRtiMcpOBOFlowAuthConfig":
        """Load OBO Flow configuration from environment variables."""
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
            kusto_audience=os.getenv(
                FabricRtiMcpOBOFlowEnvVarNames.kusto_audience, DEFAULT_FABRIC_RTI_MCP_KUSTO_AUDIENCE
            ),
        )

    @staticmethod
    def existing_env_vars() -> List[str]:
        """Return a list of environment variable names that are currently set."""
        result: List[str] = []
        env_vars = [
            FabricRtiMcpOBOFlowEnvVarNames.azure_tenant_id,
            FabricRtiMcpOBOFlowEnvVarNames.entra_app_client_id,
            FabricRtiMcpOBOFlowEnvVarNames.umi_client_id,
            FabricRtiMcpOBOFlowEnvVarNames.kusto_audience,
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
        )


obo_config = FabricRtiMcpOBOFlowAuthConfig.with_args()
