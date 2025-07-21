#!/usr/bin/env python3
"""
Show the REST API payload for creating the TestMCPSampleBikesDS eventstream
"""

import json
import uuid
from datetime import datetime

# The eventstream definition from the builder
definition = {
    "sources": [
        {
            "name": "BicycleSampleData",
            "type": "SampleData",
            "properties": {
                "type": "Bicycles"
            }
        }
    ],
    "destinations": [
        {
            "name": "SampleBikesOutput",
            "type": "CustomEndpoint",
            "properties": {},
            "inputNodes": [
                {
                    "name": "SampleBikesDS"
                }
            ]
        }
    ],
    "operators": [],
    "streams": [
        {
            "name": "DefaultBikeStream-stream",
            "type": "DefaultStream",
            "properties": {},
            "inputNodes": [
                {
                    "name": "BicycleSampleData"
                }
            ]
        },
        {
            "name": "SampleBikesDS",
            "type": "DerivedStream",
            "properties": {
                "inputSerialization": {
                    "type": "Json",
                    "properties": {
                        "encoding": "UTF8"
                    }
                }
            },
            "inputNodes": [
                {
                    "name": "DefaultBikeStream-stream"
                }
            ]
        }
    ],
    "compatibilityLevel": "1.0"
}

# Create the REST API payload
workspace_id = "bff1ab3a-47f0-4b85-9226-509c4cfdda10"
eventstream_name = "TestMCPSampleBikesDS"
eventstream_id = str(uuid.uuid4())

# This is the payload that would be sent to the Microsoft Fabric API
rest_api_payload = {
    "displayName": eventstream_name,
    "type": "Eventstream",
    "definition": definition
}

print("=" * 80)
print("EVENTSTREAM DEFINITION")
print("=" * 80)
print(json.dumps({
    "name": eventstream_name,
    "workspace_id": workspace_id,
    "definition": definition
}, indent=2))

print("\n" + "=" * 80)
print("REST API PAYLOAD")
print("=" * 80)
print(f"POST https://dailyapi.fabric.microsoft.com/v1/workspaces/{workspace_id}/items")
print("Content-Type: application/json")
print("Authorization: Bearer <ACCESS_TOKEN>")
print()
print(json.dumps(rest_api_payload, indent=2))

print("\n" + "=" * 80)
print("EVENTSTREAM FLOW DESCRIPTION")
print("=" * 80)
print(f"1. Source: BicycleSampleData (Bicycles sample data)")
print(f"2. Default Stream: DefaultBikeStream-stream (connects source to processing)")
print(f"3. Derived Stream: SampleBikesDS (processes the bike data)")
print(f"4. Destination: SampleBikesOutput (custom endpoint)")
print(f"")
print(f"Data Flow: BicycleSampleData → DefaultBikeStream-stream → SampleBikesDS → SampleBikesOutput")
print(f"")
print(f"The eventstream '{eventstream_name}' will be created in workspace '{workspace_id}'")
print(f"with the derived stream 'SampleBikesDS' as requested.")
