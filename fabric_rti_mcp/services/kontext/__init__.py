"""
Kontext memory service for fabric-rti-mcp.

Provides semantic memory capabilities for storing and recalling facts, contexts,
and thoughts using Kusto with vector similarity search.
"""

from fabric_rti_mcp.services.kontext import kontext_tools

__all__ = ["kontext_tools"]
