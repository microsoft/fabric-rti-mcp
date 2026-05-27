import time
from contextvars import ContextVar
from contextvars import Token as ContextToken
from typing import Any

from azure.core.credentials import AccessToken, TokenCredential
from azure.identity import DefaultAzureCredential

_request_token: ContextVar[str | None] = ContextVar("_request_token", default=None)


def set_auth_token(token: str | None) -> ContextToken[str | None]:
    """Set the auth token for the current request context."""
    return _request_token.set(token)


def get_auth_token() -> str | None:
    """Get the auth token from the current request context."""
    return _request_token.get()


def reset_auth_token(context_token: ContextToken[str | None]) -> None:
    """Reset the auth token context to its previous value."""
    _request_token.reset(context_token)


class BearerTokenCredential(TokenCredential):
    """A credential that reads the bearer token from the current request's ContextVar on each call."""

    def get_token(self, *scopes: str, **kwargs: Any) -> AccessToken:
        token = get_auth_token()
        if not token:
            raise ValueError("No auth token available in request context")
        return AccessToken(token=token, expires_on=int(time.time()) + 3600)


def get_azure_credential_or_http_header_token(authority: str | None = None) -> TokenCredential:
    """Use the HTTP request bearer token when present, otherwise create a DefaultAzureCredential."""
    if get_auth_token():
        return BearerTokenCredential()

    credential_args: dict[str, Any] = {
        "exclude_shared_token_cache_credential": True,
        "exclude_interactive_browser_credential": False,
    }
    if authority:
        credential_args["authority"] = authority

    return DefaultAzureCredential(**credential_args)
