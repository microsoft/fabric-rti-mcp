import contextvars
from unittest.mock import Mock

from fabric_rti_mcp.fabric_api_http_client import (
    FabricAPIHttpClient,
    get_fabric_auth_token,
    set_fabric_auth_token,
)


class TestFabricAuthTokenContextVar:
    def test_set_and_get(self) -> None:
        set_fabric_auth_token("my-fabric-token")
        assert get_fabric_auth_token() == "my-fabric-token"

    def test_default_is_none(self) -> None:
        set_fabric_auth_token(None)
        assert get_fabric_auth_token() is None

    def test_isolation_via_copy_context(self) -> None:
        """ContextVar must scope per request-context.

        asyncio.create_task() copies the current context; mutations inside
        a task do not leak back to the parent. We verify that property
        synchronously here using contextvars.copy_context(), which is the
        same mechanism asyncio uses under the hood.
        """
        set_fabric_auth_token("outer")
        captured: list[str | None] = []

        def in_copy() -> None:
            # Inside a copied context, set a different value.
            set_fabric_auth_token("inner")
            captured.append(get_fabric_auth_token())

        contextvars.copy_context().run(in_copy)

        # Child saw its own value.
        assert captured == ["inner"]
        # Parent context unchanged by the child's write.
        assert get_fabric_auth_token() == "outer"


class TestAccessTokenShortCircuit:
    """_get_access_token must prefer the ContextVar's pre-exchanged token
    over the cached self.credential. Without this, every request would
    fall through to DefaultAzureCredential and per-user delegation would
    be lost.
    """

    def test_uses_contextvar_when_set(self) -> None:
        set_fabric_auth_token("ctx-fabric-token")
        client = FabricAPIHttpClient(api_base_url="https://example.test/v1")

        # If the short-circuit fails, this would call into self.credential.
        # Replacing it with a Mock that fails ensures we see the bug if
        # the short-circuit regresses.
        client.credential = Mock(  # ty: ignore[invalid-assignment]
            get_token=Mock(side_effect=AssertionError("credential should not be consulted"))
        )

        assert client._get_access_token() == "ctx-fabric-token"

    def test_falls_back_to_credential_when_unset(self) -> None:
        set_fabric_auth_token(None)
        client = FabricAPIHttpClient(api_base_url="https://example.test/v1")

        mock_token = Mock(token="default-credential-token", expires_on=9999999999)
        client.credential = Mock(get_token=Mock(return_value=mock_token))  # ty: ignore[invalid-assignment]

        assert client._get_access_token() == "default-credential-token"
        client.credential.get_token.assert_called_once_with("https://api.fabric.microsoft.com/.default")
