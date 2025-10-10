"""
Eventstream Builder Tools Registration for Microsoft Fabric RTI MCP
Registers all builder-related tools with the MCP server
"""

from fastmcp import FastMCP

from fabric_rti_mcp.eventstream import eventstream_builder_service


def register_tools(mcp: FastMCP) -> None:
    """Register all available Eventstream Builder tools with the MCP server using modern decorator pattern."""

    # Session management tools
    @mcp.tool()
    def eventstream_start_definition(name: str, description: str = None):
        """Start a new eventstream definition builder session."""
        return eventstream_builder_service.eventstream_start_definition(name, description)

    @mcp.tool()
    def eventstream_get_current_definition(session_id: str):
        """Get the current eventstream definition."""
        return eventstream_builder_service.eventstream_get_current_definition(session_id)

    @mcp.tool()
    def eventstream_clear_definition(session_id: str):
        """Clear the current eventstream definition and start over."""
        return eventstream_builder_service.eventstream_clear_definition(session_id)

    # Data source tools
    @mcp.tool()
    def eventstream_add_sample_data_source(session_id: str, sample_type: str = "Bicycles", source_name: str = None):
        """Add a sample data source to the eventstream definition."""
        return eventstream_builder_service.eventstream_add_sample_data_source(session_id, sample_type, source_name)

    @mcp.tool()
    def eventstream_add_custom_endpoint_source(session_id: str, source_name: str = None, endpoint_url: str = None):
        """Add a custom endpoint source to the eventstream definition."""
        return eventstream_builder_service.eventstream_add_custom_endpoint_source(session_id, source_name, endpoint_url)

    # Stream tools
    @mcp.tool()
    def eventstream_add_derived_stream(session_id: str, stream_name: str, input_nodes: list = None):
        """Add a derived stream to the eventstream definition.

        If input_nodes is not provided and only one stream exists, automatically connects to that stream.
        """
        return eventstream_builder_service.eventstream_add_derived_stream(session_id, stream_name, input_nodes)

    # Destination tools
    @mcp.tool()
    def eventstream_add_eventhouse_destination(
        session_id: str,
        workspace_id: str,
        item_id: str,
        database_name: str,
        table_name: str,
        input_streams: list,
        destination_name: str = None,
        data_ingestion_mode: str = "ProcessedIngestion",
        encoding: str = "UTF8",
    ):
        """Add an Eventhouse destination to the eventstream definition."""
        return eventstream_builder_service.eventstream_add_eventhouse_destination(
            session_id,
            workspace_id,
            item_id,
            database_name,
            table_name,
            input_streams,
            destination_name,
            data_ingestion_mode,
            encoding,
        )

    @mcp.tool()
    def eventstream_add_custom_endpoint_destination(
        session_id: str,
        input_streams: list,
        destination_name: str = None,
        endpoint_url: str = None,
        method: str = "POST",
        headers: dict = None,
    ):
        """Add a custom endpoint destination to the eventstream definition."""
        return eventstream_builder_service.eventstream_add_custom_endpoint_destination(
            session_id, input_streams, destination_name, endpoint_url, method, headers
        )

    # Validation and creation tools
    @mcp.tool()
    def eventstream_validate_definition(session_id: str):
        """Validate the current eventstream definition."""
        return eventstream_builder_service.eventstream_validate_definition(session_id)

    @mcp.tool()
    def eventstream_create_from_definition(session_id: str, workspace_id: str):
        """Create an eventstream in Fabric from the current definition."""
        return eventstream_builder_service.eventstream_create_from_definition(session_id, workspace_id)

    @mcp.tool()
    def eventstream_list_available_components():
        """List available components for building eventstreams."""
        return eventstream_builder_service.eventstream_list_available_components()
