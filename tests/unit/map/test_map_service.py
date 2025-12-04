import base64
import json
from typing import Any, Generator
from unittest.mock import MagicMock

import pytest

from fabric_rti_mcp.services.map import map_service


@pytest.fixture()
def mock_http_client(monkeypatch: pytest.MonkeyPatch) -> Generator[MagicMock, None, None]:
    client: MagicMock = MagicMock()

    def fake_get_client(*_: object) -> MagicMock:
        return client

    monkeypatch.setattr(map_service.FabricHttpClientCache, "get_client", fake_get_client)
    yield client


def test_map_create(mock_http_client: MagicMock) -> None:
    mock_http_client.make_request.return_value = {"id": "123"}
    workspace_id = "0b67c1e8-04cb-4b05-9e7a-e4c2c8db7d8a"
    map_name = "Example Map"
    definition = {"nodes": ["n1"]}
    description = "Example description"
    folder_id = "87654321-0000-1111-2222-123456789abc"

    result = map_service.map_create(
        workspace_id=workspace_id,
        map_name=map_name,
        definition=definition,
        description=description,
        folder_id=folder_id,
    )

    expected_payload: dict[str, Any] = {
        "displayName": map_name,
        "description": description,
        "folderId": folder_id,
        "definition": {
            "parts": [
                {
                    "path": "map.json",
                    "payload": base64.b64encode(json.dumps(definition).encode("utf-8")).decode("utf-8"),
                    "payloadType": "InlineBase64",
                }
            ]
        },
    }

    assert result == {"id": "123"}
    mock_http_client.make_request.assert_called_once_with(
        "POST",
        f"/workspaces/{workspace_id}/Maps",
        expected_payload,
    )


def test_map_get_returns_response(mock_http_client: MagicMock) -> None:
    mock_http_client.make_request.return_value = {"item": "value"}
    workspace_id = "12345678-04cb-4b05-9e7a-e4c2c8db7d8a"
    item_id = "87654321-0000-1111-2222-123456789abc"

    result = map_service.map_get(workspace_id, item_id)

    assert result == {"item": "value"}
    mock_http_client.make_request.assert_called_once_with(
        "GET",
        f"/workspaces/{workspace_id}/Maps/{item_id}",
    )


def test_map_list_fetches_all_maps(mock_http_client: MagicMock) -> None:
    mock_http_client.make_request.return_value = {"value": []}
    workspace_id = "12345678-04cb-4b05-9e7a-e4c2c8db7d8a"

    result = map_service.map_list(workspace_id)

    assert result == {"value": []}
    mock_http_client.make_request.assert_called_once_with("GET", f"/workspaces/{workspace_id}/Maps")


def test_map_delete_uses_items_endpoint(mock_http_client: MagicMock) -> None:
    mock_http_client.make_request.return_value = {"deleted": True}
    workspace_id = "12345678-04cb-4b05-9e7a-e4c2c8db7d8a"
    item_id = "87654321-0000-1111-2222-123456789abc"

    result = map_service.map_delete(workspace_id, item_id)

    assert result == {"deleted": True}
    mock_http_client.make_request.assert_called_once_with(
        "DELETE",
        f"/workspaces/{workspace_id}/items/{item_id}",
    )


def test_map_update_includes_provided_fields(mock_http_client: MagicMock) -> None:
    mock_http_client.make_request.return_value = {"updated": True}
    workspace_id = "12345678-04cb-4b05-9e7a-e4c2c8db7d8a"
    item_id = "87654321-0000-1111-2222-123456789abc"

    result = map_service.map_update(
        workspace_id=workspace_id,
        item_id=item_id,
        display_name="New Name",
        description="New description",
    )

    assert result == {"updated": True}
    mock_http_client.make_request.assert_called_once_with(
        "PATCH",
        f"/workspaces/{workspace_id}/items/{item_id}",
        {"displayName": "New Name", "description": "New description"},
    )


def test_map_update_handles_empty_payload(mock_http_client: MagicMock) -> None:
    mock_http_client.make_request.return_value = {"updated": False}

    result = map_service.map_update(
        workspace_id="de7d2c68-cc49-4f62-9ce0-2acb28a5d51f",
        item_id="3a4d0d47-5a61-4f3f-8e1b-9f4aab9c9a62",
    )

    assert result == {"updated": False}
    mock_http_client.make_request.assert_called_once_with(
        "PATCH",
        "/workspaces/de7d2c68-cc49-4f62-9ce0-2acb28a5d51f/items/3a4d0d47-5a61-4f3f-8e1b-9f4aab9c9a62",
        {},
    )


def test_map_update_definition_encodes_payload(mock_http_client: MagicMock) -> None:
    mock_http_client.make_request.return_value = {"updated": True}
    workspace_id = "12345678-04cb-4b05-9e7a-e4c2c8db7d8a"
    item_id = "87654321-0000-1111-2222-123456789abc"
    definition = {"streams": [1, 2, 3]}

    result = map_service.map_update_definition(workspace_id, item_id, definition)

    encoded_payload = base64.b64encode(json.dumps(definition).encode("utf-8")).decode("utf-8")
    expected_payload: dict[str, Any] = {
        "definition": {"parts": [{"path": "map.json", "payload": encoded_payload, "payloadType": "InlineBase64"}]}
    }

    assert result == {"updated": True}
    mock_http_client.make_request.assert_called_once_with(
        "POST",
        f"/workspaces/{workspace_id}/Maps/{item_id}/updateDefinition",
        expected_payload,
    )


def test_map_get_definition_requests_items_endpoint(mock_http_client: MagicMock) -> None:
    mock_http_client.make_request.return_value = {"definition": {}}
    workspace_id = "12345678-04cb-4b05-9e7a-e4c2c8db7d8a"
    item_id = "87654321-0000-1111-2222-123456789abc"

    result = map_service.map_get_definition(workspace_id, item_id)

    assert result == {"definition": {}}
    mock_http_client.make_request.assert_called_once_with(
        "GET",
        f"/workspaces/{workspace_id}/items/{item_id}/getDefinition",
    )
