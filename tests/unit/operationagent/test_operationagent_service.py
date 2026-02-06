import base64
import json
from typing import Any, Generator
from unittest.mock import MagicMock

import pytest

from fabric_rti_mcp.services.operationagent import operationagent_service


@pytest.fixture()
def mock_http_client(monkeypatch: pytest.MonkeyPatch) -> Generator[MagicMock, None, None]:
    client: MagicMock = MagicMock()

    def fake_get_client(*_: object) -> MagicMock:
        return client

    monkeypatch.setattr(operationagent_service.FabricHttpClientCache, "get_client", fake_get_client)
    yield client


def test_operationagent_list_calls_operations_agents_endpoint(mock_http_client: MagicMock) -> None:
    mock_http_client.make_request.return_value = {
        "value": [
            {"id": "1", "type": "OperationAgent"},
            {"id": "2", "type": "Eventstream"},
        ]
    }

    workspace_id = "0b67c1e8-04cb-4b05-9e7a-e4c2c8db7d8a"
    result = operationagent_service.operationagent_list(workspace_id)

    assert result == [{"id": "1", "type": "OperationAgent"}, {"id": "2", "type": "Eventstream"}]
    mock_http_client.make_request.assert_called_once_with("GET", f"/workspaces/{workspace_id}/OperationsAgents")


def test_operationagent_get_calls_items_endpoint(mock_http_client: MagicMock) -> None:
    mock_http_client.make_request.return_value = {"id": "123"}

    workspace_id = "0b67c1e8-04cb-4b05-9e7a-e4c2c8db7d8a"
    item_id = "87654321-0000-1111-2222-123456789abc"

    result = operationagent_service.operationagent_get(workspace_id, item_id)

    assert result == {"id": "123"}
    mock_http_client.make_request.assert_called_once_with("GET", f"/workspaces/{workspace_id}/OperationsAgents/{item_id}")


def test_operationagent_get_definition_uses_get_definition_endpoint(mock_http_client: MagicMock) -> None:
    mock_http_client.make_request.return_value = {"definition": {}}

    workspace_id = "0b67c1e8-04cb-4b05-9e7a-e4c2c8db7d8a"
    item_id = "87654321-0000-1111-2222-123456789abc"

    result = operationagent_service.operationagent_get_definition(workspace_id, item_id)

    assert result == {"definition": {}}
    mock_http_client.make_request.assert_called_once_with(
        "POST", f"/workspaces/{workspace_id}/OperationsAgents/{item_id}/getDefinition"
    )


def test_operationagent_create_with_definition_encodes_payload(mock_http_client: MagicMock) -> None:
    mock_http_client.make_request.return_value = {"id": "created"}

    workspace_id = "0b67c1e8-04cb-4b05-9e7a-e4c2c8db7d8a"
    display_name = "Example Operation Agent"
    definition = {"nodes": ["n1"]}

    result = operationagent_service.operationagent_create(
        workspace_id=workspace_id,
        display_name=display_name,
        definition=definition,
        description="desc",
    )

    encoded = base64.b64encode(json.dumps(definition).encode("utf-8")).decode("utf-8")
    expected_payload: dict[str, Any] = {
        "displayName": display_name,
        "description": "desc",
        "definition": {
            "parts": [
                {
                    "path": "Configurations.json",
                    "payload": encoded,
                    "payloadType": "InlineBase64",
                }
            ]
        },
    }

    assert result == {"id": "created"}
    mock_http_client.make_request.assert_called_once_with(
        "POST", f"/workspaces/{workspace_id}/OperationsAgents", expected_payload
    )


def test_operationagent_update_patches_metadata(mock_http_client: MagicMock) -> None:
    mock_http_client.make_request.return_value = {"updated": True}

    workspace_id = "0b67c1e8-04cb-4b05-9e7a-e4c2c8db7d8a"
    item_id = "87654321-0000-1111-2222-123456789abc"

    result = operationagent_service.operationagent_update(
        workspace_id, item_id, display_name="New Name", description="New description"
    )

    assert result == {"updated": True}
    mock_http_client.make_request.assert_called_once_with(
        "PATCH",
        f"/workspaces/{workspace_id}/OperationsAgents/{item_id}",
        {"displayName": "New Name", "description": "New description"},
    )


