#!/usr/bin/env python3
"""
Test script for Fabric API Base Configuration Tools
"""

import sys
import os

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_api_config():
    """Test the Fabric API configuration functions."""
    try:
        from fabric_rti_mcp.eventstream.eventstream_service import (
            get_fabric_api_base, 
            set_fabric_api_base, 
            reset_fabric_api_base
        )
        
        print('Testing Fabric API Base Configuration Tools:')
        print('=' * 50)
        
        # Test getting current API base
        current = get_fabric_api_base()
        print(f'Current API base: {current}')
        
        # Test setting a custom API base
        custom_url = 'https://custom.fabric.example.com/v1'
        new_base = set_fabric_api_base(custom_url)
        print(f'Set custom API base: {new_base}')
        
        # Verify it was set
        current_after_set = get_fabric_api_base()
        print(f'Current API base after set: {current_after_set}')
        
        # Test resetting to default
        reset_base = reset_fabric_api_base()
        print(f'Reset API base: {reset_base}')
        
        # Verify it was reset
        current_after_reset = get_fabric_api_base()
        print(f'Current API base after reset: {current_after_reset}')
        
        # Validate test results
        if current_after_set == custom_url and current_after_reset != custom_url:
            print('\n✓ All configuration tools work correctly!')
            return True
        else:
            print('\n✗ Configuration tools did not work as expected')
            return False
            
    except Exception as e:
        print(f'\n✗ Error testing configuration tools: {e}')
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_api_config()
    sys.exit(0 if success else 1)
