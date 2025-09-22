import base64
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fabric_rti_mcp.common import GlobalFabricRTIConfig, logger
from fabric_rti_mcp.utils import FabricConnection, run_async_operation

# Microsoft Fabric API configuration

DEFAULT_TIMEOUT = 30
FABRIC_CONFIG = GlobalFabricRTIConfig.from_env()


class EventstreamConnectionCache:
    """Simple connection cache for Eventstream API clients using Azure Identity."""

    def __init__(self) -> None:
        self._connection: Optional[FabricConnection] = None

    def get_connection(self) -> FabricConnection:
        """Get or create an Eventstream connection using the configured API base URL."""
        if self._connection is None:
            api_base = FABRIC_CONFIG.fabric_api_base
            self._connection = FabricConnection(api_base, service_name="Eventstream")
            logger.info(f"Created Eventstream connection for API base: {api_base}")

        return self._connection


EVENTSTREAM_CONNECTION_CACHE = EventstreamConnectionCache()


def get_eventstream_connection() -> FabricConnection:
    """Get or create an Eventstream connection using the configured API base URL."""
    return EVENTSTREAM_CONNECTION_CACHE.get_connection()


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

    connection = get_eventstream_connection()
    result = run_async_operation(connection.execute_operation_and_return_error_in_dict("POST", endpoint, payload))
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

    connection = get_eventstream_connection()
    result = run_async_operation(connection.execute_operation_and_return_error_in_dict("GET", endpoint))
    return [result]


def eventstream_list(workspace_id: str) -> List[Dict[str, Any]]:
    """
    List all Eventstream items in a workspace.
    Authentication is handled transparently using Azure Identity.

    :param workspace_id: The workspace ID (UUID)
    :return: List of eventstream items
    """
    connection = get_eventstream_connection()
    
    result = run_async_operation(connection.list_artifacts_of_type(workspace_id, "Eventstream"))
    return result


def eventstream_delete(workspace_id: str, item_id: str) -> List[Dict[str, Any]]:
    """
    Delete an Eventstream item by workspace and item ID.
    Authentication is handled transparently using Azure Identity.

    :param workspace_id: The workspace ID (UUID)
    :param item_id: The eventstream item ID (UUID)
    :return: Deletion confirmation
    """
    endpoint = f"/workspaces/{workspace_id}/items/{item_id}"

    connection = get_eventstream_connection()
    result = run_async_operation(connection.execute_operation_and_return_error_in_dict("DELETE", endpoint))
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

    connection = get_eventstream_connection()
    result = run_async_operation(connection.execute_operation_and_return_error_in_dict("PUT", endpoint, payload))
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

    connection = get_eventstream_connection()
    result = run_async_operation(connection.execute_operation_and_return_error_in_dict("POST", endpoint))
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
