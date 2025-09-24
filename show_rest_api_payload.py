#!/usr/bin/env python3
"""
Demo script showing the exact HTTP REST API payload for TestMCPSampleBikes eventstream
"""

import base64
import json

from fabric_rti_mcp.eventstream.eventstream_builder_service import (
    eventstream_add_default_stream,
    eventstream_add_derived_stream,
    eventstream_add_sample_data_source,
    eventstream_get_current_definition,
    eventstream_start_definition,
)


def show_rest_api_payload():
    print("=== Building TestMCPSampleBikes Eventstream ===\n")

    # Build the eventstream definition using the builder
    session = eventstream_start_definition(
        "TestMCPSampleBikes", "Simple eventstream for bicycle sample data with derived stream"
    )
    session_id = session["session_id"]

    # Add components
    eventstream_add_sample_data_source(session_id, "BicycleSampleSource", "Bicycles")
    eventstream_add_default_stream(session_id, ["BicycleSampleSource"])
    eventstream_add_derived_stream(session_id, "SampleBikesDS", ["TestMCPSampleBikes-stream"])

    # Get the final definition
    final_definition = eventstream_get_current_definition(session_id)
    eventstream_definition = final_definition["definition"]

    print("=== EVENTSTREAM DEFINITION (what gets base64 encoded) ===")
    definition_json = json.dumps(eventstream_definition, indent=2)
    print(definition_json)

    # Encode as base64 (like the service does)
    definition_b64 = base64.b64encode(definition_json.encode("utf-8")).decode("utf-8")

    # Build the complete HTTP payload
    workspace_id = "bff1ab3a-47f0-4b85-9226-509c4cfdda10"
    eventstream_name = session["name"]
    description = session["description"]

    http_payload = {
        "displayName": eventstream_name,
        "type": "Eventstream",
        "description": description,
        "definition": {
            "parts": [
                {"path": "eventstream.json", "payload": definition_b64, "payloadType": "InlineBase64"},
                {"path": ".platform", "payload": definition_b64, "payloadType": "InlineBase64"},
            ]
        },
    }

    print("\n" + "=" * 60)
    print("=== COMPLETE HTTP REST API PAYLOAD ===")
    print(f"Method: POST")
    print(f"URL: https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/items")
    print(f"Headers: Authorization: Bearer <token>, Content-Type: application/json")
    print("\nPayload (JSON):")
    print(json.dumps(http_payload, indent=2))

    print("\n" + "=" * 60)
    print("=== BASE64 DECODED DEFINITION (for reference) ===")
    print("The 'payload' field above contains this definition (base64 encoded):")
    print(definition_json)

    print("\n" + "=" * 60)
    print("=== SUMMARY ===")
    print(f"✅ Eventstream Name: {eventstream_name}")
    print(f"✅ Target Workspace: {workspace_id}")
    print(f"✅ Description: {description}")
    print(f"✅ Definition Size: {len(definition_json)} characters")
    print(f"✅ Base64 Payload Size: {len(definition_b64)} characters")
    print(f"✅ Components: 1 source, 2 streams (1 default + 1 derived), 0 destinations")


if __name__ == "__main__":
    show_rest_api_payload()
