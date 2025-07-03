"""
Integrated from external MCP server: fabric_eventstream_mcp\main.py
Adapted for fabric-rti-mcp
"""

from fastapi import FastAPI, Header, HTTPException, Path, Query, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
import base64
import httpx
from fastapi.responses import JSONResponse

security = HTTPBearer()

app = FastAPI(
    title="Fabric Eventstream MCP Server", 
    description="MCP server for Microsoft Fabric Eventstream REST API integration.\n\nNote: This server runs locally, but all Eventstream operations are forwarded to the remote Microsoft Fabric API (https://api.fabric.microsoft.com). You must provide a valid Azure AD Bearer token in the Authorization header for all requests.",
    openapi_tags=[
        {
            "name": "authentication",
            "description": "Azure AD authentication for Microsoft Fabric API",
        },
        {
            "name": "eventstream",
            "description": "Operations with Microsoft Fabric Eventstream items",
        }
    ]
)

FABRIC_API_BASE = "https://api.fabric.microsoft.com/v1"

class EventstreamDefinition(BaseModel):
    sources: list
    destinations: list
    operators: list
    streams: list
    compatibilityLevel: Optional[str] = "1.0"

class EventstreamRequest(BaseModel):
    workspaceId: str
    definition: EventstreamDefinition

# Dependency to get authorization header or fetch token
async def get_authorization_header(authorization: str = Header(None)) -> str:
    """
    Use provided Authorization header, or fetch token via get_fabric_token.
    """
    if authorization:
        return authorization
    # fallback to interactive/browser credential
    try:
        from auth import get_fabric_token
    except ImportError:
        raise HTTPException(status_code=500, detail="Authentication module not available")
    token = get_fabric_token()
    if not token:
        raise HTTPException(status_code=401, detail="Authorization required and token retrieval failed")
    return f"Bearer {token}"

@app.post("/eventstream/create", tags=["eventstream"])
async def create_eventstream(req: EventstreamRequest, authorization: str = Depends(get_authorization_header)):
    # Prepare the eventstream definition as base64
    definition_json = req.definition.json()
    definition_b64 = base64.b64encode(definition_json.encode("utf-8")).decode("utf-8")
    payload = {
        "definition": {
            "parts": [
                {
                    "path": "eventstream.json",
                    "payload": definition_b64,
                    "payloadType": "InlineBase64"
                }
            ]
        }
    }
    url = f"{FABRIC_API_BASE}/workspaces/{req.workspaceId}/items"
    headers = {"Authorization": authorization, "Content-Type": "application/json"}
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        if response.status_code != 200 and response.status_code != 201:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()

@app.get("/eventstream/{workspace_id}/{item_id}", tags=["eventstream"])
async def get_eventstream(workspace_id: str = Path(...), item_id: str = Path(...), authorization: str = Depends(get_authorization_header)):
    url = f"{FABRIC_API_BASE}/workspaces/{workspace_id}/items/{item_id}"
    headers = {"Authorization": authorization}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()

@app.get("/eventstream/{workspace_id}", tags=["eventstream"])
async def list_eventstreams(workspace_id: str = Path(...), authorization: str = Depends(get_authorization_header)):
    """
    List all Eventstream items in a Fabric workspace.
    This endpoint is local, but it proxies the request to the remote Microsoft Fabric API.
    """
    url = f"{FABRIC_API_BASE}/workspaces/{workspace_id}/items"
    headers = {"Authorization": authorization}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()

@app.delete("/eventstream/{workspace_id}/{item_id}", tags=["eventstream"])
async def delete_eventstream(workspace_id: str = Path(...), item_id: str = Path(...), authorization: str = Depends(get_authorization_header)):
    url = f"{FABRIC_API_BASE}/workspaces/{workspace_id}/items/{item_id}"
    headers = {"Authorization": authorization}
    async with httpx.AsyncClient() as client:
        response = await client.delete(url, headers=headers)
        if response.status_code != 200 and response.status_code != 204:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return {"detail": "Deleted"}

