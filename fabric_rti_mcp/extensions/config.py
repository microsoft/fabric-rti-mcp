"""
Configuration management for extensions.
"""

import json
import os
from typing import Any, Dict, Optional

from fabric_rti_mcp.common import logger


class ExtensionConfig:
    """
    Manages configuration for extensions.
    
    Supports configuration through environment variables and JSON files.
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        if config_dir:
            self.config_dir = config_dir
        else:
            # Go up from fabric_rti_mcp/extensions to fabric_rti_mcp/ then to project root
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            self.config_dir = os.path.join(project_root, "extension_configs")
        self._configs: Dict[str, Dict[str, Any]] = {}
        self._load_configs()
    
    def _load_configs(self) -> None:
        """Load configurations from files and environment variables."""
        # Create config directory if it doesn't exist
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Load from JSON files if they exist
        if os.path.exists(self.config_dir):
            for filename in os.listdir(self.config_dir):
                if filename.endswith('.json'):
                    extension_name = filename[:-5]  # Remove .json extension
                    config_path = os.path.join(self.config_dir, filename)
                    try:
                        with open(config_path, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                            self._configs[extension_name] = config
                            logger.info(f"Loaded config for extension '{extension_name}' from {config_path}")
                    except Exception as e:
                        logger.error(f"Failed to load config from {config_path}: {e}")
    
    def get_extension_config(self, extension_name: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific extension.
        
        Args:
            extension_name: The name of the extension
            
        Returns:
            Optional[Dict[str, Any]]: The configuration dictionary, or None if not found
        """
        # First check environment variables
        env_config = self._get_config_from_env(extension_name)
        
        # Then check loaded file configs
        file_config = self._configs.get(extension_name, {})
        
        # Merge configs (environment takes precedence)
        if env_config or file_config:
            merged_config = {**file_config, **env_config}
            return merged_config
        
        return None
    
    def _get_config_from_env(self, extension_name: str) -> Dict[str, Any]:
        """
        Get configuration from environment variables.
        
        Environment variables should be prefixed with FABRIC_RTI_<EXTENSION_NAME>_
        
        Args:
            extension_name: The name of the extension
            
        Returns:
            Dict[str, Any]: Configuration dictionary from environment variables
        """
        config = {}
        prefix = f"FABRIC_RTI_{extension_name.upper().replace('-', '_')}_"
        
        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_key = key[len(prefix):].lower()
                # Try to parse as JSON, fall back to string
                try:
                    config[config_key] = json.loads(value)
                except json.JSONDecodeError:
                    config[config_key] = value
        
        return config
    
    def save_extension_config(self, extension_name: str, config: Dict[str, Any]) -> None:
        """
        Save configuration for an extension to a JSON file.
        
        Args:
            extension_name: The name of the extension
            config: The configuration dictionary to save
        """
        config_path = os.path.join(self.config_dir, f"{extension_name}.json")
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            self._configs[extension_name] = config
            logger.info(f"Saved config for extension '{extension_name}' to {config_path}")
        except Exception as e:
            logger.error(f"Failed to save config to {config_path}: {e}")
    
    def list_configured_extensions(self) -> list[str]:
        """
        Get a list of extensions that have configuration.
        
        Returns:
            list[str]: List of extension names with configuration
        """
        return list(self._configs.keys())
