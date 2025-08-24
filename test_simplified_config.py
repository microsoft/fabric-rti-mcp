#!/usr/bin/env python3
"""
Test script to verify the simplified environment-only API configuration
"""

import os
import sys

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_environment_only_config():
    """Test the simplified environment-only configuration."""
    print("🧪 Testing Simplified Environment-Only Configuration")
    print("=" * 60)
    
    try:
        from fabric_rti_mcp.eventstream.eventstream_service import (
            get_fabric_api_base,
            get_eventstream_connection
        )
        
        # Test 1: Default configuration
        print("📋 Test 1: Default API Base URL")
        default_url = get_fabric_api_base()
        print(f"   Default URL: {default_url}")
        assert default_url == "https://api.fabric.microsoft.com/v1"
        print("   ✅ Default URL correct")
        
        # Test 2: Environment variable override
        print("\n📋 Test 2: Environment Variable Override")
        os.environ["FABRIC_API_BASE_URL"] = "https://custom.fabric.api.com/v1"
        
        # Need to reimport to pick up the new environment variable
        import importlib
        import fabric_rti_mcp.eventstream.eventstream_service
        importlib.reload(fabric_rti_mcp.eventstream.eventstream_service)
        from fabric_rti_mcp.eventstream.eventstream_service import (
            get_fabric_api_base,
            get_eventstream_connection
        )
        
        env_url = get_fabric_api_base()
        print(f"   URL from env: {env_url}")
        assert env_url == "https://custom.fabric.api.com/v1"
        print("   ✅ Environment variable respected")
        
        # Test 3: Connection creation
        print("\n📋 Test 3: Connection Creation")
        connection = get_eventstream_connection()
        print(f"   Connection API base: {connection.api_base_url}")
        assert connection.api_base_url == "https://custom.fabric.api.com/v1"
        print("   ✅ Connection uses correct API base")
        
        # Cleanup
        del os.environ["FABRIC_API_BASE_URL"]
        
        print("\n🎉 All tests passed!")
        print("📋 Configuration is purely environment-based!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_environment_only_config()
    sys.exit(0 if success else 1)
