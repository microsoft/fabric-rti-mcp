#!/usr/bin/env python3
"""
Test script to demonstrate the fixed eventstream builder with the new requirements
"""

import json
from fabric_rti_mcp.eventstream.eventstream_builder_service import EventstreamBuilderService

def test_fixed_eventstream_builder():
    """Test the eventstream builder with the fixes applied"""
    
    # Initialize the service
    service = EventstreamBuilderService()
    
    # Create a new session
    session_id = service.create_session(
        name="TestMCPSampleBikes",
        description="Eventstream that takes bicycle sample data and stores it in MCPEventhouse database"
    )
    
    print(f"Created session: {session_id}")
    
    # Get the builder
    builder = service.get_session(session_id)
    if not builder:
        print(f"Failed to get session {session_id}")
        return None
    
    # Step 1: Add sample data source
    source_config = builder.create_sample_data_source(
        name="BicycleSampleSource",
        sample_type="Bicycles"
    )
    builder.add_source(source_config)
    
    # Step 2: Add default stream
    stream_config = builder.create_default_stream(
        name="BicycleDataStream",
        input_nodes=["BicycleSampleSource"]
    )
    builder.add_stream(stream_config)
    
    # Step 3: Add Eventhouse destination with the stream as input
    destination_config = builder.create_eventhouse_destination(
        name="MCPEventhouseDestination",
        workspace_id="bff1ab3a-47f0-4b85-9226-509c4cfdda10",
        item_id="87654321-4321-4321-4321-210987654321",
        database_name="MCPEventhouse",
        table_name="BikesData",
        input_nodes=["BicycleDataStream"]  # This is the key fix - using the stream name
    )
    builder.add_destination(destination_config)
    
    # Get the complete definition
    full_definition = builder.get_definition()
    
    print("\n🎯 FIXED EVENTSTREAM DEFINITION:")
    print("=" * 80)
    print(json.dumps(full_definition, indent=2))
    
    # Validate the definition
    validation_errors = builder.validate()
    print(f"\n✅ Validation: {'PASSED' if not validation_errors else 'FAILED'}")
    if validation_errors:
        for error in validation_errors:
            print(f"  - {error}")
    
    return full_definition

if __name__ == "__main__":
    test_fixed_eventstream_builder()
