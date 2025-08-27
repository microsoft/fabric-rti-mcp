#!/usr/bin/env python3

import asyncio
from fabric_rti_mcp.activator.activator_service import ActivatorService

async def test_workspace():
    service = ActivatorService()
    
    try:
        workspaces = await service.list_workspaces()
        print('Available workspaces:')
        for ws in workspaces:
            ws_id = ws.get("id", "N/A")
            ws_name = ws.get("displayName", ws.get("name", "N/A"))
            print(f'  - {ws_id}: {ws_name}')
    except Exception as e:
        print(f'Error listing workspaces: {str(e)}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_workspace())
