import base64
import json
import uuid
from typing import Any, cast

from fabric_rti_mcp.fabric_api_http_client import FabricHttpClientCache

_CONFIGURATION_DEFINITION_PART_PATH = "Configurations.json"


def _extract_configuration_document(definition_result: dict[str, Any]) -> dict[str, Any]:
    definition = definition_result.get("definition")
    if not isinstance(definition, dict):
        return {"error": "Missing 'definition' field", "result": definition_result}

    definition = cast(dict[str, Any], definition)

    parts = definition.get("parts")
    if not isinstance(parts, list):
        return {"error": "Missing 'definition.parts' list", "result": definition_result}

    configuration_part: dict[str, Any] | None = None
    for part_any in cast(list[Any], parts):
        if not isinstance(part_any, dict):
            continue
        part = cast(dict[str, Any], part_any)
        if part.get("path") == _CONFIGURATION_DEFINITION_PART_PATH:
            configuration_part = part
            break

    if configuration_part is None:
        return {
            "error": f"Definition part '{_CONFIGURATION_DEFINITION_PART_PATH}' not found",
            "result": definition_result,
        }

    payload = configuration_part.get("payload")
    payload_type = configuration_part.get("payloadType")

    if not isinstance(payload, str) or payload.strip() == "":
        return {"error": "Configuration payload missing or not a string", "result": definition_result}

    if payload_type != "InlineBase64":
        return {"error": f"Unsupported payloadType '{payload_type}'", "result": definition_result}

    try:
        decoded = base64.b64decode(payload).decode("utf-8")
    except Exception as exc:  # noqa: BLE001
        return {"error": f"Failed to base64-decode configuration payload: {exc}", "result": definition_result}

    try:
        document = json.loads(decoded)
    except Exception as exc:  # noqa: BLE001
        return {"error": f"Failed to parse configuration JSON: {exc}", "decoded": decoded}

    if not isinstance(document, dict):
        return {"error": "Configuration JSON is not an object", "decoded": decoded}

    return cast(dict[str, Any], document)


def _get_agent_configuration_document(workspace_id: str, item_id: str) -> dict[str, Any]:
    definition_result = _operationagent_get_definition(workspace_id, item_id)
    return _extract_configuration_document(definition_result)


def _get_configuration_dict(document: dict[str, Any]) -> dict[str, Any] | None:
    configuration = document.get("configuration")
    if isinstance(configuration, dict):
        return cast(dict[str, Any], configuration)
    return None


def _ensure_configuration_dict(document: dict[str, Any]) -> dict[str, Any]:
    configuration = document.get("configuration")
    if not isinstance(configuration, dict):
        configuration = {}
        document["configuration"] = configuration
    return cast(dict[str, Any], configuration)


def _get_agent_configuration_document_for_update(workspace_id: str, item_id: str) -> dict[str, Any]:
    document = _get_agent_configuration_document(workspace_id, item_id)
    if "error" in document:
        return document

    _ensure_configuration_dict(document)

    return document


def _ensure_string(value: Any) -> str | None:
    if isinstance(value, str):
        stripped = value.strip()
        if stripped != "":
            return stripped
    return None


def _normalize_id_keyed_object(value: Any) -> dict[str, dict[str, Any]]:
    if isinstance(value, dict):
        result: dict[str, dict[str, Any]] = {}
        for key, item_any in cast(dict[str, Any], value).items():
            if isinstance(item_any, dict):
                result[str(key)] = cast(dict[str, Any], item_any)
        return result

    if isinstance(value, list):
        result = {}
        for item_any in cast(list[Any], value):
            if not isinstance(item_any, dict):
                continue
            item = cast(dict[str, Any], item_any)
            item_id = _ensure_string(item.get("id")) or str(uuid.uuid4())
            item["id"] = item_id
            result[item_id] = item
        return result

    return {}


