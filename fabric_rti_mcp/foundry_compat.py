"""AI Foundry compatibility layer - removes anyOf/allOf from schemas."""

from typing import Any

from mcp.server.fastmcp import FastMCP


def simplify_schema_for_foundry(schema: Any, root_schema: Any | None = None) -> Any:
    """ Fix the schema for AI Foundry compatibility fixing below issues:
     - Remove anyOf/allOf constructs
     - fixes empty type strings
     - resolves $ref references by inlining definitions
    """
    if not isinstance(schema, dict):
        return schema
    
    # Keep reference to root schema for $ref resolution
    if root_schema is None:
        root_schema = schema # type: ignore[assignment]
    
    schema = schema.copy() # type: ignore[assignment]
    
    # Handle $ref by inlining the referenced definition
    if "$ref" in schema:
        ref_path = schema["$ref"]
        if ref_path.startswith("#/$defs/"):
            def_name = ref_path.split("/")[-1]
            if "$defs" in root_schema and def_name in root_schema["$defs"]:
                # Inline the definition
                referenced_schema = root_schema["$defs"][def_name].copy()
                # Remove $ref and merge with referenced schema
                schema = {**referenced_schema, **{k: v for k, v in schema.items() if k != "$ref"}}
    
    # Fix empty type string (can happen with Pydantic models)
    if schema.get("type") == "":
        schema["type"] = "object"

    if non_null_options := [
        entry for entry in schema.get("anyOf", [])
        if entry.get("type") != "null"
    ]:
        first_valid = non_null_options[0]

        # Merge keys from valid option without overwriting existing keys
        schema.update({
            key: value
            for key, value in first_valid.items()
            if key not in schema
        })

        schema.pop("anyOf", None)
    
    # Merge allOf schemas
    for sub in schema.pop("allOf", []):
        for k, v in sub.items():
            if k == "properties" and k in schema:
                schema[k].update(v)
            else:
                schema.setdefault(k, v)
    
    # Recurse into nested structures
    for key in ("properties", "$defs", "items", "additionalProperties"):
        if key in schema and isinstance(schema[key], dict):
            if key in ("properties", "$defs"):
                schema[key] = {k: simplify_schema_for_foundry(v, root_schema) for k, v in schema[key].items()}
            else:
                schema[key] = simplify_schema_for_foundry(schema[key], root_schema)
    
    # Remove $defs from final output as all refs should be inlined
    schema.pop("$defs", None)
    
    return schema


class FoundryCompatibleMCP(FastMCP):
    """FastMCP wrapper that simplifies schemas for AI Foundry compatibility."""
    
    def add_tool(self, *args: Any, **kwargs: Any) -> None:
        super().add_tool(*args, **kwargs)
        if hasattr(self, "_tools") and self._tools:  # type: ignore
            tool = self._tools[-1]  # type: ignore
            if hasattr(tool, "inputSchema") and tool.inputSchema: # type: ignore[assignment]
                tool.inputSchema = simplify_schema_for_foundry(tool.inputSchema)  # type: ignore[assignment]
    
    async def list_tools(self) -> list[Any]:
        """Override list_tools to simplify schemas on-the-fly."""
        tools = await super().list_tools()
        for tool in tools:
            if hasattr(tool, "inputSchema") and tool.inputSchema:
                tool.inputSchema = simplify_schema_for_foundry(tool.inputSchema)
        return tools
