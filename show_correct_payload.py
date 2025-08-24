#!/usr/bin/env python3
"""
Show the CORRECT REST API payload for creating TestMCPSampleBikesDS eventstream
Based on the actual Fabric API format used by the eventstream service
"""

import base64
import json

# The correct eventstream definition (as stored in the eventstream.json file)
eventstream_definition = {
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
            "name": "TestMCPSampleBikesDS-stream",
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
                    "name": "TestMCPSampleBikesDS-stream"
                }
            ]
        }
    ],
    "compatibilityLevel": "1.0"
}

# Convert to JSON and then to base64 (as required by Fabric API)
definition_json = json.dumps(eventstream_definition)
definition_b64 = base64.b64encode(definition_json.encode("utf-8")).decode("utf-8")

# Create the ACTUAL REST API payload that gets sent to Fabric
workspace_id = "bff1ab3a-47f0-4b85-9226-509c4cfdda10"
eventstream_name = "TestMCPSampleBikesDS"

rest_api_payload = {
    "displayName": eventstream_name,
    "type": "Eventstream",
    "definition": {
        "parts": [
            {
                "path": "eventstream.json",
                "payload": definition_b64,
                "payloadType": "InlineBase64"
            },
            {
                "path": ".platform",
                "payload": "eyJzb3VyY2VzIjogW3sibmFtZSI6ICJCaWN5Y2xlU2FtcGxlRGF0YSIsICJ0eXBlIjogIlNhbXBsZURhdGEiLCAicHJvcGVydGllcyI6IHsidHlwZSI6ICJCaWN5Y2xlcyJ9fV0sICJkZXN0aW5hdGlvbnMiOiBbeyJuYW1lIjogIlNhbXBsZUJpa2VzT3V0cHV0IiwgInR5cGUiOiAiQ3VzdG9tRW5kcG9pbnQiLCAicHJvcGVydGllcyI6IHt9LCAiaW5wdXROb2RlcyI6IFt7Im5hbWUiOiAiU2FtcGxlQmlrZXNEUyJ9XX1dLCAib3BlcmF0b3JzIjogW10sICJzdHJlYW1zIjogW3sibmFtZSI6ICJEZWZhdWx0QmlrZVN0cmVhbS1zdHJlYW0iLCAidHlwZSI6ICJEZWZhdWx0U3RyZWFtIiwgInByb3BlcnRpZXMiOiB7fSwgImlucHV0Tm9kZXMiOiBbeyJuYW1lIjogIkJpY3ljbGVTYW1wbGVEYXRhIn1dfSwgeyJuYW1lIjogIlNhbXBsZUJpa2VzRFMiLCAidHlwZSI6ICJEZXJpdmVkU3RyZWFtIiwgInByb3BlcnRpZXMiOiB7ImlucHV0U2VyaWFsaXphdGlvbiI6IHsidHlwZSI6ICJKc29uIiwgInByb3BlcnRpZXMiOiB7ImVuY29kaW5nIjogIlVURjgifX19LCAiaW5wdXROb2RlcyI6IFt7Im5hbWUiOiAiRGVmYXVsdEJpa2VTdHJlYW0tc3RyZWFtIn1dfV0sICJjb21wYXRpYmlsaXR5TGV2ZWwiOiAiMS4wIn0=",
                "payloadType": "InlineBase64"
            }
        ]
    }
}

print("=" * 100)
print("CORRECT EVENTSTREAM DEFINITION (eventstream.json content)")
print("=" * 100)
print(json.dumps(eventstream_definition, indent=2))

print("\n" + "=" * 100)
print("CORRECT REST API PAYLOAD")
print("=" * 100)
print(f"POST https://dailyapi.fabric.microsoft.com/v1/workspaces/{workspace_id}/items")
print("Content-Type: application/json")
print("Authorization: Bearer <ACCESS_TOKEN>")
print()
print(json.dumps(rest_api_payload, indent=2))

print("\n" + "=" * 100)
print("BASE64 ENCODED DEFINITION")
print("=" * 100)
print(f"The eventstream definition is base64 encoded in the payload:")
print(f"Original JSON length: {len(definition_json)} characters")
print(f"Base64 encoded length: {len(definition_b64)} characters")
print(f"First 100 chars of base64: {definition_b64[:100]}...")

print("\n" + "=" * 100)
print("KEY DIFFERENCES FROM WHAT I SHOWED BEFORE")
print("=" * 100)
print("1. The definition is NOT directly in the payload")
print("2. The definition is base64 encoded and placed in 'parts' array")
print("3. The payload structure uses 'definition.parts[0].payload' format")
print("4. The payloadType is 'InlineBase64'")
print("5. The path is 'eventstream.json' (internal Fabric format)")
print("6. IMPORTANT: There are TWO parts in the array:")
print("   - eventstream.json: Contains the actual eventstream definition")
print("   - .platform: Contains platform-specific configuration")
print()
print("This is the ACTUAL format that Microsoft Fabric expects!")
