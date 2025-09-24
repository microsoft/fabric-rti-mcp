from typing import Any, Dict, List, Optional

import httpx
from azure.identity import ChainedTokenCredential, DefaultAzureCredential

from fabric_rti_mcp.common import GlobalFabricRTIConfig, logger


class FabricConnection:
    """
    Base Azure Identity-based connection for Fabric APIs.
    Handles authentication transparently using Azure credential providers.
    """

    def __init__(self, api_base_url: Optional[str] = None, service_name: str = "Fabric"):
        # Use environment variable if provided, otherwise use parameter or default
        if api_base_url is None:
            config = GlobalFabricRTIConfig.from_env()
            api_base_url = config.fabric_api_base

        self.api_base_url = api_base_url.rstrip("/")
        self.service_name = service_name
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

            logger.debug(f"Successfully acquired Azure token for {self.service_name} API")
            return token.token

        except Exception as e:
            logger.error(f"Failed to get access token for {self.service_name}: {e}")
            raise Exception(f"Authentication failed: {str(e)}")

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

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        payload: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
    ) -> Dict[str, Any]:
        """
        Make an authenticated HTTP request to the Fabric API.

        :param method: HTTP method (GET, POST, PUT, DELETE, etc.)
        :param endpoint: API endpoint (relative to base URL)
        :param payload: Optional request payload for POST/PUT requests
        :param timeout: Request timeout in seconds
        :return: Parsed JSON response
        """
        url = f"{self.api_base_url}{endpoint}"
        headers = self.get_headers()

        logger.debug(f"Making {method} request to: {url}")

        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                if method.upper() in ["POST", "PUT", "PATCH"]:
                    response = await client.request(method, url, headers=headers, json=payload)
                else:
                    response = await client.request(method, url, headers=headers)

                # Log response details
                logger.debug(f"Response status: {response.status_code}")
                logger.debug(f"Response headers: {dict(response.headers)}")

                # Handle different response types
                if response.status_code == 204:
                    # No content response
                    return {"success": True, "status_code": 204}

                # Try to parse JSON response
                try:
                    result = response.json()
                    logger.debug(f"Response body: {result}")
                except Exception:
                    # If JSON parsing fails, return text content
                    result: Dict[str, Any] = {
                        "raw_response": response.text,
                        "status_code": response.status_code,
                    }

                # Check for HTTP errors
                if not response.is_success:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    logger.error(f"{self.service_name} API request failed: {error_msg}")
                    return {"error": True, "message": error_msg, "status_code": response.status_code}

                return result

            except httpx.TimeoutException:
                error_msg = f"Request timeout after {timeout} seconds"
                logger.error(error_msg)
                return {"error": True, "message": error_msg}

            except Exception as e:
                error_msg = f"Request failed: {str(e)}"
                logger.error(f"{self.service_name} API error: {error_msg}")
                return {"error": True, "message": error_msg}

    async def list_artifacts_of_type(
        self,
        workspace_id: str,
        artifact_type: str,
        timeout: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        List all artifacts of a specific type in a workspace.

        :param workspace_id: The workspace ID (UUID)
        :param artifact_type: The type of artifacts to filter for (e.g., "Eventstream", "Activator")
        :param timeout: Request timeout in seconds
        :return: List of artifacts of the specified type
        """
        endpoint = f"/workspaces/{workspace_id}/items"
        
        result = await self._make_request("GET", endpoint, timeout=timeout)
        
        # Handle error cases
        if isinstance(result, dict) and result.get("error"):
            return [result]
            
        # Filter artifacts by type
        artifacts: List[Dict[str, Any]] = []
        
        if isinstance(result, dict) and "value" in result and isinstance(result["value"], list):
            artifacts = [
                item
                for item in result["value"]  # type: ignore
                if isinstance(item, dict) and item.get("type") == artifact_type  # type: ignore
            ]
        elif isinstance(result, list):
            artifacts = [
                item
                for item in result  # type: ignore
                if isinstance(item, dict) and item.get("type") == artifact_type  # type: ignore
            ]
        else:
            # If result is neither dict with "value" nor list, return as is
            if isinstance(result, dict) and result.get("type") == artifact_type:
                artifacts = [result]
        
        return artifacts

    async def execute_operation_and_return_error_in_dict(
        self,
        method: str,
        endpoint: str,
        payload: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
    ) -> Dict[str, Any]:
        """
        Execute a generic API operation with error handling.

        :param method: HTTP method (GET, POST, PUT, DELETE, etc.)
        :param endpoint: API endpoint relative to the configured API base
        :param payload: Optional request payload
        :param timeout: Request timeout in seconds
        :return: API response as dictionary
        """
        try:
            # Make authenticated request
            result = await self._make_request(method, endpoint, payload, timeout)
            return result

        except Exception as e:
            logger.error(f"Error executing {self.service_name} operation: {e}")
            return {"error": True, "message": str(e)}