@app.put("/eventstream/{workspace_id}/{item_id}", tags=["eventstream"])
async def update_eventstream(workspace_id: str = Path(...), item_id: str = Path(...), req: EventstreamRequest = None, authorization: str = Depends(get_authorization_header)):
    # Prepare the eventstream definition as base64
    definition_json = req.definition.json()
    definition_b64 = base64.b64encode(definition_json.encode("utf-8")).decode("utf-8")
    payload = {
        "definition": {
            "parts": [
                {
                    "path": "eventstream.json",
                    "payload": definition_b64,
                    "payloadType": "InlineBase64"
                }
            ]
        }
    }
    url = f"{FABRIC_API_BASE}/workspaces/{workspace_id}/items/{item_id}"
    headers = {"Authorization": authorization, "Content-Type": "application/json"}
    async with httpx.AsyncClient() as client:
        response = await client.put(url, json=payload, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()

# MCP Tool Descriptions
MCP_TOOLS = [
    {
        "name": "create_eventstream",
        "description": "Create an Eventstream item in Microsoft Fabric.",
        "endpoint": "/eventstream/create",
        "method": "POST",
        "input_schema": EventstreamRequest.schema(),
        "output_schema": {},
    },
    {
        "name": "get_eventstream",
        "description": "Get an Eventstream item by workspace and item ID.",
        "endpoint": "/eventstream/{workspace_id}/{item_id}",
        "method": "GET",
        "input_schema": {
            "workspace_id": {"type": "string", "description": "Workspace ID (UUID)"},
            "item_id": {"type": "string", "description": "Eventstream Item ID (UUID)"}
        },
        "output_schema": {},
    },
    {
        "name": "list_eventstreams",
        "description": "List all Eventstream items in a workspace.",
        "endpoint": "/eventstream/{workspace_id}",
        "method": "GET",
        "input_schema": {
            "workspace_id": {"type": "string", "description": "Workspace ID (UUID)"}
        },
        "output_schema": {},
    },
    {
        "name": "delete_eventstream",
        "description": "Delete an Eventstream item by workspace and item ID.",
        "endpoint": "/eventstream/{workspace_id}/{item_id}",
        "method": "DELETE",
        "input_schema": {
            "workspace_id": {"type": "string", "description": "Workspace ID (UUID)"},
            "item_id": {"type": "string", "description": "Eventstream Item ID (UUID)"}
        },
        "output_schema": {},
    },
    {
        "name": "update_eventstream",
        "description": "Update an Eventstream item by workspace and item ID.",
        "endpoint": "/eventstream/{workspace_id}/{item_id}",
        "method": "PUT",
        "input_schema": {
            "workspace_id": {"type": "string", "description": "Workspace ID (UUID)"},
            "item_id": {"type": "string", "description": "Eventstream Item ID (UUID)"},
            "body": EventstreamRequest.schema()
        },
        "output_schema": {},
    }
]

@app.get("/mcp/v1/tools")
def mcp_tools():
    """MCP endpoint to list all available tools (APIs) with their descriptions."""
    return JSONResponse(content={"tools": MCP_TOOLS})

@app.post("/auth/get-token", tags=["authentication"])
async def get_authentication_token():
    """
    Get an Azure AD token for Microsoft Fabric API using interactive browser authentication.
    This endpoint triggers an interactive login flow and returns a Bearer token.
    """
    try:
        import sys
        import os
        
        # Add current directory to Python path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        import auth
        
        token = auth.get_fabric_token()
        if token:
            # Decode token to get expiration info
            token_info = auth.decode_token(token)
            return {
                "access_token": token,
                "token_type": "Bearer",
                "expires_at": token_info.get('exp'),
                "user": token_info.get('unique_name', 'Unknown'),
                "tenant": token_info.get('tid'),
                "scope": token_info.get('scp', 'Unknown')
            }
        else:
            raise HTTPException(status_code=401, detail="Authentication failed")
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"Authentication module not available: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication error: {str(e)}")

@app.get("/auth/token-info", tags=["authentication"])
async def get_token_info(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get information about the current Bearer token.
    """
    try:
        import sys
        import os
        
        # Add current directory to Python path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        import auth
        
        token_info = auth.decode_token(credentials.credentials)
        return {
            "user": token_info.get('unique_name', 'Unknown'),
            "tenant": token_info.get('tid'),
            "expires_at": token_info.get('exp'),
            "scope": token_info.get('scp', 'Unknown'),
            "app_id": token_info.get('appid'),
            "token_valid": True
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid token: {str(e)}")

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """
    Custom Swagger UI with integrated authentication button and auto-token injection.
    """
    return HTMLResponse("""
<!DOCTYPE html>
<html>
<head>
    <link type="text/css" rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui.css" />
    <link rel="shortcut icon" href="https://fastapi.tiangolo.com/img/favicon.png">
    <title>Fabric Eventstream MCP Server - Swagger UI</title>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-bundle.js"></script>
    <script>
    function initUI(token) {
        const ui = SwaggerUIBundle({
            url: '/openapi.json',
            dom_id: '#swagger-ui',
            presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.presets.standalone],
            layout: 'StandaloneLayout',
            deepLinking: true,
            showExtensions: true,
            showCommonExtensions: true,
            requestInterceptor: (req) => {
                if (token) {
                    req.headers['Authorization'] = 'Bearer ' + token;
                }
                return req;
            }
        });
    }

    // Fetch token and initialize UI
    fetch('/auth/get-token', { method: 'POST', headers: { 'Accept': 'application/json' } })
        .then(response => response.json())
        .then(data => {
            const token = data.access_token;
            // store token in memory (page context)
            window._mcp_access_token = token;
            initUI(token);
        })
        .catch(err => {
            console.error('Failed to fetch token:', err);
            // initialize UI without token
            initUI(null);
        });
    </script>
</body>
</html>
    """)
