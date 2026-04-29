"""
Live testing for Kusto tools using MCP client.
"""

import asyncio
import json
import os
import sys
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlparse

from fabric_rti_mcp.services.kusto.kusto_formatter import KustoFormatter

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from mcp.types import TextContent
except ImportError:
    print("MCP client dependencies not available. Install with: pip install mcp")
    sys.exit(1)


EXPECTED_KUSTO_TOOLS = [
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
    "kusto_deeplink_from_query",
    "kusto_show_queryplan",
    "kusto_diagnostics",
]


@dataclass
class LiveTestResult:
    name: str
    scope: str
    required: bool
    success: bool
    details: str = ""


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

        if getattr(result, "isError", False) or getattr(result, "is_error", False):
            error_parts = []
            for content_item in result.content or []:
                if isinstance(content_item, TextContent):
                    error_parts.append(content_item.text)
            return {"success": False, "error": "\n".join(error_parts) or "Tool returned an error"}

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
        self.test_cluster_uri = os.getenv("KUSTO_LIVE_CLUSTER_URI", "https://help.kusto.windows.net")
        self.test_database = os.getenv("KUSTO_LIVE_DATABASE", "Samples")
        self.min_expected_databases = int(os.getenv("KUSTO_LIVE_MIN_DATABASES", "0"))
        self.results: list[LiveTestResult] = []

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
        env["KUSTO_SERVICE_URI"] = self.test_cluster_uri
        env["KUSTO_SERVICE_DEFAULT_DB"] = self.test_database
        env["KUSTO_ALLOW_UNKNOWN_SERVICES"] = "false"
        env["KUSTO_EAGER_CONNECT"] = "false"
        env["FABRIC_RTI_TRANSPORT"] = "stdio"
        env["FABRIC_RTI_AI_FOUNDRY_COMPATIBILITY_SCHEMA"] = "false"
        env["FABRIC_RTI_KUSTO_DEEPLINK_STYLE"] = "adx"
        env["FABRIC_RTI_KUSTO_RESPONSE_FORMAT"] = "kusto_response"
        env["USE_OBO_FLOW"] = "false"
        env.pop("PORT", None)

        self.client = McpClient("fabric-rti-mcp-server", command, env)
        await self.client.connect()
        print(f"✅ Connected to MCP server: {self.client.name}")

    async def teardown(self) -> None:
        """Clean up the MCP client connection."""
        if self.client:
            await self.client.disconnect()
            print("✅ Disconnected from MCP server")

    @staticmethod
    def _payload(result: dict[str, Any]) -> Any:
        if "result" in result:
            return result["result"]
        return {key: value for key, value in result.items() if key != "success"}

    @staticmethod
    def _parse_kusto_datetime(value: str) -> datetime:
        normalized = value.replace("Z", "+00:00")
        if "." not in normalized:
            return datetime.fromisoformat(normalized)

        timestamp_part, fractional_part = normalized.split(".", 1)
        timezone_start = len(fractional_part)
        for marker in ("+", "-"):
            marker_index = fractional_part.find(marker)
            if marker_index != -1:
                timezone_start = min(timezone_start, marker_index)

        fraction = fractional_part[:timezone_start][:6].ljust(6, "0")
        timezone_part = fractional_part[timezone_start:]
        return datetime.fromisoformat(f"{timestamp_part}.{fraction}{timezone_part}")

    @staticmethod
    def _summarize_error(error: Exception) -> str:
        return str(error).replace("\n", " ")[:180]

    @staticmethod
    def _assert_positive_count(rows: list[dict[str, Any]] | None, column_name: str, label: str) -> int:
        if not rows:
            raise AssertionError(f"No data returned from {label}")

        raw_count = rows[0].get(column_name, 0)
        try:
            count_value = int(raw_count)
        except (TypeError, ValueError) as e:
            raise AssertionError(f"Expected numeric count for {label}, got {raw_count!r}") from e

        assert count_value > 0, f"Expected {label} count > 0, got {count_value}"
        return count_value

    async def _run_test(
        self,
        name: str,
        scope: str,
        required: bool,
        test_func: Callable[[], Awaitable[None]],
    ) -> None:
        try:
            await test_func()
            self.results.append(LiveTestResult(name=name, scope=scope, required=required, success=True))
        except Exception as e:
            details = self._summarize_error(e)
            print(f"❌ {name} failed: {details}")
            self.results.append(
                LiveTestResult(name=name, scope=scope, required=required, success=False, details=details)
            )

    def _print_summary(self) -> None:
        if not self.results:
            return

        print("\nLive test summary:")
        print("| Scope | Required | Test | Status | Details |")
        print("| --- | --- | --- | --- | --- |")
        for result in self.results:
            required = "yes" if result.required else "no"
            status = "PASS" if result.success else "FAIL"
            details = result.details.replace("|", "\\|")
            print(f"| {result.scope} | {required} | {result.name} | {status} | {details} |")

    async def test_list_tools(self) -> None:
        """Test listing available tools."""
        print("\n🔧 Testing tool listing...")
        if not self.client:
            raise RuntimeError("Client not initialized")

        tools = await self.client.list_tools()
        print(f"Available tools: {tools}")

        kusto_tools = [tool for tool in tools if tool.startswith("kusto_")]
        print(f"Kusto tools found: {kusto_tools}")

        missing_tools = set(EXPECTED_KUSTO_TOOLS) - set(kusto_tools)
        if missing_tools:
            raise AssertionError(f"Missing expected Kusto tools: {sorted(missing_tools)}")
        else:
            print("✅ All expected Kusto tools found")

    async def test_known_services(self) -> None:
        """Test kusto_known_services tool."""
        print("\n🔧 Testing kusto_known_services...")
        if not self.client:
            raise RuntimeError("Client not initialized")

        result = await self.client.call_tool("kusto_known_services", {})
        print(f"Known services result: {json.dumps(result, indent=2)}")

        if not result.get("success"):
            raise AssertionError(f"Failed to get known services: {result}")

        services = result.get("result", [])
        if not isinstance(services, list):
            services = [services] if services else []
        assert services, "Expected at least one known service"
        print(f"✅ Found {len(services)} known services")
        for service in services:
            print(f"  - {service.get('service_uri', 'N/A')}: {service.get('description', 'N/A')}")

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
            ["databases", [self.test_cluster_uri, None], self.min_expected_databases, None],
            ["tables", [self.test_cluster_uri, self.test_database], 50, None],
            ["external-table", [self.test_cluster_uri, self.test_database], 0, None],
            ["materialized-view", [self.test_cluster_uri, self.test_database], 0, None],
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
                    assert len(parsed_data) >= min_expected_count, (
                        f"Expected at least {min_expected_count} {entity_type}, got {len(parsed_data)}. "
                        f"Args: {json.dumps(call_args)}"
                    )
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

        result = await self.client.call_tool(
            "kusto_query",
            {"query": "print now()", "cluster_uri": self.test_cluster_uri, "database": self.test_database},
        )

        if not result.get("success"):
            raise AssertionError(f"Query failed: {result}")

        query_results = result.get("result", {})
        print(f"Query result: {json.dumps(query_results, indent=2)}")
        parsed_data = KustoFormatter.parse(query_results)

        if not parsed_data:
            raise AssertionError("No data returned from query")

        scalar_value = parsed_data[0].get("print_0", "")
        print(f"✅ Query succeeded, current time from Kusto: {scalar_value}")
        if scalar_value:
            parsed_date = self._parse_kusto_datetime(scalar_value)
            assert datetime.now(tz=timezone.utc) - parsed_date < timedelta(minutes=1), "Query result is stale"

    async def test_kql_readonly_query(self) -> None:
        """Test kusto_query with a read-only table query."""
        print("\n🔍 Testing kusto_query with a read-only table query...")
        if not self.client:
            raise RuntimeError("Client not initialized")

        if not self.test_cluster_uri:
            print("⚠️  No KUSTO_CLUSTER_URI configured, skipping read-only table query test")
            return

        result = await self.client.call_tool(
            "kusto_query",
            {
                "query": "StormEvents | summarize cnt=count()",
                "cluster_uri": self.test_cluster_uri,
                "database": self.test_database,
            },
        )

        if not result.get("success"):
            raise AssertionError(f"KQL read-only query failed: {result}")

        query_results = result.get("result", {})
        print(f"KQL read-only query result: {json.dumps(query_results, indent=2)}")
        parsed_data = KustoFormatter.parse(query_results)
        count_value = self._assert_positive_count(parsed_data, "cnt", "KQL StormEvents")
        print(f"✅ KQL read-only query succeeded, StormEvents count: {count_value}")

    async def test_sql_query_with_crp(self) -> None:
        """Test kusto_query tool with SQL query using client request properties."""
        print("\n🔍 Testing kusto_query with SQL syntax...")
        if not self.client:
            raise RuntimeError("Client not initialized")

        if not self.test_cluster_uri:
            print("⚠️  No KUSTO_CLUSTER_URI configured, skipping SQL query test")
            return

        result = await self.client.call_tool(
            "kusto_query",
            {
                "query": "SELECT COUNT(*) AS cnt FROM StormEvents",
                "cluster_uri": self.test_cluster_uri,
                "database": self.test_database,
                "client_request_properties": {"query_language": "sql"},
            },
        )

        if not result.get("success"):
            raise AssertionError(f"SQL Query failed: {result}")

        query_results = result.get("result", {})
        print(f"SQL Query result: {json.dumps(query_results, indent=2)}")
        parsed_data = KustoFormatter.parse(query_results)

        count_value = self._assert_positive_count(parsed_data, "cnt", "SQL StormEvents")
        print(f"✅ SQL Query succeeded, StormEvents count: {count_value}")

    async def test_command(self) -> None:
        """Test kusto_command with a read-only management command."""
        print("\n🛠️  Testing kusto_command...")
        if not self.client:
            raise RuntimeError("Client not initialized")

        result = await self.client.call_tool(
            "kusto_command",
            {
                "command": ".show tables | project TableName | take 1",
                "cluster_uri": self.test_cluster_uri,
                "database": self.test_database,
            },
        )

        if not result.get("success"):
            raise AssertionError(f"kusto_command failed: {result}")

        command_result = self._payload(result)
        parsed_data = KustoFormatter.parse(command_result) or []
        assert parsed_data, "Expected .show tables to return at least one table"
        print(f"✅ kusto_command succeeded, first table: {parsed_data[0].get('TableName', parsed_data[0])}")

    async def test_deeplink_from_query(self) -> None:
        """Test kusto_deeplink_from_query for the public help cluster."""
        print("\n🔗 Testing kusto_deeplink_from_query...")
        if not self.client:
            raise RuntimeError("Client not initialized")

        query = "StormEvents | take 10"
        result = await self.client.call_tool(
            "kusto_deeplink_from_query",
            {"cluster_uri": self.test_cluster_uri, "database": self.test_database, "query": query},
        )

        if not result.get("success"):
            raise AssertionError(f"kusto_deeplink_from_query failed: {result}")

        deeplink = self._payload(result)
        if not isinstance(deeplink, str):
            deeplink = result.get("content")
        assert isinstance(deeplink, str), f"Expected deeplink string, got: {type(deeplink)}"

        parsed = urlparse(deeplink)
        assert parsed.scheme == "https", f"Expected HTTPS deeplink, got: {deeplink}"
        assert parsed.netloc == "dataexplorer.azure.com", f"Expected ADX web explorer deeplink, got: {deeplink}"
        assert "/clusters/help.kusto.windows.net/databases/Samples" in parsed.path, (
            f"Expected help cluster and Samples database in deeplink, got: {deeplink}"
        )
        assert "query=" in parsed.query, f"Expected encoded query parameter in deeplink, got: {deeplink}"
        print(f"✅ Deeplink generated: {deeplink[:120]}...")

    async def test_show_queryplan(self) -> None:
        """Test kusto_show_queryplan without executing the query."""
        print("\n📈 Testing kusto_show_queryplan...")
        if not self.client:
            raise RuntimeError("Client not initialized")

        query = (
            "StormEvents "
            "| where State == 'TEXAS' "
            "| summarize EventCount=count() by EventType "
            "| top 5 by EventCount desc"
        )
        result = await self.client.call_tool(
            "kusto_show_queryplan",
            {"query": query, "cluster_uri": self.test_cluster_uri, "database": self.test_database},
        )

        if not result.get("success"):
            raise AssertionError(f"kusto_show_queryplan failed: {result}")

        plan = self._payload(result)
        assert isinstance(plan, dict), f"Expected query plan dictionary, got: {type(plan)}"
        if plan.get("error"):
            raise AssertionError(f"Query plan returned an error: {plan['error']}")

        assert any(key in plan for key in ("stats", "relop_tree", "execution_hints")), (
            f"Expected query plan details, got: {json.dumps(plan, indent=2)}"
        )
        if "stats" in plan:
            print(f"✅ Query plan stats: {json.dumps(plan['stats'], indent=2)}")
        else:
            print("✅ Query plan returned successfully")

    async def test_diagnostics(self) -> None:
        """Test kusto_diagnostics against the help cluster."""
        print("\n🩺 Testing kusto_diagnostics...")
        if not self.client:
            raise RuntimeError("Client not initialized")

        result = await self.client.call_tool(
            "kusto_diagnostics", {"cluster_uri": self.test_cluster_uri, "database": self.test_database}
        )

        if not result.get("success"):
            raise AssertionError(f"kusto_diagnostics failed: {result}")

        diagnostics = self._payload(result)
        assert isinstance(diagnostics, dict), f"Expected diagnostics dictionary, got: {type(diagnostics)}"

        expected_sections = {
            "capacity",
            "cluster",
            "principal_roles",
            "diagnostics",
            "workload_groups",
            "rowstores",
            "ingestion_failures",
        }
        missing_sections = expected_sections - set(diagnostics)
        assert not missing_sections, f"Missing diagnostics sections: {sorted(missing_sections)}"

        successful_sections = [
            name for name, value in diagnostics.items() if not (isinstance(value, dict) and "error" in value)
        ]
        assert successful_sections, f"Expected at least one diagnostics section to succeed: {diagnostics}"
        print(f"✅ Diagnostics completed; successful sections: {successful_sections}")

    async def test_get_shots(self) -> None:
        """Test kusto_get_shots when configured, otherwise verify its validation path."""
        print("\n🎯 Testing kusto_get_shots...")
        if not self.client:
            raise RuntimeError("Client not initialized")

        shots_table = os.getenv("KUSTO_LIVE_SHOTS_TABLE") or os.getenv("KUSTO_SHOTS_TABLE")
        embedding_endpoint = os.getenv("AZ_OPENAI_EMBEDDING_ENDPOINT")

        if shots_table and embedding_endpoint:
            result = await self.client.call_tool(
                "kusto_get_shots",
                {
                    "prompt": "Find a few storm events in Texas",
                    "cluster_uri": self.test_cluster_uri,
                    "database": self.test_database,
                    "shots_table_name": shots_table,
                    "embedding_endpoint": embedding_endpoint,
                    "sample_size": 1,
                },
            )

            if not result.get("success"):
                raise AssertionError(f"kusto_get_shots failed: {result}")

            shots_result = self._payload(result)
            parsed_data = KustoFormatter.parse(shots_result) or []
            print(f"✅ kusto_get_shots returned {len(parsed_data)} shot(s)")
            return

        if shots_table and not embedding_endpoint:
            print("⚠️  Skipping full kusto_get_shots call: AZ_OPENAI_EMBEDDING_ENDPOINT is not configured")
            return

        result = await self.client.call_tool(
            "kusto_get_shots",
            {
                "prompt": "Find a few storm events in Texas",
                "cluster_uri": self.test_cluster_uri,
                "database": self.test_database,
            },
        )
        assert not result.get("success"), "Expected kusto_get_shots to require a shots table when not configured"
        assert "shots_table_name" in result.get("error", ""), f"Unexpected validation error: {result}"
        print("✅ kusto_get_shots validation path confirmed")

    async def test_describe_database(self) -> None:
        """Test kusto_describe_database tool."""
        print("\n📋 Testing kusto_describe_database...")
        if not self.client:
            raise RuntimeError("Client not initialized")

        if not self.test_cluster_uri:
            print("⚠️  No KUSTO_CLUSTER_URI configured, skipping describe database test")
            return

        result = await self.client.call_tool(
            "kusto_describe_database", {"cluster_uri": self.test_cluster_uri, "database": self.test_database}
        )

        if not result.get("success"):
            raise AssertionError(f"Failed to describe database: {result}")

        query_result = result.get("result", {})
        parsed_data = KustoFormatter.parse(query_result) or []

        print(f"✅ Found {len(parsed_data)} entities in database schema")

        entity_types = {}
        for row in parsed_data:
            entity_type = row.get("EntityType", "unknown")
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1

        for entity_type, count in entity_types.items():
            print(f"  - {entity_type}: {count}")

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
            ["StormEvents", "table", ["Schema"]],
            # Add more entities as they are discovered
        ]

        for entity_name, entity_type, expected_fields in test_data:
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

            if not result.get("success"):
                raise AssertionError(f"Failed to describe {entity_type} '{entity_name}': {result}")

            query_result = result.get("result", {})
            parsed_data = KustoFormatter.parse(query_result) or []

            print(f"    ✅ Retrieved schema for {entity_type} '{entity_name}' ({len(parsed_data)} rows)")

            if parsed_data and expected_fields:
                first_row = parsed_data[0]
                for field in expected_fields:
                    assert field in first_row, f"Missing expected field: {field}"
                    print(f"      ✅ Found expected field: {field}")

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

            if not result.get("success"):
                raise AssertionError(f"Failed to sample {entity_type} '{entity_name}': {result}")

            query_result = result.get("result", {})
            parsed_data = KustoFormatter.parse(query_result) or []

            assert len(parsed_data) >= min_expected_count, (
                f"Expected at least {min_expected_count} sample records, got {len(parsed_data)}."
            )
            print(f"    ✅ Retrieved {len(parsed_data)} sample records")

    async def test_graph_query(self) -> None:
        """Test kusto_graph_query tool if graphs are available."""
        print("\n🕸️  Testing kusto_graph_query...")
        if not self.client:
            raise RuntimeError("Client not initialized")

        if not self.test_cluster_uri:
            print("⚠️  No KUSTO_CLUSTER_URI configured, skipping graph query test")
            return

        list_result = await self.client.call_tool(
            "kusto_list_entities",
            {"cluster_uri": self.test_cluster_uri, "entity_type": "graphs", "database": self.test_database},
        )

        if not list_result.get("success"):
            raise AssertionError(f"Could not list graphs: {list_result}")

        query_result = list_result.get("result", {})
        parsed_data = KustoFormatter.parse(query_result) or []

        if len(parsed_data) == 0:
            raise AssertionError("No graphs found in database")

        graph_name = parsed_data[0].get("Name", "")
        if not graph_name:
            raise AssertionError("No valid graph name found")

        print(f"  Testing graph query on '{graph_name}'...")

        result = await self.client.call_tool(
            "kusto_graph_query",
            {
                "graph_name": graph_name,
                "query": "| graph-match (node) project labels=labels(node) | take 5",
                "cluster_uri": self.test_cluster_uri,
                "database": self.test_database,
            },
        )

        if not result.get("success"):
            raise AssertionError(f"Graph query failed: {result}")

        query_result = result.get("result", {})
        parsed_data = KustoFormatter.parse(query_result) or []
        print(f"    ✅ Graph query succeeded, returned {len(parsed_data)} rows")

    async def run_all_tests(self) -> None:
        """Run all available tests."""
        print("🚀 Starting Kusto tools live testing...")

        try:
            try:
                await self.setup()
                self.results.append(
                    LiveTestResult(
                        name="MCP server connection", scope="required-read-only", required=True, success=True
                    )
                )
            except Exception as e:
                details = self._summarize_error(e)
                self.results.append(
                    LiveTestResult(
                        name="MCP server connection",
                        scope="required-read-only",
                        required=True,
                        success=False,
                        details=details,
                    )
                )
                raise

            required_scope = "required-read-only"
            optional_scope = "best-effort-metadata"

            await self._run_test("tools/list exposes Kusto tools", required_scope, True, self.test_list_tools)
            await self._run_test("kusto_known_services", required_scope, True, self.test_known_services)
            await self._run_test("kusto_query print now()", required_scope, True, self.test_simple_query)
            await self._run_test(
                "kusto_query KQL StormEvents count", required_scope, True, self.test_kql_readonly_query
            )
            await self._run_test(
                "kusto_query SQL StormEvents count", required_scope, True, self.test_sql_query_with_crp
            )

            await self._run_test("kusto_list_entities", optional_scope, False, self.test_list_entities)
            await self._run_test("kusto_command .show tables", optional_scope, False, self.test_command)
            await self._run_test("kusto_deeplink_from_query", optional_scope, False, self.test_deeplink_from_query)
            await self._run_test("kusto_show_queryplan", optional_scope, False, self.test_show_queryplan)
            await self._run_test("kusto_diagnostics", optional_scope, False, self.test_diagnostics)
            await self._run_test("kusto_get_shots validation", optional_scope, False, self.test_get_shots)
            await self._run_test("kusto_describe_database", optional_scope, False, self.test_describe_database)
            await self._run_test(
                "kusto_describe_database_entity",
                optional_scope,
                False,
                self.test_describe_database_entity,
            )
            await self._run_test("kusto_sample_entity", optional_scope, False, self.test_sample_entity)
            await self._run_test("kusto_graph_query", optional_scope, False, self.test_graph_query)

            required_failures = [result for result in self.results if result.required and not result.success]
            if required_failures:
                names = ", ".join(result.name for result in required_failures)
                raise AssertionError(f"Required live tests failed: {names}")

            print("\n✅ Required read-only live tests completed successfully")
        finally:
            self._print_summary()
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
