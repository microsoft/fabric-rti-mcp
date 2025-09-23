import argparse
import asyncio
import json
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import requests
from azure.identity import DefaultAzureCredential

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from fabric_rti_mcp.kusto.kusto_formatter import KustoFormatter


class HttpMcpClient:
    """HTTP MCP client for tool calls."""

    def __init__(self, host: str, port: int, cluster_uri: str):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.mcp_url = f"{self.base_url}/mcp"
        self.session_id = None  # Will be set during connection
        self.session = None
        self._connected = False

        # Try to get a token using DefaultAzureCredential
        auth_header = None
        try:

            print("Getting Kusto access token using DefaultAzureCredential...")
            credential = DefaultAzureCredential()
            # Get token for Kusto resource
            token = credential.get_token(f"{cluster_uri}/.default")
            auth_header = f"Bearer {token.token}"
            print("✅ Successfully obtained token from DefaultAzureCredential")
        except Exception as e:
            print(f"⚠️ Error getting token with DefaultAzureCredential: {str(e)}")
            auth_header = None

        # If all authentication methods failed, use the default hardcoded token
        if not auth_header:
            raise Exception("Error in getting token with Kusto audience")

        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "Authorization": auth_header,
        }

    async def connect(self) -> None:
        """Connect to the HTTP MCP server by initializing the session.

        For HTTP MCP, we need to:
        1. Send an initialize request to get a session ID
        2. Send an initialized notification to complete the handshake
        3. Store the session ID for future requests
        """
        if self._connected:
            return

        # Step 1: Initialize request with capabilities and protocol version
        init_payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "initialize",
            "params": {
                "protocolVersion": "1.0",
                "capabilities": {},
                "clientInfo": {"name": "http_mcp_client", "version": "1.0"},
            },
        }

        print(f"Initializing HTTP MCP session to {self.mcp_url}...")

        try:
            init_response = requests.post(self.mcp_url, headers=self.headers, json=init_payload, timeout=120)
            init_response.raise_for_status()
            self.session_id = init_response.headers.get("mcp-session-id")

            if not self.session_id:
                response_data = init_response.json()
                if "result" in response_data and "sessionId" in response_data["result"]:
                    self.session_id = response_data["result"]["sessionId"]
                elif "error" in response_data:
                    raise RuntimeError(f"Initialization failed: {response_data['error']}")

            if not self.session_id:
                raise Exception("Error in initialization - no session ID received")
            else:
                print(f"Received session ID: {self.session_id}")

            self.headers["mcp-session-id"] = self.session_id

            # Step 2: Send the "initialized" notification
            initialized_payload = {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}

            print("Sending 'initialized' notification to complete initialization...")
            initialized_response = requests.post(
                self.mcp_url, headers=self.headers, json=initialized_payload, timeout=60
            )
            initialized_response.raise_for_status()

            self._connected = True
            print("✅ Successfully initialized HTTP MCP session")

        except requests.exceptions.Timeout:
            print("❌ Connection timed out after 60 seconds. Server might be unresponsive.")
            raise RuntimeError("Connection to HTTP MCP server timed out after 60 seconds")
        except Exception as e:
            print(f"❌ Failed to initialize HTTP MCP session: {str(e)}")
            raise RuntimeError(f"Failed to connect to HTTP MCP server: {str(e)}")

        return None

    async def disconnect(self) -> None:
        """Disconnect from the HTTP MCP server.

        For HTTP mode, this simply clears the session state.
        """
        if not self._connected:
            return

        self.session_id = None
        self.session = None
        self._connected = False
        print("Disconnected from HTTP MCP server")

    async def list_tools(self) -> List[str]:
        """List available tools from the server."""
        if not self._connected:
            await self.connect()

        request_id = str(uuid.uuid4())
        request_data: Dict[str, Any] = {"jsonrpc": "2.0", "id": request_id, "method": "tools/list", "params": {}}

        print(f"Listing tools from {self.mcp_url}...")
        try:
            response = requests.post(self.mcp_url, json=request_data, headers=self.headers, timeout=120)
            if response.status_code == 200:
                try:
                    # Check content type before parsing
                    content_type = response.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        result = response.json()
                        if "result" in result and "tools" in result["result"]:
                            return [tool["name"] for tool in result["result"]["tools"]]
                        return []
                    else:
                        lines = response.text.strip().split("\n")
                        for line in lines:
                            if line.startswith("data: "):
                                data_json = line[6:]  # Remove "data: " prefix
                                parsed_data = json.loads(data_json)
                                if "result" in parsed_data and "tools" in parsed_data["result"]:
                                    return [tool["name"] for tool in parsed_data["result"]["tools"]]
                                elif "error" in parsed_data:
                                    print(f"Error in tool list response: {parsed_data['error']}")
                                    return []
                        return []
                except Exception as e:
                    print(f"Error parsing tools response: {e}")
                    return []
            else:
                print(f"Failed to list tools: {response.status_code}")
                print(f"Response: {response.text}")
                return []
        except requests.exceptions.Timeout:
            print("❌ List tools request timed out after 30 seconds. Server might be unresponsive.")
            return []
        except Exception as e:
            print(f"❌ Error listing tools: {str(e)}")
            return []

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the server."""
        if not self._connected:
            await self.connect()

        request_id = str(uuid.uuid4())
        request_data: Dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }

        print(f"Calling tool {tool_name} with arguments: {json.dumps(arguments, indent=2)}")
        try:
            response = requests.post(self.mcp_url, json=request_data, headers=self.headers, timeout=60)

            if response.status_code != 200:
                print(f"Tool call failed with status code: {response.status_code}")
                return {"success": False, "error": f"Request failed with status code: {response.status_code}"}

            content_type = response.headers.get("Content-Type", "")

            try:
                if "application/json" in content_type:
                    return self._parse_json_response(response.json())

                else:
                    return self._parse_text(response.text)

            except json.JSONDecodeError as e:
                print(f"Could not parse response as JSON: {e}")
                return {"success": False, "error": f"JSON parse error: {str(e)}"}
            except Exception as e:
                print(f"Error parsing response: {e}")
                return {"success": False, "error": f"Error parsing response: {str(e)}"}

        except requests.exceptions.Timeout:
            print(f"❌ Tool call to {tool_name} timed out after 60 seconds.")
            return {"success": False, "error": "Tool call timed out after 60 seconds"}
        except Exception as e:
            print(f"❌ Error calling tool: {str(e)}")
            return {"success": False, "error": f"Error calling tool: {str(e)}"}

    def _parse_json_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse a JSON response from the server."""
        if "result" not in data:
            return {"success": False, "error": "No result in response"}

        result = data["result"]

        content = result.get("content", [])
        if content and len(content) > 0:
            try:
                parsed_result = json.loads(content[0]["text"])
                return {"result": parsed_result, "success": True}
            except json.JSONDecodeError:
                return {"content": content[0]["text"], "success": True}

        elif "structuredContent" in result:
            return {"result": result["structuredContent"], "success": True}

        return {"success": False, "error": "No content in response"}

    def _parse_text(self, text: str) -> Dict[str, Any]:
        """Parse an event stream response from the server."""
        lines = text.strip().split("\n")

        for line in lines:
            if line.startswith("data: "):
                data_json = line[6:]  # Remove "data: " prefix
                parsed_data = json.loads(data_json)

                if "result" in parsed_data:
                    result = parsed_data["result"]

                    content = result.get("content", [])
                    if content and len(content) > 0:
                        try:
                            parsed_content = json.loads(content[0]["text"])
                            return {"result": parsed_content, "success": True}
                        except json.JSONDecodeError:
                            return {"content": content[0]["text"], "success": True}

                    elif "structuredContent" in result:
                        return {"result": result["structuredContent"]["result"], "success": True}

                    return {"success": True, "result": result}

                elif "error" in parsed_data:
                    return {"success": False, "error": f"Server error: {parsed_data['error']}"}

        return {"success": False, "error": "Could not parse response"}


