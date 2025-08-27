#!/usr/bin/env python3

import asyncio
import sys
from fabric_rti_mcp.activator.activator_service import ActivatorService

async def test_activator():
    service = ActivatorService()
    
    # Test creating a storm data alert
    try:
        result = await service.create_kql_alert(
            kql_query='StormEvents | where State == "TEXAS" and EventType == "Flood" | take 10',
            cluster_uri='https://help.kusto.windows.net',
            workspace_id='3f3142b4-e29e-4e7f-91ed-333dcbe3cc6e',  # Kusto-Reflex Bug Bash Workspace
            alert_name='Texas Flood Alert Test',
            notification_recipients=['test@example.com'],
            frequency_minutes=60,
            database='Samples',
            description='Test alert for Texas flood events'
        )
        print('SUCCESS: Alert created successfully!')
        print(f'Result: {result}')
    except Exception as e:
        print(f'Error: {str(e)}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_activator())
