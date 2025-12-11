"""
Tool registration for Kontext memory service.

Kontext provides semantic memory capabilities for storing and recalling facts,
contexts, and thoughts with vector similarity search.
"""

from typing import Any, Literal

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from fabric_rti_mcp.config import logger
from fabric_rti_mcp.services.kontext.kontext_config import KontextConfig
from fabric_rti_mcp.services.kontext.kontext_service import KontextClientCache


class MemoryType:
    """Valid memory types for the kontext service."""

    FACT: Literal["fact"] = "fact"
    CONTEXT: Literal["context"] = "context"
    THOUGHT: Literal["thought"] = "thought"


def kontext_remember(fact: str, type: str, scope: Literal["user", "global"] = "user") -> str:
    """
    Stores a memory item.

    :param fact: Text to remember.
    :param type: Type of the memory item. Options are:
        "fact" - General knowledge. Can be as many facts as needed.
        "context" - One per scope. State or context information.
            For example, summarized context of a conversation on a topic.
        "thought" - Mental note. Could be something useful to remember,
            but not a fact, like a plan or idea.
    :param scope: "user" to use the caller's identifier, "global" to share across users.
    :return: id as a string of the ingested fact.

    Note: Scope is automatically retrieved from Kusto principal roles when using "user".
    """
    client = KontextClientCache.get_client()
    logger.info(f"Storing memory item of type '{type}' with scope '{scope}'")
    return client.remember(fact, type, scope)


def kontext_recall(
    query: str,
    filters: dict[str, Any] | None = None,
    top_k: int = 10,
    scope: Literal["user", "global"] = "user",
) -> list[dict[str, Any]]:
    """
    Retrieves relevant memories.

    :param query: Search query.
    :param filters: Optional filters to apply to the results, e.g. {"type": "fact"}.
    :param top_k: Max rows.
    :param scope: "user" to use the caller's identifier, "global" to search shared scope.
    :return: List of {id, fact, type, scope, creation_time, sim}
    """
    client = KontextClientCache.get_client()
    logger.info(f"Recalling facts for query: {query[:50]}... with scope '{scope}'")
    results = client.recall(query, filters, top_k, scope)
    return results


def register_tools(mcp: FastMCP) -> None:
    """Register Kontext memory tools with the MCP server."""
    # Check if required configuration is set
    env_vars = KontextConfig.existing_env_vars()
    missing = [k for k, v in env_vars.items() if not v]

    if missing:
        logger.info(f"Kontext tools not registered - missing configuration: {', '.join(missing)}")
        return

    logger.info("Registering Kontext memory tools")

    mcp.add_tool(
        kontext_remember,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
    )

    mcp.add_tool(
        kontext_recall,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
