from __future__ import annotations

from typing import Any, Dict, Optional

import msal
from azure.identity import ManagedIdentityCredential

from fabric_rti_mcp.common import logger, GlobalFabricRTIEnvVarNames, config as global_config


class TokenOboExchanger:
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the TokenOboExchanger with optional configuration.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.logger = logger
        self.tenant_id = global_config.azure_tenant_id
        self.client_id = global_config.azure_client_id
        # Always use managed identity
        self.use_managed_identity = True

    async def perform_obo_token_exchange(
        self, 
        user_token: str, 
        resource_uri: str
    ) -> str:
        """
        Perform an On-Behalf-Of token exchange to get a new token for a resource.

        Args:
            user_token: The original user token
            resource_uri: The URI of the target resource for which to get a token (e.g., https://graph.microsoft.com)

        Returns:
            New access token for the specified resource
        """
        self.logger.info(f"Performing OBO token exchange for target resource: {resource_uri}")
        
        # Use provided client_id or fall back to environment variable
        client_id = self.client_id
        
        if not client_id:
            self.logger.error("Client ID not provided for OBO token exchange")
            raise ValueError(f"Client ID is required for OBO token exchange. Set {GlobalFabricRTIEnvVarNames.azure_client_id} environment variable.")
        
        if not self.tenant_id:
            self.logger.error("Tenant ID not available for OBO token exchange")
            raise ValueError(f"{GlobalFabricRTIEnvVarNames.azure_tenant_id} environment variable is required for OBO token exchange")
        
        try:
            authority = f"https://login.microsoftonline.com/{self.tenant_id}"

            self.logger.info(f"Using Managed Identity for OBO token exchange with client ID: {client_id} and Tenant id: {self.tenant_id}")

            # Get a token for the client application using managed identity
            # credential = ManagedIdentityCredential(client_id=client_id)
            
            # For the app's own token
            # app_token = credential.get_token("https://management.azure.com/.default")

            mgid = "a6f04c9b-1ff2-405e-baa4-d12c456b8a01"
            managed_identity_credential = ManagedIdentityCredential(client_id=mgid)
            miScopes = f"https://management.azure.com/.default"
            self.logger.info(f"Start: Managed Identity token acquire {miScopes}")
            access_token_result = managed_identity_credential.get_token(miScopes)
            assertion_token = access_token_result.token

            self.logger.info(f"Create MSAL with Managed Identity token acquired token = {assertion_token[7:18]}")
            # Create the MSAL application using the token we got
            app = msal.ConfidentialClientApplication(
                client_id=client_id,
                authority=authority,
                client_credential={"client_assertion": assertion_token, "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer"}
            )
            
            # Set the scopes for the target resource we want to access
            target_scopes = [f"{resource_uri}/.default"]
            self.logger.info(f"Requesting access to scopes: {target_scopes}")
            
            # Use the user token to acquire a new token for the target resource
            result = app.acquire_token_on_behalf_of(
                user_assertion=user_token,
                scopes=target_scopes
            )
            
            if "access_token" not in result:
                error_message = f"Failed to acquire token: {result.get('error_description', result.get('error', 'Unknown error'))}"
                self.logger.error(error_message)
                raise Exception(error_message)
            
            self.logger.info("Successfully acquired OBO token")
            return result["access_token"]
        except Exception as e:
            self.logger.error(f"Error performing OBO token exchange: {e}")
            raise
