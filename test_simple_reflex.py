#!/usr/bin/env python3

import asyncio
from fabric_rti_mcp.activator.fabric_connection import FabricConnection

async def test_simple_reflex_creation():
    connection = FabricConnection()
    
    try:
        # Try to create a simple Reflex without definition first
        workspace_id = '3f3142b4-e29e-4e7f-91ed-333dcbe3cc6e'
        result = await connection.create_reflex_with_definition(
            workspace_id=workspace_id,
            name='Test Reflex Simple',
            description='Simple test reflex without definition'
            # No reflex_definition provided
        )
        print('SUCCESS: Simple Reflex created successfully!')
        print(f'Result: {result}')
    except Exception as e:
        print(f'Error creating simple Reflex: {str(e)}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_simple_reflex_creation())
