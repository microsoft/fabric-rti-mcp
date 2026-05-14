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
        try:
            cred.get_token("scope")
            assert False, "Expected ValueError"
        except ValueError as e:
            assert "No auth token" in str(e)

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
