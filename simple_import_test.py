#!/usr/bin/env python3
"""Simple import test"""

print("Testing imports step by step...")

try:
    print("1. Testing basic import...")
    import fabric_rti_mcp
    print("✅ fabric_rti_mcp imported")
    
    print("2. Testing eventstream module...")
    from fabric_rti_mcp import eventstream
    print("✅ eventstream module imported")
    
    print("3. Testing builder service...")
    from fabric_rti_mcp.eventstream import eventstream_builder_service
    print("✅ eventstream_builder_service imported")
    
    print("4. Testing EventstreamDefinitionBuilder...")
    from fabric_rti_mcp.eventstream.eventstream_builder_service import EventstreamDefinitionBuilder
    print("✅ EventstreamDefinitionBuilder imported")
    
    print("5. Creating builder instance...")
    builder = EventstreamDefinitionBuilder()
    print(f"✅ Builder created: {builder.session_id}")
    
    print("🎉 All basic imports work!")
    
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
