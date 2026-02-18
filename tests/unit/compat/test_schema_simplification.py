import asyncio
import json

from fabric_rti_mcp.compat.ms_foundry import SchemaCompatibleMCP, simplify_schema


class TestSimplifySchema:
    def test_removes_anyof_with_null(self):
        schema = {
            "properties": {"name": {"anyOf": [{"type": "string"}, {"type": "null"}], "default": None, "title": "Name"}},
            "type": "object",
        }
        result = simplify_schema(schema)
        assert "anyOf" not in json.dumps(result)
        assert result["properties"]["name"]["type"] == "string"

    def test_resolves_ref(self):
        schema = {
            "$defs": {"MyModel": {"type": "object", "properties": {"x": {"type": "integer"}}}},
            "properties": {"item": {"$ref": "#/$defs/MyModel"}},
            "type": "object",
        }
        result = simplify_schema(schema)
        assert "$ref" not in json.dumps(result)
        assert "$defs" not in result
        assert result["properties"]["item"]["type"] == "object"

    def test_fixes_empty_type(self):
        schema = {"type": ""}
        result = simplify_schema(schema)
        assert result["type"] == "object"

    def test_merges_allof(self):
        schema = {"allOf": [{"properties": {"a": {"type": "string"}}}, {"properties": {"b": {"type": "integer"}}}]}
        result = simplify_schema(schema)
        assert "allOf" not in result
        assert "a" in result["properties"]
        assert "b" in result["properties"]

    def test_passthrough_simple_schema(self):
        schema = {"type": "string", "title": "Name"}
        result = simplify_schema(schema)
        assert result == schema


class TestSchemaCompatibleMCP:
    def test_tool_schemas_simplified(self):
        mcp = SchemaCompatibleMCP("test")

        def sample_tool(name: str, value: str | None = None) -> str:
            """A sample tool."""
            return name

        mcp.add_tool(sample_tool)

        tools = asyncio.run(mcp.list_tools())
        assert len(tools) == 1

        schema_str = json.dumps(tools[0].inputSchema)
        assert "anyOf" not in schema_str
        assert "$ref" not in schema_str
        assert "$defs" not in schema_str

    def test_all_registered_tools_have_simplified_schemas(self):
        mcp = SchemaCompatibleMCP("test")

        from fabric_rti_mcp.services.activator import activator_tools
        from fabric_rti_mcp.services.eventstream import eventstream_tools
        from fabric_rti_mcp.services.kusto import kusto_tools
        from fabric_rti_mcp.services.map import map_tools

        kusto_tools.register_tools(mcp)
        eventstream_tools.register_tools(mcp)
        activator_tools.register_tools(mcp)
        map_tools.register_tools(mcp)

        tools = asyncio.run(mcp.list_tools())
        assert len(tools) > 0

        for tool in tools:
            schema_str = json.dumps(tool.inputSchema)
            assert "anyOf" not in schema_str, f"Tool '{tool.name}' schema contains anyOf: {schema_str}"
            assert "$ref" not in schema_str, f"Tool '{tool.name}' schema contains $ref: {schema_str}"
            assert "$defs" not in schema_str, f"Tool '{tool.name}' schema contains $defs: {schema_str}"
