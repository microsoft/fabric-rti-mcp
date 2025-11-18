import uuid
from datetime import datetime
from typing import Any, cast

from fabric_rti_mcp.config import logger
from fabric_rti_mcp.services.eventstream.eventstream_service import eventstream_create as _eventstream_create

# Global session storage
_builder_sessions: dict[str, dict[str, Any]] = {}


def _generate_session_id() -> str:
    """Generate a unique session ID."""
    return str(uuid.uuid4())


def _get_session(session_id: str) -> dict[str, Any] | None:
    """Get a builder session by ID."""
    return _builder_sessions.get(session_id)


def _update_session(session_id: str, updates: dict[str, Any]) -> None:  # type: ignore
    """Update a builder session with new data."""
    if session_id in _builder_sessions:
        _builder_sessions[session_id].update(updates)


def _generate_sequential_name(base_name: str, existing_names: list[str]) -> str:
    """
    Generate a sequential name that doesn't conflict with existing names.

    :param base_name: The base name to use (e.g., "TestMCP80-source")
    :param existing_names: List of existing names to check against
    :return: Sequential name (base_name, base_name-2, base_name-3, etc.)
    """
    if base_name not in existing_names:
        return base_name

    counter = 2
    while f"{base_name}-{counter}" in existing_names:
        counter += 1

    return f"{base_name}-{counter}"


def _create_basic_definition(name: str, description: str | None = None) -> dict[str, Any]:
    """
    Create a basic eventstream definition template for the interactive builder workflow.
    This creates a structure with a default stream that gets populated through builder methods.
    Note: name and description are NOT included here as they belong in the outer HTTP payload.

    :param name: Name of the eventstream being built (used for default stream naming)
    :param description: Optional description of the eventstream (used for session metadata only)
    :return: Eventstream definition template with default stream ready for builder population
    """
    return {
        "sources": [],
        "streams": [{"name": f"{name}-stream", "type": "DefaultStream", "properties": {}, "inputNodes": []}],
        "destinations": [],
        "operators": [],
        "compatibilityLevel": "1.0",
    }


def eventstream_start_definition(name: str, description: str | None = None) -> dict[str, Any]:
    """
    Start a new eventstream definition builder session.

    :param name: Name of the eventstream to create
    :param description: Optional description of the eventstream
    :return: Session information and next steps
    """
    try:
        session_id = _generate_session_id()
        definition = _create_basic_definition(name, description)

        session_data = {  # type: ignore
            "session_id": session_id,
            "name": name,
            "description": description,
            "definition": definition,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "status": "building",
        }

        _builder_sessions[session_id] = session_data

        logger.info(f"Started eventstream builder session: {session_id}")

        return {
            "session_id": session_id,
            "name": name,
            "description": description,
            "status": "ready",
            "next_steps": [
                "Add sources using eventstream_add_sample_data_source or eventstream_add_custom_endpoint_source",
                "Add derived streams using eventstream_add_derived_stream "
                "(default stream auto-created as '{name}-stream')",
                "Add destinations using eventstream_add_eventhouse_destination or "
                "eventstream_add_custom_endpoint_destination",
                "Validate with eventstream_validate_definition",
                "Create with eventstream_create_from_definition",
            ],
        }
    except Exception as e:
        logger.error(f"Error starting eventstream definition: {str(e)}")
        raise


def eventstream_get_current_definition(session_id: str) -> dict[str, Any]:
    """
    Get the current eventstream definition.

    :param session_id: Builder session ID
    :return: Current definition
    """
    session = _get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    return {
        "session_id": session_id,
        "name": session["name"],
        "description": session["description"],
        "definition": session["definition"],
        "status": session["status"],
        "last_updated": session["last_updated"],
    }


def eventstream_clear_definition(session_id: str) -> dict[str, str]:
    """
    Clear the current eventstream definition and start over.

    :param session_id: Builder session ID
    :return: Confirmation of clearing
    """
    session = _get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    # Reset definition while keeping session metadata
    session["definition"] = _create_basic_definition(session["name"], session["description"])
    session["last_updated"] = datetime.now().isoformat()

    logger.info(f"Cleared eventstream definition for session: {session_id}")

    return {"status": "cleared", "message": f"Definition cleared for session {session_id}"}