class KustoHttpClientTester:
    """Tester for Kusto tools via HTTP MCP client."""

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.client: Optional[HttpMcpClient] = None
        self.server_process: Optional[subprocess.Popen[bytes]] = None
        self.test_cluster_uri = "https://help.kusto.windows.net"
        self.test_database = "Samples"

    async def setup(self) -> None:
        """Set up the test environment."""
        self.client = HttpMcpClient(self.host, self.port, self.test_cluster_uri)
        print(f"✅ Created HTTP MCP client for {self.host}:{self.port}")

    async def test_list_tools(self) -> None:
        """Test listing available tools."""
        print("\n🔧 Testing tool listing...")
        if not self.client:
            raise RuntimeError("Client not initialized")

        try:
            tools = await self.client.list_tools()

            if not tools:
                print("⚠️ No tools returned, possibly timed out or server error")
                return

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
                print(f"⚠️ Missing expected tools: {missing_tools}")
            else:
                print("✅ All expected Kusto tools found")
        except Exception as e:
            print(f"❌ Error during tool listing test: {str(e)}")
            raise

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

    async def run_all_tests(self) -> None:
        """Run all tests."""
        try:
            await self.setup()

            try:
                await self.test_list_tools()
                await self.test_list_entities()
                await self.test_simple_query()
            except Exception as test_error:
                print(f"\n❌ Specific test failed: {test_error}")

            print("\n✅ Tests execution completed!")

        except Exception as e:
            print(f"\n❌ Test setup failed: {e}")
            raise


