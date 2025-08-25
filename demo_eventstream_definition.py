#!/usr/bin/env python3
"""
Demo script showing the full eventstream definition for:
TestMCPSampleBikes with bicycle sample data and derived stream SampleBikesDS
"""

import json
from fabric_rti_mcp.eventstream.eventstream_builder_service import (
    eventstream_start_definition,
    eventstream_add_sample_data_source, 
    eventstream_add_default_stream,
    eventstream_add_derived_stream,
    eventstream_get_current_definition,
    eventstream_validate_definition
)

def main():
    print("=== Building Eventstream: TestMCPSampleBikes ===\n")
    
    # Step 1: Start the definition
    print("Step 1: Starting definition...")
    session = eventstream_start_definition(
        'TestMCPSampleBikes', 
        'Simple eventstream for bicycle sample data with derived stream'
    )
    session_id = session['session_id']
    print(f"✅ Session started: {session_id}\n")
    
    # Step 2: Add bicycle sample data source
    print("Step 2: Adding bicycle sample data source...")
    source_result = eventstream_add_sample_data_source(
        session_id, 
        'BicycleSampleSource', 
        'Bicycles'
    )
    print(f"✅ Added source: {source_result['source_added']}\n")
    
    # Step 3: Add default stream to process the source data
    print("Step 3: Adding default stream...")
    default_stream_result = eventstream_add_default_stream(
        session_id, 
        ['BicycleSampleSource']
    )
    print(f"✅ Added default stream: {default_stream_result['stream_added']}\n")
    
    # Step 4: Add derived stream
    print("Step 4: Adding derived stream...")
    derived_stream_result = eventstream_add_derived_stream(
        session_id, 
        'SampleBikesDS', 
        ['TestMCPSampleBikes-stream']  # Using the auto-generated default stream name
    )
    print(f"✅ Added derived stream: {derived_stream_result['stream_added']}\n")
    
    # Step 5: Get the final definition
    print("=== FINAL EVENTSTREAM DEFINITION ===")
    final_definition = eventstream_get_current_definition(session_id)
    print(json.dumps(final_definition['definition'], indent=2))
    print()
    
    # Step 6: Validate
    print("=== VALIDATION RESULTS ===")
    validation = eventstream_validate_definition(session_id)
    print(f"✅ Is Valid: {validation['is_valid']}")
    
    if validation['errors']:
        print(f"❌ Errors: {validation['errors']}")
    if validation['warnings']:
        print(f"⚠️  Warnings: {validation['warnings']}")
    
    print(f"\n📊 Summary:")
    print(f"   Sources: {validation['summary']['sources']}")
    print(f"   Streams: {validation['summary']['streams']} (1 default + 1 derived)")
    print(f"   Destinations: {validation['summary']['destinations']}")
    print(f"   Operators: {validation['summary']['operators']}")

if __name__ == "__main__":
    main()
