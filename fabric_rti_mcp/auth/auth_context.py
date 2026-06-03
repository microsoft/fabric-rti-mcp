import time
from contextvars import ContextVar
from contextvars import Token as ContextToken
from dataclasses import dataclass
from enum import Enum
from typing import Any

from azure.core.credentials import AccessToken, TokenCredential
from azure.identity import DefaultAzureCredential


class TokenTarget(str, Enum):
    KUSTO = "kusto"
    FABRIC = "fabric"


@dataclass(frozen=True, slots=True)
class RequestTokenContext:
    target: TokenTarget
    context_token: ContextToken[str | None]


_request_tokens: dict[TokenTarget, ContextVar[str | None]] = {
    TokenTarget.KUSTO: ContextVar("_kusto_request_token", default=None),
    TokenTarget.FABRIC: ContextVar("_fabric_request_token", default=None),
}


def set_request_token(target: TokenTarget, token: str | None) -> RequestTokenContext:
    """Set the auth token for the current request context."""
    return RequestTokenContext(target=target, context_token=_request_tokens[target].set(token))


def reset_request_token(request_token_context: RequestTokenContext) -> None:
    """Reset the auth token context to its previous value."""
    _request_tokens[request_token_context.target].reset(request_token_context.context_token)


class BearerTokenCredential(TokenCredential):
    """A credential that reads the bearer token from the current request's ContextVar on each call."""

    def __init__(self, token_target: TokenTarget) -> None:
        self._token_target = token_target

    def get_token(self, *scopes: str, **kwargs: Any) -> AccessToken:
        token = _request_tokens[self._token_target].get()
        if not token:
            raise ValueError("No auth token available in request context")
        return AccessToken(token=token, expires_on=int(time.time()) + 3600)


def get_credential(token_target: TokenTarget, authority: str | None = None) -> TokenCredential:
    """Use the HTTP request bearer token when present, otherwise create a DefaultAzureCredential."""
    if _request_tokens[token_target].get():
        return BearerTokenCredential(token_target)

    credential_kwargs: dict[str, Any] = {
        "exclude_shared_token_cache_credential": True,
        "exclude_interactive_browser_credential": False,
    }
    if authority:
        credential_kwargs["authority"] = authority

    return DefaultAzureCredential(**credential_kwargs)
