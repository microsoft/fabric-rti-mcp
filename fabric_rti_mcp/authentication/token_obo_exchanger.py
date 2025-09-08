from __future__ import annotations

from typing import Any, Dict, Optional

import msal  # type: ignore
from azure.identity import ManagedIdentityCredential

from fabric_rti_mcp.common import logger
from fabric_rti_mcp.config.obo_config import FabricRtiMcpOBOFlowEnvVarNames, obo_config


class TokenOboExchanger:

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the TokenOboExchanger with optional configuration.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.logger = logger
        self.tenant_id = obo_config.azure_tenant_id
        self.entra_app_client_id = obo_config.entra_app_client_id
        self.umi_client_id = obo_config.umi_client_id
        self.logger.info(
            f"TokenOboExchanger initialized with tenant_id: {self.tenant_id}, "
            f"entra_app_client_id: {self.entra_app_client_id} and umi_client_id: {self.umi_client_id}"
        )

    async def perform_obo_token_exchange(self, user_token: str, resource_uri: str) -> str:
        """
        Perform an On-Behalf-Of token exchange to get a new token for a resource.

        Args:
            user_token: The original user token
            resource_uri: The URI of the target resource to get a token (ex. https://kusto.kusto.windows.net)

        Returns:
            New access token for the specified resource
        """
        self.logger.info(f"TokenOboExchanger: Performing OBO token exchange for target resource: {resource_uri}")

        client_id = self.entra_app_client_id

        if not client_id:
            self.logger.error("TokenOboExchanger: Entra App client ID is not provided for OBO token exchange")
            raise ValueError(
                f"Entra App client ID is required for OBO token exchange. "
                f"Set {FabricRtiMcpOBOFlowEnvVarNames.entra_app_client_id} environment variable."
            )

        if not self.tenant_id:
            self.logger.error("TokenOboExchanger: Tenant ID not available for OBO token exchange")
            raise ValueError(
                f"{FabricRtiMcpOBOFlowEnvVarNames.azure_tenant_id} environment variable required for OBO token exchange"
            )

        if not self.umi_client_id:
            self.logger.error("TokenOboExchanger: UMI Client ID not available for OBO token exchange")
            raise ValueError(
                f"{FabricRtiMcpOBOFlowEnvVarNames.umi_client_id} environment variable required for OBO token exchange"
            )

        try:
            authority = f"https://login.microsoftonline.com/{self.tenant_id}"
            self.logger.info(
                f"TokenOboExchanger: Using Managed Identity for OBO token exchange tenant_id: {self.tenant_id}, "
                f"entra_app_client_id: {self.entra_app_client_id} and umi_client_id: {self.umi_client_id}"
            )

            managed_identity_credential = ManagedIdentityCredential(client_id=self.umi_client_id)
            miScopes = "api://AzureADTokenExchange/.default"  # this is the default scope to be used
            self.logger.info(f"TokenOboExchanger: Start managed identity token acquire for scopes {miScopes}")
            access_token_result = managed_identity_credential.get_token(
                miScopes
            )  # get the MI token to be used as client assesrtion for OBO
            assertion_token = access_token_result.token

            app = msal.ConfidentialClientApplication(
                client_id=client_id,
                authority=authority,
                client_credential={
                    "client_assertion": assertion_token,
                    "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                },
            )

            # Set the scopes for the target resource we want to access
            target_scopes = [f"{resource_uri}/.default"]
            self.logger.info(f"TokenOboExchanger: Requesting access to scopes: {target_scopes}")

            # Use the user token to acquire a new token for the target resource
            result = app.acquire_token_on_behalf_of(user_assertion=user_token, scopes=target_scopes)

            if "access_token" not in result:
                error_msg = result.get("error_description") or result.get("error") or "Unknown error"
                error_message = f"TokenOboExchanger: Failed to acquire token: {error_msg}"
                self.logger.error(error_message)
                raise Exception(error_message)

            self.logger.info("TokenOboExchanger: Successfully acquired OBO token")
            access_token: str = result["access_token"]
            return access_token
        except Exception as e:
            self.logger.error(f"TokenOboExchanger: Error performing OBO token exchange: {e}")
            raise Exception(f"OBO token exchange failed: {e}") from e
