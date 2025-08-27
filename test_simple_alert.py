#!/usr/bin/env python3
"""
Simple test script to create a Data Activator alert.
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fabric_rti_mcp.activator.activator_service import ActivatorService

async def test_create_alert():
    """Test creating a simple alert."""
    print("=== Testing Data Activator Alert Creation ===")
    
    # Initialize the service
    service = ActivatorService()
    
    try:
        # First, let's get available workspaces
        print("\n1. Getting available workspaces...")
        workspaces = await service.list_workspaces()
        print(f"Found {len(workspaces)} workspaces:")
        for ws in workspaces:
            print(f"  - {ws.get('displayName', ws.get('name', 'Unknown'))}: {ws.get('id')}")
        
        if not workspaces:
            print("No workspaces found. Cannot create alert.")
            return
        
        # Use the first workspace for testing
        workspace_id = workspaces[0]['id']
        workspace_name = workspaces[0].get('displayName', workspaces[0].get('name', 'Unknown'))
        print(f"\n2. Using workspace: {workspace_name} ({workspace_id})")
        
        # Test parameters
        alert_name = "Test Alert - Print 1"
        kql_query = "print 1"
        cluster_uri = "https://help.kusto.windows.net"  # Public demo cluster
        database = "Samples"  # Public demo database
        notification_recipients = ["radennis@microsoft.com"]
        
        print(f"\n3. Creating alert with parameters:")
        print(f"   Alert Name: {alert_name}")
        print(f"   KQL Query: {kql_query}")
        print(f"   Cluster: {cluster_uri}")
        print(f"   Database: {database}")
        print(f"   Recipients: {notification_recipients}")
        
        # Create the alert
        result = await service.create_kql_alert(
            kql_query=kql_query,
            cluster_uri=cluster_uri,
            workspace_id=workspace_id,
            alert_name=alert_name,
            notification_recipients=notification_recipients,
            database=database,
            description="Test alert for monitoring a simple KQL query"
        )
        
        print(f"\n4. ✅ SUCCESS! Alert created successfully!")
        print(f"   Alert ID: {result.get('alert_id')}")
        print(f"   Activator Item: {result.get('activator_item', {}).get('displayName')}")
        print(f"   Status: {result.get('status')}")
        print(f"   Message: {result.get('message')}")
        
        if 'next_steps' in result:
            print(f"\n   Next Steps:")
            for step in result['next_steps']:
                print(f"   - {step}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ ERROR: Failed to create alert")
        print(f"Error details: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(test_create_alert())
