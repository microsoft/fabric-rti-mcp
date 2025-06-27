"""
Eventstream service module for Microsoft Fabric RTI MCP
Provides Microsoft Fabric Eventstream operations through MCP tools
"""

import asyncio
import base64
import json
from typing import Any, Dict, List, Optional, Coroutine
from collections import defaultdict
import httpx

from fabric_rti_mcp.common import logger

# Microsoft Fabric API configuration
FABRIC_API_BASE = "https://api.fabric.microsoft.com/v1"
DEFAULT_TIMEOUT = 30


class EventstreamConnectionCache(defaultdict[str, Dict[str, Any]]):
    """Connection cache for Eventstream API clients."""
    def __missing__(self, key: str) -> Dict[str, Any]:
        # For eventstream, we use httpx AsyncClient with auth token
        # The key will be the authorization token
        client_config: Dict[str, Any] = {
            "timeout": DEFAULT_TIMEOUT,
            "headers": {"Authorization": key}
        }
        self[key] = client_config
        return client_config


EVENTSTREAM_CONNECTION_CACHE: Dict[str, Dict[str, Any]] = EventstreamConnectionCache()


def get_eventstream_client_config(authorization_token: str) -> Dict[str, Any]:
    """Get or create client configuration from cache."""
    # Clean up the token since agents can send messy inputs
    authorization_token = authorization_token.strip()
    if not authorization_token.startswith("Bearer "):
        authorization_token = f"Bearer {authorization_token}"
    return EVENTSTREAM_CONNECTION_CACHE[authorization_token]


def _run_async_operation(coro: Coroutine[Any, Any, Any]) -> Any:
    """
    Helper function to run async operations in sync context.
    Handles event loop management gracefully.
    """
    try:
        # Try to get the existing event loop
        loop = asyncio.get_running_loop()
        # If we're already in an event loop, we need to run in a thread
        import concurrent.futures
        import threading
        
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


