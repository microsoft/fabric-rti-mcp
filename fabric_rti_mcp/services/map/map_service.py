import base64
import json
import os
import time
import jsonschema
import jsonschema.exceptions

# import uuid
from typing import Any, Optional, Tuple

from fabric_rti_mcp.fabric_api_http_client import FabricHttpClientCache

# from fabric_rti_mcp.common import GlobalFabricRTIConfig, logger

# Microsoft Fabric API configuration

# DEFAULT_TIMEOUT = 30
# FABRIC_CONFIG = GlobalFabricRTIConfig.from_env()
map_schema = json.load(open(os.path.join(os.path.dirname(__file__), "schemas", "map_schema.json"), "r"))
bubble_layer_options_schema = json.load(open(os.path.join(os.path.dirname(__file__), "schemas", "bubble_layer_options_schema.json"), "r"))
heatmap_layer_options_schema = json.load(open(os.path.join(os.path.dirname(__file__), "schemas", "heatmap_layer_options_schema.json"), "r"))
line_layer_options_schema = json.load(open(os.path.join(os.path.dirname(__file__), "schemas", "line_layer_options_schema.json"), "r"))
polygon_layer_options_schema = json.load(open(os.path.join(os.path.dirname(__file__), "schemas", "polygon_layer_options_schema.json"), "r"))
basemap_options_schema = json.load(open(os.path.join(os.path.dirname(__file__), "schemas", "basemap_options_schema.json"), "r"))
layer_source_options_schema = json.load(open(os.path.join(os.path.dirname(__file__), "schemas", "layer_source_options_schema.json"), "r"))

