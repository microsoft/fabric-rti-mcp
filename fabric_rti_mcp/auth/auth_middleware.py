from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from typing import Any, cast

from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from fabric_rti_mcp.auth.auth_context import (
    RequestTokenContext,
    TokenTarget,
    http_allows_missing_bearer,
    reset_request_token,
    set_request_token,
)
from fabric_rti_mcp.auth.token_obo_exchanger import TokenOboExchanger
from fabric_rti_mcp.config import global_config as config
from fabric_rti_mcp.config import logger
from fabric_rti_mcp.config.obo import obo_config

# Algorithms allowed for bearer token shape screening.
# Microsoft Entra ID uses RS256 (per https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration).
# This is not cryptographic token validation; production HTTP deployments should use upstream validation or OBO.
ALLOWED_JWT_ALGORITHMS = ["RS256"]


def extract_token_from_header(auth_header: str) -> str:
    """Extract clean token from authorization header."""
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:]  # Remove "Bearer " (7 characters)
    return auth_header


def _decode_base64url(data: str) -> bytes:
    """Decode a base64url-encoded string (with padding fixup)."""
    padding = "=" * (4 - len(data) % 4) if len(data) % 4 else ""
    return base64.b64decode(data.replace("-", "+").replace("_", "/") + padding)


def decode_jwt_token(token: str) -> dict[str, Any]:
    """
    Decode a JWT token without verification.

    This function decodes the JWT token and extracts its payload.
    It doesn't verify the signature since we're just interested in logging the claims.
    It doesn't modify the original token - it only reads and extracts information.

    Args:
        token: The JWT token string

    Returns:
        Dict containing the decoded payload
    """
    # Create a copy of the token to ensure we don't modify the original
    token_copy = token[:]

    try:
        # JWT tokens have 3 parts: header.payload.signature
        parts = token_copy.split(".")
        if len(parts) != 3:
            logger.warning("Invalid JWT token format")
            return {}

        # Decode the payload (middle part)
        payload_encoded = parts[1]

        # Add padding if needed
        padding = "=" * (4 - len(payload_encoded) % 4) if len(payload_encoded) % 4 else ""
        payload_padded = payload_encoded + padding

        # Replace URL safe characters
        payload_fixed = payload_padded.replace("-", "+").replace("_", "/")

        # Decode base64
        try:
            decoded = base64.b64decode(payload_fixed)
            payload: dict[str, Any] = json.loads(decoded)
            return payload
        except Exception as e:
            logger.warning(f"Failed to decode JWT payload: {str(e)}")
            return {}
    except Exception as e:
        logger.warning(f"Error decoding JWT token: {str(e)}")
        return {}  # TBD : Handle token validation errors errors when validation is added


def validate_jwt_token_format(token: str) -> tuple[bool, str]:
    """Validate JWT has 3 non-empty dot-separated parts."""
    parts = token.split(".")
    if len(parts) != 3:
        return False, f"Invalid JWT format: expected 3 parts, got {len(parts)}"
    for i, part in enumerate(parts):
        if not part:
            return False, f"Invalid JWT format: part {i} is empty"
    return True, ""


def validate_jwt_token_expiration(token_payload: dict[str, Any]) -> tuple[bool, str]:
    """Validate the token is not expired. Passes if 'exp' claim is absent."""
    exp = token_payload.get("exp")
    if exp is None:
        return True, ""

    current_time = datetime.now(timezone.utc).timestamp()
    if current_time > exp:
        return False, "Token has expired"

    logger.info(f"Token valid for {int(exp - current_time)} seconds")
    return True, ""


def validate_jwt_token_structure(token: str) -> tuple[bool, str]:
    """Validate the JWT header is decodable and uses a secure algorithm."""
    parts = token.split(".")

    try:
        header = json.loads(_decode_base64url(parts[0]))
    except Exception as e:
        return False, f"Failed to decode token header: {e}"

    alg = header.get("alg")
    if not alg:
        return False, "Token missing 'alg' (algorithm) in header"

    if alg not in ALLOWED_JWT_ALGORITHMS:
        return False, f"Token uses unsupported algorithm: {alg}"

    return True, ""


