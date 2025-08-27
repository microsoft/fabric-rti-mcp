#!/usr/bin/env python3
"""
Simple test script for the Data Activator functionality.
Run this script to test the activator service directly without going through MCP.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to Python path so we can import our modules
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from fabric_rti_mcp.activator.activator_service import ActivatorService


async def test_data_activator():
    """Test the Data Activator creation functionality."""
    
    print("🚀 Starting Data Activator Test")
    print("=" * 50)
    
    # Create the service instance
    service = ActivatorService()
    
    # Test parameters - using the working configuration
    test_params = {
        "alert_name": "Direct Python Test Alert",
        "cluster_uri": "https://trd-g5bqmk5yh7guhpjwmz.z9.kusto.fabric.microsoft.com",
        "kql_query": "fdg | take 10", 
        "notification_recipients": ["test@example.com"],
        "workspace_id": "724adb3c-4be2-4655-b9bd-dd6c189a4696",
        "frequency_minutes": 60,
        "database": "eventhouseravit",
        "description": "Test alert created via direct Python script"
    }
    
    print("📋 Test Parameters:")
    for key, value in test_params.items():
        print(f"   {key}: {value}")
    print()
    
    try:
        print("🔄 Calling create_kql_alert...")
        result = await service.create_kql_alert(**test_params)
        
        print("✅ SUCCESS!")
        print("📄 Result:")
        print("-" * 30)
        
        # Pretty print the result
        if isinstance(result, dict):
            for key, value in result.items():
                if key == "next_steps" and isinstance(value, list):
                    print(f"   {key}:")
                    for step in value:
                        print(f"     - {step}")
                else:
                    print(f"   {key}: {value}")
        else:
            print(f"   {result}")
            
    except Exception as e:
        print("❌ ERROR!")
        print(f"   Exception Type: {type(e).__name__}")
        print(f"   Error Message: {str(e)}")
        
        # Print detailed traceback for debugging
        import traceback
        print("\n🔍 Detailed Traceback:")
        print("-" * 30)
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("Test completed.")


async def test_list_workspaces():
    """Test listing accessible workspaces."""
    
    print("\n🏢 Testing Workspace Listing")
    print("-" * 30)
    
    service = ActivatorService()
    
    try:
        workspaces = await service.list_workspaces()
        print(f"✅ Found {len(workspaces)} workspaces:")
        
        for workspace in workspaces:
            print(f"   - {workspace.get('displayName', 'No Name')} ({workspace.get('id', 'No ID')})")
            
    except Exception as e:
        print(f"❌ Error listing workspaces: {e}")


async def main():
    """Main test function."""
    
    print("🧪 Data Activator Direct Test Script")
    print("=" * 60)
    
    # Test 1: List workspaces (simpler test first)
    await test_list_workspaces()
    
    # Test 2: Create Data Activator alert
    await test_data_activator()
    
    print("\n🏁 All tests completed!")


if __name__ == "__main__":
    # Check if we're in the right directory
    if not os.path.exists("fabric_rti_mcp"):
        print("❌ Error: Please run this script from the fabric-rti-mcp project root directory.")
        print("   Current directory:", os.getcwd())
        print("   Expected to find: fabric_rti_mcp/ directory")
        sys.exit(1)
    
    # Run the async tests
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user (Ctrl+C)")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
