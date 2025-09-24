#!/usr/bin/env python3
"""
Quick sanity check for builder tools
"""


def quick_check():
    print("🔍 Quick Builder Tools Check")
    print("=" * 40)

    # Test imports
    try:
        from fabric_rti_mcp.server import mcp

        print("✅ Server imported")

        tools = mcp.list_tools()
        builder_tools = [
            t.name
            for t in tools
            if "eventstream" in t.name
            and any(k in t.name for k in ["add_", "start_", "validate_", "create_from_", "clear_"])
        ]

        print(f"✅ Found {len(tools)} total tools")
        print(f"✅ Found {len(builder_tools)} builder tools")

        expected_builders = [
            "eventstream_start_definition",
            "eventstream_add_sample_data_source",
            "eventstream_validate_definition",
            "eventstream_create_from_definition",
        ]

        print("\n🏗️ Key Builder Tools:")
        for tool in expected_builders:
            status = "✅" if tool in builder_tools else "❌"
            print(f"  {status} {tool}")

        # Test basic functionality
        print("\n🧪 Testing basic functionality:")
        from fabric_rti_mcp.eventstream.eventstream_builder_service import eventstream_start_definition

        result = eventstream_start_definition("test", "test description")
        if "session_id" in result:
            print("✅ Builder functionality works")
        else:
            print("❌ Builder functionality failed")

        print(f"\n🎉 Builder tools ready: {len(builder_tools)}/12 expected tools available")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    quick_check()
