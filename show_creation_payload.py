#!/usr/bin/env python3
"""
Show the exact HTTP payload that would be sent to create the TestMCPSampleBikesDS eventstream
"""

import json
import base64
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fabric_rti_mcp.eventstream.eventstream_builder_service import EventstreamBuilderService

def show_eventstream_creation_payload():
    """Show the exact HTTP payload that would be sent to Fabric API"""
    
    print("🔍 ANALYZING EVENTSTREAM CREATION PAYLOAD")
    print("=" * 80)
    
    # Recreate the exact eventstream definition that was built
    service = EventstreamBuilderService()
    session_id = service.create_session(
        name="TestMCPSampleBikesDS",
        description="Eventstream that takes bicycle sample data and processes it through a derived stream named SampleBikesDS with required default stream"
    )
    
    builder = service.get_session(session_id)
    if not builder:
        print("❌ Failed to create builder session")
        return
    
    # Add the exact same components as we did in the creation process
    # 1. Sample data source
    source_config = builder.create_sample_data_source(
        name="BicycleSampleSource",
        sample_type="Bicycles"
    )
    builder.add_source(source_config)
    
    # 2. Default stream (required by Fabric)
    default_stream_config = builder.create_default_stream(
        name="DefaultBicycleStream",
        input_nodes=["BicycleSampleSource"]
    )
    builder.add_stream(default_stream_config)
    
    # 3. Derived stream (the one we wanted)
    derived_stream_config = builder.create_derived_stream(
        name="SampleBikesDS",
        input_nodes=["BicycleSampleSource"]  # Directly from source to avoid validation issues
    )
    builder.add_stream(derived_stream_config)
    
    # 4. Custom endpoint destination
    destination_config = builder.create_custom_endpoint_destination(
        name="ProcessedDataEndpoint",
        endpoint_url="https://example.com/webhook",
        input_nodes=["SampleBikesDS"]
    )
    builder.add_destination(destination_config)
    
    # Get the complete definition
    full_definition = builder.get_definition()
    eventstream_definition = full_definition["definition"]
    
    print("📋 EVENTSTREAM DEFINITION THAT WAS SENT:")
    print("=" * 50)
    print(json.dumps(eventstream_definition, indent=2))
    
    # Show the exact HTTP payload that would be sent to Fabric
    definition_json = json.dumps(eventstream_definition)
    definition_b64 = base64.b64encode(definition_json.encode("utf-8")).decode("utf-8")
    
    fabric_payload = {
        "displayName": "TestMCPSampleBikesDS",
        "type": "Eventstream",
        "definition": {
            "parts": [
                {
                    "path": "eventstream.json",
                    "payload": definition_b64,
                    "payloadType": "InlineBase64"
                }
            ]
        },
        "description": "Eventstream that takes bicycle sample data and processes it through a derived stream named SampleBikesDS with required default stream"
    }
    
    print("\n🌐 HTTP PAYLOAD SENT TO FABRIC API:")
    print("=" * 50)
    print("URL: POST https://api.fabric.microsoft.com/v1/workspaces/bff1ab3a-47f0-4b85-9226-509c4cfdda10/items")
    print("Headers:")
    print("  Content-Type: application/json")
    print("  Authorization: Bearer <access_token>")
    print("\nPayload:")
    print(json.dumps(fabric_payload, indent=2))
    
    print("\n🔍 DECODED BASE64 DEFINITION:")
    print("=" * 50)
    decoded_definition = base64.b64decode(definition_b64).decode("utf-8")
    print(decoded_definition)
    
    print("\n🚨 POTENTIAL ISSUES IDENTIFIED:")
    print("=" * 50)
    
    # Check for common issues
    issues = []
    
    # Check if sources have IDs (some Fabric APIs require them)
    for source in eventstream_definition.get("sources", []):
        if "id" not in source:
            issues.append(f"❌ Source '{source.get('name')}' missing 'id' field")
    
    # Check if streams have IDs
    for stream in eventstream_definition.get("streams", []):
        if "id" not in stream:
            issues.append(f"❌ Stream '{stream.get('name')}' missing 'id' field")
    
    # Check inputNodes format
    for stream in eventstream_definition.get("streams", []):
        input_nodes = stream.get("inputNodes", [])
        for node in input_nodes:
            if not isinstance(node, dict) or "name" not in node:
                issues.append(f"❌ Stream '{stream.get('name')}' has invalid inputNodes format")
                break
    
    # Check if destinations have proper connections
    for dest in eventstream_definition.get("destinations", []):
        input_nodes = dest.get("inputNodes", [])
        if not input_nodes:
            issues.append(f"❌ Destination '{dest.get('name')}' has no inputNodes")
    
    if issues:
        for issue in issues:
            print(issue)
    else:
        print("✅ No obvious format issues detected")
    
    print(f"\n📊 SUMMARY:")
    print(f"- Definition size: {len(definition_json)} characters")
    print(f"- Base64 payload size: {len(definition_b64)} characters")
    print(f"- Sources: {len(eventstream_definition.get('sources', []))}")
    print(f"- Streams: {len(eventstream_definition.get('streams', []))}")
    print(f"- Destinations: {len(eventstream_definition.get('destinations', []))}")
    print(f"- Operators: {len(eventstream_definition.get('operators', []))}")

if __name__ == "__main__":
    show_eventstream_creation_payload()
