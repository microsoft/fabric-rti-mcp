import asyncio
from typing import Any, Coroutine, Dict, Optional, cast

import httpx
from azure.identity import ChainedTokenCredential, DefaultAzureCredential

from fabric_rti_mcp.common import GlobalFabricRTIConfig, logger


class FabricAPIHttpClient:
    """
    Generic Azure Identity-based HTTP client for Microsoft Fabric APIs.
    Handles authentication transparently using Azure credential providers.
    Can be used for any Fabric service public APIs
    """

    def __init__(self, api_base_url: Optional[str] = None):
        """
        Initialize the Fabric API HTTP client.
        
        Args:
            api_base_url: Optional base URL for Fabric API. If None, uses environment config.
        """
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
        Get Azure credential for authentication.
        This ensures consistent authentication behavior across all Fabric services.

        Uses the user's default tenant, allowing the client to work
        for users in any tenant (not hard-coded to Microsoft's tenant).
        """
        return DefaultAzureCredential(
            exclude_shared_token_cache_credential=True,
            exclude_interactive_browser_credential=False,
        )

    def _get_access_token(self) -> str:
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

    def _get_headers(self) -> Dict[str, str]:
        access_token = self._get_access_token()
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _run_async_operation(self, coro: Coroutine[Any, Any, Any]) -> Any:
        try:
            # Try to get the existing event loop
            asyncio.get_running_loop()
            # If we're already in an event loop, we need to run in a thread
            import concurrent.futures

            def run_in_thread() -> Any:
                # Create a new event loop for this thread
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(coro)
                finally:
                    new_loop.close()

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_thread)
                return future.result()

        except RuntimeError:
            # No event loop running, we can use asyncio.run
            return asyncio.run(coro)

    async def make_request_async(
        self, method: str, endpoint: str, payload: Optional[Dict[str, Any]] = None, timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Make an authenticated HTTP request to the Fabric API (async version).

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (relative to api_base_url)
            payload: Optional request payload for POST/PUT
            timeout: Request timeout in seconds

        Returns:
            Dict containing the API response
        """
        url = f"{self.api_base_url}{endpoint}"
        headers = self._get_headers()

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

    def make_request(
        self, method: str, endpoint: str, payload: Optional[Dict[str, Any]] = None, timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Make an authenticated HTTP request to the Fabric API (sync version).
        
        This is a synchronous wrapper around make_request_async that handles
        event loop management automatically.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (relative to api_base_url)
            payload: Optional request payload for POST/PUT
            timeout: Request timeout in seconds

        Returns:
            Dict containing the API response
        """
        return self._run_async_operation(
            self.make_request_async(method, endpoint, payload, timeout)
        )


class FabricHttpClientCache:
    """Generic connection cache for Fabric API clients using Azure Identity."""
    
    _connection: Optional[FabricAPIHttpClient] = None

    @classmethod
    def get_client(cls) -> FabricAPIHttpClient:
        """Get or create a Fabric API connection using the configured API base URL."""
        if cls._connection is None:
            config = GlobalFabricRTIConfig.from_env()
            api_base = config.fabric_api_base
            cls._connection = FabricAPIHttpClient(api_base)
            logger.info(f"Created Fabric API connection for API base: {api_base}")

        return cls._connection
