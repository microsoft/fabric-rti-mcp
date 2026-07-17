from mcp.types import ToolAnnotations

from fabric_rti_mcp.services import AddTool
from fabric_rti_mcp.services.kusto import kusto_service


def register_tools(add_tool: AddTool) -> None:
    add_tool(
        kusto_service.kusto_known_services,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
    add_tool(
        kusto_service.kusto_query,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
    add_tool(
        kusto_service.kusto_command,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
    )
    add_tool(
        kusto_service.kusto_show_command,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
    add_tool(
        kusto_service.kusto_list_entities,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
    add_tool(
        kusto_service.kusto_describe_database,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
    add_tool(
        kusto_service.kusto_describe_database_entity,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
    add_tool(
        kusto_service.kusto_graph_query,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
    add_tool(
        kusto_service.kusto_sample_entity,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
    add_tool(
        kusto_service.kusto_ingest_inline_into_table,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
    )
    if kusto_service.CONFIG.shots_table:
        add_tool(
            kusto_service.kusto_get_shots,
            annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
        )
    add_tool(
        kusto_service.kusto_deeplink_from_query,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
    add_tool(
        kusto_service.kusto_show_queryplan,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
    add_tool(
        kusto_service.kusto_diagnostics,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
