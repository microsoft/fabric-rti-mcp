from unittest.mock import MagicMock

import pytest

from fabric_rti_mcp.authentication.auth_context import get_azure_credential_or_http_header_token
from fabric_rti_mcp.services.kusto.kusto_connection import BearerTokenCredential, get_auth_token, set_auth_token


class TestBearerTokenCredential:
    def test_returns_current_context_token(self) -> None:
        set_auth_token("token-A")
        cred = BearerTokenCredential()
        result = cred.get_token("https://kusto.kusto.windows.net/.default")
        assert result.token == "token-A"

    def test_tracks_token_updates(self) -> None:
        set_auth_token("token-A")
        cred = BearerTokenCredential()
        assert cred.get_token("scope").token == "token-A"

        set_auth_token("token-B")
        assert cred.get_token("scope").token == "token-B"

    def test_raises_when_no_token_in_context(self) -> None:
        set_auth_token(None)
        cred = BearerTokenCredential()
        with pytest.raises(ValueError, match="No auth token"):
            cred.get_token("scope")

    def test_token_not_stale_after_context_change(self) -> None:
        """Simulates the exact bug from issue #128."""
        set_auth_token("request-1-token")
        cred = BearerTokenCredential()

        # First request uses token correctly
        assert cred.get_token("scope").token == "request-1-token"

        # Second request updates the context
        set_auth_token("request-2-token")

        # Same credential instance must return the new token
        assert cred.get_token("scope").token == "request-2-token"


class TestAuthTokenContextVar:
    def test_set_and_get(self) -> None:
        set_auth_token("my-token")
        assert get_auth_token() == "my-token"

    def test_default_is_none(self) -> None:
        set_auth_token(None)
        assert get_auth_token() is None


class TestAzureCredentialOrHttpHeaderToken:
    def test_uses_http_header_token_when_present(self) -> None:
        set_auth_token("caller-token")
        azure_credential_factory = MagicMock()

        credential = get_azure_credential_or_http_header_token(azure_credential_factory)

        assert isinstance(credential, BearerTokenCredential)
        assert credential.get_token("scope").token == "caller-token"
        azure_credential_factory.assert_not_called()

    def test_falls_back_to_azure_credential_without_http_header_token(self) -> None:
        set_auth_token(None)
        azure_credential = MagicMock()

        credential = get_azure_credential_or_http_header_token(lambda: azure_credential)

        assert credential is azure_credential
