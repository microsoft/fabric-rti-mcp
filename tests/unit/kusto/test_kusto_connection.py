import pytest

from fabric_rti_mcp.services.kusto.kusto_connection import BearerTokenCredential, get_auth_token, set_auth_token


def test_bearer_token_credential_reflects_updated_token() -> None:
    """BearerTokenCredential.get_token() must return the current context token, not a stale one."""
    set_auth_token("token-A")
    cred = BearerTokenCredential()

    # Simulate a new request updating the token
    set_auth_token("token-B")

    assert get_auth_token() == "token-B"
    assert cred.get_token("https://kusto.kusto.windows.net/.default").token == "token-B"


def test_bearer_token_credential_raises_when_no_token() -> None:
    """BearerTokenCredential.get_token() raises ValueError when no token is set."""
    set_auth_token(None)
    cred = BearerTokenCredential()

    with pytest.raises(ValueError, match="No auth token available"):
        cred.get_token("https://kusto.kusto.windows.net/.default")
