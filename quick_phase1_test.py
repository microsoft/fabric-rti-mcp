#!/usr/bin/env python3
"""
Quick Phase 1 Verification Test
Tests just the core functionality without complex workflows
"""

def quick_test():
    print("🔍 Quick Phase 1 Verification")
    print("=" * 40)
    
    try:
        # Test 1: Core imports
        print("1. Testing core imports...")
        from fabric_rti_mcp.eventstream.eventstream_builder_service import EventstreamDefinitionBuilder
        print("✅ EventstreamDefinitionBuilder imported")
        
        # Test 2: Builder creation
        print("2. Testing builder creation...")
        builder = EventstreamDefinitionBuilder()
        print(f"✅ Builder created: {builder.session_id}")
        
        # Test 3: Add components
        print("3. Testing component creation...")
        builder.set_metadata("TestStream", "Test description")
        
        source = builder.create_sample_data_source("TestSource", "Bicycles")
        builder.add_source(source)
        print("✅ Source added")
        
        stream = builder.create_default_stream("TestStream", ["TestSource"])
        builder.add_stream(stream)
        print("✅ Stream added")
        
        dest = builder.create_eventhouse_destination(
            "TestDest", "ws-123", "item-456", "db", "table", ["TestStream"]
        )
        builder.add_destination(dest)
        print("✅ Destination added")
        
        # Test 4: Validation
        print("4. Testing validation...")
        errors = builder.validate()
        if errors:
            print(f"❌ Validation errors: {errors}")
            return False
        print("✅ Validation passed")
        
        # Test 5: Service tools
        print("5. Testing service tools...")
        from fabric_rti_mcp.eventstream.eventstream_builder_tools import eventstream_start_definition
        result = eventstream_start_definition("QuickTest", "Quick test stream")
        print("✅ Tool execution successful")
        
        print("\n🎉 QUICK TEST PASSED!")
        print("Phase 1 implementation is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = quick_test()
    if success:
        print("\n✅ Ready for manual testing with MCP server!")
    else:
        print("\n❌ Issues found - needs debugging")
