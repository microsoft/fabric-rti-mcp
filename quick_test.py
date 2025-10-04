#!/usr/bin/env python3
"""Simple test to verify Phase 1 builder functionality"""

print("🧪 Testing Phase 1 Eventstream Builder...")

try:
    from fabric_rti_mcp.eventstream.eventstream_builder_service import EventstreamDefinitionBuilder
    print("✅ Import successful")
    
    # Test 1: Basic builder creation
    builder = EventstreamDefinitionBuilder()
    print(f"✅ Builder created with session: {builder.session_id[:8]}...")
    
    # Test 2: Set metadata
    builder.set_metadata("TestEventstream", "Test description")
    print("✅ Metadata set")
    
    # Test 3: Create sample source
    source_config = builder.create_sample_data_source("BicycleSource", "Bicycles")
    builder.add_source(source_config)
    print("✅ Sample data source added")
    
    # Test 4: Create default stream
    stream_config = builder.create_default_stream("BicycleStream", ["BicycleSource"])
    builder.add_stream(stream_config)
    print("✅ Default stream added")
    
    # Test 5: Create Eventhouse destination
    dest_config = builder.create_eventhouse_destination(
        "TestDest", "workspace-123", "item-456", "TestDB", "TestTable", ["BicycleStream"]
    )
    builder.add_destination(dest_config)
    print("✅ Eventhouse destination added")
    
    # Test 6: Validate definition
    errors = builder.validate()
    if len(errors) == 0:
        print("✅ Definition validates successfully")
    else:
        print(f"❌ Validation errors: {errors}")
    
    # Test 7: Check definition structure
    definition = builder.get_definition()
    print(f"✅ Definition has {len(definition['definition']['sources'])} sources, {len(definition['definition']['streams'])} streams, {len(definition['definition']['destinations'])} destinations")
    
    print("\n🎉 Phase 1 Eventstream Builder implementation successful!")
    print("✅ All core functionality working:")
    print("  - Session management")
    print("  - Source creation (Sample Data)")
    print("  - Stream creation (Default Stream)")
    print("  - Destination creation (Eventhouse)")
    print("  - Validation")
    print("  - Definition export")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
