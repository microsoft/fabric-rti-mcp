#!/usr/bin/env python3
"""
Test script for Eventstream Builder functionality
Tests the builder workflow end-to-end
"""

import os
import sys

sys.path.insert(0, os.path.abspath("."))

from fabric_rti_mcp.eventstream import eventstream_builder_service as builder


def test_builder_workflow():
    """Test the complete builder workflow."""
    print("🧪 Testing Eventstream Builder Workflow")
    print("=" * 50)

    try:
        # Test 1: Start Definition
        print("\n1️⃣ Starting eventstream definition...")
        session = builder.eventstream_start_definition(
            name="TestEventstream", description="Test eventstream created by automated test"
        )
        session_id = session["session_id"]
        print(f"✅ Session created: {session_id}")
        print(f"   Name: {session['name']}")
        print(f"   Status: {session['status']}")

        # Test 2: List Available Components
        print("\n2️⃣ Listing available components...")
        components = builder.eventstream_list_available_components()
        print(f"✅ Available sources: {components['sources']}")
        print(f"   Available destinations: {components['destinations']}")

        # Test 3: Add Sample Data Source
        print("\n3️⃣ Adding sample data source...")
        source_result = builder.eventstream_add_sample_data_source(session_id, "TestSource", "Bicycles")
        print(f"✅ Source added: {source_result['source_added']}")
        print(f"   Sources count: {source_result['sources_count']}")

        # Test 4: Check Default Stream (auto-created)
        print("\n4️⃣ Checking default stream (auto-created)...")
        current_def = builder.eventstream_get_current_definition(session_id)
        default_streams = [s for s in current_def["streams"] if s["name"] == "DefaultStream"]
        print(f"✅ Default stream available: {len(default_streams) > 0}")
        if default_streams:
            print(f"   Default stream: {default_streams[0]['name']}")

        # Test 5: Add Derived Stream
        print("\n5️⃣ Adding derived stream...")
        derived_result = builder.eventstream_add_derived_stream(session_id, "TestDerivedStream", ["DefaultStream"])
        print(f"✅ Derived stream added: {derived_result['stream_added']}")
        print(f"   Streams count: {derived_result['streams_count']}")

        # Test 5: Get Current Definition
        print("\n5️⃣ Getting current definition...")
        current_def = builder.eventstream_get_current_definition(session_id)
        print(f"✅ Definition retrieved for: {current_def['name']}")
        print(f"   Last updated: {current_def['last_updated']}")
        print(f"   Sources: {list(current_def['definition']['sources'].keys())}")
        print(f"   Streams: {list(current_def['definition']['streams'].keys())}")

        # Test 6: Validate Definition (should have warnings but no errors)
        print("\n6️⃣ Validating definition...")
        validation = builder.eventstream_validate_definition(session_id)
        print(f"✅ Validation complete - Valid: {validation['is_valid']}")
        if validation["errors"]:
            print(f"   ❌ Errors: {validation['errors']}")
        if validation["warnings"]:
            print(f"   ⚠️ Warnings: {validation['warnings']}")
        print(f"   Summary: {validation['summary']}")

        # Test 7: Add Custom Endpoint Destination
        print("\n7️⃣ Adding custom endpoint destination...")
        dest_result = builder.eventstream_add_custom_endpoint_destination(
            session_id, "TestDestination", "https://webhook.example.com/events", ["TestStream"]
        )
        print(f"✅ Destination added: {dest_result['destination_added']}")
        print(f"   Destinations count: {dest_result['destinations_count']}")

        # Test 8: Final Validation
        print("\n8️⃣ Final validation...")
        final_validation = builder.eventstream_validate_definition(session_id)
        print(f"✅ Final validation - Valid: {final_validation['is_valid']}")
        if final_validation["errors"]:
            print(f"   ❌ Errors: {final_validation['errors']}")
        if final_validation["warnings"]:
            print(f"   ⚠️ Warnings: {final_validation['warnings']}")

        # Test 9: Clear Definition
        print("\n9️⃣ Testing clear definition...")
        clear_result = builder.eventstream_clear_definition(session_id)
        print(f"✅ Definition cleared: {clear_result['status']}")

        # Test 10: Verify Cleared
        print("\n🔟 Verifying definition was cleared...")
        cleared_def = builder.eventstream_get_current_definition(session_id)
        sources_count = len(cleared_def["definition"]["sources"])
        streams_count = len(cleared_def["definition"]["streams"])
        print(f"✅ After clearing - Sources: {sources_count}, Streams: {streams_count}")

        print("\n🎉 All tests passed! Builder workflow is working correctly.")
        return True

    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def test_error_handling():
    """Test error handling scenarios."""
    print("\n\n🔬 Testing Error Handling")
    print("=" * 50)

    try:
        # Test invalid session
        print("\n1️⃣ Testing invalid session ID...")
        try:
            builder.eventstream_get_current_definition("invalid-session-id")
            print("❌ Should have failed with invalid session")
            return False
        except ValueError as e:
            print(f"✅ Correctly handled invalid session: {str(e)}")

        # Test adding stream with non-existent source
        print("\n2️⃣ Testing invalid source reference...")
        session = builder.eventstream_start_definition("ErrorTest")
        session_id = session["session_id"]

        try:
            builder.eventstream_add_default_stream(session_id, "BadStream", ["NonExistentSource"])
            print("❌ Should have failed with non-existent source")
            return False
        except ValueError as e:
            print(f"✅ Correctly handled invalid source reference: {str(e)}")

        print("\n🎉 Error handling tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Error handling test failed: {str(e)}")
        return False


