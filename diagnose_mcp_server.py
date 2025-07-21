#!/usr/bin/env python3
"""
Test script to diagnose MCP server startup issues
"""

import os
import sys
import traceback

# Add the project root to the Python path
sys.path.insert(0, '.')

print("🔍 MCP Server Diagnostic Test")
print("=" * 40)

def test_imports():
    """Test all required imports"""
    print("\n1. Testing imports...")
    
    try:
        from mcp.server.fastmcp import FastMCP
        print("   ✅ FastMCP imported successfully")
    except Exception as e:
        print(f"   ❌ FastMCP import failed: {e}")
        return False
    
    try:
        from fabric_rti_mcp import __version__
        print(f"   ✅ Version imported: {__version__}")
    except Exception as e:
        print(f"   ❌ Version import failed: {e}")
        return False
    
    try:
        from fabric_rti_mcp.common import logger
        print("   ✅ Logger imported successfully")
    except Exception as e:
        print(f"   ❌ Logger import failed: {e}")
        return False
    
    try:
        from fabric_rti_mcp.kusto import kusto_tools
        print("   ✅ Kusto tools imported successfully")
    except Exception as e:
        print(f"   ❌ Kusto tools import failed: {e}")
        return False
    
    try:
        from fabric_rti_mcp.eventstream import eventstream_tools
        print("   ✅ Eventstream tools imported successfully")
    except Exception as e:
        print(f"   ❌ Eventstream tools import failed: {e}")
        return False
    
    try:
        from fabric_rti_mcp.eventstream import eventstream_builder_tools
        print("   ✅ Eventstream builder tools imported successfully")
    except Exception as e:
        print(f"   ❌ Eventstream builder tools import failed: {e}")
        return False
    
    return True

def test_mcp_creation():
    """Test MCP server creation"""
    print("\n2. Testing MCP server creation...")
    
    try:
        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("test-server")
        print("   ✅ FastMCP server created successfully")
        return True
    except Exception as e:
        print(f"   ❌ FastMCP server creation failed: {e}")
        traceback.print_exc()
        return False

def test_tool_registration():
    """Test tool registration"""
    print("\n3. Testing tool registration...")
    
    try:
        from mcp.server.fastmcp import FastMCP
        from fabric_rti_mcp.kusto import kusto_tools
        from fabric_rti_mcp.eventstream import eventstream_tools
        from fabric_rti_mcp.eventstream import eventstream_builder_tools
        
        mcp = FastMCP("test-server")
        
        # Test each tool registration
        kusto_tools.register_tools(mcp)
        print("   ✅ Kusto tools registered successfully")
        
        eventstream_tools.register_tools(mcp)
        print("   ✅ Eventstream tools registered successfully")
        
        eventstream_builder_tools.register_builder_tools(mcp)
        print("   ✅ Eventstream builder tools registered successfully")
        
        return True
    except Exception as e:
        print(f"   ❌ Tool registration failed: {e}")
        traceback.print_exc()
        return False

def test_environment():
    """Test environment variables"""
    print("\n4. Testing environment variables...")
    
    kusto_uri = os.getenv("KUSTO_SERVICE_URI")
    kusto_db = os.getenv("KUSTO_DATABASE")
    fabric_api = os.getenv("FABRIC_API_BASE_URL")
    
    print(f"   KUSTO_SERVICE_URI: {kusto_uri}")
    print(f"   KUSTO_DATABASE: {kusto_db}")
    print(f"   FABRIC_API_BASE_URL: {fabric_api}")
    
    return True

def main():
    """Run all diagnostic tests"""
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print(f"Working directory: {os.getcwd()}")
    
    # Run all tests
    tests = [
        test_imports,
        test_mcp_creation,
        test_tool_registration,
        test_environment
    ]
    
    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"   ❌ Test failed with exception: {e}")
            traceback.print_exc()
    
    print(f"\n📊 Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("✅ All tests passed! MCP server should be able to start.")
    else:
        print("❌ Some tests failed. This might explain the MCP server startup issues.")

if __name__ == "__main__":
    main()
