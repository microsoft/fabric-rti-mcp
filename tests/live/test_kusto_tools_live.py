"""
Live testing for Kusto tools using MCP client.
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Any

from fabric_rti_mcp.kusto.kusto_formatter import KustoFormatter

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from mcp.types import TextContent
except ImportError:
    print("MCP client dependencies not available. Install with: pip install mcp")
    sys.exit(1)


class McpClient:
    """MCP client bound to a single MCP server."""

    def __init__(self, server_name: str, command: list[str], env: dict[str, str] | None = None):
        self.server_name = server_name
        self.command = command
        self.env = env or {}
        self.session: ClientSession | None = None
        self.stdio_context: Any | None = None
        self.session_context: Any | None = None
        self._connected = False

    async def connect(self) -> ClientSession:
        """Connect to the configured MCP server."""
        if self._connected and self.session is not None:
            return self.session

        server_params = StdioServerParameters(
            command=self.command[0], args=self.command[1:] if len(self.command) > 1 else [], env=self.env
        )

        self.stdio_context = stdio_client(server_params)
        read, write = await self.stdio_context.__aenter__()

        self.session_context = ClientSession(read, write)
        self.session = await self.session_context.__aenter__()

        # Initialize the session
        if self.session is not None:
            await self.session.initialize()
        self._connected = True

        if self.session is None:
            raise RuntimeError("Failed to create session")

        return self.session

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        if not self._connected:
            return

        if self.session_context:
            await self.session_context.__aexit__(None, None, None)
            self.session_context = None

        if self.stdio_context:
            await self.stdio_context.__aexit__(None, None, None)
            self.stdio_context = None

        self.session = None
        self._connected = False

    @property
    def name(self) -> str:
        """Get the server name this client is bound to."""
        return self.server_name

    async def list_tools(self) -> list[str]:
        """List available tools from the server."""
        if not self._connected or not self.session:
            return []

        tools_result = await self.session.list_tools()
        return [tool.name for tool in tools_result.tools]

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call a tool on the server."""
        if not self._connected or not self.session:
            raise RuntimeError(f"No active MCP session for server: {self.server_name}")

        result = await self.session.call_tool(tool_name, arguments=arguments)

        # First, check if there's structured content (preferred)
        if hasattr(result, "structuredContent") and result.structuredContent:
            return {"result": result.structuredContent.get("result", result.structuredContent), "success": True}

        # Fall back to parsing text content
        if result.content and len(result.content) > 0:
            # If there are multiple content items, try to parse each as JSON and combine
            if len(result.content) > 1:
                parsed_items = []
                for content_item in result.content:
                    if isinstance(content_item, TextContent):
                        try:
                            parsed_item = json.loads(content_item.text)
                            parsed_items.append(parsed_item)
                        except json.JSONDecodeError:
                            # If parsing fails, treat as text
                            parsed_items.append(content_item.text)

                # Return the array of parsed items
                return {"result": parsed_items, "success": True}

            # Single content item - parse as before
            content_item = result.content[0]
            if isinstance(content_item, TextContent):
                try:
                    # Try to parse as JSON first
                    parsed_result = json.loads(content_item.text)

                    # If the result is a list, wrap it in a dictionary for consistent handling
                    if isinstance(parsed_result, list):
                        return {"result": parsed_result, "success": True}

                    # If it's already a dict, ensure it has success flag
                    if isinstance(parsed_result, dict):
                        if "success" not in parsed_result:
                            parsed_result["success"] = True
                        return parsed_result

                    # For other types, wrap in a dictionary
                    return {"result": parsed_result, "success": True}

                except json.JSONDecodeError:
                    # If not JSON, return as plain text result
                    return {"content": content_item.text, "success": True}

        return {"success": False, "error": "No response from server"}

    async def is_connected(self) -> bool:
        """Check if the MCP server is connected."""
        return self._connected


