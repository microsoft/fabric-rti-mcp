from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from fabric_rti_mcp.services.operationagent import operationagent_service


def register_tools(mcp: FastMCP) -> None:
    """Register all OperationAgent tools with the MCP server."""

    mcp.add_tool(
        operationagent_service.operationagent_list,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
    mcp.add_tool(
        operationagent_service.operationagent_get,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )

    mcp.add_tool(
        operationagent_service.operationagent_get_goals,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
    mcp.add_tool(
        operationagent_service.operationagent_get_instructions,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
    mcp.add_tool(
        operationagent_service.operationagent_get_knowledge_sources,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
    mcp.add_tool(
        operationagent_service.operationagent_get_actions,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )

    mcp.add_tool(
        operationagent_service.operationagent_set_goals,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
    )
    mcp.add_tool(
        operationagent_service.operationagent_set_instructions,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
    )
    mcp.add_tool(
        operationagent_service.operationagent_add_knowledge_source,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
    )
    mcp.add_tool(
        operationagent_service.operationagent_remove_knowledge_source,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
    )
    mcp.add_tool(
        operationagent_service.operationagent_add_action,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
    )
    mcp.add_tool(
        operationagent_service.operationagent_remove_action,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
    )

    mcp.add_tool(
        operationagent_service.operationagent_create,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
    )
    mcp.add_tool(
        operationagent_service.operationagent_update,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
    )
