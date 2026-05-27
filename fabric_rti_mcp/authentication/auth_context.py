from contextvars import ContextVar, Token

_request_token: ContextVar[str | None] = ContextVar("_request_token", default=None)


def set_auth_token(token: str | None) -> Token[str | None]:
    """Set the auth token for the current request context."""
    return _request_token.set(token)


def get_auth_token() -> str | None:
    """Get the auth token from the current request context."""
    return _request_token.get()


def reset_auth_token(context_token: Token[str | None]) -> None:
    """Reset the auth token context to its previous value."""
    _request_token.reset(context_token)
