#!/usr/bin/env python3
"""
Simple test script to verify MCP server functionality
"""

import subprocess
import sys
import json

def test_mcp_server():
    """Test if the MCP server starts correctly"""
    print("Testing Fabric RTI MCP Server...")
    
    try:
        # Test if uvx can find the package
        result = subprocess.run(
            ["uvx", "microsoft-fabric-rti-mcp", "--help"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("✅ MCP Server starts successfully!")
            print("Server output:")
            print(result.stdout)
            if result.stderr:
                print("Server logs:")
                print(result.stderr)
        else:
            print("❌ MCP Server failed to start")
            print("Error output:")
            print(result.stderr)
            
    except subprocess.TimeoutExpired:
        print("⚠️  MCP Server started but took too long to respond")
    except FileNotFoundError:
        print("❌ uvx command not found. Please install uv first:")
        print("pip install uv")
    except Exception as e:
        print(f"❌ Error testing MCP server: {e}")

def show_claude_config():
    """Show the correct Claude Desktop configuration"""
    config = {
        "mcpServers": {
            "fabric-rti-mcp": {
                "command": "uvx",
                "args": ["microsoft-fabric-rti-mcp"]
            }
        }
    }
    
    print("\n" + "="*50)
    print("Claude Desktop Configuration")
    print("="*50)
    print("File location: %APPDATA%\\Claude\\claude_desktop_config.json")
    print("\nConfiguration content:")
    print(json.dumps(config, indent=2))
    print("\nAfter updating the config:")
    print("1. Restart Claude Desktop completely")
    print("2. Wait a few seconds for the MCP server to initialize")
    print("3. Try asking Claude: 'What MCP tools do you have available?'")

if __name__ == "__main__":
    test_mcp_server()
    show_claude_config()
