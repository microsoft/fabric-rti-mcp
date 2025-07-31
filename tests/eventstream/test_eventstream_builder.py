"""
Test for Eventstream Builder - Phase 1 functionality
"""

from fabric_rti_mcp.eventstream.eventstream_builder_service import (
    EventstreamDefinitionBuilder,
    EventstreamBuilderService
)


def test_builder_initialization():
    """Test basic builder initialization."""
    builder = EventstreamDefinitionBuilder()
    
    assert builder.session_id is not None
    assert builder.metadata["session_id"] == builder.session_id
    assert builder.definition["compatibilityLevel"] == "1.0"
    assert len(builder.definition["sources"]) == 0
    assert len(builder.definition["destinations"]) == 0
    assert len(builder.definition["streams"]) == 0


def test_sample_data_source_creation():
    """Test creating a sample data source."""
    builder = EventstreamDefinitionBuilder()
    
    source_config = builder.create_sample_data_source("TestBikes", "Bicycles")
    
    assert source_config["name"] == "TestBikes"
    assert source_config["type"] == "SampleData"
    assert source_config["properties"]["sampleType"] == "Bicycles"


def test_eventhouse_destination_creation():
    """Test creating an Eventhouse destination."""
    builder = EventstreamDefinitionBuilder()
    
    dest_config = builder.create_eventhouse_destination(
        name="TestEventhouse",
        workspace_id="workspace-123",
        item_id="item-456",
        database_name="TestDB",
        table_name="TestTable",
        input_nodes=["TestStream"]
    )
    
    assert dest_config["name"] == "TestEventhouse"
    assert dest_config["type"] == "Eventhouse"
    assert dest_config["properties"]["workspaceId"] == "workspace-123"
    assert dest_config["properties"]["databaseName"] == "TestDB"
    assert dest_config["inputNodes"] == ["TestStream"]


def test_default_stream_creation():
    """Test creating a default stream."""
    builder = EventstreamDefinitionBuilder()
    
    stream_config = builder.create_default_stream("TestStream", ["TestSource"])
    
    assert stream_config["name"] == "TestStream"
    assert stream_config["type"] == "DefaultStream"
    assert stream_config["inputNodes"] == ["TestSource"]


def test_basic_validation():
    """Test basic validation of eventstream definition."""
    builder = EventstreamDefinitionBuilder()
    
    # Empty definition should have validation errors
    errors = builder.validate()
    assert len(errors) > 0
    assert "Eventstream name is required" in errors
    assert "At least one source is required" in errors
    
    # Add metadata and components
    builder.set_metadata("TestEventstream", "Test description")
    
    source_config = builder.create_sample_data_source("TestSource", "Bicycles")
    builder.add_source(source_config)
    
    stream_config = builder.create_default_stream("TestStream", ["TestSource"])
    builder.add_stream(stream_config)
    
    dest_config = builder.create_eventhouse_destination(
        "TestDest", "workspace-123", "item-456", "TestDB", "TestTable", ["TestStream"]
    )
    builder.add_destination(dest_config)
    
    # Now should validate successfully
    errors = builder.validate()
    assert len(errors) == 0


def test_service_session_management():
    """Test builder service session management."""
    service = EventstreamBuilderService()
    
    # Create a session
    session_id = service.create_session("TestEventstream", "Test description")
    assert session_id is not None
    
    # Get the session
    builder = service.get_session(session_id)
    assert builder is not None
    assert builder.metadata["name"] == "TestEventstream"
    
    # Clear the session
    success = service.clear_session(session_id)
    assert success is True
    
    # Session should still exist but be cleared
    builder = service.get_session(session_id)
    assert builder is not None
    assert len(builder.definition["sources"]) == 0
    
    # Remove the session
    success = service.remove_session(session_id)
    assert success is True
    
    # Session should no longer exist
    builder = service.get_session(session_id)
    assert builder is None


def test_bicycle_to_eventhouse_workflow():
    """Test the main Phase 1 workflow: Bicycle sample → Eventhouse."""
    builder = EventstreamDefinitionBuilder()
    
    # 1. Set metadata
    builder.set_metadata("BicycleAnalytics", "Sample bicycle data to Eventhouse")
    
    # 2. Add bicycle sample source
    source_config = builder.create_sample_data_source("BicycleSource", "Bicycles")
    builder.add_source(source_config)
    
    # 3. Add default stream
    stream_config = builder.create_default_stream("BicycleStream", ["BicycleSource"])
    builder.add_stream(stream_config)
    
    # 4. Add Eventhouse destination
    dest_config = builder.create_eventhouse_destination(
        name="AnalyticsDB",
        workspace_id="1fe73fdf-9574-47fe-9b23-cb0b6d8d74b1",
        item_id="ad39bea2-f4ba-4cb6-adfa-598dd1ccb594", 
        database_name="RoomSensorsEventhouse",
        table_name="BicycleData",
        input_nodes=["BicycleStream"]
    )
    builder.add_destination(dest_config)
    
    # 5. Validate
    errors = builder.validate()
    assert len(errors) == 0, f"Validation errors: {errors}"
    
    # 6. Check definition structure
    definition = builder.get_definition()
    assert definition["metadata"]["name"] == "BicycleAnalytics"
    assert len(definition["definition"]["sources"]) == 1
    assert len(definition["definition"]["streams"]) == 1
    assert len(definition["definition"]["destinations"]) == 1
    
    # Verify the flow connections
    assert definition["definition"]["sources"][0]["name"] == "BicycleSource"
    assert definition["definition"]["streams"][0]["inputNodes"] == ["BicycleSource"]
    assert definition["definition"]["destinations"][0]["inputNodes"] == ["BicycleStream"]


if __name__ == "__main__":
    # Run basic tests
    test_builder_initialization()
    test_sample_data_source_creation()
    test_eventhouse_destination_creation()
    test_default_stream_creation()
    test_basic_validation()
    test_service_session_management()
    test_bicycle_to_eventhouse_workflow()
    print("✅ All Phase 1 builder tests passed!")
