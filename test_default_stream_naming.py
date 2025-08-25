#!/usr/bin/env python3
"""
Test script to verify the default stream naming fix
"""

import json
from fabric_rti_mcp.eventstream.eventstream_builder_service import (
    eventstream_start_definition,
    eventstream_add_sample_data_source, 
    eventstream_add_default_stream,
    eventstream_get_current_definition
)

def test_default_stream_naming():
    print("Testing default stream naming convention...")
    
    # Start with an eventstream named "TestMCPSampleBikes"
    session = eventstream_start_definition('TestMCPSampleBikes', 'Test eventstream')
    session_id = session['session_id']
    print(f"✅ Started session for eventstream: {session['name']}")
    
    # Add a source
    eventstream_add_sample_data_source(session_id, 'BicycleSource', 'Bicycles')
    print("✅ Added sample data source")
    
    # Add default stream (no stream name parameter - should auto-generate)
    result = eventstream_add_default_stream(session_id, ['BicycleSource'])
    print(f"✅ Added default stream: {result['stream_added']}")
    
    # Get the current definition to verify the stream name
    definition = eventstream_get_current_definition(session_id)
    
    streams = definition['definition']['streams']
    if len(streams) == 1:
        stream_name = streams[0]['name']
        expected_name = 'TestMCPSampleBikes-stream'
        
        if stream_name == expected_name:
            print(f"✅ PASS: Default stream named correctly: '{stream_name}'")
        else:
            print(f"❌ FAIL: Expected '{expected_name}', got '{stream_name}'")
    else:
        print(f"❌ FAIL: Expected 1 stream, got {len(streams)}")
    
    print("\nGenerated definition:")
    print(json.dumps(definition['definition'], indent=2))

if __name__ == "__main__":
    test_default_stream_naming()
