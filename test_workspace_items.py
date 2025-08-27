#!/usr/bin/env python3

import asyncio
from fabric_rti_mcp.activator.activator_service import ActivatorService

async def test_workspace_items():
    service = ActivatorService()
    
    try:
        # Try to list items in the bug bash workspace
        workspace_id = '3f3142b4-e29e-4e7f-91ed-333dcbe3cc6e'
        items = await service.list_activators(workspace_id)
        print(f'Items in workspace {workspace_id}:')
        for item in items:
            item_id = item.get("id", "N/A")
            item_name = item.get("displayName", item.get("name", "N/A"))
            item_type = item.get("type", "N/A")
            print(f'  - {item_id}: {item_name} ({item_type})')
    except Exception as e:
        print(f'Error listing workspace items: {str(e)}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_workspace_items())
