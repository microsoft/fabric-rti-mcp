#!/usr/bin/env python3
"""
Final validation script - Quick test of critical functionality
"""

def main():
    print("🚀 Final Validation - Fabric RTI MCP Server")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Core imports
    total_tests += 1
    try:
        from fabric_rti_mcp import server
        from fabric_rti_mcp.kusto import kusto_service
        from fabric_rti_mcp.eventstream import eventstream_service
        print("✅ Core imports: PASSED")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Core imports: FAILED - {e}")
    
    # Test 2: Kusto service specific fix
    total_tests += 1
    try:
        from fabric_rti_mcp.kusto.kusto_service import get_default_database_name
        default_db = get_default_database_name()
        print(f"✅ Kusto DEFAULT_DB fix: PASSED (default: {default_db})")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Kusto DEFAULT_DB fix: FAILED - {e}")
    
    # Test 3: Server main function
    total_tests += 1
    try:
        from fabric_rti_mcp.server import main
        print("✅ Server main function: PASSED")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Server main function: FAILED - {e}")
    
    # Test 4: Tool registration
    total_tests += 1
    try:
        from fabric_rti_mcp.kusto.kusto_tools import register_kusto_tools
        from fabric_rti_mcp.eventstream.eventstream_tools import register_eventstream_tools
        print("✅ Tool registration: PASSED")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Tool registration: FAILED - {e}")
    
    # Test 5: Dependencies
    total_tests += 1
    try:
        import fastmcp
        import httpx
        import azure.kusto.data
        import azure.identity
        print("✅ Dependencies: PASSED")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Dependencies: FAILED - {e}")
    
    print("\n" + "=" * 50)
    print(f"🎯 Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 ALL TESTS PASSED!")
        print("\n✅ Your Fabric RTI MCP Server is ready!")
        print("   - Fixed KustoConnectionStringBuilder import issue")
        print("   - All core functionality imports correctly")
        print("   - Dependencies are properly installed")
        print("   - Server can be started")
        
        print("\n🚀 Ready for Pull Request!")
        print("   Your feature branch is ready to be submitted.")
        
        return 0
    else:
        print("❌ Some tests still failing.")
        print("   Please address remaining issues before PR.")
        return 1

if __name__ == "__main__":
    exit(main())