def _log_token_claims(token_payload: dict[str, Any]) -> None:
    """Log token claims for debugging (informational only, never rejects)."""
    aud = token_payload.get("aud", "N/A")
    tid = token_payload.get("tid", "N/A")
    oid = token_payload.get("oid", "N/A")
    iss = token_payload.get("iss", "N/A")
    scp = token_payload.get("scp", token_payload.get("roles", "N/A"))
    logger.info(f"Token claims - Audience: {aud}, Tenant: {tid}, Object ID: {oid}")
    logger.info(f"Token claims - Issuer: {iss}, Scopes/Roles: {scp}")


def validate_token(token: str) -> tuple[bool, str]:
    """
    Perform deployment-agnostic bearer token shape screening:
    - Format (3 parts, non-empty)
    - Header decodable with secure algorithm
    - Not expired

    This does not verify the token signature, issuer, or audience.
    """
    is_valid, error_msg = validate_jwt_token_format(token)
    if not is_valid:
        return False, error_msg

    is_valid, error_msg = validate_jwt_token_structure(token)
    if not is_valid:
        return False, error_msg

    payload = decode_jwt_token(token)
    if not payload:
        return False, "Failed to decode token payload"

    is_valid, error_msg = validate_jwt_token_expiration(payload)
    if not is_valid:
        return False, error_msg

    _log_token_claims(payload)
    return True, ""


def token_target_for_tool_name(tool_name: str) -> TokenTarget:
    """Return the auth token target used by a registered MCP tool."""
    if tool_name.startswith("kusto_"):
        return TokenTarget.KUSTO
    return TokenTarget.FABRIC


def _as_json_object(value: object) -> dict[str, object] | None:
    if not isinstance(value, dict):
        return None
    return cast(dict[str, object], value)


def _tool_name_from_jsonrpc_payload(payload: object) -> str | None:
    payload_object = _as_json_object(payload)
    if payload_object is None or payload_object.get("method") != "tools/call":
        return None

    params = _as_json_object(payload_object.get("params"))
    if params is None:
        raise ValueError("MCP tools/call request is missing object params")

    tool_name = params.get("name")
    if not isinstance(tool_name, str) or not tool_name:
        raise ValueError("MCP tools/call request is missing a tool name")

    return tool_name


def token_target_for_jsonrpc_payload(payload: object) -> TokenTarget | None:
    """Return the auth token target required by a JSON-RPC request payload."""
    tool_name = _tool_name_from_jsonrpc_payload(payload)
    if tool_name is None:
        return None
    return token_target_for_tool_name(tool_name)


def token_target_for_request_body(body: bytes) -> TokenTarget | None:
    if not body:
        return None

    try:
        payload: object = json.loads(body)
    except json.JSONDecodeError:
        return None

    return token_target_for_jsonrpc_payload(payload)


def _receive_replayed_body(body: bytes, original_receive: Receive) -> Receive:
    body_sent = False

    async def receive() -> Message:
        nonlocal body_sent
        if body_sent:
            return await original_receive()
        body_sent = True
        return {"type": "http.request", "body": body, "more_body": False}

    return receive


def _audience_for_token_target(token_target: TokenTarget) -> str:
    if token_target is TokenTarget.KUSTO:
        return obo_config.kusto_audience
    if token_target is TokenTarget.FABRIC:
        return obo_config.fabric_audience
    raise ValueError(f"Unsupported auth token target: {token_target}")


