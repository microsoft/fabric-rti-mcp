"""
Extension system for Fabric RTI MCP Server.

This module provides the base infrastructure for creating domain-specific extensions
that can be easily plugged into the MCP server.
"""

from .base import ExtensionBase
from .registry import ExtensionRegistry

__all__ = [
    "ExtensionBase",
    "ExtensionRegistry",
]
