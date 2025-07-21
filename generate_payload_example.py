#!/usr/bin/env python3
"""
Generate REST API payload example for Phase 1 target user prompt.
Shows the exact payload that would be sent to Microsoft Fabric API.
"""

import json
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from fabric_rti_mcp.eventstream.eventstream_builder_service import EventstreamBuilderService

def generate_target_payload():
    """Generate the payload for the target user prompt workflow."""
    
    print("🎯 Phase 1 Target User Prompt:")
    print('"I want to create a simple eventstream that takes bicycle sample data and stores it in my Eventhouse database. Can you help me build this step by step?"')
    print()
    
    # Initialize builder service
    service = EventstreamBuilderService()
    
    # Step 1: Start definition
    print("Step 1: Starting eventstream definition...")
    session_id = service.create_session(
        name="BicycleToEventhouse",
        description="Eventstream to capture bicycle sample data and store in Eventhouse"
    )
    print(f"   Session ID: {session_id}")
    print()
    
    # Get the builder session
    builder = service.get_session(session_id)
    if not builder:
        print("❌ Failed to get builder session")
        return None
    
    # Step 2: Add bicycle sample data source
    print("Step 2: Adding bicycle sample data source...")
    source_config = builder.create_sample_data_source(
        name="BicycleDataSource",
        sample_type="Bicycles"
    )
    builder.add_source(source_config)
    print(f"   Source added: {source_config['name']}")
    print()
    
    # Step 3: Add default stream
    print("Step 3: Creating default stream from source...")
    stream_config = builder.create_default_stream(
        name="BicycleStream",
        input_nodes=[source_config["name"]]
    )
    builder.add_stream(stream_config)
    print(f"   Stream created: {stream_config['name']}")
    print()
    
    # Step 4: Add Eventhouse destination
    print("Step 4: Adding Eventhouse destination...")
    destination_config = builder.create_eventhouse_destination(
        name="BicycleEventhouse",
        workspace_id="12345678-1234-1234-1234-123456789012",  # Example workspace ID
        item_id="87654321-4321-4321-4321-210987654321",      # Example eventhouse item ID
        database_name="BicycleData",
        table_name="BicycleEvents",
        input_nodes=[stream_config["name"]]
    )
    builder.add_destination(destination_config)
    print(f"   Destination added: {destination_config['name']}")
    print()
    
    # Step 5: Get final definition and payload
    print("Step 5: Generating final REST API payload...")
    final_definition = builder.get_definition()
    
    # The payload that would be sent to Microsoft Fabric API
    fabric_payload = {
        "displayName": builder.metadata["name"],
        "description": builder.metadata.get("description", ""),
        "definition": final_definition
    }
    
    print("\n" + "="*80)
    print("🚀 MICROSOFT FABRIC REST API PAYLOAD")
    print("="*80)
    print()
    print("This is the exact payload that would be sent to:")
    print("POST https://api.fabric.microsoft.com/v1/workspaces/{workspaceId}/items")
    print()
    print("Headers:")
    print("  Content-Type: application/json")
    print("  Authorization: Bearer {access_token}")
    print()
    print("Body:")
    print(json.dumps(fabric_payload, indent=2))
    print()
    print("="*80)
    print()
    
    # Also show the validation result
    print("📋 Validation Result:")
    validation_errors = builder.validate()
    if validation_errors:
        print(f"   Valid: False")
        print(f"   Errors: {validation_errors}")
    else:
        print(f"   Valid: True")
        print(f"   Sources: {len(final_definition.get('sources', []))}")
        print(f"   Streams: {len(final_definition.get('streams', []))}")
        print(f"   Destinations: {len(final_definition.get('destinations', []))}")
    print()
    
    return fabric_payload

if __name__ == "__main__":
    try:
        payload = generate_target_payload()
        print("✅ Payload generation completed successfully!")
    except Exception as e:
        print(f"❌ Error generating payload: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