async def _execute_eventstream_operation(
    method: str,
    endpoint: str,
    authorization_token: str,
    payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Base execution method for Eventstream operations.
    
    :param method: HTTP method (GET, POST, PUT, DELETE)
    :param endpoint: API endpoint relative to FABRIC_API_BASE
    :param authorization_token: Bearer token for authentication
    :param payload: Optional request payload
    :return: API response as dictionary
    """
    # Get client configuration
    client_config = get_eventstream_client_config(authorization_token)
    
    # Build full URL
    url = f"{FABRIC_API_BASE}{endpoint}"
    
    try:
        async with httpx.AsyncClient(timeout=client_config["timeout"]) as client:
            headers = client_config["headers"].copy()
            if payload:
                headers["Content-Type"] = "application/json"
            
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
                logger.error(f"Eventstream API error {response.status_code}: {error_detail}")
                return {
                    "error": True,
                    "status_code": response.status_code,
                    "detail": error_detail
                }
            
            # Return JSON response or success message
            if response.status_code == 204:  # No content
                return {"success": True, "message": "Operation completed successfully"}
            
            try:
                return response.json()
            except Exception:
                return {"success": True, "message": response.text}
                
    except Exception as e:
        logger.error(f"Error executing Eventstream operation: {e}")
        return {
            "error": True,
            "message": str(e)
        }


def eventstream_create(
    workspace_id: str,
    eventstream_name: str,
    definition: Dict[str, Any],
    authorization_token: str,
    description: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Create an Eventstream item in Microsoft Fabric.
    
    :param workspace_id: The workspace ID (UUID)
    :param eventstream_name: Name for the new eventstream
    :param definition: Eventstream definition with sources, destinations, operators, streams
    :param authorization_token: Bearer token for authentication
    :param description: Optional description for the eventstream
    :return: Created eventstream details
    """
    # Prepare the eventstream definition as base64
    definition_json = json.dumps(definition)
    definition_b64 = base64.b64encode(definition_json.encode("utf-8")).decode("utf-8")
    
    payload: Dict[str, Any] = {
        "displayName": eventstream_name,
        "type": "Eventstream",
        "definition": {
            "parts": [
                {
                    "path": "eventstream.json",
                    "payload": definition_b64,
                    "payloadType": "InlineBase64"
                }
            ]
        }
    }
    
    if description:
        payload["description"] = description
    
    endpoint = f"/workspaces/{workspace_id}/items"
    
    result = _run_async_operation(_execute_eventstream_operation("POST", endpoint, authorization_token, payload))
    return [result]


def eventstream_get(
    workspace_id: str,
    item_id: str,
    authorization_token: str
) -> List[Dict[str, Any]]:
    """
    Get an Eventstream item by workspace and item ID.
    
    :param workspace_id: The workspace ID (UUID)
    :param item_id: The eventstream item ID (UUID)
    :param authorization_token: Bearer token for authentication
    :return: Eventstream item details
    """
    endpoint = f"/workspaces/{workspace_id}/items/{item_id}"
    
    result = _run_async_operation(_execute_eventstream_operation("GET", endpoint, authorization_token))
    return [result]


def eventstream_list(
    workspace_id: str,
    authorization_token: str
) -> List[Dict[str, Any]]:
    """
    List all Eventstream items in a workspace.
    
    :param workspace_id: The workspace ID (UUID)
    :param authorization_token: Bearer token for authentication
    :return: List of eventstream items
    """
    endpoint = f"/workspaces/{workspace_id}/items"
    
    result = _run_async_operation(_execute_eventstream_operation("GET", endpoint, authorization_token))
    
    # Filter only Eventstream items if the result contains a list
    if isinstance(result, dict) and "value" in result and isinstance(result["value"], list):
        eventstreams = [item for item in result["value"] if isinstance(item, dict) and item.get("type") == "Eventstream"]
        return eventstreams
    elif isinstance(result, list):
        eventstreams = [item for item in result if isinstance(item, dict) and item.get("type") == "Eventstream"]
        return eventstreams
    
    return [result]


def eventstream_delete(
    workspace_id: str,
    item_id: str,
    authorization_token: str
) -> List[Dict[str, Any]]:
    """
    Delete an Eventstream item by workspace and item ID.
    
    :param workspace_id: The workspace ID (UUID)
    :param item_id: The eventstream item ID (UUID)
    :param authorization_token: Bearer token for authentication
    :return: Deletion confirmation
    """
    endpoint = f"/workspaces/{workspace_id}/items/{item_id}"
    
    result = _run_async_operation(_execute_eventstream_operation("DELETE", endpoint, authorization_token))
    return [result]


def eventstream_update(
    workspace_id: str,
    item_id: str,
    definition: Dict[str, Any],
    authorization_token: str
) -> List[Dict[str, Any]]:
    """
    Update an Eventstream item by workspace and item ID.
    
    :param workspace_id: The workspace ID (UUID)
    :param item_id: The eventstream item ID (UUID)
    :param definition: Updated eventstream definition
    :param authorization_token: Bearer token for authentication
    :return: Updated eventstream details
    """
    # Prepare the eventstream definition as base64
    definition_json = json.dumps(definition)
    definition_b64 = base64.b64encode(definition_json.encode("utf-8")).decode("utf-8")
    
    payload: Dict[str, Any] = {
        "definition": {
            "parts": [
                {
                    "path": "eventstream.json",
                    "payload": definition_b64,
                    "payloadType": "InlineBase64"
                }
            ]
        }
    }
    
    endpoint = f"/workspaces/{workspace_id}/items/{item_id}"
    
    result = _run_async_operation(_execute_eventstream_operation("PUT", endpoint, authorization_token, payload))
    return [result]


def eventstream_get_definition(
    workspace_id: str,
    item_id: str,
    authorization_token: str
) -> List[Dict[str, Any]]:
    """
    Get the definition of an Eventstream item.
    
    :param workspace_id: The workspace ID (UUID)
    :param item_id: The eventstream item ID (UUID)
    :param authorization_token: Bearer token for authentication
    :return: Eventstream definition
    """
    endpoint = f"/workspaces/{workspace_id}/items/{item_id}/getDefinition"
    
    result = _run_async_operation(_execute_eventstream_operation("POST", endpoint, authorization_token))
    return [result]


# List of destructive operations
DESTRUCTIVE_TOOLS = {
    eventstream_create.__name__,
    eventstream_delete.__name__,
    eventstream_update.__name__,
}
