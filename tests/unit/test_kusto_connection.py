from unittest.mock import MagicMock

import pytest

from fabric_rti_mcp.auth.auth_context import BearerTokenCredential, get_credential, set_request_token


class TestBearerTokenCredential:
    def test_returns_current_context_token(self) -> None:
        set_request_token("token-A")
        cred = BearerTokenCredential()
        result = cred.get_token("https://kusto.kusto.windows.net/.default")
        assert result.token == "token-A"

    def test_tracks_token_updates(self) -> None:
        set_request_token("token-A")
        cred = BearerTokenCredential()
        assert cred.get_token("scope").token == "token-A"

        set_request_token("token-B")
        assert cred.get_token("scope").token == "token-B"

    def test_raises_when_no_token_in_context(self) -> None:
        set_request_token(None)
        cred = BearerTokenCredential()
        with pytest.raises(ValueError, match="No auth token"):
            cred.get_token("scope")

    def test_token_not_stale_after_context_change(self) -> None:
        """Simulates the exact bug from issue #128."""
        set_request_token("request-1-token")
        cred = BearerTokenCredential()

        # First request uses token correctly
        assert cred.get_token("scope").token == "request-1-token"

        # Second request updates the context
        set_request_token("request-2-token")

        # Same credential instance must return the new token
        assert cred.get_token("scope").token == "request-2-token"


class TestGetCredential:
    def test_uses_http_header_token_when_present(self, monkeypatch: pytest.MonkeyPatch) -> None:
        set_request_token("caller-token")
        default_credential = MagicMock()
        monkeypatch.setattr("fabric_rti_mcp.auth.auth_context.DefaultAzureCredential", default_credential)

        credential = get_credential()

        assert isinstance(credential, BearerTokenCredential)
        assert credential.get_token("scope").token == "caller-token"
        default_credential.assert_not_called()

    def test_falls_back_to_default_azure_credential_without_http_header_token(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        set_request_token(None)
        azure_credential = MagicMock()
        default_credential = MagicMock(return_value=azure_credential)
        monkeypatch.setattr("fabric_rti_mcp.auth.auth_context.DefaultAzureCredential", default_credential)

        credential = get_credential()

        assert credential is azure_credential
        default_credential.assert_called_once_with(
            exclude_shared_token_cache_credential=True,
            exclude_interactive_browser_credential=False,
        )

    def test_passes_authority_to_default_azure_credential(self, monkeypatch: pytest.MonkeyPatch) -> None:
        set_request_token(None)
        azure_credential = MagicMock()
        default_credential = MagicMock(return_value=azure_credential)
        monkeypatch.setattr("fabric_rti_mcp.auth.auth_context.DefaultAzureCredential", default_credential)

        credential = get_credential(authority="https://login.example")

        assert credential is azure_credential
        default_credential.assert_called_once_with(
            exclude_shared_token_cache_credential=True,
            exclude_interactive_browser_credential=False,
            authority="https://login.example",
        )
