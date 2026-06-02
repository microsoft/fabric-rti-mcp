import asyncio
from collections.abc import Generator
from types import TracebackType
from typing import Any
from unittest.mock import MagicMock

import pytest
from azure.core.credentials import AccessToken, TokenCredential

from fabric_rti_mcp.auth.auth_context import set_request_token
from fabric_rti_mcp.fabric_api_http_client import FabricAPIHttpClient


class FakeResponse:
    status_code = 200
    text = '{"ok": true}'

    def json(self) -> dict[str, bool]:
        return {"ok": True}


class FakeCredential(TokenCredential):
    def __init__(self, token: str = "managed-identity-token") -> None:
        self.get_token_mock = MagicMock(return_value=AccessToken(token=token, expires_on=123))

    def get_token(self, *scopes: str, **kwargs: Any) -> AccessToken:
        return self.get_token_mock(*scopes, **kwargs)


class FakeAsyncClient:
    last_headers: dict[str, str] = {}

    def __init__(self, timeout: int) -> None:
        self.timeout = timeout

    async def __aenter__(self) -> "FakeAsyncClient":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        return None

    async def get(self, url: str, headers: dict[str, str]) -> FakeResponse:
        FakeAsyncClient.last_headers = headers
        return FakeResponse()


@pytest.fixture(autouse=True)
def clear_auth_token() -> Generator[None, None, None]:
    set_request_token(None)
    yield
    set_request_token(None)


def mock_default_credential(monkeypatch: pytest.MonkeyPatch, credential: FakeCredential) -> MagicMock:
    default_credential = MagicMock(return_value=credential)
    monkeypatch.setattr("fabric_rti_mcp.auth.auth_context.DefaultAzureCredential", default_credential)
    return default_credential


def test_get_headers_uses_request_token_without_default_credential(monkeypatch: pytest.MonkeyPatch) -> None:
    credential = FakeCredential()
    default_credential = mock_default_credential(monkeypatch, credential)
    client = FabricAPIHttpClient("https://fabric.example")

    set_request_token("caller-token")
    headers = client._get_headers()

    assert headers["Authorization"] == "Bearer caller-token"
    default_credential.assert_not_called()
    credential.get_token_mock.assert_not_called()


def test_get_headers_falls_back_to_default_credential_without_request_token(monkeypatch: pytest.MonkeyPatch) -> None:
    credential = FakeCredential()
    default_credential = mock_default_credential(monkeypatch, credential)
    client = FabricAPIHttpClient("https://fabric.example")

    headers = client._get_headers()

    assert headers["Authorization"] == "Bearer managed-identity-token"
    default_credential.assert_called_once_with(
        exclude_shared_token_cache_credential=True,
        exclude_interactive_browser_credential=False,
    )
    credential.get_token_mock.assert_called_once_with("https://api.fabric.microsoft.com/.default")


def test_extra_headers_cannot_override_request_authorization(monkeypatch: pytest.MonkeyPatch) -> None:
    credential = FakeCredential()
    default_credential = mock_default_credential(monkeypatch, credential)
    client = FabricAPIHttpClient("https://fabric.example")

    set_request_token("caller-token")
    headers = client._get_headers({"Authorization": "Bearer attacker-token", "x-ms-custom": "value"})

    assert headers["Authorization"] == "Bearer caller-token"
    assert headers["x-ms-custom"] == "value"
    default_credential.assert_not_called()
    credential.get_token_mock.assert_not_called()


def test_make_request_preserves_request_token_when_running_inside_event_loop(monkeypatch: pytest.MonkeyPatch) -> None:
    credential = FakeCredential()
    default_credential = mock_default_credential(monkeypatch, credential)
    monkeypatch.setattr("fabric_rti_mcp.fabric_api_http_client.httpx.AsyncClient", FakeAsyncClient)
    client = FabricAPIHttpClient("https://fabric.example")

    async def run_request() -> dict[str, Any]:
        set_request_token("caller-token")
        return client.make_request("GET", "/items")

    result = asyncio.run(run_request())

    assert result == {"ok": True}
    assert FakeAsyncClient.last_headers["Authorization"] == "Bearer caller-token"
    default_credential.assert_not_called()
    credential.get_token_mock.assert_not_called()