def test_operationagent_update_definition_encodes_definition(mock_http_client: MagicMock) -> None:
    mock_http_client.make_request.return_value = {"updated": True}

    workspace_id = "0b67c1e8-04cb-4b05-9e7a-e4c2c8db7d8a"
    item_id = "87654321-0000-1111-2222-123456789abc"
    definition = {"hello": "world"}

    result = operationagent_service.operationagent_update_definition(workspace_id, item_id, definition)

    encoded = base64.b64encode(json.dumps(definition).encode("utf-8")).decode("utf-8")
    expected_payload = {
        "definition": {
            "parts": [{"path": "Configurations.json", "payload": encoded, "payloadType": "InlineBase64"}]
        }
    }

    assert result == {"updated": True}
    mock_http_client.make_request.assert_called_once_with(
        "POST",
        f"/workspaces/{workspace_id}/OperationsAgents/{item_id}/updateDefinition",
        expected_payload,
    )


def test_get_agent_goals_extracts_goals_from_configurations_json(mock_http_client: MagicMock) -> None:
    config_doc: dict[str, Any] = {
        "configuration": {
            "goals": "monitor my fabric",
            "instructions": "",
            "dataSources": {},
            "actions": {},
        }
    }
    payload_b64 = base64.b64encode(json.dumps(config_doc).encode("utf-8")).decode("utf-8")

    mock_http_client.make_request.return_value = {
        "definition": {
            "format": "OperationsAgentV1",
            "parts": [
                {
                    "path": "Configurations.json",
                    "payload": payload_b64,
                    "payloadType": "InlineBase64",
                }
            ],
        }
    }

    workspace_id = "0b67c1e8-04cb-4b05-9e7a-e4c2c8db7d8a"
    item_id = "87654321-0000-1111-2222-123456789abc"

    result = operationagent_service.get_agent_goals(workspace_id, item_id)

    assert result == {"goals": "monitor my fabric"}


def test_get_agent_instructions_extracts_instructions_from_configurations_json(mock_http_client: MagicMock) -> None:
    config_doc: dict[str, Any] = {
        "configuration": {"goals": "x", "instructions": "do the thing", "dataSources": {}, "actions": {}}
    }
    payload_b64 = base64.b64encode(json.dumps(config_doc).encode("utf-8")).decode("utf-8")

    mock_http_client.make_request.return_value = {
        "definition": {
            "format": "OperationsAgentV1",
            "parts": [
                {
                    "path": "Configurations.json",
                    "payload": payload_b64,
                    "payloadType": "InlineBase64",
                }
            ],
        }
    }

    workspace_id = "0b67c1e8-04cb-4b05-9e7a-e4c2c8db7d8a"
    item_id = "87654321-0000-1111-2222-123456789abc"

    result = operationagent_service.get_agent_instructions(workspace_id, item_id)

    assert result == {"instructions": "do the thing"}


def test_get_agent_knowledge_sources_extracts_data_sources_as_list(mock_http_client: MagicMock) -> None:
    config_doc: dict[str, Any] = {
        "configuration": {
            "goals": "x",
            "instructions": "y",
            "dataSources": {
                "ds1": {"id": "ds1", "type": "KustoDatabase", "workspaceId": "w1"},
                "ds2": {"id": "ds2", "type": "Lakehouse", "workspaceId": "w2"},
            },
            "actions": {},
        }
    }
    payload_b64 = base64.b64encode(json.dumps(config_doc).encode("utf-8")).decode("utf-8")

    mock_http_client.make_request.return_value = {
        "definition": {
            "format": "OperationsAgentV1",
            "parts": [
                {
                    "path": "Configurations.json",
                    "payload": payload_b64,
                    "payloadType": "InlineBase64",
                }
            ],
        }
    }

    workspace_id = "0b67c1e8-04cb-4b05-9e7a-e4c2c8db7d8a"
    item_id = "87654321-0000-1111-2222-123456789abc"

    result = operationagent_service.get_agent_knowledge_sources(workspace_id, item_id)

    assert result["knowledge_sources"] == [
        {"id": "ds1", "type": "KustoDatabase", "workspaceId": "w1"},
        {"id": "ds2", "type": "Lakehouse", "workspaceId": "w2"},
    ]