def start_server(
    host: str = "127.0.0.1", port: int = 3000, transport: str = "http", additional_args: Any = None
) -> subprocess.Popen[bytes]:
    """Start the server in HTTP mode as a subprocess."""

    # Set required environment variables
    env = os.environ.copy()
    env["FABRIC_RTI_TRANSPORT"] = transport
    env["FABRIC_RTI_HTTP_HOST"] = host
    env["FABRIC_RTI_HTTP_PORT"] = str(port)
    env["FABRIC_RTI_HTTP_PATH"] = (
        additional_args.path if additional_args and hasattr(additional_args, "path") else "/mcp"
    )
    env["FABRIC_RTI_STATELESS_HTTP"] = (
        "true"
        if additional_args and hasattr(additional_args, "stateless_http") and additional_args.stateless_http
        else "false"
    )

    # OBO Flow configuration
    env["USE_OBO_FLOW"] = (
        "true"
        if additional_args and hasattr(additional_args, "use_obo_flow") and additional_args.use_obo_flow
        else "false"
    )
    if additional_args and hasattr(additional_args, "azure_tenant_id") and additional_args.azure_tenant_id:
        env["FABRIC_RTI_MCP_AZURE_TENANT_ID"] = additional_args.azure_tenant_id
    if additional_args and hasattr(additional_args, "entra_app_client_id") and additional_args.entra_app_client_id:
        env["FABRIC_RTI_MCP_ENTRA_APP_CLIENT_ID"] = additional_args.entra_app_client_id
    if additional_args and hasattr(additional_args, "umi_client_id") and additional_args.umi_client_id:
        env["FABRIC_RTI_MCP_USER_MANAGED_IDENTITY_CLIENT_ID"] = additional_args.umi_client_id

    env["KUSTO_EAGER_CONNECT"] = "false"
    if additional_args and hasattr(additional_args, "cluster_uri") and additional_args.cluster_uri:
        env["KUSTO_SERVICE_URI"] = additional_args.cluster_uri
    if additional_args and hasattr(additional_args, "database") and additional_args.database:
        env["KUSTO_SERVICE_DEFAULT_DB"] = additional_args.database

    print(f"Starting server on {host}:{port}...")
    server_process = subprocess.Popen(
        [sys.executable, "-m", "fabric_rti_mcp.server", "--http"],
        env=env,
    )

    # Wait for server to start
    time.sleep(2)
    # Check if the process is still running
    if server_process.poll() is not None:
        # Process terminated, get output
        stdout, stderr = server_process.communicate()
        print("Server process terminated unexpectedly!")
        print(f"Server stdout: {stdout.decode('utf-8', errors='replace')}")
        print(f"Server stderr: {stderr.decode('utf-8', errors='replace')}")
        raise RuntimeError("Server failed to start")

    # Poll health endpoint to ensure server is ready
    print("Waiting for server to be ready...")
    max_retries = 30
    for i in range(max_retries):
        try:
            health_response = requests.get(f"http://{host}:{port}/health", timeout=2)
            if health_response.status_code == 200:
                print(f"✅ Server is ready after {i + 1} attempts")
                break
        except Exception:
            pass

        if i == max_retries - 1:
            print("❌ Server failed to become ready within 30 seconds")
            raise RuntimeError("Server failed to become ready")

        time.sleep(1)

    print(f"Started server on {host}:{port}...")
    return server_process


def main():
    parser = argparse.ArgumentParser(description="HTTP MCP client for Fabric RTI")
    # Server connection parameters
    parser.add_argument("--host", default="127.0.0.1", help="Server host")
    parser.add_argument("--port", type=int, default=3000, help="Server port")
    parser.add_argument("--path", default="/mcp", help="HTTP path for MCP endpoint")
    parser.add_argument("--transport", choices=["stdio", "http"], default="http", help="Transport mode")
    parser.add_argument("--stateless-http", action="store_true", default=False, help="Enable stateless HTTP mode")

    # OBO Flow authentication parameters
    parser.add_argument(
        "--use-obo-flow",
        action="store_true",
        default=False,
        help="Enable OBO (On-Behalf-Of) flow to get token with Kusto audience",
    )
    parser.add_argument("--azure-tenant-id", default="72f988bf-86f1-41af-91ab-2d7cd011db47", help="Azure tenant ID")
    parser.add_argument("--entra-app-client-id", default=None, help="Azure AAD App Client ID")
    parser.add_argument("--umi-client-id", default=None, help="User Managed Identity Client ID")

    # Kusto configuration
    parser.add_argument(
        "--cluster",
        "--cluster-uri",
        dest="cluster_uri",
        default="https://help.kusto.windows.net",
        help="Kusto cluster URI",
    )
    parser.add_argument("--database", default="Samples", help="Kusto database name")

    args = parser.parse_args()

    print("=" * 60)
    print("Fabric RTI MCP - HTTP Client Test")
    print("=" * 60)

    server_proc = start_server(args.host, args.port, args.transport, args)
    try:
        time.sleep(3)

        async def run_tests():
            tester = KustoHttpClientTester(args.host, args.port)
            await tester.run_all_tests()

        asyncio.run(run_tests())
    finally:
        print("Stopping server...")
        server_proc.terminate()
        try:
            server_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_proc.kill()
        time.sleep(1)  # Give subprocess time to clean up


if __name__ == "__main__":
    main()
