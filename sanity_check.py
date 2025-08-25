#!/usr/bin/env python3
"""
Sanity check script for Fabric RTI MCP Server
Tests key components and functionality
"""

import sys
import os
from typing import List

def test_imports() -> bool:
    """Test that all required modules can be imported"""
    print("🧪 Testing imports...")
    try:
        import fabric_rti_mcp
        print(f"✅ fabric_rti_mcp version: {fabric_rti_mcp.__version__}")
        
        from fabric_rti_mcp.server import mcp
        print("✅ Server module imported")
        
        from fabric_rti_mcp.kusto import kusto_service, kusto_tools
        print("✅ Kusto modules imported")
        
        from fabric_rti_mcp.eventstream import eventstream_service, eventstream_tools
        print("✅ Eventstream modules imported")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_mcp_tools() -> bool:
    """Test MCP tools registration"""
    print("\n🔧 Testing MCP tools registration...")
    try:
        from fabric_rti_mcp.server import mcp
        
        # Get list of tools
        tools = mcp.list_tools()
        print(f"✅ Found {len(tools)} registered tools:")
        
        kusto_tools = []
        eventstream_basic_tools = []
        eventstream_builder_tools = []
        
        for tool in tools:
            print(f"  - {tool.name}")
            if 'kusto' in tool.name:
                kusto_tools.append(tool.name)
            elif 'eventstream' in tool.name:
                if any(keyword in tool.name for keyword in ['add_', 'start_', 'validate_', 'create_from_', 'clear_', 'get_current_', 'list_available_']):
                    eventstream_builder_tools.append(tool.name)
                else:
                    eventstream_basic_tools.append(tool.name)
        
        print(f"\n📊 Kusto tools ({len(kusto_tools)}): {kusto_tools}")
        print(f"🌊 Basic Eventstream tools ({len(eventstream_basic_tools)}): {eventstream_basic_tools}")
        print(f"🏗️ Builder Eventstream tools ({len(eventstream_builder_tools)}): {eventstream_builder_tools}")
        
        return len(tools) > 0
    except Exception as e:
        print(f"❌ Tools test failed: {e}")
        return False

def test_builder_tools_detailed() -> bool:
    """Test builder tools in detail"""
    print("\n🏗️ Testing Builder Tools in Detail...")
    
    expected_builder_tools = [
        "eventstream_start_definition",
        "eventstream_get_current_definition", 
        "eventstream_clear_definition",
        "eventstream_add_sample_data_source",
        "eventstream_add_custom_endpoint_source",
        "eventstream_add_derived_stream",
        "eventstream_add_derived_stream",
        "eventstream_add_eventhouse_destination",
        "eventstream_add_custom_endpoint_destination",
        "eventstream_validate_definition",
        "eventstream_create_from_definition",
        "eventstream_list_available_components"
    ]
    
    try:
        from fabric_rti_mcp.server import mcp
        tools = mcp.list_tools()
        available_tools = [t.name for t in tools]
        
        print(f"Expected {len(expected_builder_tools)} builder tools:")
        
        missing_tools = []
        present_tools = []
        
        for tool in expected_builder_tools:
            if tool in available_tools:
                print(f"  ✅ {tool}")
                present_tools.append(tool)
            else:
                print(f"  ❌ {tool} (MISSING)")
                missing_tools.append(tool)
        
        print(f"\n📈 Builder Tools Summary:")
        print(f"  Present: {len(present_tools)}/{len(expected_builder_tools)}")
        print(f"  Missing: {len(missing_tools)}")
        
        if missing_tools:
            print(f"  Missing tools: {missing_tools}")
        
        return len(missing_tools) == 0
        
    except Exception as e:
        print(f"❌ Builder tools test failed: {e}")
        return False

def test_builder_functionality() -> bool:
    """Test basic builder functionality"""
    print("\n🧪 Testing Builder Functionality...")
    
    try:
        from fabric_rti_mcp.eventstream.eventstream_builder_service import (
            eventstream_start_definition,
            eventstream_get_current_definition,
            eventstream_list_available_components
        )
        
        # Test 1: Start a definition
        print("  Testing eventstream_start_definition...")
        result = eventstream_start_definition("test-stream", "Test eventstream for sanity check")
        if 'session_id' in result and 'status' in result:
            print(f"    ✅ Started session: {result['session_id']}")
            session_id = result['session_id']
        else:
            print("    ❌ Failed to start session")
            return False
        
        # Test 2: Get current definition
        print("  Testing eventstream_get_current_definition...")
        current_def = eventstream_get_current_definition(session_id)
        if 'definition' in current_def:
            print("    ✅ Retrieved current definition")
        else:
            print("    ❌ Failed to get current definition")
            return False
            
        # Test 3: List available components
        print("  Testing eventstream_list_available_components...")
        components = eventstream_list_available_components()
        if isinstance(components, dict):
            print("    ✅ Listed available components")
        else:
            print("    ❌ Failed to list components")
            return False
            
        print("  🎉 All basic builder functionality tests passed!")
        return True
        
    except Exception as e:
        print(f"  ❌ Builder functionality test failed: {e}")
        return False

def test_environment() -> bool:
    """Test environment variables"""
    print("\n🌍 Testing environment variables...")
    
    env_vars = {
        'KUSTO_SERVICE_URI': os.getenv('KUSTO_SERVICE_URI'),
        'KUSTO_DATABASE': os.getenv('KUSTO_DATABASE'), 
        'FABRIC_API_BASE_URL': os.getenv('FABRIC_API_BASE_URL')
    }
    
    for name, value in env_vars.items():
        if value:
            print(f"✅ {name}: {value}")
        else:
            print(f"⚠️  {name}: Not set")
    
    return True

def main():
    """Run all sanity checks"""
    print("🚀 Fabric RTI MCP Server Sanity Check with Builder Tools")
    print("=" * 65)
    
    tests = [
        ("Imports", test_imports),
        ("MCP Tools Registration", test_mcp_tools),
        ("Builder Tools Detail", test_builder_tools_detailed),
        ("Builder Functionality", test_builder_functionality),
        ("Environment Variables", test_environment)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} test crashed: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 65)
    print("📋 DETAILED SANITY CHECK REPORT")
    print("=" * 65)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status:<8} {name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 65)
    if all_passed:
        print("🎉 ALL SANITY CHECKS PASSED!")
        print("   MCP server with full builder tools is ready for use.")
        print("   You can now:")
        print("   - Use all 12 builder tools in VS Code Copilot Chat")
        print("   - Build eventstreams step-by-step")
        print("   - Query Kusto databases")
        print("   - Create and manage Fabric eventstreams")
    else:
        print("⚠️  SOME CHECKS FAILED!")
        print("   Review the detailed output above to identify issues.")
        print("   The MCP server may not function correctly.")
    
    print("=" * 65)
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
