from collections.abc import Generator
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from mcp.server.lowlevel.server import request_ctx
from mcp.shared.context import RequestContext

from fabric_rti_mcp.auth.auth_context import (
    BearerTokenCredential,
    CredentialSource,
    TokenTarget,
    credential_source_cache_key,
    get_credential,
    resolve_credential_source,
    set_request_token,
)


@pytest.fixture(autouse=True)
def clear_request_tokens() -> Generator[None, None, None]:
    set_request_token(TokenTarget.KUSTO, None)
    set_request_token(TokenTarget.FABRIC, None)
    yield
    set_request_token(TokenTarget.KUSTO, None)
    set_request_token(TokenTarget.FABRIC, None)


class TestBearerTokenCredential:
    def test_returns_current_context_token(self) -> None:
        set_request_token(TokenTarget.KUSTO, "token-A")
        cred = BearerTokenCredential(TokenTarget.KUSTO)
        result = cred.get_token("https://kusto.kusto.windows.net/.default")
        assert result.token == "token-A"

    def test_tracks_token_updates(self) -> None:
        set_request_token(TokenTarget.KUSTO, "token-A")
        cred = BearerTokenCredential(TokenTarget.KUSTO)
        assert cred.get_token("scope").token == "token-A"

        set_request_token(TokenTarget.KUSTO, "token-B")
        assert cred.get_token("scope").token == "token-B"

    def test_raises_when_no_token_in_context(self) -> None:
        set_request_token(TokenTarget.KUSTO, None)
        cred = BearerTokenCredential(TokenTarget.KUSTO)
        with pytest.raises(ValueError, match="No auth token"):
            cred.get_token("scope")

    def test_token_not_stale_after_context_change(self) -> None:
        """Simulates the exact bug from issue #128."""
        set_request_token(TokenTarget.KUSTO, "request-1-token")
        cred = BearerTokenCredential(TokenTarget.KUSTO)

        # First request uses token correctly
        assert cred.get_token("scope").token == "request-1-token"

        # Second request updates the context
        set_request_token(TokenTarget.KUSTO, "request-2-token")

        # Same credential instance must return the new token
        assert cred.get_token("scope").token == "request-2-token"


