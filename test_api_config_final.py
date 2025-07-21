#!/usr/bin/env python3
"""
Test script to verify the Fabric API configuration changes
"""

import os
import sys

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_api_configuration():
    """Test the API configuration functionality."""
    print("🧪 Testing Fabric API Configuration")
    print("=" * 50)
    
    try:
        from fabric_rti_mcp.eventstream.eventstream_service import (
            get_fabric_api_base,
            set_fabric_api_base,
            reset_fabric_api_base,
            get_eventstream_connection
        )
        
        # Test 1: Default configuration
        print("📋 Test 1: Default API Base URL")
        default_url = get_fabric_api_base()
        print(f"   Default URL: {default_url}")
        assert default_url == "https://api.fabric.microsoft.com/v1"
        print("   ✅ Default URL correct")
        
        # Test 2: Set custom URL
        print("\n📋 Test 2: Set Custom API Base URL")
        custom_url = "https://custom.fabric.api.com/v1"
        result = set_fabric_api_base(custom_url)
        print(f"   Set URL to: {result}")
        current_url = get_fabric_api_base()
        print(f"   Current URL: {current_url}")
        assert current_url == custom_url
        print("   ✅ Custom URL set correctly")
        
        # Test 3: Environment variable override
        print("\n📋 Test 3: Environment Variable Override")
        os.environ["FABRIC_API_BASE_URL"] = "https://env.fabric.api.com/v1"
        reset_result = reset_fabric_api_base()
        print(f"   Reset result: {reset_result}")
        env_url = get_fabric_api_base()
        print(f"   URL from env: {env_url}")
        assert env_url == "https://env.fabric.api.com/v1"
        print("   ✅ Environment variable respected")
        
        # Test 4: Connection creation
        print("\n📋 Test 4: Connection Creation")
        connection = get_eventstream_connection()
        print(f"   Connection API base: {connection.api_base_url}")
        assert connection.api_base_url == "https://env.fabric.api.com/v1"
        print("   ✅ Connection uses correct API base")
        
        # Test 5: Dynamic URL change
        print("\n📋 Test 5: Dynamic URL Change")
        set_fabric_api_base("https://dynamic.fabric.api.com/v1")
        new_connection = get_eventstream_connection()
        print(f"   New connection API base: {new_connection.api_base_url}")
        assert new_connection.api_base_url == "https://dynamic.fabric.api.com/v1"
        print("   ✅ Connection adapts to URL changes")
        
        # Cleanup
        del os.environ["FABRIC_API_BASE_URL"]
        reset_fabric_api_base()
        
        print("\n🎉 All tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_api_configuration()
    sys.exit(0 if success else 1)