def test_get_agents_actions_extracts_actions_dict(mock_http_client: MagicMock) -> None:
    config_doc: dict[str, Any] = {
        "configuration": {
            "goals": "x",
            "instructions": "y",
            "dataSources": {},
            "actions": {"a1": {"type": "Notify"}},
        }
    }
    payload_b64 = base64.b64encode(json.dumps(config_doc).encode("utf-8")).decode("utf-8")

    mock_http_client.make_request.return_value = {
        "definition": {
            "format": "OperationsAgentV1",
            "parts": [
                {
                    "path": "Configurations.json",
                    "payload": payload_b64,
                    "payloadType": "InlineBase64",
                }
            ],
        }
    }

    workspace_id = "0b67c1e8-04cb-4b05-9e7a-e4c2c8db7d8a"
    item_id = "87654321-0000-1111-2222-123456789abc"

    result = operationagent_service.get_agents_actions(workspace_id, item_id)

    assert result == {"actions": {"a1": {"type": "Notify"}}}


def _make_get_definition_response(config_doc: dict[str, Any]) -> dict[str, Any]:
    payload_b64 = base64.b64encode(json.dumps(config_doc).encode("utf-8")).decode("utf-8")
    return {
        "definition": {
            "format": "OperationsAgentV1",
            "parts": [
                {
                    "path": "Configurations.json",
                    "payload": payload_b64,
                    "payloadType": "InlineBase64",
                }
            ],
        }
    }


def _decode_update_definition_payload(call_args: tuple[Any, ...]) -> dict[str, Any]:
    # call_args is (method, endpoint, payload)
    payload = call_args[2]
    encoded = payload["definition"]["parts"][0]["payload"]
    decoded_json = base64.b64decode(encoded).decode("utf-8")
    return json.loads(decoded_json)


def test_get_agent_goals_returns_none_when_configuration_missing(mock_http_client: MagicMock) -> None:
    mock_http_client.make_request.return_value = _make_get_definition_response({})

    workspace_id = "0b67c1e8-04cb-4b05-9e7a-e4c2c8db7d8a"
    item_id = "87654321-0000-1111-2222-123456789abc"

    result = operationagent_service.get_agent_goals(workspace_id, item_id)
    assert result == {"goals": None}


def test_get_agent_instructions_returns_none_when_configuration_not_object(mock_http_client: MagicMock) -> None:
    mock_http_client.make_request.return_value = _make_get_definition_response({"configuration": "nope"})

    workspace_id = "0b67c1e8-04cb-4b05-9e7a-e4c2c8db7d8a"
    item_id = "87654321-0000-1111-2222-123456789abc"

    result = operationagent_service.get_agent_instructions(workspace_id, item_id)
    assert result == {"instructions": None}


def test_get_agent_knowledge_sources_returns_empty_when_configuration_invalid(mock_http_client: MagicMock) -> None:
    mock_http_client.make_request.return_value = _make_get_definition_response({"configuration": []})

    workspace_id = "0b67c1e8-04cb-4b05-9e7a-e4c2c8db7d8a"
    item_id = "87654321-0000-1111-2222-123456789abc"

    result = operationagent_service.get_agent_knowledge_sources(workspace_id, item_id)
    assert result == {"knowledge_sources": []}


