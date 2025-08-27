#!/usr/bin/env python3
"""
Test the full end-to-end workflow for anomaly detection alerts.
"""

import asyncio
from fabric_rti_mcp.activator.activator_service import ActivatorService

async def test_full_workflow():
    print('=== TESTING FULL ANOMALY DETECTION WORKFLOW ===')
    
    # For this test, we'll use the help.kusto.windows.net public cluster
    cluster_uri = 'https://help.kusto.windows.net'
    database = 'Samples'
    
    print(f'Using cluster: {cluster_uri}')
    print(f'Using database: {database}')
    
    # Step 2: Create an anomaly detection KQL query
    anomaly_query = '''
    StormEvents
    | where StartTime >= ago(30d)
    | summarize EventCount = count() by bin(StartTime, 1d), State
    | extend AvgCount = avg(EventCount) over (partition by State)
    | extend StdDev = stdev(EventCount) over (partition by State)
    | extend Threshold = AvgCount + (2 * StdDev)
    | where EventCount > Threshold
    | project StartTime, State, EventCount, Threshold, AnomalyScore = (EventCount - AvgCount) / StdDev
    | order by AnomalyScore desc
    '''
    
    print(f'Generated anomaly detection query: {anomaly_query[:100]}...')
    
    # Step 3: Create Data Activator alert
    activator_service = ActivatorService()
    
    # Get workspaces
    try:
        workspaces = await activator_service.list_workspaces()
        print(f'Available workspaces: {len(workspaces)}')
        
        if not workspaces:
            print('No workspaces available, cannot create alert')
            return
            
        workspace_id = workspaces[0]['id']
        print(f'Using workspace: {workspace_id}')
        
    except Exception as e:
        print(f'Error getting workspaces: {e}')
        # Use a mock workspace ID for testing
        workspace_id = 'mock-workspace-id-12345'
        print(f'Using mock workspace: {workspace_id}')
    
    # Step 4: Create the alert
    try:
        result = await activator_service.create_kql_alert(
            kql_query=anomaly_query,
            cluster_uri=cluster_uri,
            workspace_id=workspace_id,
            alert_name='Daily Anomaly Detection Alert',
            notification_recipients=['radennis@microsoft.com'],
            database=database,
            description='Automated alert that detects anomalies in storm events data and notifies when unusual patterns are found'
        )
        
        print('=== ALERT CREATION SUCCESS ===')
        print(f'Alert ID: {result.get("alert_id")}')
        print(f'Message: {result.get("message")}')
        print(f'Workspace ID: {result.get("workspace_id")}')
        print(f'Next steps: {result.get("next_steps")}')
        
    except Exception as e:
        print(f'=== ALERT CREATION FAILED ===')
        print(f'Error: {str(e)}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_full_workflow())
