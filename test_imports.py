#!/usr/bin/env python3
"""Test individual imports to isolate the hanging issue."""

import sys

def test_import(module_name, description):
    """Test importing a module."""
    try:
        print(f"Testing {description}...")
        __import__(module_name)
        print(f"✓ {description} import successful")
        return True
    except Exception as e:
        print(f"✗ {description} import error: {e}")
        return False

# Test basic imports first
test_import("logging", "logging")
test_import("sys", "sys")
test_import("os", "os")

# Test MCP imports
test_import("mcp", "mcp")
test_import("mcp.server.fastmcp", "FastMCP")

# Test Azure imports (these might be the issue)
test_import("azure", "azure base")
test_import("azure.identity", "Azure Identity")
test_import("azure.kusto.data", "Azure Kusto Data")

# Test httpx
test_import("httpx", "httpx")

# Test our package imports step by step
test_import("fabric_rti_mcp", "fabric_rti_mcp base")
test_import("fabric_rti_mcp.common", "fabric_rti_mcp.common")
test_import("fabric_rti_mcp.kusto", "fabric_rti_mcp.kusto")

print("Basic import tests completed.")
