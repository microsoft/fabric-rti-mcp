"""
Extension registry for automatic discovery and management of extensions.
"""

import importlib
import inspect
import os
import pkgutil
from types import ModuleType
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

from fabric_rti_mcp.common import logger

from .base import ExtensionBase
from .config import ExtensionConfig


class ExtensionRegistry:
    """
    Registry for managing and discovering MCP extensions.

    This class handles automatic discovery of extensions in the extensions
    directory and provides methods for registering and managing them.
    """

    def __init__(self):
        self._extensions: Dict[str, ExtensionBase] = {}
        self._config = ExtensionConfig()

    def register(self, extension: ExtensionBase) -> None:
        """
        Register an extension with the registry.

        Args:
            extension: The extension instance to register

        Raises:
            ValueError: If an extension with the same name is already registered
        """
        if extension.name in self._extensions:
            logger.warning(
                f"Extension '{extension.name}' is already registered, skipping"
            )
            return

        logger.info(f"Registering extension: {extension.name} v{extension.version}")

        # Initialize the extension with its configuration
        config = self._config.get_extension_config(extension.name)
        if hasattr(extension, "initialize"):
            extension.initialize(config)

        self._extensions[extension.name] = extension

    def discover_extensions(self) -> None:
        """
        Automatically discover and register extensions in the extensions directory.

        This method scans the extensions directory for Python modules that contain
        ExtensionBase subclasses and automatically registers them.
        """
        extensions_path = os.path.dirname(__file__)
        logger.info(f"Discovering extensions in: {extensions_path}")

        # Import the extensions package
        import fabric_rti_mcp.extensions as extensions_pkg

        # Walk through all modules in the extensions package
        for _, modname, _ in pkgutil.walk_packages(
            extensions_pkg.__path__, extensions_pkg.__name__ + "."
        ):
            # Skip base modules, templates, and test files
            if (
                modname.endswith((".base", ".registry", ".config", ".templates"))
                or "test_" in modname
            ):
                continue

            try:
                module = importlib.import_module(modname)
                self._register_extensions_from_module(module)
            except Exception as e:
                logger.error(f"Failed to load extension module {modname}: {e}")

    def _register_extensions_from_module(self, module: ModuleType) -> None:
        """
        Register all ExtensionBase subclasses found in a module.

        Args:
            module: The Python module to scan for extensions
        """
        for name, obj in inspect.getmembers(module):
            if (
                inspect.isclass(obj)
                and issubclass(obj, ExtensionBase)
                and obj is not ExtensionBase
                and not inspect.isabstract(obj)
            ):

                try:
                    extension_instance = obj()
                    self.register(extension_instance)
                except Exception as e:
                    logger.error(f"Failed to instantiate extension {name}: {e}")

    def register_all_tools(self, mcp: FastMCP) -> None:
        """
        Register tools from all registered extensions with the MCP server.

        Args:
            mcp: The FastMCP server instance to register tools with
        """
        for extension_name, extension in self._extensions.items():
            try:
                logger.info(f"Registering tools for extension: {extension_name}")
                extension.register_tools(mcp)
            except Exception as e:
                logger.error(
                    f"Failed to register tools for extension {extension_name}: {e}"
                )

    def get_extension(self, name: str) -> Optional[ExtensionBase]:
        """
        Get a registered extension by name.

        Args:
            name: The name of the extension to retrieve

        Returns:
            Optional[ExtensionBase]: The extension instance, or None if not found
        """
        return self._extensions.get(name)

    def list_extensions(self) -> List[str]:
        """
        Get a list of all registered extension names.

        Returns:
            List[str]: List of registered extension names
        """
        return list(self._extensions.keys())

    def get_extension_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all registered extensions.

        Returns:
            Dict[str, Dict[str, Any]]: Dictionary mapping extension names to their info
        """
        return {
            name: {
                "version": ext.version,
                "description": ext.description,
                "dependencies": ext.get_dependencies(),
            }
            for name, ext in self._extensions.items()
        }

    def cleanup_all(self) -> None:
        """
        Cleanup all registered extensions.
        """
        for extension_name, extension in self._extensions.items():
            try:
                logger.info(f"Cleaning up extension: {extension_name}")
                extension.cleanup()
            except Exception as e:
                logger.error(f"Failed to cleanup extension {extension_name}: {e}")
