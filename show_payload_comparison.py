#!/usr/bin/env python3
"""
Display the REST API payload and eventstream definition comparison
"""

import json
import base64

# This is the FIXED definition from our eventstream builder (after fixes)
fixed_definition = {
    "sources": [
        {
            "name": "BicycleSampleSource",
            "type": "SampleData",
            "properties": {
                "sampleType": "Bicycles"
            }
        }
    ],
    "destinations": [
        {
            "name": "MCPEventhouseDestination",
            "type": "Eventhouse",
            "properties": {
                "workspaceId": "bff1ab3a-47f0-4b85-9226-509c4cfdda10",
                "itemId": "87654321-4321-4321-4321-210987654321",
                "databaseName": "MCPEventhouse",
                "tableName": "BikesData",
                "dataIngestionMode": "ProcessedIngestion",
                "encoding": "UTF8"
            }
            # ✅ FIXED: Removed inputNodes from destinations
        }
    ],
    "operators": [],
    "streams": [
        {
            "name": "BicycleDataStream",
            "type": "DefaultStream",
            "properties": {},  # ✅ FIXED: Added empty properties object
            "inputNodes": [     # ✅ FIXED: Changed to object format
                {"name": "BicycleSampleSource"}
            ]
        }
    ],
    "compatibilityLevel": "1.0"
}

# This is the working format from an existing eventstream (decoded)
working_definition = {
    "sources": [
        {
            "id": "7cdfd6cd-d98d-43da-8d88-ae53a189f04f",
            "name": "OpportunitySource-Json",
            "type": "CustomEndpoint",
            "properties": {}
        }
    ],
    "destinations": [],
    "streams": [
        {
            "id": "86981105-b0e2-4d3e-bbc9-c6a82996ab52",
            "name": "SimpleJsonOpportunityStream-stream",
            "type": "DefaultStream",
            "properties": {},
            "inputNodes": [
                {
                    "name": "OpportunitySource-Json"
                }
            ]
        }
    ],
    "operators": [],
    "compatibilityLevel": "1.0"
}

print("🔍 EVENTSTREAM DEFINITION COMPARISON")
print("=" * 80)

print("\n📋 FIXED DEFINITION (after applying fixes):")
print("=" * 50)
print(json.dumps(fixed_definition, indent=2))

print("\n📋 WORKING DEFINITION (from existing eventstream):")
print("=" * 50)
print(json.dumps(working_definition, indent=2))

print("\n🔧 FIXES APPLIED:")
print("=" * 50)
print("✅ FIXED: Added empty 'properties' objects to streams")
print("✅ FIXED: Converted inputNodes from strings to objects with 'name' property")
print("✅ FIXED: Removed inputNodes from destinations (connections handled by streams)")
print("\n🔧 REMAINING ISSUES:")
print("=" * 50)
print("❌ STILL MISSING: 'id' fields for sources and streams (UUIDs)")
print("❌ STILL NEEDED: Connection mechanism from streams to destinations")

print("\n🚀 MICROSOFT FABRIC REST API PAYLOAD:")
print("=" * 80)
print("URL: POST https://api.fabric.microsoft.com/v1/workspaces/{workspaceId}/items")
print("Headers:")
print("  Content-Type: application/json")
print("  Authorization: Bearer {access_token}")
print("\nBody:")

# The payload that would be sent to Fabric API
fabric_payload = {
    "displayName": "BicycleDataFlow",
    "description": "Eventstream that takes bicycle sample data and stores it in MCPEventhouse database",
    "definition": {
        "parts": [
            {
                "path": "eventstream.json",
                "payload": base64.b64encode(json.dumps(fixed_definition).encode()).decode(),
                "payloadType": "InlineBase64"
            },
            {
                "path": "eventstreamProperties.json", 
                "payload": base64.b64encode(json.dumps({
                    "retentionTimeInDays": 1,
                    "eventThroughputLevel": "Low"
                }).encode()).decode(),
                "payloadType": "InlineBase64"
            },
            {
                "path": ".platform",
                "payload": base64.b64encode(json.dumps({
                    "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
                    "metadata": {
                        "type": "Eventstream",
                        "displayName": "BicycleDataFlow"
                    },
                    "config": {
                        "version": "2.0",
                        "logicalId": "00000000-0000-0000-0000-000000000000"
                    }
                }).encode()).decode(),
                "payloadType": "InlineBase64"
            }
        ]
    }
}

print(json.dumps(fabric_payload, indent=2))

print("\n🎯 FIXES NEEDED:")
print("=" * 80)
print("To make the eventstream builder work correctly, we need to:")
print("1. Add unique 'id' fields (UUIDs) to all sources and streams")
print("2. Add empty 'properties' objects to streams")
print("3. Convert inputNodes from string arrays to object arrays with 'name' property")
print("4. Move inputNodes from destinations to streams or handle connection properly")
print("5. Ensure the base64 encoding matches Fabric's expectations")