def test_get_agents_actions_returns_empty_when_actions_not_object(mock_http_client: MagicMock) -> None:
    mock_http_client.make_request.return_value = _make_get_definition_response({"configuration": {"actions": []}})

    workspace_id = "0b67c1e8-04cb-4b05-9e7a-e4c2c8db7d8a"
    item_id = "87654321-0000-1111-2222-123456789abc"

    result = operationagent_service.get_agents_actions(workspace_id, item_id)
    assert result == {"actions": {}}


def test_set_agent_goals_updates_config_and_calls_update_definition(mock_http_client: MagicMock) -> None:
    workspace_id = "0b67c1e8-04cb-4b05-9e7a-e4c2c8db7d8a"
    item_id = "87654321-0000-1111-2222-123456789abc"

    config_doc: dict[str, Any] = {
        "$schema": "https://example/schema.json",
        "configuration": {"goals": "old", "instructions": "x", "dataSources": {}, "actions": {}},
        "shouldRun": False,
    }

    mock_http_client.make_request.side_effect = [_make_get_definition_response(config_doc), {"success": True}]

    result = operationagent_service.set_agent_goals(workspace_id, item_id, "new goals")

    assert result == {"success": True}
    assert mock_http_client.make_request.call_count == 2

    update_call = mock_http_client.make_request.call_args_list[1].args
    updated_doc = _decode_update_definition_payload(update_call)
    assert updated_doc["$schema"] == "https://example/schema.json"
    assert updated_doc["shouldRun"] is False
    assert updated_doc["configuration"]["goals"] == "new goals"
    assert updated_doc["configuration"]["instructions"] == "x"


def test_set_agent_instructions_updates_config_and_calls_update_definition(mock_http_client: MagicMock) -> None:
    workspace_id = "0b67c1e8-04cb-4b05-9e7a-e4c2c8db7d8a"
    item_id = "87654321-0000-1111-2222-123456789abc"

    config_doc: dict[str, Any] = {"configuration": {"goals": "g", "instructions": "old", "dataSources": {}, "actions": {}}}
    mock_http_client.make_request.side_effect = [_make_get_definition_response(config_doc), {"ok": True}]

    result = operationagent_service.set_agent_instructions(workspace_id, item_id, "new instructions")

    assert result == {"ok": True}
    update_call = mock_http_client.make_request.call_args_list[1].args
    updated_doc = _decode_update_definition_payload(update_call)
    assert updated_doc["configuration"]["instructions"] == "new instructions"
    assert updated_doc["configuration"]["goals"] == "g"


def test_add_agent_knowledge_source_inserts_into_data_sources(mock_http_client: MagicMock) -> None:
    workspace_id = "0b67c1e8-04cb-4b05-9e7a-e4c2c8db7d8a"
    item_id = "87654321-0000-1111-2222-123456789abc"

    config_doc: dict[str, Any] = {"configuration": {"goals": "g", "instructions": "i", "dataSources": {}, "actions": {}}}
    mock_http_client.make_request.side_effect = [_make_get_definition_response(config_doc), {"success": True}]

    knowledge_source = {"type": "KustoDatabase", "workspaceId": "w1"}
    result = operationagent_service.add_agent_knowledge_source(
        workspace_id, item_id, knowledge_source=knowledge_source, knowledge_source_id="ds1"
    )

    assert result["knowledge_source_id"] == "ds1"
    assert result["result"] == {"success": True}

    update_call = mock_http_client.make_request.call_args_list[1].args
    updated_doc = _decode_update_definition_payload(update_call)
    assert updated_doc["configuration"]["dataSources"]["ds1"]["id"] == "ds1"
    assert updated_doc["configuration"]["dataSources"]["ds1"]["type"] == "KustoDatabase"