class AuthMiddleware:
    """HTTP middleware that screens bearer tokens and propagates them to MCP tool calls."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        try:
            request = Request(scope, receive)

            # Skip auth check for health endpoint
            if request.url.path == "/health":
                await self.app(scope, receive, send)
                return

            # Skip auth check for OPTIONS requests (preflight)
            if request.method == "OPTIONS":
                await self.app(scope, receive, send)
                return

            # Check for Authorization header
            auth_header = request.headers.get("Authorization", "") or request.headers.get("authorization", "")

            if not auth_header and not http_allows_missing_bearer():
                response = JSONResponse(
                    {"error": "unauthorized", "message": "Authorization header required"},
                    status_code=401,
                )
                await response(scope, receive, send)
                return

            request_uri = str(request.url) if "url" in request else ""
            request_method = request.method if "method" in request else "GET"
            logger.info(f"Request URI: {request_uri}, Method: {request_method}")

            body = await request.body()
            replay_receive = _receive_replayed_body(body, receive)

            try:
                token_target = token_target_for_request_body(body)
            except ValueError as e:
                logger.error(f"Auth token routing failed: {e}")
                response = JSONResponse({"error": "bad_request", "message": str(e)}, status_code=400)
                await response(scope, receive, send)
                return

            token = extract_token_from_header(auth_header) if auth_header else ""
            if token:
                is_valid, error_msg = validate_token(token)
                if not is_valid:
                    logger.error(f"Token screening failed: {error_msg}")
                    response = JSONResponse(
                        {"error": "unauthorized", "message": f"Invalid token: {error_msg}"}, status_code=401
                    )
                    await response(scope, receive, send)
                    return
            else:
                logger.warning("HTTP request has no bearer token; using explicitly configured credential fallback")

            request_token_context: RequestTokenContext | None = None
            try:
                if token_target and token:
                    token_exchanger = TokenOboExchanger() if config.use_obo_flow else None
                    if token_exchanger:
                        logger.info(f"Started performing OBO token exchange for {token_target.value}")
                        token_for_target = await token_exchanger.perform_obo_token_exchange(
                            user_token=token,
                            resource_uri=_audience_for_token_target(token_target),
                        )
                        logger.info(f"Successfully performed OBO token exchange for {token_target.value}")
                    else:
                        logger.info(f"OBO flow not enabled; using original token for {token_target.value}")
                        token_for_target = token
                    request_token_context = set_request_token(token_target, token_for_target)
                elif token_target:
                    logger.info(
                        f"No bearer token provided; relying on configured credential fallback for {token_target.value}"
                    )
                else:
                    logger.info("No auth token target required for request")
            except Exception as e:
                logger.error(f"Error during OBO token exchange: {e}")
                response = JSONResponse(
                    {
                        "error": "unauthorized",
                        "message": "Unauthorized to get the required token to access the resource",
                    },
                    status_code=401,
                )
                await response(scope, receive, send)
                return

            try:
                await self.app(scope, replay_receive, send)
            finally:
                if request_token_context:
                    reset_request_token(request_token_context)

        except Exception as e:
            logger.error(f"Error in auth middleware: {e}")
            response = JSONResponse({"error": "server_error", "message": "Internal server error"}, status_code=500)
            await response(scope, receive, send)


def add_auth_middleware(fastmcp: FastMCP) -> None:
    """
    Add HTTP authorization middleware by overriding streamable_http_app method.

    It adds authentication middleware to the HTTP transport layer.

    Args:
        fastmcp: The FastMCP instance to add middleware to
    """

    # Store the original streamable_http_app method
    original_streamable_app = fastmcp.streamable_http_app

    def auth_required_streamable_app() -> Starlette:
        """StreamableHTTP app with auth middleware."""
        app = original_streamable_app()

        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,  # ty: ignore[invalid-argument-type]
            allow_origins=cors_allowed_origins(),
            allow_credentials=True,
            allow_methods=["*"],  # Allows all methods
            allow_headers=["*"],  # Allows all headers
        )

        # Add middleware to check authentication for MCP endpoints
        app.add_middleware(AuthMiddleware)  # ty: ignore[invalid-argument-type]

        return app

    # Replace the streamable_http_app method with auth-enabled version
    fastmcp.streamable_http_app = auth_required_streamable_app  # type: ignore


def _split_comma_separated(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def cors_allowed_origins() -> list[str]:
    """Return CORS origins for HTTP mode; wildcard requires explicit configuration or debug mode."""
    configured_origins = _split_comma_separated(config.cors_allowed_origins)
    if configured_origins:
        return configured_origins
    if config.http_debug_mode:
        return ["*"]
    return [
        f"http://127.0.0.1:{config.http_port}",
        f"http://localhost:{config.http_port}",
        f"http://[::1]:{config.http_port}",
    ]