def eventstream_add_sample_data_source(
    session_id: str, sample_type: str = "Bicycles", source_name: str | None = None
) -> dict[str, Any]:
    """
    Add a sample data source to the eventstream definition.

    :param session_id: Builder session ID
    :param sample_type: Type of sample data (Bicycles, Stock, etc.)
    :param source_name: Name for the source (auto-generated if not provided)
    :return: Updated definition summary
    """
    session = _get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    # Auto-generate source name if not provided
    if source_name is None:
        source_name = f"{sample_type.lower()}-source"

    source_config = {"name": source_name, "type": "SampleData", "properties": {"type": sample_type}}  # type: ignore

    session["definition"]["sources"].append(source_config)
    session["last_updated"] = datetime.now().isoformat()

    logger.info(f"Added sample data source '{source_name}' to session {session_id}")

    return {
        "session_id": session_id,
        "source_added": source_name,
        "source_type": "SampleData",
        "sources_count": len(session["definition"]["sources"]),
    }


def eventstream_add_custom_endpoint_source(
    session_id: str, source_name: str | None = None, endpoint_url: str | None = None
) -> dict[str, Any]:
    """
    Add a custom endpoint source to the eventstream definition.

    :param session_id: Builder session ID
    :param source_name: Name for the source (auto-generated if not provided)
    :param endpoint_url: Custom endpoint URL (deprecated - use data connections instead)
    :return: Updated definition summary
    """
    session = _get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    # Auto-generate source name if not provided using sequential numbering
    if source_name is None:
        base_name = f"{session['name']}-source"
        existing_source_names = [s["name"] for s in session["definition"]["sources"]]
        source_name = _generate_sequential_name(base_name, existing_source_names)

    source_config = {"name": source_name, "type": "CustomEndpoint", "properties": {}}  # type: ignore

    session["definition"]["sources"].append(source_config)
    session["last_updated"] = datetime.now().isoformat()

    logger.info(f"Added custom endpoint source '{source_name}' to session {session_id}")

    return {
        "session_id": session_id,
        "source_added": source_name,
        "source_type": "CustomEndpoint",
        "sources_count": len(session["definition"]["sources"]),
    }


def eventstream_add_derived_stream(
    session_id: str, stream_name: str, input_nodes: list[str] | None = None
) -> dict[str, Any]:
    """
    Add a derived stream to the eventstream definition.

    :param session_id: Builder session ID
    :param stream_name: Name for the stream
    :param input_nodes: List of node names (sources, operators, or other streams) that feed this stream.
                       If None and only one stream exists, automatically connects to that stream.
    :return: Updated definition summary
    """
    session = _get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    # Get available nodes for validation and auto-connection
    source_names = [s["name"] for s in session["definition"]["sources"]]
    operator_names = [o["name"] for o in session["definition"]["operators"]]
    stream_names = [s["name"] for s in session["definition"]["streams"]]

    # Smart default: if input_nodes not provided or empty and only one stream exists, use it
    if not input_nodes:  # This handles both None and empty list []
        # Auto-connect logic: if only one stream and no operators, connect to that stream
        if len(stream_names) == 1 and len(operator_names) == 0:
            input_nodes = stream_names.copy()  # Use copy to avoid reference issues
            logger.info(f"Auto-connecting derived stream '{stream_name}' to default stream '{stream_names[0]}'")
        else:
            raise ValueError(
                "input_nodes must be specified when multiple streams/operators exist."
                f"Available: streams={stream_names}, operators={operator_names}"
            )

    # Validate that input nodes exist (can be sources, operators, or streams)
    for node in input_nodes:
        if node not in source_names and node not in operator_names and node not in stream_names:
            raise ValueError(f"Input node '{node}' not found in sources, operators, or streams")

    stream_config = {  # type: ignore
        "name": stream_name,
        "type": "DerivedStream",
        "properties": {"inputSerialization": {"type": "Json", "properties": {"encoding": "UTF8"}}},
        "inputNodes": [{"name": node} for node in input_nodes],
    }

    session["definition"]["streams"].append(stream_config)
    session["last_updated"] = datetime.now().isoformat()

    logger.info(f"Added derived stream '{stream_name}' to session {session_id}")

    return {
        "session_id": session_id,
        "stream_added": stream_name,
        "stream_type": "DerivedStream",
        "streams_count": len(session["definition"]["streams"]),
    }


