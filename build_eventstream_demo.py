#!/usr/bin/env python3
"""
Step-by-step eventstream builder demo
Creates TestMCPSampleBikes22 with bicycle sample data and derived stream
"""

from fabric_rti_mcp.eventstream.eventstream_builder_service import (
    eventstream_add_derived_stream,
    eventstream_add_sample_data_source,
    eventstream_create_from_definition,
    eventstream_get_current_definition,
    eventstream_list_available_components,
    eventstream_start_definition,
    eventstream_validate_definition,
)


def build_eventstream_step_by_step():
    """Build the TestMCPSampleBikes22 eventstream step by step"""

    print("🚀 Building EventStream: TestMCPSampleBikes22")
    print("=" * 60)

    # Configuration
    eventstream_name = "TestMCPSampleBikes22"
    workspace_id = "bff1ab3a-47f0-4b85-9226-509c4cfdda10"
    description = "EventStream with bicycle sample data and derived stream"

    try:
        # STEP 1: Start the eventstream definition
        print("📋 STEP 1: Starting eventstream definition...")
        session_result = eventstream_start_definition(name=eventstream_name, description=description)
        session_id = session_result["session_id"]
        print(f"✅ Started session: {session_id}")
        print(f"   Name: {session_result['name']}")
        print(f"   Status: {session_result['status']}")
        print()

        # STEP 2: Add bicycle sample data source
        print("🚲 STEP 2: Adding bicycle sample data source...")
        source_result = eventstream_add_sample_data_source(
            session_id=session_id, source_name="BicycleDataSource", sample_type="Bicycles"
        )
        print(f"✅ Added data source: {source_result['source_added']}")
        print(f"   Type: {source_result['source_type']}")
        print(f"   Total sources: {source_result['sources_count']}")
        print()

        # STEP 3: Default stream is automatically created
        print("🌊 STEP 3: Default stream automatically created with definition...")
        print(f"✅ Default stream available for derived streams")
        print(f"   Total streams: 1 (DefaultStream)")
        print()

        # STEP 4: Add derived stream "SampleBikesDS"
        print("🔄 STEP 4: Adding derived stream 'SampleBikesDS'...")
        derived_stream_result = eventstream_add_derived_stream(
            session_id=session_id,
            stream_name="SampleBikesDS",
            source_stream=f"{eventstream_name}-stream",
            transformation_query="| where isnotempty(BikeId) | extend ProcessedAt = now()",
        )
        print(f"✅ Added derived stream: {derived_stream_result['stream_added']}")
        print(f"   Source stream: {derived_stream_result['source_stream']}")
        print(f"   Total streams: {derived_stream_result['streams_count']}")
        print()

        # STEP 5: Get current definition to review
        print("📄 STEP 5: Reviewing current definition...")
        current_def = eventstream_get_current_definition(session_id)
        print(f"✅ Current definition status: {current_def['status']}")
        print(f"   Sources: {len(current_def['definition']['sources'])}")
        print(f"   Streams: {len(current_def['definition']['streams'])}")
        print(f"   Last updated: {current_def['last_updated']}")
        print()

        # STEP 6: Validate the definition
        print("🔍 STEP 6: Validating eventstream definition...")
        validation_result = eventstream_validate_definition(session_id)
        print(f"✅ Validation status: {validation_result['status']}")
        if validation_result["status"] == "valid":
            print("   All components are properly configured")
            print("   Ready for creation!")
        else:
            print(f"   Issues found: {validation_result.get('issues', [])}")
        print()

        # STEP 7: Create the eventstream (if validation passed)
        if validation_result["status"] == "valid":
            print("🎯 STEP 7: Creating eventstream in Fabric workspace...")
            creation_result = eventstream_create_from_definition(session_id=session_id, workspace_id=workspace_id)
            print(f"✅ Creation status: {creation_result['status']}")
            if "item_id" in creation_result:
                print(f"   Item ID: {creation_result['item_id']}")
            if "message" in creation_result:
                print(f"   Message: {creation_result['message']}")
        else:
            print("❌ STEP 7: Skipping creation due to validation issues")

        print()
        print("🎉 EVENTSTREAM BUILD COMPLETE!")
        print("=" * 60)
        print(f"EventStream: {eventstream_name}")
        print(f"Workspace: {workspace_id}")
        print(f"Data Source: Bicycle sample data")
        print(f"Default Stream: {eventstream_name}-stream")
        print(f"Derived Stream: SampleBikesDS")
        print("=" * 60)

        return session_id

    except Exception as e:
        print(f"❌ Error during eventstream building: {e}")
        import traceback

        traceback.print_exc()
        return None


if __name__ == "__main__":
    build_eventstream_step_by_step()
