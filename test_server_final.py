#!/usr/bin/env python3
"""Test server startup by importing and checking tool registration."""

def test_server_startup():
    """Test that the server can start and register tools without errors."""
    print("Testing MCP server startup...")
    
    try:
        from fastmcp import FastMCP
        from fabric_rti_mcp.server import register_tools
        
        print("✓ Imports successful")
        
        # Create test MCP instance
        mcp = FastMCP("test-server")
        print("✓ FastMCP instance created")
        
        # Try to register tools
        register_tools(mcp)
        print("✓ Tools registered successfully")
        
        print("\n🎉 MCP server startup test PASSED!")
        print("The server should now work with VS Code.")
        return True
        
    except Exception as e:
        print(f"❌ Server startup test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_server_startup()