def eventstream_add_eventhouse_destination(
    session_id: str,
    workspace_id: str,
    item_id: str,
    database_name: str,
    table_name: str,
    input_streams: list[str],
    destination_name: str | None = None,
    data_ingestion_mode: str = "ProcessedIngestion",
    encoding: str = "UTF8",
) -> dict[str, Any]:
    """
    Add an Eventhouse destination to the eventstream definition.

    :param session_id: Builder session ID
    :param workspace_id: Fabric workspace ID
    :param item_id: Eventhouse item ID
    :param database_name: Target database name
    :param table_name: Target table name
    :param input_streams: List of stream names that feed this destination
    :param destination_name: Name for the destination (auto-generated if not provided)
    :param data_ingestion_mode: Ingestion mode (ProcessedIngestion or DirectIngestion)
    :param encoding: Input encoding
    :return: Updated definition summary
    """
    session = _get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    # Auto-generate destination name if not provided
    if destination_name is None:
        destination_name = f"{session['name']}-eventhouse-destination"

    # Validate that input streams exist
    stream_names = [s["name"] for s in session["definition"]["streams"]]
    for stream in input_streams:
        if stream not in stream_names:
            raise ValueError(f"Stream '{stream}' not found in definition")

    destination_config = {  # type: ignore
        "name": destination_name,
        "type": "Eventhouse",
        "properties": {
            "dataIngestionMode": data_ingestion_mode,
            "workspaceId": workspace_id,
            "itemId": item_id,
            "databaseName": database_name,
            "tableName": table_name,
            "inputSerialization": {"type": "Json", "properties": {"encoding": encoding}},
        },
        "inputNodes": [{"name": stream} for stream in input_streams],
    }

    session["definition"]["destinations"].append(destination_config)
    session["last_updated"] = datetime.now().isoformat()

    logger.info(f"Added Eventhouse destination '{destination_name}' to session {session_id}")

    return {
        "session_id": session_id,
        "destination_added": destination_name,
        "destination_type": "Eventhouse",
        "destinations_count": len(session["definition"]["destinations"]),
    }


