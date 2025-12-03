from typing import Any, Dict, Optional, cast

import httpx
from azure.identity import ChainedTokenCredential, DefaultAzureCredential

from fabric_rti_mcp.common import GlobalFabricRTIConfig, logger


class EventstreamConnection:
    """
    Azure Identity-based connection for Fabric Eventstream API.
    Handles authentication transparently using Azure credential providers.
    """

    def __init__(self, api_base_url: Optional[str] = None):
        # Use environment variable if provided, otherwise use parameter or default
        if api_base_url is None:
            config = GlobalFabricRTIConfig.from_env()
            api_base_url = config.fabric_api_base

        self.api_base_url = api_base_url.rstrip("/")
        self.credential = self._get_credential()
        self.token_scope = "https://api.fabric.microsoft.com/.default"
        self._cached_token = None
        self._token_expiry = None

    def _get_credential(self) -> ChainedTokenCredential:
        """
        Get Azure credential using the same pattern as Kusto module.
        This ensures consistent authentication behavior across both modules.

        Uses the user's default tenant, allowing the MCP server to work
        for users in any tenant (not hard-coded to Microsoft's tenant).
        """
        return DefaultAzureCredential(
            exclude_shared_token_cache_credential=True,
            exclude_interactive_browser_credential=False,
        )

    def _get_access_token(self) -> str:
        """
        Get a valid access token for Fabric API.
        Handles token caching and refresh automatically.
        """
        try:
            # Get token from Azure credential
            token = self.credential.get_token(self.token_scope)

            if not token:
                raise Exception("Failed to acquire token from Azure credential")

            logger.debug(f"Successfully acquired Fabric API token (expires: {token.expires_on})")
            return token.token

        except Exception as e:
            logger.error(f"Failed to get Fabric API access token: {e}")
            raise Exception(f"Authentication failed: {e}")

    def get_headers(self) -> Dict[str, str]:
        """
        Get HTTP headers with valid authentication.
        """
        access_token = self._get_access_token()
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def make_request(
        self, method: str, endpoint: str, payload: Optional[Dict[str, Any]] = None, timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Make an authenticated HTTP request to the Fabric API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (relative to api_base_url)
            payload: Optional request payload for POST/PUT
            timeout: Request timeout in seconds

        Returns:
            Dict containing the API response
        """
        url = f"{self.api_base_url}{endpoint}"
        headers = self.get_headers()

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                # Execute request based on method
                if method.upper() == "GET":
                    response = await client.get(url, headers=headers)
                elif method.upper() == "POST":
                    response = await client.post(url, json=payload, headers=headers)
                elif method.upper() == "PUT":
                    response = await client.put(url, json=payload, headers=headers)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                # Handle response
                if response.status_code >= 400:
                    error_detail = response.text
                    logger.error(f"Fabric API error {response.status_code}: {error_detail}")
                    return {"error": True, "status_code": response.status_code, "detail": error_detail}

                # Return JSON response or success message
                if response.status_code == 204:  # No content
                    return {"success": True, "message": "Operation completed successfully"}

                try:
                    return cast(Dict[str, Any], response.json())
                except Exception:
                    return {"success": True, "message": response.text}

        except Exception as e:
            logger.error(f"Error making Fabric API request: {e}")
            return {"error": True, "message": str(e)}
