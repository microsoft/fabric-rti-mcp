"""
Middleware module for MCP servers with auth

This module provides middleware components for authentication, authorization in Http mode.
"""
from __future__ import annotations

import base64
import json
from typing import Callable, Awaitable, Dict, Any

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse
from fabric_rti_mcp.common import logger
from fabric_rti_mcp.kusto.kusto_connection import set_auth_token

def extract_token_from_header(auth_header: str) -> str:
    """Extract clean token from authorization header."""
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:]  # Remove "Bearer " (7 characters)
    return auth_header

def decode_jwt_token(token: str) -> Dict[str, Any]:
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
        parts = token_copy.split('.')
        if len(parts) != 3:
            logger.warning("Invalid JWT token format")
            return {}
        
        # Decode the payload (middle part)
        payload_encoded = parts[1]
        
        # Add padding if needed
        padding = '=' * (4 - len(payload_encoded) % 4) if len(payload_encoded) % 4 else ''
        payload_padded = payload_encoded + padding
        
        # Replace URL safe characters
        payload_fixed = payload_padded.replace('-', '+').replace('_', '/')
        
        # Decode base64
        try:
            decoded = base64.b64decode(payload_fixed)
            return json.loads(decoded)
        except Exception as e:
            logger.warning(f"Failed to decode JWT payload: {str(e)}")
            return {}
    except Exception as e:
        logger.warning(f"Error decoding JWT token: {str(e)}")
        return {}

def add_auth_middleware(fastmcp: FastMCP) -> None:
    """
    Add HTTP authorization middleware by overriding streamable_http_app method.
    
    It adds authentication middleware to the HTTP transport layer.
    
    Args:
        fastmcp: The FastMCP instance to add middleware to
    """
    
    # Store the original streamable_http_app method
    original_streamable_app = fastmcp.streamable_http_app

    def auth_required_streamable_app():
        """StreamableHTTP app with auth middleware."""
        app = original_streamable_app()

        # Add CORS middleware
        from starlette.middleware.cors import CORSMiddleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Allows all origins
            allow_credentials=True,
            allow_methods=["*"],  # Allows all methods
            allow_headers=["*"],  # Allows all headers
        )
        
        # Add middleware to check authentication for MCP endpoints
        @app.middleware("http")  # type: ignore
        async def check_auth(request: Request, call_next: Callable[[Request], Awaitable[JSONResponse]]) -> JSONResponse:  # noqa: F811  # type: ignore[reportUnusedFunction]
            try:
                # Store request context for tools to access
                #set_current_request_context(request)

                # Skip auth check for health endpoint
                if request.url.path == "/health":
                    return await call_next(request)

                # Skip auth check for OPTIONS requests (preflight)
                if request.method == "OPTIONS":
                    return await call_next(request)

                # Check for Authorization header
                auth_header = request.headers.get("Authorization", "") or request.headers.get("authorization", "")

                if not auth_header:
                    return JSONResponse({
                        "error": "unauthorized",
                        "message": "Authorization header required"
                    }, status_code=401)

                # Validate the token using MISE-compliant approach
                request_uri = str(request.url) if hasattr(request, 'url') else ""
                request_method = request.method if hasattr(request, 'method') else "GET"
                logger.info(f"Request URI: {request_uri}, Method: {request_method}")

                # Extract and store the token to be accessible in tools
                token = extract_token_from_header(auth_header)
                
                # Store the original token without modification
                set_auth_token(token)
                
                # Decode and log token claims (doesn't modify the original token)
                token_payload = decode_jwt_token(token)
                
                # Log relevant claims
                audience = token_payload.get('aud', 'N/A')
                tenant_id = token_payload.get('tid', 'N/A')
                scopes = token_payload.get('scp', token_payload.get('roles', 'N/A'))
                
                logger.info(f"Token audience: {audience}")
                logger.info(f"Token tenant ID: {tenant_id}")
                logger.info(f"Token scopes/roles: {scopes}")

                # Continue with request
                response = await call_next(request)
                
                # Log response details
                logger.info(f"Response status code: {response.status_code}")
                
                return response

            except Exception as e:
                logger.error(f"Error in auth middleware: {e}")
                return JSONResponse({
                    "error": "server_error",
                    "message": "Internal server error"
                }, status_code=500)
           # finally:
                # Always clear request context, regardless of how the request completes
                #clear_current_request_context()

        return app
    
    # Replace the streamable_http_app method with auth-enabled version
    fastmcp.streamable_http_app = auth_required_streamable_app