def eventstream_add_custom_endpoint_destination(
    session_id: str,
    input_streams: list[str],
    destination_name: str | None = None,
    endpoint_url: str | None = None,
    method: str = "POST",
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Add a custom endpoint destination to the eventstream definition.

    :param session_id: Builder session ID
    :param input_streams: List of stream names that feed this destination
    :param destination_name: Name for the destination (auto-generated if not provided)
    :param endpoint_url: Custom endpoint URL (deprecated - use data connections instead)
    :param method: HTTP method (deprecated)
    :param headers: Optional HTTP headers (deprecated)
    :return: Updated definition summary
    """
    session = _get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    # Auto-generate destination name if not provided using sequential numbering
    if destination_name is None:
        base_name = f"{session['name']}-destination"
        existing_destination_names = [d["name"] for d in session["definition"]["destinations"]]
        destination_name = _generate_sequential_name(base_name, existing_destination_names)

    # Validate that input streams exist
    stream_names = [s["name"] for s in session["definition"]["streams"]]
    for stream in input_streams:
        if stream not in stream_names:
            raise ValueError(f"Stream '{stream}' not found in definition")

    destination_config = {  # type: ignore
        "name": destination_name,
        "type": "CustomEndpoint",
        "properties": {},
        "inputNodes": [{"name": stream} for stream in input_streams],
    }

    session["definition"]["destinations"].append(destination_config)
    session["last_updated"] = datetime.now().isoformat()

    logger.info(f"Added custom endpoint destination '{destination_name}' to session {session_id}")

    return {
        "session_id": session_id,
        "destination_added": destination_name,
        "destination_type": "CustomEndpoint",
        "destinations_count": len(session["definition"]["destinations"]),
    }


def eventstream_validate_definition(session_id: str) -> dict[str, Any]:
    """
    Validate the current eventstream definition.

    :param session_id: Builder session ID
    :return: Validation results
    """
    session = _get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    definition = session["definition"]
    errors: list[str] = []
    warnings: list[str] = []

    # Basic validation
    if not definition.get("sources"):
        errors.append("At least one source is required")

    if not definition.get("streams"):
        warnings.append("No streams defined - consider adding at least one stream")

    if not definition.get("destinations"):
        warnings.append("No destinations defined - data will not be persisted")

    # Get name mappings for validation
    source_names = [s["name"] for s in definition.get("sources", [])]
    stream_names = [s["name"] for s in definition.get("streams", [])]

    # Stream validation
    for stream in definition.get("streams", []):
        if stream.get("type") == "DefaultStream":
            for input_node in stream.get("inputNodes", []):
                source_name = input_node.get("name")
                if source_name not in source_names:
                    errors.append(f"Stream '{stream['name']}' references unknown source '{source_name}'")

    # Destination validation
    for dest in definition.get("destinations", []):
        for input_node in dest.get("inputNodes", []):
            stream_name = input_node.get("name")
            if stream_name not in stream_names:
                errors.append(f"Destination '{dest['name']}' references unknown stream '{stream_name}'")

    is_valid = len(errors) == 0
    session["status"] = "valid" if is_valid else "invalid"
    session["last_updated"] = datetime.now().isoformat()

    logger.info(f"Validated definition for session {session_id}: {'valid' if is_valid else 'invalid'}")

    return {
        "session_id": session_id,
        "is_valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "sources": len(definition.get("sources", [])),
            "streams": len(definition.get("streams", [])),
            "destinations": len(definition.get("destinations", [])),
            "operators": len(definition.get("operators", [])),
        },
    }


def eventstream_create_from_definition(session_id: str, workspace_id: str) -> dict[str, Any]:
    """
    Create an eventstream in Fabric from the current definition.

    :param session_id: Builder session ID
    :param workspace_id: Target Fabric workspace ID
    :return: Creation results
    """
    session = _get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    # Validate definition first
    validation_result = eventstream_validate_definition(session_id)
    if not validation_result["is_valid"]:
        raise ValueError(f"Definition is invalid: {', '.join(validation_result['errors'])}")

    try:
        # Create the eventstream using the base service
        result = _eventstream_create(
            workspace_id=workspace_id,
            eventstream_name=session["name"],
            eventstream_id=None,  # Auto-generate
            definition=session["definition"],
            description=session["description"],
        )

        # Mark session as completed
        session["status"] = "created"

        # Handle different response types safely
        if result and len(result) > 0:
            result_data = result[0]
            if isinstance(result_data, dict):
                result_data = cast(dict[str, Any], result_data)
                if result_data.get("error"):
                    # Handle API errors
                    error_msg = result_data.get("detail", result_data.get("message", "Unknown error"))
                    session["status"] = "error"
                    session["error"] = error_msg
                    raise Exception(f"API Error: {error_msg}")
                else:
                    # Success case - get ID if available
                    session["created_item_id"] = result_data.get("id")
                    logger.info(f"Created eventstream from session {session_id}: {result_data.get('id', 'Success')}")
            else:
                session["created_item_id"] = None
                logger.info(f"Created eventstream from session {session_id}: Success (no ID returned)")
        else:
            session["created_item_id"] = None
            logger.info(f"Created eventstream from session {session_id}: Success (empty response)")

        session["last_updated"] = datetime.now().isoformat()

        return {
            "session_id": session_id,
            "status": "created",
            "eventstream": result[0] if result and len(result) > 0 else {"success": True},
            "workspace_id": workspace_id,
        }

    except Exception as e:
        logger.error(f"Error creating eventstream from session {session_id}: {str(e)}")
        session["status"] = "error"
        session["error"] = str(e)
        raise


def eventstream_list_available_components() -> dict[str, list[str]]:
    """
    List available components for building eventstreams.

    :return: Available components
    """
    return {
        "sources": [
            "SampleData",
            "CustomEndpoint",
            "AzureEventHub",
            "AzureIoTHub",
            "AmazonKinesis",
            "ApacheKafka",
            "ConfluentCloud",
            "FabricWorkspaceItemEvents",
            "FabricJobEvents",
            "FabricOneLakeEvents",
        ],
        "streams": ["DefaultStream", "DerivedStream"],
        "destinations": ["Eventhouse", "CustomEndpoint", "Lakehouse"],
        "operators": ["Filter", "Join", "ManageFields", "Aggregate", "GroupBy", "Union", "Expand"],
        "sample_data_types": ["Bicycles", "Buses", "SemanticModelLogs", "SP500Stocks", "StockMarket", "YellowTaxi"],
    }
