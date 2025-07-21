#!/usr/bin/env python3
"""Quick test script to verify environment variable configuration"""

import os

# Test 1: Check default value when no env var is set
print("=== Test 1: Default API Base URL ===")
if 'FABRIC_API_BASE_URL' in os.environ:
    del os.environ['FABRIC_API_BASE_URL']

from fabric_rti_mcp.eventstream.eventstream_service import get_fabric_api_base
print(f"Default API Base URL: {get_fabric_api_base()}")

# Test 2: Check custom value when env var is set
print("\n=== Test 2: Custom API Base URL ===")
os.environ['FABRIC_API_BASE_URL'] = "https://custom.fabric.api.com/v1"

# Need to reimport to pick up the new environment variable
import importlib
import fabric_rti_mcp.eventstream.eventstream_service
importlib.reload(fabric_rti_mcp.eventstream.eventstream_service)
from fabric_rti_mcp.eventstream.eventstream_service import get_fabric_api_base

print(f"Custom API Base URL: {get_fabric_api_base()}")

print("\n=== Test 3: Connection Creation ===")
from fabric_rti_mcp.eventstream.eventstream_service import get_eventstream_connection
try:
    connection = get_eventstream_connection()
    print(f"Connection API Base: {connection.api_base_url}")
    print("✅ Connection created successfully")
except Exception as e:
    print(f"❌ Error creating connection: {e}")

print("\n✅ All tests completed!")