def operationagent_list(workspace_id: str) -> list[dict[str, Any]]:
    """
    List all OperationAgent items in a Fabric workspace.

    This uses the OperationsAgents endpoint.

    :param workspace_id: The Fabric workspace ID (UUID)
    :return: List of OperationAgent items
    """
    endpoint = f"/workspaces/{workspace_id}/OperationsAgents"
    result = FabricHttpClientCache.get_client().make_request("GET", endpoint)

    if "value" in result and isinstance(result["value"], list):
        value = cast(list[Any], result["value"])
        items: list[dict[str, Any]] = [cast(dict[str, Any], item) for item in value if isinstance(item, dict)]
        return items

    return [result]


def operationagent_get(workspace_id: str, item_id: str) -> dict[str, Any]:
    """
    Get an OperationAgent item by workspace and item ID.

    :param workspace_id: The Fabric workspace ID (UUID)
    :param item_id: The OperationAgent item ID (UUID)
    :return: OperationAgent item details
    """
    endpoint = f"/workspaces/{workspace_id}/OperationsAgents/{item_id}"
    return FabricHttpClientCache.get_client().make_request("GET", endpoint)


def _operationagent_get_definition(workspace_id: str, item_id: str) -> dict[str, Any]:
    """
    Get the definition of an OperationAgent item.

    :param workspace_id: The Fabric workspace ID (UUID)
    :param item_id: The OperationAgent item ID (UUID)
    :return: Item definition
    """
    endpoint = f"/workspaces/{workspace_id}/OperationsAgents/{item_id}/getDefinition"
    return FabricHttpClientCache.get_client().make_request("POST", endpoint)


def operationagent_get_goals(workspace_id: str, item_id: str) -> dict[str, Any]:
    """Get the configured natural-language goals for an OperationAgent."""

    document = _get_agent_configuration_document(workspace_id, item_id)
    if "error" in document:
        return document

    configuration = _get_configuration_dict(document)
    if configuration is None:
        return {"goals": None}

    return {"goals": configuration.get("goals")}


def operationagent_get_instructions(workspace_id: str, item_id: str) -> dict[str, Any]:
    """Get the configured instructions for an OperationAgent."""

    document = _get_agent_configuration_document(workspace_id, item_id)
    if "error" in document:
        return document

    configuration = _get_configuration_dict(document)
    if configuration is None:
        return {"instructions": None}

    return {"instructions": configuration.get("instructions")}


def operationagent_get_knowledge_sources(workspace_id: str, item_id: str) -> dict[str, Any]:
    """Get the configured knowledge sources (dataSources) for an OperationAgent."""

    document = _get_agent_configuration_document(workspace_id, item_id)
    if "error" in document:
        return document

    configuration = _get_configuration_dict(document)
    if configuration is None:
        return {"knowledge_sources": []}

    data_sources = configuration.get("dataSources")
    if isinstance(data_sources, dict):
        # Most schemas use an object keyed by id.
        data_sources_dict = cast(dict[str, Any], data_sources)
        sources: list[dict[str, Any]] = [
            cast(dict[str, Any], value) for value in data_sources_dict.values() if isinstance(value, dict)
        ]
        return {"knowledge_sources": sources}

    if isinstance(data_sources, list):
        sources = [cast(dict[str, Any], value) for value in cast(list[Any], data_sources) if isinstance(value, dict)]
        return {"knowledge_sources": sources}

    return {"knowledge_sources": []}


def operationagent_get_actions(workspace_id: str, item_id: str) -> dict[str, Any]:
    """Get the configured actions for an OperationAgent."""

    document = _get_agent_configuration_document(workspace_id, item_id)
    if "error" in document:
        return document

    configuration = _get_configuration_dict(document)
    if configuration is None:
        return {"actions": {}}

    actions = configuration.get("actions")
    if isinstance(actions, dict):
        return {"actions": actions}

    return {"actions": {}}


