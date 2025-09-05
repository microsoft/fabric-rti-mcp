import argparse
import os
from dataclasses import dataclass
from typing import List


class OBOFlowEnvVarNames:
    """Environment variable names for OBO Flow configuration."""

    azure_tenant_id = "AZURE_TENANT_ID"
    entra_app_client_id = (
        "ENTRA_APP_CLIENT_ID"  # client id for the AAD App which is used to authenticate the user from gateway (APIM)
    )
    # user assigned managed identity client id used as Federated credentials on the Entra App (entra_app_client_id)
    umi_client_id = "USER_MANAGED_IDENTITY_CLIENT_ID"
    kusto_audience = "KUSTO_AUDIENCE"  # Kusto audience, ex: https://<clustername>.kusto.windows.net


# Default values for OBO Flow configuration
DEFAULT_AZURE_TENANT_ID = "72f988bf-86f1-41af-91ab-2d7cd011db47"  # MS tenant id
DEFAULT_ENTRA_APP_CLIENT_ID = ""
DEFAULT_USER_MANAGED_IDENTITY_CLIENT_ID = ""
DEFAULT_KUSTO_AUDIENCE = "https://kusto.kusto.windows.net"


@dataclass(slots=True, frozen=True)
class OBOFlowConfig:
    """Configuration for OBO (On-Behalf-Of) Flow authentication."""

    azure_tenant_id: str
    entra_app_client_id: str
    umi_client_id: str
    kusto_audience: str

    @staticmethod
    def from_env() -> "OBOFlowConfig":
        """Load OBO Flow configuration from environment variables."""
        return OBOFlowConfig(
            azure_tenant_id=os.getenv(OBOFlowEnvVarNames.azure_tenant_id, DEFAULT_AZURE_TENANT_ID),
            entra_app_client_id=os.getenv(OBOFlowEnvVarNames.entra_app_client_id, DEFAULT_ENTRA_APP_CLIENT_ID),
            umi_client_id=os.getenv(OBOFlowEnvVarNames.umi_client_id, DEFAULT_USER_MANAGED_IDENTITY_CLIENT_ID),
            kusto_audience=os.getenv(OBOFlowEnvVarNames.kusto_audience, DEFAULT_KUSTO_AUDIENCE),
        )

    @staticmethod
    def existing_env_vars() -> List[str]:
        """Return a list of environment variable names that are currently set."""
        result: List[str] = []
        env_vars = [
            OBOFlowEnvVarNames.azure_tenant_id,
            OBOFlowEnvVarNames.entra_app_client_id,
            OBOFlowEnvVarNames.umi_client_id,
            OBOFlowEnvVarNames.kusto_audience,
        ]
        for env_var in env_vars:
            if os.getenv(env_var) is not None:
                result.append(env_var)
        return result

    @staticmethod
    def with_args() -> "OBOFlowConfig":
        """Load OBO Flow configuration from environment variables and command line arguments."""
        obo_config = OBOFlowConfig.from_env()

        # Parse command line arguments
        parser = argparse.ArgumentParser(description="Fabric RTI MCP Server OBO Flow Configuration")
        parser.add_argument("--entra-app-client-id", type=str, help="Azure AAD App Client ID")
        parser.add_argument("--umi-client-id", type=str, help="User Managed Identity Client ID")
        # Parse arguments but ignore unknown ones
        args, _ = parser.parse_known_args()

        entra_app_client_id = (
            args.entra_app_client_id if args.entra_app_client_id is not None else obo_config.entra_app_client_id
        )
        umi_client_id = args.umi_client_id if args.umi_client_id is not None else obo_config.umi_client_id

        return OBOFlowConfig(
            azure_tenant_id=obo_config.azure_tenant_id,
            entra_app_client_id=entra_app_client_id,
            umi_client_id=umi_client_id,
            kusto_audience=obo_config.kusto_audience,
        )


obo_config = OBOFlowConfig.with_args()