class TestGetCredential:
    def test_uses_http_header_token_when_present(self, monkeypatch: pytest.MonkeyPatch) -> None:
        set_request_token(TokenTarget.KUSTO, "caller-token")
        default_credential = MagicMock()
        monkeypatch.setattr("fabric_rti_mcp.auth.auth_context.DefaultAzureCredential", default_credential)

        credential = get_credential(TokenTarget.KUSTO)

        assert isinstance(credential, BearerTokenCredential)
        assert credential.get_token("scope").token == "caller-token"
        default_credential.assert_not_called()

    def test_does_not_mix_token_targets(self, monkeypatch: pytest.MonkeyPatch) -> None:
        set_request_token(TokenTarget.KUSTO, "kusto-token")
        set_request_token(TokenTarget.FABRIC, None)
        azure_credential = MagicMock()
        default_credential = MagicMock(return_value=azure_credential)
        monkeypatch.setattr("fabric_rti_mcp.auth.auth_context.DefaultAzureCredential", default_credential)

        kusto_credential = get_credential(TokenTarget.KUSTO)
        fabric_credential = get_credential(TokenTarget.FABRIC)

        assert isinstance(kusto_credential, BearerTokenCredential)
        assert kusto_credential.get_token("scope").token == "kusto-token"
        assert fabric_credential is azure_credential
        default_credential.assert_called_once_with(
            exclude_shared_token_cache_credential=True,
            exclude_interactive_browser_credential=False,
        )

    def test_falls_back_to_default_azure_credential_without_http_header_token(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        set_request_token(TokenTarget.KUSTO, None)
        azure_credential = MagicMock()
        default_credential = MagicMock(return_value=azure_credential)
        monkeypatch.setattr("fabric_rti_mcp.auth.auth_context.DefaultAzureCredential", default_credential)

        credential = get_credential(TokenTarget.KUSTO)

        assert credential is azure_credential
        default_credential.assert_called_once_with(
            exclude_shared_token_cache_credential=True,
            exclude_interactive_browser_credential=False,
        )

    def test_passes_authority_to_default_azure_credential(self, monkeypatch: pytest.MonkeyPatch) -> None:
        set_request_token(TokenTarget.KUSTO, None)
        azure_credential = MagicMock()
        default_credential = MagicMock(return_value=azure_credential)
        monkeypatch.setattr("fabric_rti_mcp.auth.auth_context.DefaultAzureCredential", default_credential)

        credential = get_credential(TokenTarget.KUSTO, authority="https://login.example")

        assert credential is azure_credential
        default_credential.assert_called_once_with(
            exclude_shared_token_cache_credential=True,
            exclude_interactive_browser_credential=False,
            authority="https://login.example",
        )

    def test_http_without_token_fails_closed_by_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        set_request_token(TokenTarget.KUSTO, None)
        default_credential = MagicMock()
        monkeypatch.setattr("fabric_rti_mcp.auth.auth_context.DefaultAzureCredential", default_credential)
        monkeypatch.setattr(
            "fabric_rti_mcp.auth.auth_context.config",
            SimpleNamespace(transport="http", http_allow_mi=False, http_debug_mode=False),
        )

        with pytest.raises(ValueError, match="No HTTP request bearer token"):
            get_credential(TokenTarget.KUSTO)

        default_credential.assert_not_called()

    def test_http_managed_identity_fallback_requires_opt_in(self, monkeypatch: pytest.MonkeyPatch) -> None:
        set_request_token(TokenTarget.KUSTO, None)
        managed_identity_credential = MagicMock()
        managed_identity = MagicMock(return_value=managed_identity_credential)
        monkeypatch.setattr("fabric_rti_mcp.auth.auth_context.ManagedIdentityCredential", managed_identity)
        monkeypatch.setattr(
            "fabric_rti_mcp.auth.auth_context.config",
            SimpleNamespace(transport="http", http_allow_mi=True, http_debug_mode=False),
        )
        monkeypatch.setattr("fabric_rti_mcp.auth.auth_context.obo_config", SimpleNamespace(umi_client_id="umi-client"))

        credential = get_credential(TokenTarget.KUSTO)

        assert credential is managed_identity_credential
        managed_identity.assert_called_once_with(client_id="umi-client")

    def test_http_debug_mode_uses_default_credential_for_local_testing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        set_request_token(TokenTarget.KUSTO, None)
        azure_credential = MagicMock()
        default_credential = MagicMock(return_value=azure_credential)
        monkeypatch.setattr("fabric_rti_mcp.auth.auth_context.DefaultAzureCredential", default_credential)
        monkeypatch.setattr(
            "fabric_rti_mcp.auth.auth_context.config",
            SimpleNamespace(transport="http", http_allow_mi=False, http_debug_mode=True),
        )

        credential = get_credential(TokenTarget.KUSTO, authority="https://login.example")

        assert credential is azure_credential
        default_credential.assert_called_once_with(
            exclude_shared_token_cache_credential=True,
            exclude_interactive_browser_credential=False,
            authority="https://login.example",
        )

    def test_credential_source_cache_key_for_managed_identity(self, monkeypatch: pytest.MonkeyPatch) -> None:
        set_request_token(TokenTarget.KUSTO, None)
        monkeypatch.setattr(
            "fabric_rti_mcp.auth.auth_context.config",
            SimpleNamespace(transport="http", http_allow_mi=True, http_debug_mode=True),
        )
        monkeypatch.setattr("fabric_rti_mcp.auth.auth_context.obo_config", SimpleNamespace(umi_client_id="umi-client"))

        credential_source = resolve_credential_source(TokenTarget.KUSTO)
        assert credential_source is CredentialSource.MANAGED_IDENTITY
        assert credential_source_cache_key(credential_source) == "managed-identity:umi-client"

    def test_credential_source_cache_key_for_bearer_token(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "fabric_rti_mcp.auth.auth_context.config",
            SimpleNamespace(transport="http", http_allow_mi=False, http_debug_mode=False),
        )
        set_request_token(TokenTarget.KUSTO, "request-token")

        credential_source = resolve_credential_source(TokenTarget.KUSTO)
        assert credential_source is CredentialSource.BEARER_TOKEN
        assert credential_source_cache_key(credential_source) == "bearer-token"

    def test_bearer_token_credential_reads_mcp_request_context(self, monkeypatch: pytest.MonkeyPatch) -> None:
        set_request_token(TokenTarget.KUSTO, None)
        monkeypatch.setattr(
            "fabric_rti_mcp.auth.auth_context.config",
            SimpleNamespace(transport="http", http_allow_mi=False, http_debug_mode=False),
        )
        request = SimpleNamespace(headers={"Authorization": "Bearer mcp-request-token"})
        context_token = request_ctx.set(
            RequestContext(
                request_id="request-id",
                meta=None,
                session=MagicMock(),
                lifespan_context=None,
                request=request,
            )
        )
        try:
            credential_source = resolve_credential_source(TokenTarget.KUSTO)
            credential = get_credential(TokenTarget.KUSTO)
            token = credential.get_token("scope")
        finally:
            request_ctx.reset(context_token)

        assert credential_source is CredentialSource.BEARER_TOKEN
        assert isinstance(credential, BearerTokenCredential)
        assert token.token == "mcp-request-token"