def test_remove_agent_knowledge_source_removes_and_updates(mock_http_client: MagicMock) -> None:
    workspace_id = "0b67c1e8-04cb-4b05-9e7a-e4c2c8db7d8a"
    item_id = "87654321-0000-1111-2222-123456789abc"

    config_doc: dict[str, Any] = {
        "configuration": {
            "goals": "g",
            "instructions": "i",
            "dataSources": {"ds1": {"id": "ds1", "type": "KustoDatabase", "workspaceId": "w1"}},
            "actions": {},
        }
    }
    mock_http_client.make_request.side_effect = [_make_get_definition_response(config_doc), {"success": True}]

    result = operationagent_service.remove_agent_knowledge_source(workspace_id, item_id, "ds1")
    assert result["removed"] is True

    update_call = mock_http_client.make_request.call_args_list[1].args
    updated_doc = _decode_update_definition_payload(update_call)
    assert updated_doc["configuration"]["dataSources"] == {}


def test_remove_agent_knowledge_source_noop_when_missing_does_not_update(mock_http_client: MagicMock) -> None:
    workspace_id = "0b67c1e8-04cb-4b05-9e7a-e4c2c8db7d8a"
    item_id = "87654321-0000-1111-2222-123456789abc"

    config_doc: dict[str, Any] = {"configuration": {"goals": "g", "instructions": "i", "dataSources": {}, "actions": {}}}
    mock_http_client.make_request.return_value = _make_get_definition_response(config_doc)

    result = operationagent_service.remove_agent_knowledge_source(workspace_id, item_id, "missing")
    assert result == {"removed": False, "knowledge_source_id": "missing"}
    assert mock_http_client.make_request.call_count == 1


def test_add_agent_action_inserts_into_actions(mock_http_client: MagicMock) -> None:
    workspace_id = "0b67c1e8-04cb-4b05-9e7a-e4c2c8db7d8a"
    item_id = "87654321-0000-1111-2222-123456789abc"

    config_doc: dict[str, Any] = {"configuration": {"goals": "g", "instructions": "i", "dataSources": {}, "actions": {}}}
    mock_http_client.make_request.side_effect = [_make_get_definition_response(config_doc), {"success": True}]

    action = {"type": "Notify"}
    result = operationagent_service.add_agent_action(workspace_id, item_id, action=action, action_id="a1")

    assert result["action_id"] == "a1"
    assert result["result"] == {"success": True}

    update_call = mock_http_client.make_request.call_args_list[1].args
    updated_doc = _decode_update_definition_payload(update_call)
    assert updated_doc["configuration"]["actions"]["a1"]["type"] == "Notify"


def test_remove_agent_action_removes_and_updates(mock_http_client: MagicMock) -> None:
    workspace_id = "0b67c1e8-04cb-4b05-9e7a-e4c2c8db7d8a"
    item_id = "87654321-0000-1111-2222-123456789abc"

    config_doc: dict[str, Any] = {
        "configuration": {"goals": "g", "instructions": "i", "dataSources": {}, "actions": {"a1": {"type": "Notify"}}}
    }
    mock_http_client.make_request.side_effect = [_make_get_definition_response(config_doc), {"success": True}]

    result = operationagent_service.remove_agent_action(workspace_id, item_id, "a1")
    assert result["removed"] is True

    update_call = mock_http_client.make_request.call_args_list[1].args
    updated_doc = _decode_update_definition_payload(update_call)
    assert updated_doc["configuration"]["actions"] == {}


def test_remove_agent_action_noop_when_missing_does_not_update(mock_http_client: MagicMock) -> None:
    workspace_id = "0b67c1e8-04cb-4b05-9e7a-e4c2c8db7d8a"
    item_id = "87654321-0000-1111-2222-123456789abc"

    config_doc: dict[str, Any] = {"configuration": {"goals": "g", "instructions": "i", "dataSources": {}, "actions": {}}}
    mock_http_client.make_request.return_value = _make_get_definition_response(config_doc)

    result = operationagent_service.remove_agent_action(workspace_id, item_id, "missing")
    assert result == {"removed": False, "action_id": "missing"}
    assert mock_http_client.make_request.call_count == 1
