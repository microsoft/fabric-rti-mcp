"""
Fixed version of eventstream creation to match Fabric API requirements
"""

import base64
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

def create_fixed_eventstream_payload(
    eventstream_name: str,
    definition: Dict[str, Any],
    description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create properly formatted eventstream payload with all three required parts.
    
    :param eventstream_name: Name of the eventstream
    :param definition: Eventstream definition dictionary
    :param description: Optional description
    :return: Complete API payload
    """
    
    # 1. Prepare eventstream.json (main definition)
    definition_json = json.dumps(definition)
    definition_b64 = base64.b64encode(definition_json.encode("utf-8")).decode("utf-8")
    
    # 2. Prepare eventstreamProperties.json (retention and throughput settings)
    properties = {
        "retentionTimeInDays": 1,
        "eventThroughputLevel": "Low"
    }
    properties_json = json.dumps(properties)
    properties_b64 = base64.b64encode(properties_json.encode("utf-8")).decode("utf-8")
    
    # 3. Prepare .platform (metadata and config)
    platform_metadata = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {
            "type": "Eventstream",
            "displayName": eventstream_name,
            "description": description or ""
        },
        "config": {
            "version": "2.0",
            "logicalId": "00000000-0000-0000-0000-000000000000"
        }
    }
    platform_json = json.dumps(platform_metadata)
    platform_b64 = base64.b64encode(platform_json.encode("utf-8")).decode("utf-8")
    
    # Create the complete payload
    payload = {
        "displayName": eventstream_name,
        "type": "Eventstream",
        "description": description or "",
        "definition": {
            "parts": [
                {
                    "path": "eventstream.json",
                    "payload": definition_b64,
                    "payloadType": "InlineBase64"
                },
                {
                    "path": "eventstreamProperties.json",
                    "payload": properties_b64,
                    "payloadType": "InlineBase64"
                },
                {
                    "path": ".platform",
                    "payload": platform_b64,
                    "payloadType": "InlineBase64"
                }
            ]
        }
    }
    
    return payload


def create_test_bikes_definition() -> Dict[str, Any]:
    """
    Create the TestMCPSampleBikes22 eventstream definition.
    """
    
    # Generate UUIDs for all components
    source_id = str(uuid.uuid4())
    default_stream_id = str(uuid.uuid4())
    derived_stream_id = str(uuid.uuid4())
    
    definition = {
        "sources": [
            {
                "id": source_id,
                "name": "BicycleDataSource",
                "type": "SampleData",
                "properties": {
                    "type": "Bicycles"
                }
            }
        ],
        "streams": [
            {
                "id": default_stream_id,
                "name": "TestMCPSampleBikes22-stream",
                "type": "DefaultStream",
                "properties": {},
                "inputNodes": [
                    {
                        "name": "BicycleDataSource"
                    }
                ]
            },
            {
                "id": derived_stream_id,
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
                        "name": "TestMCPSampleBikes22-stream"
                    }
                ]
            }
        ],
        "destinations": [],
        "operators": [],
        "compatibilityLevel": "1.0"
    }
    
    return definition


# Test the fixed format
if __name__ == "__main__":
    definition = create_test_bikes_definition()
    payload = create_fixed_eventstream_payload(
        "TestMCPSampleBikes22",
        definition,
        "Eventstream with Bicycles sample data and derived stream SampleBikesDS"
    )
    
    print("=== FIXED PAYLOAD STRUCTURE ===")
    print(f"Parts count: {len(payload['definition']['parts'])}")
    for i, part in enumerate(payload['definition']['parts']):
        print(f"Part {i+1}: {part['path']}")
    
    print("\n=== DEFINITION STRUCTURE ===")
    print(json.dumps(definition, indent=2))