def operationagent_set_goals(workspace_id: str, item_id: str, goals: str) -> dict[str, Any]:
    """Set the natural-language goals for an OperationAgent."""

    document = _get_agent_configuration_document_for_update(workspace_id, item_id)
    if "error" in document:
        return document

    configuration = cast(dict[str, Any], document["configuration"])
    configuration["goals"] = goals

    return _operationagent_update_definition(workspace_id, item_id, document)


def operationagent_set_instructions(workspace_id: str, item_id: str, instructions: str) -> dict[str, Any]:
    """Set the instructions for an OperationAgent."""

    document = _get_agent_configuration_document_for_update(workspace_id, item_id)
    if "error" in document:
        return document

    configuration = cast(dict[str, Any], document["configuration"])
    configuration["instructions"] = instructions

    return _operationagent_update_definition(workspace_id, item_id, document)


def operationagent_add_knowledge_source(
    workspace_id: str,
    item_id: str,
    knowledge_source: dict[str, Any],
    knowledge_source_id: str | None = None,
) -> dict[str, Any]:
    """
    Add or replace a knowledge source (dataSource) in an OperationAgent.

    The OperationAgent schema typically stores data sources in `configuration.dataSources` as an object keyed by id.
    This tool normalizes list/dict variants to an id-keyed object.

    :param workspace_id: The Fabric workspace ID (UUID)
    :param item_id: The OperationAgent item ID (UUID)
    :param knowledge_source: Knowledge source object to add
    :param knowledge_source_id: Optional id to use; defaults to knowledge_source["id"] or a generated UUID
    :return: Update result; includes the knowledge_source_id
    """

    document = _get_agent_configuration_document_for_update(workspace_id, item_id)
    if "error" in document:
        return document

    configuration = cast(dict[str, Any], document["configuration"])

    existing = _normalize_id_keyed_object(configuration.get("dataSources"))
    source_id = _ensure_string(knowledge_source_id) or _ensure_string(knowledge_source.get("id")) or str(uuid.uuid4())
    knowledge_source["id"] = source_id
    existing[source_id] = knowledge_source
    configuration["dataSources"] = existing

    result = _operationagent_update_definition(workspace_id, item_id, document)
    return {"knowledge_source_id": source_id, "result": result}


def operationagent_remove_knowledge_source(workspace_id: str, item_id: str, knowledge_source_id: str) -> dict[str, Any]:
    """Remove a knowledge source (dataSource) from an OperationAgent by id."""

    document = _get_agent_configuration_document_for_update(workspace_id, item_id)
    if "error" in document:
        return document

    configuration = cast(dict[str, Any], document["configuration"])
    existing = _normalize_id_keyed_object(configuration.get("dataSources"))

    source_id = _ensure_string(knowledge_source_id)
    if source_id is None or source_id not in existing:
        return {"removed": False, "knowledge_source_id": knowledge_source_id}

    existing.pop(source_id, None)
    configuration["dataSources"] = existing

    result = _operationagent_update_definition(workspace_id, item_id, document)
    return {"removed": True, "knowledge_source_id": source_id, "result": result}


def operationagent_add_action(
    workspace_id: str,
    item_id: str,
    action: dict[str, Any],
    action_id: str | None = None,
) -> dict[str, Any]:
    """
    Add or replace an action in an OperationAgent.

    Actions are stored in `configuration.actions` as an object keyed by action id.

    :param workspace_id: The Fabric workspace ID (UUID)
    :param item_id: The OperationAgent item ID (UUID)
    :param action: Action object to add
    :param action_id: Optional id to use; defaults to a generated UUID
    :return: Update result; includes the action_id
    """

    document = _get_agent_configuration_document_for_update(workspace_id, item_id)
    if "error" in document:
        return document

    configuration = cast(dict[str, Any], document["configuration"])
    actions_any = configuration.get("actions")
    actions: dict[str, Any] = cast(dict[str, Any], actions_any) if isinstance(actions_any, dict) else {}

    resolved_action_id = _ensure_string(action_id) or _ensure_string(action.get("id")) or str(uuid.uuid4())
    action.setdefault("id", resolved_action_id)
    actions[resolved_action_id] = action
    configuration["actions"] = actions

    result = _operationagent_update_definition(workspace_id, item_id, document)
    return {"action_id": resolved_action_id, "result": result}


