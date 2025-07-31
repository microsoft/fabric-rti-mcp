"""
Integrated from external MCP server: fabric_eventstream_mcp\auth.py
Adapted for fabric-rti-mcp
"""

"""
Authentication utilities for Microsoft Fabric API using Azure Identity.
"""
import jwt
import requests
from azure.identity import InteractiveBrowserCredential
from typing import Optional

# Tenant ID for the Fabric API
TENANT_ID = "72f988bf-86f1-41af-91ab-2d7cd011db47"

# Set the scope for the token - updated for Fabric API
FABRIC_TOKEN_SCOPE = "https://api.fabric.microsoft.com/.default"
POWERBI_TOKEN_SCOPE = "https://analysis.windows.net/powerbi/api/user_impersonation"

def authenticate_and_get_token(scope: str = FABRIC_TOKEN_SCOPE) -> Optional[str]:
    """
    Authenticates the user using InteractiveBrowserCredential from azure.identity library.
    
    Parameters:
    scope (str): The scope for the token. Defaults to Fabric API scope.
    
    Returns:
    str: The access token if successful, None otherwise.
    """
    try:
        credential = InteractiveBrowserCredential(tenant_id=TENANT_ID)
        
        # Acquire a token from Entra
        token = credential.get_token(scope)
        
        # Check if the token was acquired successfully
        if not token:
            print("Failed to acquire token from Entra")
            return None
        
        # Return the token
        return token.token
    
    except Exception as e:
        print(f"Authentication failed: {e}")
        return None

def get_fabric_token() -> Optional[str]:
    """
    Get a token specifically for Microsoft Fabric API.
    
    Returns:
    str: The access token for Fabric API if successful, None otherwise.
    """
    return authenticate_and_get_token(FABRIC_TOKEN_SCOPE)

def get_powerbi_token() -> Optional[str]:
    """
    Get a token specifically for Power BI API (legacy scope).
    
    Returns:
    str: The access token for Power BI API if successful, None otherwise.
    """
    return authenticate_and_get_token(POWERBI_TOKEN_SCOPE)

def make_authenticated_request(api_endpoint: str, method: str = "GET", headers: dict = None, **kwargs) -> Optional[requests.Response]:
    """
    Make an authenticated request to a Fabric API endpoint.
    
    Parameters:
    api_endpoint (str): The API endpoint URL
    method (str): HTTP method (GET, POST, PUT, DELETE, etc.)
    headers (dict): Additional headers to include
    **kwargs: Additional arguments to pass to requests
    
    Returns:
    requests.Response: The response object if successful, None otherwise.
    """
    # Get access token
    access_token = get_fabric_token()
    if access_token is None:
        print("Failed to get access token")
        return None
    
    # Set up headers
    auth_headers = {"Authorization": f"Bearer {access_token}"}
    if headers:
        auth_headers.update(headers)
    
    try:
        # Make the request
        response = requests.request(method, api_endpoint, headers=auth_headers, **kwargs)
        
        # Check if the response is successful
        if response.status_code not in [200, 201, 202, 204]:
            print(f"API request failed with status {response.status_code}: {response.text}")
            return None
        
        return response
    
    except Exception as e:
        print(f"Request failed: {e}")
        return None

def decode_token(token: str) -> dict:
    """
    Decode a JWT token to inspect its contents (without verification).
    
    Parameters:
    token (str): The JWT token to decode
    
    Returns:
    dict: The decoded token payload
    """
    try:
        # Decode without verification (for inspection only)
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded
    except Exception as e:
        print(f"Failed to decode token: {e}")
        return {}

# Example usage
if __name__ == "__main__":
    # Authenticate and get access token
    access_token = get_fabric_token()
    if access_token:
        print("Authentication successful!")
        
        # Decode and print token info
        token_info = decode_token(access_token)
        print(f"Token valid until: {token_info.get('exp', 'Unknown')}")
        print(f"User: {token_info.get('unique_name', 'Unknown')}")
        
        # Example API call
        # api_endpoint = "https://api.fabric.microsoft.com/v1/workspaces"
        # response = make_authenticated_request(api_endpoint)
        # if response:
        #     print("API call successful!")
        #     print(response.json())
    else:
        print("Authentication failed!")
