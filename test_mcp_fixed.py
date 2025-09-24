#!/usr/bin/env python3
"""Test script to verify all MCP imports work correctly."""


def test_basic_imports():
    """Test that all required imports work."""
    print("Testing basic imports...")

    # Test FastMCP import
    try:
        from fastmcp import FastMCP

        print("✓ FastMCP import successful")
    except Exception as e:
        print(f"✗ FastMCP import failed: {e}")
        return False

    # Test fabric_rti_mcp imports
    try:
        from fabric_rti_mcp import __version__

        print(f"✓ fabric_rti_mcp version: {__version__}")
    except Exception as e:
        print(f"✗ fabric_rti_mcp import failed: {e}")
        return False

    # Test common module
    try:
        from fabric_rti_mcp.common import logger

        print("✓ fabric_rti_mcp.common import successful")
    except Exception as e:
        print(f"✗ fabric_rti_mcp.common import failed: {e}")
        return False

    # Test kusto tools
    try:
        from fabric_rti_mcp.kusto import kusto_tools

        print("✓ kusto_tools import successful")
    except Exception as e:
        print(f"✗ kusto_tools import failed: {e}")
        return False

    # Test eventstream tools
    try:
        from fabric_rti_mcp.eventstream import eventstream_tools

        print("✓ eventstream_tools import successful")
    except Exception as e:
        print(f"✗ eventstream_tools import failed: {e}")
        return False

    return True


def test_server_creation():
    """Test creating a FastMCP server instance."""
    print("\nTesting server creation...")

    try:
        from fastmcp import FastMCP

        mcp = FastMCP("test-server")
        print("✓ FastMCP server instance created successfully")
        return True
    except Exception as e:
        print(f"✗ FastMCP server creation failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    print("=== MCP Server Import Test ===")

    if not test_basic_imports():
        print("\n❌ Basic imports failed!")
        return

    if not test_server_creation():
        print("\n❌ Server creation failed!")
        return

    print("\n✅ All tests passed! The MCP server should start successfully.")


if __name__ == "__main__":
    main()
