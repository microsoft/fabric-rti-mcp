"""
Base classes and interfaces for Fabric RTI MCP extensions.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from mcp.server.fastmcp import FastMCP


class ExtensionBase(ABC):
    """
    Abstract base class for all MCP extensions.
    
    Extensions must implement this interface to be automatically
    discovered and registered by the extension system.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Returns the unique name of the extension.
        
        Returns:
            str: The extension name (e.g., "financial-analytics")
        """
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """
        Returns the version of the extension.
        
        Returns:
            str: The extension version (e.g., "1.0.0")
        """
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """
        Returns a description of the extension's functionality.
        
        Returns:
            str: Brief description of what the extension does
        """
        pass
    
    @abstractmethod
    def register_tools(self, mcp: FastMCP) -> None:
        """
        Register the extension's tools with the MCP server.
        
        Args:
            mcp: The FastMCP server instance to register tools with
        """
        pass
    
    def get_dependencies(self) -> List[str]:
        """
        Returns a list of required dependencies for this extension.
        
        Returns:
            List[str]: List of required package names
        """
        return []
    
    def get_configuration_schema(self) -> Optional[Dict[str, Any]]:
        """
        Returns the configuration schema for this extension.
        
        Returns:
            Optional[Dict[str, Any]]: JSON schema for extension configuration
        """
        return None
    
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the extension with optional configuration.
        
        Args:
            config: Optional configuration dictionary
        """
        pass
    
    def cleanup(self) -> None:
        """
        Cleanup resources when the extension is being unloaded.
        """
        pass