class KustoToolsLiveTester:
    """Live tester for Kusto tools via MCP client."""

    def __init__(self) -> None:
        self.client: McpClient | None = None
        self.test_cluster_uri = "https://help.kusto.windows.net"
        self.test_database = "Samples"

    async def setup(self) -> None:
        """Set up the MCP client connection."""
        # Get the path to the server script
        server_script = os.path.join(os.path.dirname(__file__), "..", "..", "fabric_rti_mcp", "server.py")
        server_script = os.path.abspath(server_script)

        if not os.path.exists(server_script):
            raise FileNotFoundError(f"Server script not found at {server_script}")

        # Create MCP client with Python command to run the server
        command = [sys.executable, server_script]
        env = dict(os.environ)  # Copy current environment

        # Configure the test environment with known services for live testing
        test_services = [
            {
                "service_uri": self.test_cluster_uri,
                "default_database": self.test_database,
                "description": "Test cluster for live testing",
            }
        ]
        env["KUSTO_KNOWN_SERVICES"] = json.dumps(test_services)
        env["KUSTO_ALLOW_UNKNOWN_SERVICES"] = "true"

        self.client = McpClient("fabric-rti-mcp-server", command, env)
        await self.client.connect()
        print(f"✅ Connected to MCP server: {self.client.name}")

    async def teardown(self) -> None:
        """Clean up the MCP client connection."""
        if self.client:
            await self.client.disconnect()
            print("✅ Disconnected from MCP server")

    async def test_list_tools(self) -> None:
        """Test listing available tools."""
        print("\n🔧 Testing tool listing...")
        if not self.client:
            raise RuntimeError("Client not initialized")

        tools = await self.client.list_tools()
        print(f"Available tools: {tools}")

        kusto_tools = [tool for tool in tools if tool.startswith("kusto_")]
        print(f"Kusto tools found: {kusto_tools}")

        expected_kusto_tools = [
            "kusto_known_services",
            "kusto_query",
            "kusto_command",
            "kusto_list_entities",
            "kusto_describe_database",
            "kusto_describe_database_entity",
            "kusto_graph_query",
            "kusto_sample_entity",
            "kusto_ingest_inline_into_table",
            "kusto_get_shots",
        ]

        missing_tools = set(expected_kusto_tools) - set(kusto_tools)
        if missing_tools:
            print(f"⚠️  Missing expected tools: {missing_tools}")
        else:
            print("✅ All expected Kusto tools found")

    async def test_known_services(self) -> None:
        """Test kusto_known_services tool."""
        print("\n🔧 Testing kusto_known_services...")
        if not self.client:
            raise RuntimeError("Client not initialized")

        try:
            result = await self.client.call_tool("kusto_known_services", {})
            print(f"Known services result: {json.dumps(result, indent=2)}")

            if result.get("success"):
                services = result.get("result", [])
                if not isinstance(services, list):
                    services = [services] if services else []
                print(f"✅ Found {len(services)} known services")
                for service in services:
                    print(f"  - {service.get('service_uri', 'N/A')}: {service.get('description', 'N/A')}")
            else:
                print(f"❌ Failed to get known services: {result}")

        except Exception as e:
            print(f"❌ Error testing known services: {e}")

    async def test_list_entities(self) -> None:
        """Test kusto_list_entities tool for all entity types."""
        print("\n🗄️  Testing kusto_list_entities...")
        if not self.client:
            raise RuntimeError("Client not initialized")

        if not self.test_cluster_uri:
            print("⚠️  No KUSTO_CLUSTER_URI configured, skipping entities listing test")
            return

        # Test data: [entity_type, [cluster_uri, database], min_expected_count, expected_first_value]
        test_data = [
            ["databases", [self.test_cluster_uri, None], 8, None],
            ["tables", [self.test_cluster_uri, self.test_database], 50, None],
            ["materialized-views", [self.test_cluster_uri, self.test_database], 0, None],
            ["functions", [self.test_cluster_uri, self.test_database], 0, None],
            ["graphs", [self.test_cluster_uri, self.test_database], 0, None],
        ]

        for entity_type, args, min_expected_count, expected_first_value in test_data:
            try:
                print(f"  Testing {entity_type}...")
                cluster_uri, database = args

                call_args = {"cluster_uri": cluster_uri, "entity_type": entity_type, "database": database}

                result = await self.client.call_tool("kusto_list_entities", call_args)

                if result.get("success"):
                    # Use the new parser to convert to canonical format
                    query_result = result.get("result", {})
                    parsed_data = KustoFormatter.parse(query_result) or []

                    # Assert minimum count
                    assert (
                        len(parsed_data) >= min_expected_count
                    ), f"Expected at least {min_expected_count} {entity_type}, "
                    "got {len(parsed_data)}. Args: {json.dumps(call_args)}"
                    print(f"    ✅ Found {len(parsed_data)} {entity_type}")

                    # Check expected first value if specified
                    if expected_first_value and len(parsed_data) > 0:
                        first_row = parsed_data[0]
                        # For databases, check DatabaseName; for others, check appropriate name field
                        name_field = "DatabaseName" if entity_type == "databases" else "Name"
                        if entity_type == "tables":
                            name_field = "TableName"
                        elif entity_type == "functions":
                            name_field = "Name"

                        actual_first = first_row.get(name_field, "")
                        if expected_first_value in actual_first or actual_first == expected_first_value:
                            print(f"    ✅ Expected first value found: {actual_first}")
                else:
                    print(f"    ❌ Failed to list {entity_type}: {result}")
                    print(f"    Raw failure result: {json.dumps(result, indent=4)}")
                    if min_expected_count > 0:  # Only raise for entity types we expect to exist
                        raise AssertionError(f"{entity_type} listing failed: {result}")

            except Exception as e:
                print(f"    ❌ Error testing {entity_type}: {e}")
                if min_expected_count > 0:  # Only raise for entity types we expect to exist
                    raise

    async def test_simple_query(self) -> None:
        """Test kusto_query tool with a simple query."""
        print("\n🔍 Testing kusto_query...")
        if not self.client:
            raise RuntimeError("Client not initialized")

        if not self.test_cluster_uri:
            print("⚠️  No KUSTO_CLUSTER_URI configured, skipping query test")
            return

        try:
            # Simple query to get current time
            result = await self.client.call_tool(
                "kusto_query",
                {"query": "print now()", "cluster_uri": self.test_cluster_uri, "database": self.test_database},
            )

            if result.get("success"):
                # Use the new parser to convert to canonical format
                query_results = result.get("result", {})
                print(f"Query result: {json.dumps(query_results, indent=2)}")
                parsed_data = KustoFormatter.parse(query_results)

                if parsed_data and len(parsed_data) > 0:
                    # Get the timestamp value from the first row
                    scalar_value = parsed_data[0].get("print_0", "")
                    print(f"✅ Query succeeded, current time from Kusto: {scalar_value}")
                    if scalar_value:
                        parsed_date = datetime.fromisoformat(scalar_value.replace("Z", "+00:00"))
                        assert datetime.now(tz=timezone.utc) - parsed_date < timedelta(
                            minutes=1
                        ), "Query result is stale"
                else:
                    print("❌ No data returned from query")
            else:
                print(f"❌ Query failed: {result}")

        except Exception as e:
            print(f"❌ Error testing query: {e}")

    async def test_sql_query_with_crp(self) -> None:
        """Test kusto_query tool with SQL query using client request properties."""
        print("\n🔍 Testing kusto_query with SQL syntax...")
        if not self.client:
            raise RuntimeError("Client not initialized")

        if not self.test_cluster_uri:
            print("⚠️  No KUSTO_CLUSTER_URI configured, skipping SQL query test")
            return

        try:
            # SQL query to count StormEvents records
            result = await self.client.call_tool(
                "kusto_query",
                {
                    "query": "SELECT COUNT(*) AS cnt FROM StormEvents",
                    "cluster_uri": self.test_cluster_uri,
                    "database": self.test_database,
                    "client_request_properties": {"query_language": "sql"},
                },
            )

            if result.get("success"):
                # Use the new parser to convert to canonical format
                query_results = result.get("result", {})
                print(f"SQL Query result: {json.dumps(query_results, indent=2)}")
                parsed_data = KustoFormatter.parse(query_results)

                if parsed_data and len(parsed_data) > 0:
                    # Get the count value from the first row
                    count_value = parsed_data[0].get("cnt", 0)
                    print(f"✅ SQL Query succeeded, StormEvents count: {count_value}")
                    assert count_value > 0, f"Expected count > 0, got {count_value}"
                else:
                    print("❌ No data returned from SQL query")
            else:
                print(f"❌ SQL Query failed: {result}")

        except Exception as e:
            print(f"❌ Error testing SQL query: {e}")

    async def test_describe_database(self) -> None:
        """Test kusto_describe_database tool."""
        print("\n📋 Testing kusto_describe_database...")
        if not self.client:
            raise RuntimeError("Client not initialized")

        if not self.test_cluster_uri:
            print("⚠️  No KUSTO_CLUSTER_URI configured, skipping describe database test")
            return

        try:
            result = await self.client.call_tool(
                "kusto_describe_database", {"cluster_uri": self.test_cluster_uri, "database": self.test_database}
            )

            if result.get("success"):
                # Use the new parser to convert to canonical format
                query_result = result.get("result", {})
                parsed_data = KustoFormatter.parse(query_result) or []

                print(f"✅ Found {len(parsed_data)} entities in database schema")

                # Group by entity type to show summary
                entity_types = {}
                for row in parsed_data:
                    entity_type = row.get("EntityType", "unknown")
                    entity_types[entity_type] = entity_types.get(entity_type, 0) + 1

                for entity_type, count in entity_types.items():
                    print(f"  - {entity_type}: {count}")

            else:
                print(f"❌ Failed to describe database: {result}")

        except Exception as e:
            print(f"❌ Error testing describe database: {e}")

    async def test_describe_database_entity(self) -> None:
        """Test kusto_describe_database_entity tool for different entity types."""
        print("\n🔍 Testing kusto_describe_database_entity...")
        if not self.client:
            raise RuntimeError("Client not initialized")

        if not self.test_cluster_uri:
            print("⚠️  No KUSTO_CLUSTER_URI configured, skipping describe entity test")
            return

        # Test data: [entity_name, entity_type, expected_schema_fields]
        test_data = [
            ["StormEvents", "table", ["ColumnName", "ColumnType"]],
            # Add more entities as they are discovered
        ]

        for entity_name, entity_type, expected_fields in test_data:
            try:
                print(f"  Testing {entity_type} '{entity_name}'...")
                result = await self.client.call_tool(
                    "kusto_describe_database_entity",
                    {
                        "entity_name": entity_name,
                        "entity_type": entity_type,
                        "cluster_uri": self.test_cluster_uri,
                        "database": self.test_database,
                    },
                )

                if result.get("success"):
                    # Use the new parser to convert to canonical format
                    query_result = result.get("result", {})
                    parsed_data = KustoFormatter.parse(query_result) or []

                    print(f"    ✅ Retrieved schema for {entity_type} '{entity_name}' ({len(parsed_data)} rows)")

                    # Check if expected schema fields are present
                    if parsed_data and expected_fields:
                        first_row = parsed_data[0]
                        for field in expected_fields:
                            if field in first_row:
                                print(f"      ✅ Found expected field: {field}")
                            else:
                                print(f"      ⚠️  Missing expected field: {field}")
                else:
                    print(f"    ❌ Failed to describe {entity_type} '{entity_name}': {result}")

            except Exception as e:
                print(f"    ❌ Error testing {entity_type} '{entity_name}': {e}")

    async def test_sample_entity(self) -> None:
        """Test kusto_sample_entity tool for different entity types."""
        print("\n📝 Testing kusto_sample_entity...")
        if not self.client:
            raise RuntimeError("Client not initialized")

        if not self.test_cluster_uri:
            print("⚠️  No KUSTO_CLUSTER_URI configured, skipping entity sample test")
            return

        # Test data: [entity_name, entity_type, sample_size, min_expected_count]
        test_data = [
            ["StormEvents", "table", 3, 3],
            ["LDBC_SNB_Interactive", "graph", 3, 3],
            # Add more entities as they are discovered
        ]

        for entity_name, entity_type, sample_size, min_expected_count in test_data:
            try:
                print(f"  Testing {entity_type} '{entity_name}' (sample size: {sample_size})...")
                result = await self.client.call_tool(
                    "kusto_sample_entity",
                    {
                        "entity_name": entity_name,
                        "entity_type": entity_type,
                        "cluster_uri": self.test_cluster_uri,
                        "sample_size": sample_size,
                        "database": self.test_database,
                    },
                )

                if result.get("success"):
                    # Use the new parser to convert to canonical format
                    query_result = result.get("result", {})
                    parsed_data = KustoFormatter.parse(query_result) or []

                    # Assert minimum count
                    assert (
                        len(parsed_data) >= min_expected_count
                    ), f"Expected at least {min_expected_count} sample records, got {len(parsed_data)}."
                    print(f"    ✅ Retrieved {len(parsed_data)} sample records")
                else:
                    print(f"    ❌ Failed to sample {entity_type} '{entity_name}': {result}")

            except Exception as e:
                print(f"    ❌ Error testing {entity_type} '{entity_name}': {e}")

    async def test_graph_query(self) -> None:
        """Test kusto_graph_query tool if graphs are available."""
        print("\n🕸️  Testing kusto_graph_query...")
        if not self.client:
            raise RuntimeError("Client not initialized")

        if not self.test_cluster_uri:
            print("⚠️  No KUSTO_CLUSTER_URI configured, skipping graph query test")
            return

        try:
            # First check if there are any graphs available
            list_result = await self.client.call_tool(
                "kusto_list_entities",
                {"cluster_uri": self.test_cluster_uri, "entity_type": "graphs", "database": self.test_database},
            )

            if not list_result.get("success"):
                print("  ⚠️  Could not list graphs, skipping graph query test")
                return

            query_result = list_result.get("result", {})
            parsed_data = KustoFormatter.parse(query_result) or []

            if len(parsed_data) == 0:
                print("  ⚠️  No graphs found in database, skipping graph query test")
                return

            # Use the first graph found
            graph_name = parsed_data[0].get("Name", "")
            if not graph_name:
                print("  ⚠️  No valid graph name found, skipping graph query test")
                return

            print(f"  Testing graph query on '{graph_name}'...")

            # Simple graph query to count nodes
            result = await self.client.call_tool(
                "kusto_graph_query",
                {
                    "graph_name": graph_name,
                    "query": "| graph-match (node) project labels=labels(node) | take 5",
                    "cluster_uri": self.test_cluster_uri,
                    "database": self.test_database,
                },
            )

            if result.get("success"):
                query_result = result.get("result", {})
                parsed_data = KustoFormatter.parse(query_result) or []
                print(f"    ✅ Graph query succeeded, returned {len(parsed_data)} rows")
            else:
                print(f"    ❌ Graph query failed: {result}")

        except Exception as e:
            print(f"❌ Error testing graph query: {e}")

    async def run_all_tests(self) -> None:
        """Run all available tests."""
        print("🚀 Starting Kusto tools live testing...")

        try:
            await self.setup()

            # Run tests for generic tools with all entity types
            await self.test_list_tools()
            await self.test_known_services()
            await self.test_list_entities()
            await self.test_simple_query()
            await self.test_sql_query_with_crp()
            await self.test_describe_database()
            await self.test_describe_database_entity()
            await self.test_sample_entity()
            await self.test_graph_query()

            print("\n✅ All tests completed!")

        except Exception as e:
            print(f"\n❌ Test suite failed: {e}")
            raise
        finally:
            await self.teardown()


async def main() -> None:
    """Main entry point for live testing."""
    print("=" * 60)
    print("Fabric RTI MCP - Kusto Tools Live Testing")
    print("=" * 60)

    tester = KustoToolsLiveTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