def operationagent_remove_action(workspace_id: str, item_id: str, action_id: str) -> dict[str, Any]:
    """Remove an action from an OperationAgent by id."""

    document = _get_agent_configuration_document_for_update(workspace_id, item_id)
    if "error" in document:
        return document

    configuration = cast(dict[str, Any], document["configuration"])
    actions_any = configuration.get("actions")
    actions: dict[str, Any] = cast(dict[str, Any], actions_any) if isinstance(actions_any, dict) else {}

    resolved_action_id = _ensure_string(action_id)
    if resolved_action_id is None or resolved_action_id not in actions:
        return {"removed": False, "action_id": action_id}

    actions.pop(resolved_action_id, None)
    configuration["actions"] = actions

    result = _operationagent_update_definition(workspace_id, item_id, document)
    return {"removed": True, "action_id": resolved_action_id, "result": result}


def operationagent_create(
    workspace_id: str,
    display_name: str,
    definition: dict[str, Any] | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """
    Create an OperationAgent item in a Fabric workspace.

    Note: Fabric may require a valid definition for some item types. If you don't provide a
    definition and the API rejects the request, supply one via the `definition` parameter.

    :param workspace_id: The Fabric workspace ID (UUID)
    :param display_name: Display name for the new item
    :param definition: Optional item definition (JSON) encoded and sent as a definition part
    :param description: Optional description
    :return: Created item details
    """
    payload: dict[str, Any] = {"displayName": display_name}

    if description is not None:
        payload["description"] = description

    if definition is not None:
        definition_json = json.dumps(definition)
        definition_b64 = base64.b64encode(definition_json.encode("utf-8")).decode("utf-8")
        payload["definition"] = {
            "parts": [
                {
                    "path": _CONFIGURATION_DEFINITION_PART_PATH,
                    "payload": definition_b64,
                    "payloadType": "InlineBase64",
                }
            ]
        }

    endpoint = f"/workspaces/{workspace_id}/OperationsAgents"
    return FabricHttpClientCache.get_client().make_request("POST", endpoint, payload)


def operationagent_update(
    workspace_id: str,
    item_id: str,
    display_name: str | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """
    Update an OperationAgent item's metadata.

    :param workspace_id: The Fabric workspace ID (UUID)
    :param item_id: The OperationAgent item ID (UUID)
    :param display_name: Optional new display name
    :param description: Optional new description
    :return: Updated item details
    """
    payload: dict[str, Any] = {}
    if display_name is not None:
        payload["displayName"] = display_name
    if description is not None:
        payload["description"] = description

    endpoint = f"/workspaces/{workspace_id}/OperationsAgents/{item_id}"
    return FabricHttpClientCache.get_client().make_request("PATCH", endpoint, payload)


def _operationagent_update_definition(workspace_id: str, item_id: str, definition: dict[str, Any]) -> dict[str, Any]:
    """
    Update an OperationAgent item's definition.

    :param workspace_id: The Fabric workspace ID (UUID)
    :param item_id: The OperationAgent item ID (UUID)
    :param definition: Updated OperationAgent definition for the Configurations.json part
    :return: Updated item details
    """
    definition_json = json.dumps(definition)
    definition_b64 = base64.b64encode(definition_json.encode("utf-8")).decode("utf-8")

    payload: dict[str, Any] = {
        "definition": {
            "parts": [
                {
                    "path": _CONFIGURATION_DEFINITION_PART_PATH,
                    "payload": definition_b64,
                    "payloadType": "InlineBase64",
                }
            ]
        }
    }

    endpoint = f"/workspaces/{workspace_id}/OperationsAgents/{item_id}/updateDefinition"
    return FabricHttpClientCache.get_client().make_request("POST", endpoint, payload)