def map_create(
    workspace_id: str,
    map_name: str,
    map_definition_json: dict[str, Any] | None = None,
    description: str | None = None,
    folder_id: str | None = None,
) -> dict[str, Any]:
    """
    Create a Map item in Microsoft Fabric.
    Validate the map definition JSON against the schema (fetch using get_map_definition_schema).
    Authentication is handled transparently using Azure Identity.

    :param workspace_id: The workspace ID (UUID)
    :param map_name: Name for the new map item
    :param map_definition_json: Map item definition (auto-generated basic one if not provided).
    :param description: Optional description for the map
    :param folder_id: Optional folder ID (UUID) to place the map in.
    If not specified, the Map is created with the workspace root folder.
    :return: Created map details
    """
    payload: dict[str, Any] = {"displayName": map_name}

    if description:
        payload["description"] = description

    if map_definition_json:
        # Validate the map definition JSON against the schema
        is_valid, error_message = _validate_map_definition(map_definition_json)
        if not is_valid:
            return {
                "success": False,
                "error": f"Invalid map definition JSON: {error_message}",
            }
        # Prepare the map definition as base64
        definition_json = json.dumps(map_definition_json)
        definition_b64 = base64.b64encode(definition_json.encode("utf-8")).decode("utf-8")

        payload["definition"] = {
            "parts": [
                {"path": "map.json", "payload": definition_b64, "payloadType": "InlineBase64"}
            ]
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
    endpoint = f"/workspaces/{workspace_id}/Maps/{item_id}"

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

    endpoint = f"/workspaces/{workspace_id}/Maps/{item_id}"

    result = FabricHttpClientCache.get_client().make_request("PATCH", endpoint, payload)

    return result


def map_get_definition(workspace_id: str, item_id: str) -> Optional[dict[str, Any]]:
    """
    Get the definition of a Map item.
    Authentication is handled transparently using Azure Identity.

    :param workspace_id: The workspace ID (UUID)
    :param item_id: The map item ID (UUID)
    :return: Map definition
    """
    endpoint = f"/workspaces/{workspace_id}/Maps/{item_id}/getDefinition"

    lro_result = FabricHttpClientCache.get_client().make_request("POST", endpoint)
    result = _resolve_lro_response(lro_result)
    map_definition_json = None

    if result \
        and "definition" in result \
        and "parts" in result["definition"] \
        and len(result["definition"]["parts"]) == 2:
        # Decode the base64-encoded map definition
        map_definition_b64 = result["definition"]["parts"][0]["payload"]
        map_definition_decoded = base64.b64decode(map_definition_b64).decode("utf-8")
        map_definition_json = json.loads(map_definition_decoded)

    return map_definition_json

def map_update_definition(workspace_id: str, item_id: str, map_definition_json: dict[str, Any]) -> Optional[dict[str, Any]]:
    """
    FETCH latest map definition using map_get_definition.
    UPDATE a Map item's definition by workspace and item ID.
    VALIDATE the updated map definition JSON against the schema (fetch using get_map_definition_schema).
        To fetch schema for basemap options, use get_basemap_options_schema.
        For layer source options, use get_layer_source_options_schema.
        For layer options (bubble, heatmap, line, polygon), use the respective functions (get_bubble_layer_options_schema, get_heatmap_layer_options_schema, get_line_layer_options_schema, get_polygon_layer_options_schema).
        Once options are finalized, SERIALIZE them 
        Eg: "layerSettings": [
            {
                "id": "your-layer-guid",
                "name": "My Layer",
                "sourceId": "your-source-guid",
                "options": "{\"color\":\"#1A73AA\",\"type\":\"vector\",\"visible\":true, \"pointLayerType\": \"bubble\", \"bubbleOptions\": {\"opacity\": 0.8, \"strokeWidth\": 2, \"strokeColor\": \"white\"}...}"
            }
        ]
    Authentication is handled transparently using Azure Identity.

    :param workspace_id: The workspace ID (UUID)
    :param item_id: The map item ID (UUID)
    :param map_definition_json: Updated map definition JSON (not encoded)
    :return: Updated map details
    """
    # Validate the map definition JSON against the schema
    is_valid, error_message = _validate_map_definition(map_definition_json)
    if not is_valid:
        return {
            "success": False,
            "error": f"Invalid map definition JSON: {error_message}",
        }

    # Prepare the map definition as base64
    map_definition_str = json.dumps(map_definition_json)
    map_definition_b64 = base64.b64encode(map_definition_str.encode("utf-8")).decode("utf-8")

    payload: dict[str, Any] = {
        "definition": {
            "parts": [
                {"path": "map.json", "payload": map_definition_b64, "payloadType": "InlineBase64"},
            ]
        }
    }

    endpoint = f"/workspaces/{workspace_id}/Maps/{item_id}/updateDefinition"

    lro_result = FabricHttpClientCache.get_client().make_request("POST", endpoint, payload)
    result = _resolve_lro_response(lro_result)

    return result

def get_map_definition_schema() -> dict[str, Any]:
    """
    Get the map definition schema.
    To fetch schema for basemap options, use get_basemap_options_schema.
    For layer source options, use get_layer_source_options_schema.
    For layer options (bubble, heatmap, line, polygon), use the respective functions (get_bubble_layer_options_schema, get_heatmap_layer_options_schema, get_line_layer_options_schema, get_polygon_layer_options_schema).

    Also read get_map_basemap_options_schema and get_layer_source_options_schema to understand this better.
    :return: The map definition schema
    """
    return map_schema

def get_bubble_layer_options_schema() -> dict[str, Any]:
    """
    Get the bubble layer options schema.
    Once bubble layer options are created, you can store them under LayerSetting.options in the map definition JSON.
    Eg: "layerSettings": [
       {
         "id": "your-layer-guid",
         "name": "My Layer",
         "sourceId": "your-source-guid",
         "options": "{\"color\":\"#1A73AA\",\"type\":\"vector\",\"visible\":true, \"pointLayerType\": \"bubble\", \"bubbleOptions\": {\"opacity\": 0.8, \"strokeWidth\": 2, \"strokeColor\": \"white\"}...}"
       }
    ]

    :return: The bubble layer options schema
    """
    return bubble_layer_options_schema

def get_heatmap_layer_options_schema() -> dict[str, Any]:
    """
    Get the heatmap layer options schema.
    Once heatmap layer options are created, you can store them under LayerSetting.options in the map definition JSON.
    Eg: "layerSettings": [
       {
         "id": "your-layer-guid",
         "name": "My Layer",
         "sourceId": "your-source-guid",
         "options": "{\"color\":\"#1A73AA\",\"type\":\"vector\",\"visible\":true, \"pointLayerType\": \"heatmap\", \"heatmapOptions\": {\"opacity\": 0.8, \"radius\": 10, \"blur\": 0.8}...}"
       }
    ]

    :return: The heatmap layer options schema
    """
    return heatmap_layer_options_schema

def get_line_layer_options_schema() -> dict[str, Any]:
    """
    Get the line layer options schema.
    Once line layer options are created, you can store them under LayerSetting.options in the map definition JSON.
    Eg: "layerSettings": [
       {
         "id": "your-layer-guid",
         "name": "My Layer",
         "sourceId": "your-source-guid",
         "options": "{\"color\":\"#1A73AA\",\"type\":\"vector\",\"visible\":true, \"lineLayerType\": \"line\", \"lineOptions\": {\"opacity\": 0.8, \"strokeWidth\": 2, \"strokeColor\": \"white\"}...}"
       }
    ]

    :return: The line layer options schema
    """
    return line_layer_options_schema

def get_polygon_layer_options_schema() -> dict[str, Any]:
    """
    Get the polygon layer options schema.
    Once polygon layer options are created, you can store them under LayerSetting.options in the map definition JSON.
    Eg: "layerSettings": [
       {
         "id": "your-layer-guid",
         "name": "My Layer",
         "sourceId": "your-source-guid",
         "options": "{\"color\":\"#1A73AA\",\"type\":\"vector\",\"visible\":true, \"polygonLayerType\": \"polygon\", \"polygonOptions\": {\"opacity\": 0.8, \"strokeWidth\": 2, \"strokeColor\": \"white\"}...}"
       }
    ]

    :return: The polygon layer options schema
    """
    return polygon_layer_options_schema

def get_basemap_options_schema() -> dict[str, Any]:
    """
    Get the basemap options schema.
    Once basemap options are created, you can store them under Basemap.options in the map definition JSON.
    Eg: "basemap": {
       "id": "your-basemap-guid",
       "name": "My Basemap",
       "options": "{\"color\":\"#1A73AA\",\"type\":\"vector\",\"visible\":true, \"basemapType\": \"streets\", \"basemapOptions\": {\"opacity\": 0.8}...}"
    }

    Also read get_map_schema and get_layer_source_options_schema to understand this better.

    :return: The basemap options schema
    """
    return basemap_options_schema

def get_layer_source_options_schema() -> dict[str, Any]:
    """
    Get the layer source options schema.
    Once layer source options are created, you can store them under LayerSource.options in the map definition JSON.
    Eg: "layerSources": [
       {
         "id": "your-source-guid",
         "name": "My Source",
         "options": "{\"color\":\"#1A73AA\",\"type\":\"vector\",\"visible\":true, \"sourceType\": \"geojson\", \"geojsonOptions\": {\"url\": \"https://example.com/data.geojson\"}...}"
       }
    ]

    Also read get_map_schema and get_basemap_options_schema to understand this better.

    :return: The layer source options schema
    """
    return layer_source_options_schema

def _resolve_lro_response(response: dict[str, Any]) -> Optional[dict[str, Any]]:
    """
    Resolve the long-running operation (LRO) response.
    Authentication is handled transparently using Azure Identity.

    :param response: The LRO response
    :return: The final result of the LRO
    """
    if response.get("success", False) and response.get("status_code") == 202:
        operation_id = response.get("headers", {}).get("x-ms-operation-id", None)
        if operation_id:
            operation_url = f"/operations/{operation_id}"
            result_url = f"{operation_url}/result"
            # Use the operation URL to poll for the LRO completion
            # Once the LRO is completed, return the final result using the result URL

            counter = 0
            while counter < 5:  # Poll for a maximum of 5 seconds
                lro_response = FabricHttpClientCache.get_client().make_request("GET", operation_url)
                lro_status = lro_response.get("status", None)
                if lro_status == "Failed": # If the LRO has failed, return the error
                    return lro_response
                elif lro_status == "Succeeded": # If the LRO has succeeded, return the final result
                    return FabricHttpClientCache.get_client().make_request("GET", result_url)
                else: # If the LRO is still in progress, wait for 1 second before polling again
                    counter += 1
                    time.sleep(1)
    return None

def _validate_schema(input_json: dict[str, Any], schema: dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate the input JSON against the given schema.
    Authentication is handled transparently using Azure Identity.

    :param input_json: The JSON to validate
    :param schema: The schema to validate against
    :return: True if the JSON is valid, False otherwise
    """
    try:
        jsonschema.validate(instance=input_json, schema=schema)
        return (True, "")
    except jsonschema.exceptions.ValidationError as e:
        return (False, e.message)
    except Exception as e:
        return (False, str(e))

def _validate_map_definition(map_definition_json: dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate the map definition JSON against the schema.
    Authentication is handled transparently using Azure Identity.

    :param map_definition_json: The map definition JSON to validate
    :return: True if the map definition is valid, False otherwise
    """
    return _validate_schema(map_definition_json, map_schema)