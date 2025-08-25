#!/usr/bin/env python3
"""Test script to check server import issues."""

try:
    print("Testing fabric_rti_mcp.server import...")
    import fabric_rti_mcp.server
    print("✓ Server import successful")
except Exception as e:
    print(f"✗ Import error: {e}")
    import traceback
    traceback.print_exc()

try:
    print("\nTesting eventstream_builder_service import...")
    import fabric_rti_mcp.eventstream.eventstream_builder_service
    print("✓ Builder service import successful")
except Exception as e:
    print(f"✗ Builder service import error: {e}")
    import traceback
    traceback.print_exc()

try:
    print("\nTesting eventstream_tools import...")
    import fabric_rti_mcp.eventstream.eventstream_tools
    print("✓ Eventstream tools import successful")
except Exception as e:
    print(f"✗ Eventstream tools import error: {e}")
    import traceback
    traceback.print_exc()

print("\nTesting complete.")