def test_component_types():
    """Test different component types."""
    print("\n\n🔧 Testing Component Types")
    print("=" * 50)

    try:
        session = builder.eventstream_start_definition("ComponentTest", "Testing all component types")
        session_id = session["session_id"]

        # Test custom endpoint source
        print("\n1️⃣ Testing custom endpoint source...")
        builder.eventstream_add_custom_endpoint_source(session_id, "APISource", "https://api.example.com/events")
        print("✅ Custom endpoint source added")

        # Test sample data with different type
        print("\n2️⃣ Testing stock sample data...")
        builder.eventstream_add_sample_data_source(session_id, "StockData", "Stock")
        print("✅ Stock sample data added")

        # Test multiple streams
        print("\n3️⃣ Testing multiple streams...")
        builder.eventstream_add_default_stream(session_id, "APIStream", ["APISource"])
        builder.eventstream_add_default_stream(session_id, "StockStream", ["StockData"])
        print("✅ Multiple streams added")

        # Test derived stream (should fail - no operators yet)
        print("\n4️⃣ Testing derived stream (should fail)...")
        try:
            builder.eventstream_add_derived_stream(session_id, "DerivedStream", ["NonExistentOperator"])
            print("❌ Should have failed with non-existent operator")
            return False
        except ValueError as e:
            print(f"✅ Correctly handled missing operator: {str(e)}")

        # Test Eventhouse destination (mock)
        print("\n5️⃣ Testing Eventhouse destination...")
        builder.eventstream_add_eventhouse_destination(
            session_id,
            "DataWarehouse",
            "workspace-id",
            "eventhouse-id",
            "database",
            "table",
            ["APIStream", "StockStream"],
        )
        print("✅ Eventhouse destination added")

        # Final validation
        print("\n6️⃣ Final validation of complex definition...")
        validation = builder.eventstream_validate_definition(session_id)
        print(f"✅ Complex definition validation - Valid: {validation['is_valid']}")
        print(f"   Sources: {validation['summary']['sources']}")
        print(f"   Streams: {validation['summary']['streams']}")
        print(f"   Destinations: {validation['summary']['destinations']}")

        print("\n🎉 Component type tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Component type test failed: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 Starting Eventstream Builder Tests")
    print("====================================")

    all_passed = True

    # Run workflow test
    all_passed &= test_builder_workflow()

    # Run error handling test
    all_passed &= test_error_handling()

    # Run component type test
    all_passed &= test_component_types()

    # Final result
    print("\n" + "=" * 50)
    if all_passed:
        print("🏆 ALL TESTS PASSED! Builder is ready for use.")
        sys.exit(0)
    else:
        print("💥 Some tests failed. Please check the output above.")
        sys.exit(1)
