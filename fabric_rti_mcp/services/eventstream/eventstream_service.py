import base64
import json
import uuid
from datetime import datetime
from typing import Any

from fabric_rti_mcp.fabric_api_http_client import FabricHttpClientCache

# Microsoft Fabric API configuration

DEFAULT_TIMEOUT = 30


def eventstream_create(
    workspace_id: str,
    eventstream_name: str | None = None,
    eventstream_id: str | None = None,
    definition: dict[str, Any] | None = None,
    description: str | None = None,
) -> list[dict[str, Any] | Any]:
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

    payload: dict[str, Any] = {
        "displayName": eventstream_name,
        "type": "Eventstream",
        "definition": {
            "parts": [{"path": "eventstream.json", "payload": definition_b64, "payloadType": "InlineBase64"}]
        },
    }

    if description:
        payload["description"] = description

    endpoint = f"/workspaces/{workspace_id}/items"

    result = FabricHttpClientCache.get_client().make_request("POST", endpoint, payload)
    return [result]


def eventstream_get(workspace_id: str, item_id: str) -> list[dict[str, Any]]:
    """
    Get an Eventstream item by workspace and item ID.
    Authentication is handled transparently using Azure Identity.

    :param workspace_id: The workspace ID (UUID)
    :param item_id: The eventstream item ID (UUID)
    :return: Eventstream item details
    """
    endpoint = f"/workspaces/{workspace_id}/items/{item_id}"

    result = FabricHttpClientCache.get_client().make_request("GET", endpoint)
    return [result]


def eventstream_list(workspace_id: str) -> list[dict[str, Any]]:
    """
    List all Eventstream items in a workspace.
    Authentication is handled transparently using Azure Identity.

    :param workspace_id: The workspace ID (UUID)
    :return: List of eventstream items
    """
    endpoint = f"/workspaces/{workspace_id}/items"

    result = FabricHttpClientCache.get_client().make_request("GET", endpoint)

    # Filter only Eventstream items if the result contains a list
    if "value" in result and isinstance(result["value"], list):
        eventstreams: list[dict[str, Any]] = [
            item
            for item in result["value"]  # type: ignore
            if isinstance(item, dict) and item.get("type") == "Eventstream"  # type: ignore
        ]
        return eventstreams

    return [result]


def eventstream_delete(workspace_id: str, item_id: str) -> list[dict[str, Any]]:
    """
    Delete an Eventstream item by workspace and item ID.
    Authentication is handled transparently using Azure Identity.

    :param workspace_id: The workspace ID (UUID)
    :param item_id: The eventstream item ID (UUID)
    :return: Deletion confirmation
    """
    endpoint = f"/workspaces/{workspace_id}/items/{item_id}"

    result = FabricHttpClientCache.get_client().make_request("DELETE", endpoint)
    return [result]


def eventstream_update(workspace_id: str, item_id: str, definition: dict[str, Any]) -> list[dict[str, Any]]:
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

    payload: dict[str, Any] = {
        "definition": {
            "parts": [{"path": "eventstream.json", "payload": definition_b64, "payloadType": "InlineBase64"}]
        }
    }

    endpoint = f"/workspaces/{workspace_id}/items/{item_id}"

    result = FabricHttpClientCache.get_client().make_request("PUT", endpoint, payload)
    return [result]


def eventstream_get_definition(workspace_id: str, item_id: str) -> list[dict[str, Any]]:
    """
    Get the definition of an Eventstream item.
    Authentication is handled transparently using Azure Identity.

    :param workspace_id: The workspace ID (UUID)
    :param item_id: The eventstream item ID (UUID)
    :return: Eventstream definition
    """
    endpoint = f"/workspaces/{workspace_id}/items/{item_id}/getDefinition"

    result = FabricHttpClientCache.get_client().make_request("POST", endpoint)
    return [result]


def _create_basic_eventstream_definition(name: str, stream_id: str | None = None) -> dict[str, Any]:
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


def eventstream_create_simple(workspace_id: str, name: str, description: str | None = None) -> list[dict[str, Any]]:
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
