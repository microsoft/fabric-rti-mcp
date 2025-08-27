import base64
import json
from typing import Any, Dict, List, Optional, Union

import httpx
from azure.identity import DefaultAzureCredential


class FabricConnection:
    """Connection class for Fabric REST API interactions."""
    
    def __init__(self):
        self.base_url = "https://dailyapi.fabric.microsoft.com/v1"
        self.credential = DefaultAzureCredential(
            exclude_shared_token_cache_credential=True,
            exclude_interactive_browser_credential=False,
        )
        self._access_token: Optional[str] = None
    
    async def _get_access_token(self) -> str:
        """Get or refresh the access token for Fabric API."""
        if not self._access_token:
            token = self.credential.get_token("https://api.fabric.microsoft.com/.default")
            self._access_token = token.token
        return self._access_token
    
    async def _make_request(self, method: str, endpoint: str, use_full_url: bool = False, **kwargs: Any) -> Dict[str, Any]:
        """Make an authenticated request to the Fabric API."""
        token = await self._get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            **kwargs.get("headers", {})
        }
        
        # Determine the full URL
        if use_full_url:
            url = endpoint
        else:
            url = f"{self.base_url}{endpoint}"
        
        # Debug logging - show everything
        import sys
        sys.stderr.write(f"=== FABRIC API REQUEST TRACE ===\n")
        sys.stderr.write(f"Method: {method}\n")
        sys.stderr.write(f"URL: {url}\n")
        sys.stderr.write(f"Headers: {dict(headers)}\n")
        sys.stderr.write(f"Token (first 20 chars): {token[:20]}...\n")
        if kwargs.get("json"):
            import json as json_lib
            sys.stderr.write(f"Payload:\n{json_lib.dumps(kwargs['json'], indent=2)}\n")
        else:
            sys.stderr.write("No JSON payload\n")
        sys.stderr.flush()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                **{k: v for k, v in kwargs.items() if k != "headers" and k != "use_full_url"}
            )
            sys.stderr.write(f"Response status: {response.status_code}\n")
            sys.stderr.write(f"Response headers: {dict(response.headers)}\n")
            sys.stderr.write(f"Response text: {response.text}\n")
            sys.stderr.write(f"=== END FABRIC API TRACE ===\n")
            sys.stderr.flush()
            response.raise_for_status()
            return response.json()
    
    async def get_workspaces(self) -> List[Dict[str, Any]]:
        """Get list of accessible workspaces."""
        response = await self._make_request("GET", "/workspaces")
        return response.get("value", [])
    
    async def get_workspace_items(self, workspace_id: str, item_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get items in a workspace, optionally filtered by type."""
        endpoint = f"/workspaces/{workspace_id}/items"
        if item_type:
            endpoint += f"?type={item_type}"
        response = await self._make_request("GET", endpoint)
        return response.get("value", [])
    
    async def create_reflex_with_definition(
        self, 
        workspace_id: str, 
        name: str, 
        description: Optional[str] = None,
        reflex_definition: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None
    ) -> Dict[str, Any]:
        """Create a new Reflex (Data Activator) item with a definition."""
        
        if reflex_definition:
            # Create the definition payload based on the example structure
            definition_parts = []
            
            # Create ReflexEntities.json as raw array (no entities wrapper) to match working example
            
            # Debug: Show the raw array structure before encoding
            import sys
            sys.stderr.write(f"=== RAW ARRAY STRUCTURE (before encoding) ===\n")
            sys.stderr.write(f"{json.dumps(reflex_definition, indent=2)}\n")
            sys.stderr.write(f"=== END RAW ARRAY ===\n")
            sys.stderr.flush()
            
            entities_json = json.dumps(reflex_definition, separators=(',', ':'))
            entities_b64 = base64.b64encode(entities_json.encode('utf-8')).decode('utf-8')
            
            # manual fix attempt:
            # Take reflex_definition as-is (array) and encode directly to base64
            reflex_json = json.dumps(reflex_definition)
            reflex_b64 = base64.b64encode(reflex_json.encode('utf-8')).decode('utf-8')

            # Replace the entities part with the direct encoding
            # definition_parts[0] = {
            #     "path": "ReflexEntities.json",
            #     "payload": reflex_b64,
            #     "payloadType": "InlineBase64"
            # }
            
            # definition_parts.append({
            #     "path": "ReflexEntities.json",
            #     "payload": entities_b64,
            #     "payloadType": "InlineBase64"
            # })
            
            # Create .platform file with the working example structure
            platform_data = {
                "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
                "metadata": {
                    "type": "Reflex",
                    "displayName": "My activatorTest2",
                    "description": "m ativator test2"
                },
                "config": {
                    "version": "2.0",
                    "logicalId": "4042fb10-1349-b4c0-4361-514b6b19c1fe"
                }
            }
            
            # Debug: Show the .platform file structure before encoding
            import sys
            sys.stderr.write(f"=== .PLATFORM FILE STRUCTURE (before encoding) ===\n")
            sys.stderr.write(f"{json.dumps(platform_data, indent=2)}\n")
            sys.stderr.write(f"=== END .PLATFORM FILE ===\n")
            sys.stderr.flush()
            
            platform_json = json.dumps(platform_data)
            platform_b64 = base64.b64encode(platform_json.encode('utf-8')).decode('utf-8')

            # definition_parts[1] ={
            #     "path": ".platform",
            #     "payload": platform_b64,
            #     "payloadType": "InlineBase64"
            # }
            
            payload = {
                "displayName": name,
                "description": description or f"Data Activator created for KQL monitoring",
                "definition": {
                    "parts": [
                        {
                            "path": "ReflexEntities.json",
                            "payload": reflex_b64,
                            "payloadType": "InlineBase64"
                        },
                        {
                            "path": ".platform",
                            "payload": platform_b64,
                            "payloadType": "InlineBase64"
                        }
                    ]
                }
            }
        else:
            # Simple reflex without definition
            payload = {
                "displayName": name,
                "description": description or f"Data Activator created for KQL monitoring"
            }
        
        # Use the correct endpoint for reflex creation
        endpoint = f"/workspaces/{workspace_id}/reflexes"
        return await self._make_request(
            "POST", 
            endpoint,
            json=payload
        )
    
    async def create_activator_item(self, workspace_id: str, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        """Create a new Activator item in the specified workspace."""
        return await self.create_reflex_with_definition(workspace_id, name, description)
