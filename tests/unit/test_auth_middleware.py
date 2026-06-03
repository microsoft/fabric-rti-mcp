from fabric_rti_mcp.auth.auth_context import TokenTarget
from fabric_rti_mcp.auth.auth_middleware import token_target_for_jsonrpc_payload, token_target_for_tool_name


class TestToolTokenTargetRouting:
    def test_routes_kusto_tools_to_kusto_target(self) -> None:
        assert token_target_for_tool_name("kusto_query") is TokenTarget.KUSTO

    def test_routes_non_kusto_tools_to_fabric_target(self) -> None:
        assert token_target_for_tool_name("eventstream_list") is TokenTarget.FABRIC
        assert token_target_for_tool_name("activator_create_trigger") is TokenTarget.FABRIC
        assert token_target_for_tool_name("map_get") is TokenTarget.FABRIC
        assert token_target_for_tool_name("unknown_tool") is TokenTarget.FABRIC


class TestJsonRpcTokenTargetRouting:
    def test_extracts_target_from_tool_call(self) -> None:
        payload = {"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "kusto_query", "arguments": {}}}

        assert token_target_for_jsonrpc_payload(payload) is TokenTarget.KUSTO

    def test_ignores_non_tool_call_payloads(self) -> None:
        assert token_target_for_jsonrpc_payload({"jsonrpc": "2.0", "method": "tools/list", "params": {}}) is None

    def test_routes_unknown_tool_call_to_fabric_target(self) -> None:
        payload = {"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "unknown_tool", "arguments": {}}}

        assert token_target_for_jsonrpc_payload(payload) is TokenTarget.FABRIC
