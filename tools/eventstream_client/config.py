"""
Configuration management for Fabric Eventstream MCP Server
Loads settings from environment variables or config files

Integrated from external MCP server: fabric_eventstream_mcp\\config.py
Adapted for fabric-rti-mcp
"""

import os
from typing import Optional, Dict, Any


class Config:
    """Configuration class for managing sensitive settings"""
    
    def __init__(self):
        """Initialize configuration from environment variables"""
        # Azure OpenAI Configuration
        self.azure_openai_endpoint: Optional[str] = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.azure_openai_api_key: Optional[str] = os.getenv("AZURE_OPENAI_API_KEY")
        self.azure_openai_deployment: str = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4")
        self.azure_openai_api_version: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        
        # MCP Server Configuration
        self.mcp_server_url: str = os.getenv("MCP_SERVER_URL", "http://localhost:8000")
        
        # Microsoft Fabric Configuration
        self.default_workspace_id: Optional[str] = os.getenv("FABRIC_WORKSPACE_ID")
        
        # Try to load from local config file if environment variables not set
        self._load_from_file()
    
    def _load_from_file(self) -> None:
        """Load configuration from local config file if it exists"""
        try:
            from .config_local import LOCAL_CONFIG  # type: ignore
            
            # Only override if environment variable is not set
            if not self.azure_openai_endpoint:
                self.azure_openai_endpoint = LOCAL_CONFIG.get("AZURE_OPENAI_ENDPOINT")  # type: ignore
            
            if not self.azure_openai_api_key:
                self.azure_openai_api_key = LOCAL_CONFIG.get("AZURE_OPENAI_API_KEY")  # type: ignore
            
            if not self.azure_openai_deployment:
                self.azure_openai_deployment = LOCAL_CONFIG.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4")  # type: ignore
            
            if not self.azure_openai_api_version:
                self.azure_openai_api_version = LOCAL_CONFIG.get("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")  # type: ignore
            
            if not self.default_workspace_id:
                self.default_workspace_id = LOCAL_CONFIG.get("FABRIC_WORKSPACE_ID")  # type: ignore
                
        except ImportError:
            # config_local.py doesn't exist, which is fine
            pass
        except Exception as e:
            # Handle any other config loading errors gracefully
            print(f"Warning: Could not load local config: {e}")
    
    def is_demo_mode(self) -> bool:
        """Check if we should run in demo mode (missing Azure OpenAI credentials)"""
        return (
            not self.azure_openai_api_key or 
            not self.azure_openai_endpoint or
            self.azure_openai_api_key == "<your-azure-openai-key>" or
            self.azure_openai_endpoint == "https://<your-resource-name>.openai.azure.com/"
        )
    
    def get_workspace_id(self, provided_id: Optional[str] = None) -> Optional[str]:
        """Get workspace ID from provided parameter or default configuration"""
        return provided_id or self.default_workspace_id
    
    def validate(self) -> tuple[bool, list[str]]:
        """Validate configuration and return any missing required settings"""
        missing: list[str] = []
        
        if not self.azure_openai_endpoint:
            missing.append("AZURE_OPENAI_ENDPOINT")
        
        if not self.azure_openai_api_key:
            missing.append("AZURE_OPENAI_API_KEY")
        
        # Workspace ID is optional for some operations
        
        return len(missing) == 0, missing
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary (excluding sensitive data)"""
        return {
            "azure_openai_endpoint": self.azure_openai_endpoint,
            "azure_openai_deployment": self.azure_openai_deployment,
            "azure_openai_api_version": self.azure_openai_api_version,
            "mcp_server_url": self.mcp_server_url,
            "default_workspace_id": self.default_workspace_id,
            "is_demo_mode": self.is_demo_mode()
        }


# Global configuration instance
config = Config()
