import asyncio
import base64
import json
import uuid
from datetime import datetime
from typing import Any, Coroutine, Dict, List, Optional

from fabric_rti_mcp.common import GlobalFabricRTIConfig, logger
from fabric_rti_mcp.eventstream.eventstream_connection import EventstreamConnection

# Microsoft Fabric API configuration

DEFAULT_TIMEOUT = 30
FABRIC_CONFIG = GlobalFabricRTIConfig.from_env()


class EventstreamConnectionCache:
    """Simple connection cache for Eventstream API clients using Azure Identity."""

    def __init__(self) -> None:
        self._connection: Optional[EventstreamConnection] = None

    def get_connection(self) -> EventstreamConnection:
        """Get or create an Eventstream connection using the configured API base URL."""
        if self._connection is None:
            api_base = FABRIC_CONFIG.fabric_api_base
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
        return {"error": True, "message": str(e)}


def eventstream_create(
    workspace_id: str,
    eventstream_name: Optional[str] = None,
    eventstream_id: Optional[str] = None,
    definition: Optional[Dict[str, Any]] = None,
    description: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Create an Eventstream item in Microsoft Fabric.
    Authentication is handled transparently using Azure Identity.

    User-friendly options:
    - Provide only eventstream_name: Auto-generates IDs and creates basic eventstream
    - Provide only eventstream_id: Auto-generates name as "Eventstream_YYYYMMDD_HHMMSS"
    - Provide both: Uses your specified values
    - Provide full definition: Advanced users can specify complete eventstream config

    :param workspace_id: The workspace ID (UUID)
    :param eventstream_name: Name for the new eventstream (auto-generated if not provided)
    :param eventstream_id: ID for the eventstream (auto-generated if not provided)
    :param definition: Eventstream definition (auto-generated basic one if not provided)
    :param description: Optional description for the eventstream
    :return: Created eventstream details
    """
    # Auto-generate name if ID provided but name is not
    if eventstream_id and not eventstream_name:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        eventstream_name = f"Eventstream_{timestamp}"

    # Auto-generate name if neither provided
    if not eventstream_name and not eventstream_id:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        eventstream_name = f"Eventstream_{timestamp}"

    # Ensure we have a name at this point
    if not eventstream_name:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        eventstream_name = f"Eventstream_{timestamp}"

    # Auto-generate definition if not provided
    if definition is None:
        stream_id = eventstream_id or str(uuid.uuid4())
        definition = _create_basic_eventstream_definition(eventstream_name, stream_id)

    # Prepare the eventstream definition as base64
    definition_json = json.dumps(definition)
    definition_b64 = base64.b64encode(definition_json.encode("utf-8")).decode("utf-8")

    payload: Dict[str, Any] = {
        "displayName": eventstream_name,
        "type": "Eventstream",
        "definition": {
            "parts": [{"path": "eventstream.json", "payload": definition_b64, "payloadType": "InlineBase64"}]
        },
    }

    if description:
        payload["description"] = description

    endpoint = f"/workspaces/{workspace_id}/items"

    result = _run_async_operation(_execute_eventstream_operation("POST", endpoint, payload))
    return [result]


def eventstream_get(workspace_id: str, item_id: str) -> List[Dict[str, Any]]:
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


def eventstream_list(workspace_id: str) -> List[Dict[str, Any]]:
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
        eventstreams: List[Dict[str, Any]] = [
            item
            for item in result["value"]  # type: ignore
            if isinstance(item, dict) and item.get("type") == "Eventstream"  # type: ignore
        ]
        return eventstreams
    elif isinstance(result, list):
        eventstreams = [
            item
            for item in result  # type: ignore
            if isinstance(item, dict) and item.get("type") == "Eventstream"  # type: ignore
        ]
        return eventstreams

    return [result]


def eventstream_delete(workspace_id: str, item_id: str) -> List[Dict[str, Any]]:
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


def eventstream_update(workspace_id: str, item_id: str, definition: Dict[str, Any]) -> List[Dict[str, Any]]:
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
            "parts": [{"path": "eventstream.json", "payload": definition_b64, "payloadType": "InlineBase64"}]
        }
    }

    endpoint = f"/workspaces/{workspace_id}/items/{item_id}"

    result = _run_async_operation(_execute_eventstream_operation("PUT", endpoint, payload))
    return [result]


def eventstream_get_definition(workspace_id: str, item_id: str) -> List[Dict[str, Any]]:
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


def _create_basic_eventstream_definition(name: str, stream_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a basic eventstream definition that can be extended later.

    :param name: Name for the default stream
    :param stream_id: ID for the default stream (auto-generated if not provided)
    :return: Basic eventstream definition
    """
    if stream_id is None:
        stream_id = str(uuid.uuid4())

    return {
        "compatibilityLevel": "1.0",
        "sources": [],
        "destinations": [],
        "operators": [],
        "streams": [
            {"id": stream_id, "name": f"{name}-stream", "type": "DefaultStream", "properties": {}, "inputNodes": []}
        ],
    }


def eventstream_create_simple(workspace_id: str, name: str, description: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Simple eventstream creation - just provide workspace and name.
    Perfect for quick testing and getting started.

    :param workspace_id: The workspace ID (UUID)
    :param name: Name for the new eventstream
    :param description: Optional description
    :return: Created eventstream details
    """
    return eventstream_create(workspace_id=workspace_id, eventstream_name=name, description=description)


# List of destructive operations
DESTRUCTIVE_TOOLS = {
    eventstream_create.__name__,
    eventstream_create_simple.__name__,
    eventstream_delete.__name__,
    eventstream_update.__name__,
}
