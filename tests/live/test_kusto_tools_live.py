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
            "kusto_list_databases",
            "kusto_list_tables",
            "kusto_get_entities_schema",
            "kusto_get_table_schema",
            "kusto_get_function_schema",
            "kusto_sample_table_data",
            "kusto_sample_function_data",
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

    async def test_list_databases(self) -> None:
        """Test kusto_list_databases tool if cluster URI is configured."""
        print("\n🗄️  Testing kusto_list_databases...")
        if not self.client:
            raise RuntimeError("Client not initialized")

        if not self.test_cluster_uri:
            print("⚠️  No KUSTO_CLUSTER_URI configured, skipping database listing test")
            return

        try:
            result = await self.client.call_tool("kusto_list_databases", {"cluster_uri": self.test_cluster_uri})
            print(f"List databases result: {json.dumps(result, indent=2)}")

            if result.get("success"):
                # Use the new parser to convert to canonical format
                query_result = result.get("result", {})
                parsed_data = KustoFormatter.parse(query_result)

                # Extract database names from parsed rows
                databases = [row.get("DatabaseName", "") for row in parsed_data]
                databases = [db for db in databases if db]  # Filter out empty strings

                # Assert minimum count to verify array fix is working
                min_expected_dbs = 8
                assert (
                    len(databases) >= min_expected_dbs
                ), f"Expected at least {min_expected_dbs} databases, got {len(databases)}."
                print(f"✅ Found {len(databases)} databases")
            else:
                print(f"❌ Failed to list databases: {result}")
                raise AssertionError(f"Database listing failed: {result}")

        except Exception as e:
            print(f"❌ Error testing list databases: {e}")
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

    async def test_list_tables(self) -> None:
        """Test kusto_list_tables tool."""
        print("\n📊 Testing kusto_list_tables...")
        if not self.client:
            raise RuntimeError("Client not initialized")

        if not self.test_cluster_uri:
            print("⚠️  No KUSTO_CLUSTER_URI configured, skipping tables listing test")
            return

        try:
            result = await self.client.call_tool(
                "kusto_list_tables", {"cluster_uri": self.test_cluster_uri, "database": self.test_database}
            )

            if result.get("success"):
                # Use the new parser to convert to canonical format
                query_result = result.get("result", {})
                parsed_data = KustoFormatter.parse(query_result)

                # Extract table names from parsed rows
                tables = [row.get("TableName", "") for row in parsed_data]
                tables = [table for table in tables if table]  # Filter out empty strings

                # Assert minimum count to verify array fix is working
                min_expected_tables = 50  # Samples database has many tables
                assert (
                    len(tables) > min_expected_tables
                ), f"Expected at least {min_expected_tables} tables, got {len(tables)}. "
                print(f"✅ Found {len(tables)} tables (>= {min_expected_tables} as expected)")
            else:
                print(f"❌ Failed to list tables: {result}")
                raise AssertionError(f"Table listing failed: {result}")

        except Exception as e:
            print(f"❌ Error testing list tables: {e}")
            raise

    async def test_table_sample(self) -> None:
        """Test kusto_sample_table_data tool."""
        print("\n📝 Testing kusto_sample_table_data...")
        if not self.client:
            raise RuntimeError("Client not initialized")

        if not self.test_cluster_uri:
            print("⚠️  No KUSTO_CLUSTER_URI configured, skipping table sample test")
            return

        try:
            result = await self.client.call_tool(
                "kusto_sample_table_data",
                {
                    "table_name": "StormEvents",
                    "cluster_uri": self.test_cluster_uri,
                    "sample_size": 3,
                    "database": self.test_database,
                },
            )

            if result.get("success"):
                # Handle both list and single object responses
                sample_data = result.get("result", [])
                if not isinstance(sample_data, list):
                    sample_data = [sample_data] if sample_data else []
                print(f"✅ Retrieved {len(sample_data)} sample records")
            else:
                print(f"❌ Failed to sample table data: {result}")

        except Exception as e:
            print(f"❌ Error testing table sample: {e}")

    async def run_all_tests(self) -> None:
        """Run all available tests."""
        print("🚀 Starting Kusto tools live testing...")

        try:
            await self.setup()

            # Run tests
            await self.test_list_tools()
            await self.test_known_services()
            await self.test_list_databases()
            await self.test_simple_query()
            await self.test_list_tables()
            await self.test_table_sample()

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
