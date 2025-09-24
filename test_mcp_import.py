#!/usr/bin/env python3
"""Test just the problematic MCP import."""

print("Testing basic MCP import...")

try:
    import mcp

    print("✓ mcp import successful")
    print(f"  mcp version: {getattr(mcp, '__version__', 'unknown')}")
except Exception as e:
    print(f"✗ mcp import failed: {e}")
    import traceback

    traceback.print_exc()

print("\nTesting fastmcp import...")

try:
    import fastmcp

    print("✓ fastmcp import successful")
    print(f"  fastmcp version: {getattr(fastmcp, '__version__', 'unknown')}")
except Exception as e:
    print(f"✗ fastmcp import failed: {e}")
    import traceback

    traceback.print_exc()

print("\nTesting FastMCP class import...")

try:
    from mcp.server.fastmcp import FastMCP

    print("✓ FastMCP class import successful")
except Exception as e:
    print(f"✗ FastMCP class import failed: {e}")
    import traceback

    traceback.print_exc()

print("\nTest completed.")
