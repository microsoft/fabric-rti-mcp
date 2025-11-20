#!/usr/bin/env python3
"""
Example script for testing Eventstream MCP tools locally
"""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_eventstream_tools():
    # Connect to the MCP server
    server_params = StdioServerParameters(
        command="uvx",
        args=["microsoft-fabric-rti-mcp"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()
            
            # List available tools
            tools = await session.list_tools()
            print("Available tools:")
            for tool in tools.tools:
                if "eventstream" in tool.name:
                    print(f"  - {tool.name}: {tool.description}")
            
            # Example: List eventstreams (you'll need real credentials)
            # Replace with your actual workspace ID and auth token
            workspace_id = "your-workspace-id-here"
            auth_token = "Bearer your-token-here"
            
            try:
                result = await session.call_tool(
                    "eventstream_list",
                    {
                        "workspace_id": workspace_id,
                        "authorization_token": auth_token
                    }
                )
                print("Eventstream list result:")
                print(json.dumps(result.content, indent=2))
                
            except Exception as e:
                print(f"Error calling tool: {e}")

if __name__ == "__main__":
    asyncio.run(test_eventstream_tools())
