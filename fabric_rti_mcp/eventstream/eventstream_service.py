"""
Eventstream service module for Microsoft Fabric RTI MCP
Provides Microsoft Fabric Eventstream operations through MCP tools
Uses Azure Identity for transparent authentication (consistent with Kusto module)
"""

import asyncio
import base64
import json
import os
from typing import Any, Dict, List, Optional, Coroutine

from fabric_rti_mcp.common import logger
from fabric_rti_mcp.eventstream.eventstream_connection import EventstreamConnection

# Microsoft Fabric API configuration
DEFAULT_FABRIC_API_BASE = "https://api.fabric.microsoft.com/v1"
DEFAULT_TIMEOUT = 30


def get_fabric_api_base() -> str:
    """
    Get the Fabric API base URL from environment variable.
    Falls back to default if not set.
    """
    return os.environ.get("FABRIC_API_BASE_URL", DEFAULT_FABRIC_API_BASE)


class EventstreamConnectionCache:
    """Simple connection cache for Eventstream API clients using Azure Identity."""
    def __init__(self):
        self._connection: Optional[EventstreamConnection] = None
    
    def get_connection(self) -> EventstreamConnection:
        """Get or create an Eventstream connection using the configured API base URL."""
        if self._connection is None:
            api_base = get_fabric_api_base()
            self._connection = EventstreamConnection(api_base)
            logger.info(f"Created Eventstream connection for API base: {api_base}")
        
        return self._connection


EVENTSTREAM_CONNECTION_CACHE = EventstreamConnectionCache()


def get_eventstream_connection() -> EventstreamConnection:
    """Get or create an Eventstream connection using the configured API base URL."""
    return EVENTSTREAM_CONNECTION_CACHE.get_connection()


def _run_async_operation(coro: Coroutine[Any, Any, Any]) -> Any:
    """
    Helper function to run async operations in sync context.
    Handles event loop management gracefully.
    """
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


async def _execute_eventstream_operation(
    method: str,
    endpoint: str,
    payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Base execution method for Eventstream operations using Azure Identity.
    No longer requires explicit authorization token - handled transparently.
    
    :param method: HTTP method (GET, POST, PUT, DELETE)
    :param endpoint: API endpoint relative to the configured API base
    :param payload: Optional request payload
    :return: API response as dictionary
    """
    # Get connection with automatic Azure authentication
    connection = get_eventstream_connection()
    
    try:
        # Make authenticated request
        result = await connection.make_request(method, endpoint, payload, DEFAULT_TIMEOUT)
        return result
        
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
    description: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Create an Eventstream item in Microsoft Fabric.
    Authentication is handled transparently using Azure Identity.
    
    :param workspace_id: The workspace ID (UUID)
    :param eventstream_name: Name for the new eventstream
    :param definition: Eventstream definition with sources, destinations, operators, streams
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
    
    result = _run_async_operation(_execute_eventstream_operation("POST", endpoint, payload))
    return [result]


def eventstream_get(
    workspace_id: str,
    item_id: str
) -> List[Dict[str, Any]]:
    """
    Get an Eventstream item by workspace and item ID.
    Authentication is handled transparently using Azure Identity.
    
    :param workspace_id: The workspace ID (UUID)
    :param item_id: The eventstream item ID (UUID)
    :return: Eventstream item details
    """
    endpoint = f"/workspaces/{workspace_id}/items/{item_id}"
    
    result = _run_async_operation(_execute_eventstream_operation("GET", endpoint))
    return [result]


def eventstream_list(
    workspace_id: str
) -> List[Dict[str, Any]]:
    """
    List all Eventstream items in a workspace.
    Authentication is handled transparently using Azure Identity.
    
    :param workspace_id: The workspace ID (UUID)
    :return: List of eventstream items
    """
    endpoint = f"/workspaces/{workspace_id}/items"
    
    result = _run_async_operation(_execute_eventstream_operation("GET", endpoint))
    
    # Filter only Eventstream items if the result contains a list
    if isinstance(result, dict) and "value" in result and isinstance(result["value"], list):
        eventstreams: List[Dict[str, Any]] = [item for item in result["value"] if isinstance(item, dict) and item.get("type") == "Eventstream"]
        return eventstreams
    elif isinstance(result, list):
        eventstreams = [item for item in result if isinstance(item, dict) and item.get("type") == "Eventstream"]
        return eventstreams
    
    return [result]


def eventstream_delete(
    workspace_id: str,
    item_id: str
) -> List[Dict[str, Any]]:
    """
    Delete an Eventstream item by workspace and item ID.
    Authentication is handled transparently using Azure Identity.
    
    :param workspace_id: The workspace ID (UUID)
    :param item_id: The eventstream item ID (UUID)
    :return: Deletion confirmation
    """
    endpoint = f"/workspaces/{workspace_id}/items/{item_id}"
    
    result = _run_async_operation(_execute_eventstream_operation("DELETE", endpoint))
    return [result]


def eventstream_update(
    workspace_id: str,
    item_id: str,
    definition: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Update an Eventstream item by workspace and item ID.
    Authentication is handled transparently using Azure Identity.
    
    :param workspace_id: The workspace ID (UUID)
    :param item_id: The eventstream item ID (UUID)
    :param definition: Updated eventstream definition
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
    
    result = _run_async_operation(_execute_eventstream_operation("PUT", endpoint, payload))
    return [result]


def eventstream_get_definition(
    workspace_id: str,
    item_id: str
) -> List[Dict[str, Any]]:
    """
    Get the definition of an Eventstream item.
    Authentication is handled transparently using Azure Identity.
    
    :param workspace_id: The workspace ID (UUID)
    :param item_id: The eventstream item ID (UUID)
    :return: Eventstream definition
    """
    endpoint = f"/workspaces/{workspace_id}/items/{item_id}/getDefinition"
    
    result = _run_async_operation(_execute_eventstream_operation("POST", endpoint))
    return [result]


# List of destructive operations
DESTRUCTIVE_TOOLS = {
    eventstream_create.__name__,
    eventstream_delete.__name__,
    eventstream_update.__name__,
}
