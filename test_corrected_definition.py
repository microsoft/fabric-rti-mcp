#!/usr/bin/env python3
"""
Test script to show the corrected eventstream definition after all fixes
"""

import json
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fabric_rti_mcp.eventstream.eventstream_builder_service import EventstreamBuilderService

def test_corrected_eventstream_definition():
    """Test the corrected eventstream builder"""
    
    print("🎯 TESTING CORRECTED EVENTSTREAM BUILDER")
    print("=" * 80)
    
    # Initialize service
    service = EventstreamBuilderService()
    
    # Create session
    session_id = service.create_session(
        name="TestMCPSampleBikes",
        description="Eventstream that takes bicycle sample data and stores it in MCPEventhouse database"
    )
    
    # Get builder
    builder = service.get_session(session_id)
    if not builder:
        print("❌ Failed to create session")
        return
    
    print(f"✅ Created session: {session_id}")
    
    # Step 1: Add sample data source
    source_config = builder.create_sample_data_source(
        name="BicycleSampleSource",
        sample_type="Bicycles"
    )
    builder.add_source(source_config)
    print(f"✅ Added source: {source_config}")
    
    # Step 2: Add default stream
    stream_config = builder.create_default_stream(
        name="BicycleDataStream",
        input_nodes=["BicycleSampleSource"]
    )
    builder.add_stream(stream_config)
    print(f"✅ Added stream: {stream_config}")
    
    # Step 3: Add Eventhouse destination
    destination_config = builder.create_eventhouse_destination(
        name="MCPEventhouseDestination",
        workspace_id="bff1ab3a-47f0-4b85-9226-509c4cfdda10",
        item_id="87654321-4321-4321-4321-210987654321",
        database_name="MCPEventhouse",
        table_name="BikesData",
        input_nodes=["BicycleDataStream"]
    )
    builder.add_destination(destination_config)
    print(f"✅ Added destination: {destination_config}")
    
    # Get complete definition
    full_definition = builder.get_definition()
    
    print("\n🎯 CORRECTED EVENTSTREAM DEFINITION:")
    print("=" * 80)
    print(json.dumps(full_definition, indent=2))
    
    # Validate
    try:
        validation_errors = builder.validate()
        if validation_errors:
            print(f"\n❌ Validation errors: {validation_errors}")
        else:
            print("\n✅ Validation: PASSED")
    except Exception as e:
        print(f"\n❌ Validation failed with error: {e}")
    
    return full_definition

if __name__ == "__main__":
    test_corrected_eventstream_definition()
