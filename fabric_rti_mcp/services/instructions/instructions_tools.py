from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from fabric_rti_mcp.services.instructions import instructions_service


def register_tools(mcp: FastMCP) -> None:
    mcp.add_tool(
        instructions_service.common_instructions_list,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
    mcp.add_tool(
        instructions_service.common_instructions_load,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
