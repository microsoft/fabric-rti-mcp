import time
from contextvars import ContextVar
from contextvars import Token as ContextToken
from dataclasses import dataclass
from enum import Enum
from typing import Any

from azure.core.credentials import AccessToken, TokenCredential
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from mcp.server.lowlevel.server import request_ctx

from fabric_rti_mcp.config import global_config as config
from fabric_rti_mcp.config.obo import obo_config


class TokenTarget(str, Enum):
    KUSTO = "kusto"
    FABRIC = "fabric"


class CredentialSource(str, Enum):
    BEARER_TOKEN = "bearer-token"
    MANAGED_IDENTITY = "managed-identity"
    LOCAL_DEVELOPER = "local-developer"
    UNAVAILABLE = "unavailable"


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
    """A credential that reads the bearer token from the current request context on each call."""

    def __init__(self, token_target: TokenTarget) -> None:
        self._token_target = token_target

    def get_token(self, *scopes: str, **kwargs: Any) -> AccessToken:
        token = _get_request_bearer_token(self._token_target)
        if not token:
            raise ValueError("No auth token available in request context")
        return AccessToken(token=token, expires_on=int(time.time()) + 3600)


def _default_credential_kwargs(authority: str | None = None) -> dict[str, Any]:
    credential_kwargs: dict[str, Any] = {
        "exclude_shared_token_cache_credential": True,
        "exclude_interactive_browser_credential": False,
    }
    if authority:
        credential_kwargs["authority"] = authority
    return credential_kwargs


def http_allows_missing_bearer() -> bool:
    """Return True when HTTP mode is explicitly configured to use a server/local credential without a bearer."""
    return (
        config.transport == "http" and resolve_credential_source(TokenTarget.KUSTO) is not CredentialSource.UNAVAILABLE
    )


def _extract_token_from_header(auth_header: str) -> str:
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:]
    return auth_header


def _get_request_bearer_token(token_target: TokenTarget) -> str | None:
    token = _request_tokens[token_target].get()
    if token:
        return token

    try:
        request = request_ctx.get().request
    except LookupError:
        return None
    if request is None:
        return None

    headers = getattr(request, "headers", None)
    if headers is None:
        return None

    auth_header = headers.get("Authorization", "") or headers.get("authorization", "")
    if not auth_header:
        return None
    return _extract_token_from_header(auth_header)


def resolve_credential_source(token_target: TokenTarget) -> CredentialSource:
    """Return the credential source allowed for the current transport and request context."""
    if _get_request_bearer_token(token_target):
        return CredentialSource.BEARER_TOKEN
    if config.transport == "http":
        if config.http_allow_mi:
            return CredentialSource.MANAGED_IDENTITY
        if config.http_debug_mode:
            return CredentialSource.LOCAL_DEVELOPER
        return CredentialSource.UNAVAILABLE
    return CredentialSource.LOCAL_DEVELOPER


def credential_source_cache_key(credential_source: CredentialSource) -> str:
    """Return the cache-key segment for clients that bind credential objects."""
    if credential_source is CredentialSource.MANAGED_IDENTITY:
        return f"{credential_source.value}:{obo_config.umi_client_id or 'system'}"
    return credential_source.value


def get_credential(token_target: TokenTarget, authority: str | None = None) -> TokenCredential:
    """Resolve the credential for the current transport and request context."""
    credential_source = resolve_credential_source(token_target)
    if credential_source is CredentialSource.BEARER_TOKEN:
        return BearerTokenCredential(token_target)
    if credential_source is CredentialSource.MANAGED_IDENTITY:
        return ManagedIdentityCredential(client_id=obo_config.umi_client_id or None)
    if credential_source is CredentialSource.LOCAL_DEVELOPER:
        return DefaultAzureCredential(**_default_credential_kwargs(authority))
    raise ValueError(
        "No HTTP request bearer token is available. HTTP mode does not use local credentials by default. "
        "Set FABRIC_RTI_HTTP_ALLOW_MI=true to use Managed Identity fallback, or "
        "FABRIC_RTI_HTTP_DEBUG_MODE=true for local HTTP debugging only."
    )
