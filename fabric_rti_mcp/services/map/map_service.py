import base64
import json

# import uuid
from typing import Any

from fabric_rti_mcp.fabric_api_http_client import FabricHttpClientCache

# from fabric_rti_mcp.common import GlobalFabricRTIConfig, logger

# Microsoft Fabric API configuration

# DEFAULT_TIMEOUT = 30
# FABRIC_CONFIG = GlobalFabricRTIConfig.from_env()


def map_create(
    workspace_id: str,
    map_name: str,
    definition: dict[str, Any] | None = None,
    description: str | None = None,
    folder_id: str | None = None,
) -> dict[str, Any]:
    """
    Create a Map item in Microsoft Fabric.
    Authentication is handled transparently using Azure Identity.

    :param workspace_id: The workspace ID (UUID)
    :param map_name: Name for the new map item
    :param definition: Map item definition (auto-generated basic one if not provided)
    :param description: Optional description for the map
    :param folder_id: Optional folder ID (UUID) to place the map in.
    If not specified, the Map is created with the workspace root folder.
    :return: Created map details
    """
    payload: dict[str, Any] = {"displayName": map_name}

    if description:
        payload["description"] = description

    if definition:
        # Prepare the map definition as base64
        definition_json = json.dumps(definition)
        definition_b64 = base64.b64encode(definition_json.encode("utf-8")).decode("utf-8")

        payload["definition"] = {
            "parts": [{"path": "map.json", "payload": definition_b64, "payloadType": "InlineBase64"}]
        }

    if folder_id:
        payload["folderId"] = folder_id

    endpoint = f"/workspaces/{workspace_id}/Maps"

    result = FabricHttpClientCache.get_client().make_request("POST", endpoint, payload)
    return result


def map_get(workspace_id: str, item_id: str) -> dict[str, Any]:
    """
    Get a Map item by workspace and item ID.
    Authentication is handled transparently using Azure Identity.

    :param workspace_id: The workspace ID (UUID) of the Map item
    :param item_id: The map item ID (UUID)
    :return: Map item details
    """
    endpoint = f"/workspaces/{workspace_id}/Maps/{item_id}"

    result = FabricHttpClientCache.get_client().make_request("GET", endpoint)
    return result


def map_list(workspace_id: str) -> dict[str, Any]:
    """
    List all Map items in a workspace.
    Authentication is handled transparently using Azure Identity.

    :param workspace_id: The workspace ID (UUID)
    :return: The list of map items in the specified workspace or error details
    """
    endpoint = f"/workspaces/{workspace_id}/Maps"

    result = FabricHttpClientCache.get_client().make_request("GET", endpoint)

    return result


def map_delete(workspace_id: str, item_id: str) -> dict[str, Any]:
    """
    Delete a Map item by workspace and item ID.
    Authentication is handled transparently using Azure Identity.

    :param workspace_id: The workspace ID (UUID)
    :param item_id: The map item ID (UUID)
    :return: Error details or empty response on success
    """
    endpoint = f"/workspaces/{workspace_id}/items/{item_id}"

    result = FabricHttpClientCache.get_client().make_request("DELETE", endpoint)

    return result


def map_update(
    workspace_id: str, item_id: str, display_name: str | None = None, description: str | None = None
) -> dict[str, Any]:
    """
    Update a Map item's display name and description by workspace and item ID.
    Authentication is handled transparently using Azure Identity.

    :param workspace_id: The workspace ID (UUID)
    :param item_id: The Map item ID (UUID)
    :param display_name: The Map display name. The display name must follow naming rules according to item type.
    :param description: The Map description. Maximum length is 256 characters.
    :return: Updated map details
    """

    payload: dict[str, Any] = {}

    if display_name:
        payload["displayName"] = display_name

    if description:
        payload["description"] = description

    endpoint = f"/workspaces/{workspace_id}/items/{item_id}"

    result = FabricHttpClientCache.get_client().make_request("PATCH", endpoint, payload)

    return result


def map_update_definition(workspace_id: str, item_id: str, definition: dict[str, Any]) -> dict[str, Any]:
    """
    Update a Map item's definition by workspace and item ID.
    Authentication is handled transparently using Azure Identity.

    :param workspace_id: The workspace ID (UUID)
    :param item_id: The map item ID (UUID)
    :param definition: Updated map definition
    :return: Updated map details
    """
    # Prepare the map definition as base64
    definition_json = json.dumps(definition)
    definition_b64 = base64.b64encode(definition_json.encode("utf-8")).decode("utf-8")

    payload: dict[str, Any] = {
        "definition": {"parts": [{"path": "map.json", "payload": definition_b64, "payloadType": "InlineBase64"}]}
    }

    endpoint = f"/workspaces/{workspace_id}/Maps/{item_id}/updateDefinition"

    result = FabricHttpClientCache.get_client().make_request("POST", endpoint, payload)

    return result


def map_get_definition(workspace_id: str, item_id: str) -> dict[str, Any]:
    """
    Get the definition of a Map item.
    Authentication is handled transparently using Azure Identity.

    :param workspace_id: The workspace ID (UUID)
    :param item_id: The map item ID (UUID)
    :return: Map definition
    """
    endpoint = f"/workspaces/{workspace_id}/items/{item_id}/getDefinition"

    result = FabricHttpClientCache.get_client().make_request("GET", endpoint)

    return result
