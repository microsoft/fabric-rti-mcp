import json

# Generated definition
definition = {
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
            },
            "inputNodes": ["BicycleDataStream"]
        }
    ],
    "streams": [
        {
            "name": "BicycleDataStream",
            "type": "DefaultStream", 
            "inputNodes": ["BicycleSampleSource"]
        }
    ],
    "operators": [],
    "compatibilityLevel": "1.0"
}

print("GENERATED EVENTSTREAM DEFINITION:")
print(json.dumps(definition, indent=2))
