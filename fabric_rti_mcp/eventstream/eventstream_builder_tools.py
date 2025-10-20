"""
Eventstream Builder Tools - MCP tool definitions for the eventstream builder
Provides user-friendly tools for building Fabric eventstreams step by step
"""

import json
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent, ToolAnnotations
from fabric_rti_mcp.common import logger
from fabric_rti_mcp.eventstream.eventstream_builder_service import (
    get_eventstream_builder_service,
    _run_async_operation
)


def register_builder_tools(mcp: FastMCP) -> None:
    """Register all Eventstream Builder tools with the MCP server."""
    
    # Definition management tools
    mcp.add_tool(
        eventstream_start_definition,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
    )
    
    mcp.add_tool(
        eventstream_validate_definition,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
    
    mcp.add_tool(
        eventstream_create_from_definition,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
    )
    
    # Source management tools
    mcp.add_tool(
        eventstream_add_sample_data_source,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
    )
    
    mcp.add_tool(
        eventstream_add_custom_endpoint_source,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
    )
    
    # Stream management tools
    mcp.add_tool(
        eventstream_add_default_stream,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
    )
    
    mcp.add_tool(
        eventstream_add_derived_stream,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
    )
    
    # Destination management tools
    mcp.add_tool(
        eventstream_add_eventhouse_destination,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
    )
    
    mcp.add_tool(
        eventstream_add_custom_endpoint_destination,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
    )
    
    # Helper tools
    mcp.add_tool(
        eventstream_get_current_definition,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
    
    mcp.add_tool(
        eventstream_clear_definition,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
    )
    
    mcp.add_tool(
        eventstream_list_available_components,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )


def eventstream_start_definition(
    name: str,
    description: Optional[str] = None
) -> List[TextContent]:
    """
    Start a new eventstream definition builder session.
    
    :param name: Name of the eventstream to create
    :param description: Optional description of the eventstream
    :return: Session information and next steps
    """
    try:
        service = get_eventstream_builder_service()
        session_id = service.create_session(name, description)
        
        result = {
            "success": True,
            "session_id": session_id,
            "eventstream_name": name,
            "message": f"Started building eventstream '{name}'",
            "next_steps": [
                "Add sources using eventstream_add_sample_data_source() or eventstream_add_custom_endpoint_source()",
                "Add streams using eventstream_add_default_stream() or eventstream_add_derived_stream()",
                "💡 RECOMMENDATION: Consider adding a derived stream for data processing - this follows best practices",
                "Add destinations using eventstream_add_eventhouse_destination() or eventstream_add_custom_endpoint_destination()",
                "Validate using eventstream_validate_definition()",
                "Create using eventstream_create_from_definition()"
            ],
            "architectural_guidance": "For most use cases, we recommend the pattern: Source → Default Stream → Derived Stream → Destination. This provides better separation of concerns and flexibility for future enhancements."
        }
        
        logger.info(f"Started eventstream definition: {name} (session: {session_id})")
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        logger.error(f"Error starting eventstream definition: {e}")
        return [TextContent(type="text", text=json.dumps({
            "error": True,
            "message": f"Failed to start eventstream definition: {str(e)}"
        }, indent=2))]


def eventstream_add_sample_data_source(
    session_id: str,
    source_name: str,
    sample_type: str = "Bicycles"
) -> List[TextContent]:
    """
    Add a sample data source to the eventstream definition.
    
    :param session_id: Builder session ID
    :param source_name: Name for the source
    :param sample_type: Type of sample data (Bicycles, Stock, etc.)
    :return: Updated definition summary
    """
    try:
        service = get_eventstream_builder_service()
        builder = service.get_session(session_id)
        
        if not builder:
            return [TextContent(type="text", text=json.dumps({
                "error": True,
                "message": f"Session not found: {session_id}"
            }, indent=2))]
        
        # Create and add the source
        source_config = builder.create_sample_data_source(source_name, sample_type)
        builder.add_source(source_config)
        
        result = {
            "success": True,
            "message": f"Added sample data source '{source_name}' ({sample_type})",
            "source_added": source_config,
            "current_sources": len(builder.definition["sources"]),
            "next_steps": [
                "Add a stream using eventstream_add_default_stream()",
                "Or add more sources first"
            ]
        }
        
        logger.info(f"Added sample data source: {source_name} (session: {session_id})")
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        logger.error(f"Error adding sample data source: {e}")
        return [TextContent(type="text", text=json.dumps({
            "error": True,
            "message": f"Failed to add sample data source: {str(e)}"
        }, indent=2))]


def eventstream_add_custom_endpoint_source(
    session_id: str,
    source_name: str,
    endpoint_url: str
) -> List[TextContent]:
    """
    Add a custom endpoint source to the eventstream definition.
    
    :param session_id: Builder session ID
    :param source_name: Name for the source
    :param endpoint_url: Custom endpoint URL
    :return: Updated definition summary
    """
    try:
        service = get_eventstream_builder_service()
        builder = service.get_session(session_id)
        
        if not builder:
            return [TextContent(type="text", text=json.dumps({
                "error": True,
                "message": f"Session not found: {session_id}"
            }, indent=2))]
        
        # Create and add the source
        source_config = builder.create_custom_endpoint_source(source_name, endpoint_url)
        builder.add_source(source_config)
        
        result = {
            "success": True,
            "message": f"Added custom endpoint source '{source_name}'",
            "source_added": source_config,
            "current_sources": len(builder.definition["sources"]),
            "next_steps": [
                "Add a stream using eventstream_add_default_stream()",
                "Or add more sources first"
            ]
        }
        
        logger.info(f"Added custom endpoint source: {source_name} (session: {session_id})")
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        logger.error(f"Error adding custom endpoint source: {e}")
        return [TextContent(type="text", text=json.dumps({
            "error": True,
            "message": f"Failed to add custom endpoint source: {str(e)}"
        }, indent=2))]


def eventstream_add_default_stream(
    session_id: str,
    stream_name: str,
    input_sources: List[str]
) -> List[TextContent]:
    """
    Add a default stream to the eventstream definition.
    
    :param session_id: Builder session ID
    :param stream_name: Name for the stream
    :param input_sources: List of source names that feed this stream
    :return: Updated definition summary
    """
    try:
        service = get_eventstream_builder_service()
        builder = service.get_session(session_id)
        
        if not builder:
            return [TextContent(type="text", text=json.dumps({
                "error": True,
                "message": f"Session not found: {session_id}"
            }, indent=2))]
        
        # Create and add the stream
        stream_config = builder.create_default_stream(stream_name, input_sources)
        builder.add_stream(stream_config)
        
        result = {
            "success": True,
            "message": f"Added default stream '{stream_name}'",
            "stream_added": stream_config,
            "current_streams": len(builder.definition["streams"]),
            "next_steps": [
                "💡 RECOMMENDED: Add a derived stream for data processing using eventstream_add_derived_stream()",
                "Or add destinations using eventstream_add_eventhouse_destination() or eventstream_add_custom_endpoint_destination()",
                "Or add more streams first"
            ]
        }
        
        logger.info(f"Added default stream: {stream_name} (session: {session_id})")
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        logger.error(f"Error adding default stream: {e}")
        return [TextContent(type="text", text=json.dumps({
            "error": True,
            "message": f"Failed to add default stream: {str(e)}"
        }, indent=2))]


def eventstream_add_derived_stream(
    session_id: str,
    stream_name: str,
    input_nodes: List[str]
) -> List[TextContent]:
    """
    Add a derived stream to the eventstream definition.
    
    :param session_id: Builder session ID
    :param stream_name: Name for the stream
    :param input_nodes: List of node names (sources or operators) that feed this stream
    :return: Updated definition summary
    """
    try:
        service = get_eventstream_builder_service()
        builder = service.get_session(session_id)
        
        if not builder:
            return [TextContent(type="text", text=json.dumps({
                "error": True,
                "message": f"Session not found: {session_id}"
            }, indent=2))]
        
        # Create and add the stream
        stream_config = builder.create_derived_stream(stream_name, input_nodes)
        builder.add_stream(stream_config)
        
        result = {
            "success": True,
            "message": f"Added derived stream '{stream_name}'",
            "stream_added": stream_config,
            "current_streams": len(builder.definition["streams"]),
            "next_steps": [
                "Add destinations using eventstream_add_eventhouse_destination() or eventstream_add_custom_endpoint_destination()",
                "Or add more streams first"
            ]
        }
        
        logger.info(f"Added derived stream: {stream_name} (session: {session_id})")
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        logger.error(f"Error adding derived stream: {e}")
        return [TextContent(type="text", text=json.dumps({
            "error": True,
            "message": f"Failed to add derived stream: {str(e)}"
        }, indent=2))]


def eventstream_add_eventhouse_destination(
    session_id: str,
    destination_name: str,
    workspace_id: str,
    item_id: str,
    database_name: str,
    table_name: str,
    input_streams: List[str],
    data_ingestion_mode: str = "ProcessedIngestion",
    encoding: str = "UTF8"
) -> List[TextContent]:
    """
    Add an Eventhouse destination to the eventstream definition.
    
    :param session_id: Builder session ID
    :param destination_name: Name for the destination
    :param workspace_id: Fabric workspace ID
    :param item_id: Eventhouse item ID
    :param database_name: Target database name
    :param table_name: Target table name
    :param input_streams: List of stream names that feed this destination
    :param data_ingestion_mode: Ingestion mode (ProcessedIngestion or DirectIngestion)
    :param encoding: Input encoding
    :return: Updated definition summary
    """
    try:
        service = get_eventstream_builder_service()
        builder = service.get_session(session_id)
        
        if not builder:
            return [TextContent(type="text", text=json.dumps({
                "error": True,
                "message": f"Session not found: {session_id}"
            }, indent=2))]
        
        # Create and add the destination
        destination_config = builder.create_eventhouse_destination(
            destination_name, workspace_id, item_id, database_name, 
            table_name, input_streams, data_ingestion_mode, encoding
        )
        builder.add_destination(destination_config)
        
        result = {
            "success": True,
            "message": f"Added Eventhouse destination '{destination_name}'",
            "destination_added": destination_config,
            "current_destinations": len(builder.definition["destinations"]),
            "next_steps": [
                "Validate the definition using eventstream_validate_definition()",
                "Or add more destinations first"
            ]
        }
        
        logger.info(f"Added Eventhouse destination: {destination_name} (session: {session_id})")
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        logger.error(f"Error adding Eventhouse destination: {e}")
        return [TextContent(type="text", text=json.dumps({
            "error": True,
            "message": f"Failed to add Eventhouse destination: {str(e)}"
        }, indent=2))]


def eventstream_add_custom_endpoint_destination(
    session_id: str,
    destination_name: str,
    endpoint_url: str,
    input_streams: List[str],
    method: str = "POST",
    headers: Optional[Dict[str, str]] = None
) -> List[TextContent]:
    """
    Add a custom endpoint destination to the eventstream definition.
    
    :param session_id: Builder session ID
    :param destination_name: Name for the destination
    :param endpoint_url: Custom endpoint URL
    :param input_streams: List of stream names that feed this destination
    :param method: HTTP method
    :param headers: Optional HTTP headers
    :return: Updated definition summary
    """
    try:
        service = get_eventstream_builder_service()
        builder = service.get_session(session_id)
        
        if not builder:
            return [TextContent(type="text", text=json.dumps({
                "error": True,
                "message": f"Session not found: {session_id}"
            }, indent=2))]
        
        # Create and add the destination
        destination_config = builder.create_custom_endpoint_destination(
            destination_name, endpoint_url, input_streams, method, headers
        )
        builder.add_destination(destination_config)
        
        result = {
            "success": True,
            "message": f"Added custom endpoint destination '{destination_name}'",
            "destination_added": destination_config,
            "current_destinations": len(builder.definition["destinations"]),
            "next_steps": [
                "Validate the definition using eventstream_validate_definition()",
                "Or add more destinations first"
            ]
        }
        
        logger.info(f"Added custom endpoint destination: {destination_name} (session: {session_id})")
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        logger.error(f"Error adding custom endpoint destination: {e}")
        return [TextContent(type="text", text=json.dumps({
            "error": True,
            "message": f"Failed to add custom endpoint destination: {str(e)}"
        }, indent=2))]


def eventstream_validate_definition(session_id: str) -> List[TextContent]:
    """
    Validate the current eventstream definition.
    
    :param session_id: Builder session ID
    :return: Validation results
    """
    try:
        service = get_eventstream_builder_service()
        builder = service.get_session(session_id)
        
        if not builder:
            return [TextContent(type="text", text=json.dumps({
                "error": True,
                "message": f"Session not found: {session_id}"
            }, indent=2))]
        
        # Validate the definition
        errors = builder.validate()
        
        if errors:
            result = {
                "valid": False,
                "errors": errors,
                "message": f"Validation failed with {len(errors)} errors",
                "next_steps": [
                    "Fix the validation errors",
                    "Use eventstream_get_current_definition() to review the current state"
                ]
            }
        else:
            result = {
                "valid": True,
                "message": "Definition is valid and ready to create",
                "summary": {
                    "sources": len(builder.definition["sources"]),
                    "streams": len(builder.definition["streams"]),
                    "destinations": len(builder.definition["destinations"]),
                    "operators": len(builder.definition["operators"])
                },
                "next_steps": [
                    "Create the eventstream using eventstream_create_from_definition()"
                ]
            }
        
        logger.info(f"Validated eventstream definition (session: {session_id}): {len(errors)} errors")
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        logger.error(f"Error validating eventstream definition: {e}")
        return [TextContent(type="text", text=json.dumps({
            "error": True,
            "message": f"Failed to validate eventstream definition: {str(e)}"
        }, indent=2))]


def eventstream_create_from_definition(
    session_id: str,
    workspace_id: str
) -> List[TextContent]:
    """
    Create an eventstream in Fabric from the current definition.
    
    :param session_id: Builder session ID
    :param workspace_id: Target Fabric workspace ID
    :return: Creation results
    """
    try:
        service = get_eventstream_builder_service()
        
        # Use the async operation wrapper
        result = _run_async_operation(
            service.create_eventstream_from_definition(session_id, workspace_id)
        )
        
        logger.info(f"Created eventstream from definition (session: {session_id})")
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        logger.error(f"Error creating eventstream from definition: {e}")
        return [TextContent(type="text", text=json.dumps({
            "error": True,
            "message": f"Failed to create eventstream: {str(e)}"
        }, indent=2))]


def eventstream_get_current_definition(session_id: str) -> List[TextContent]:
    """
    Get the current eventstream definition.
    
    :param session_id: Builder session ID
    :return: Current definition
    """
    try:
        service = get_eventstream_builder_service()
        builder = service.get_session(session_id)
        
        if not builder:
            return [TextContent(type="text", text=json.dumps({
                "error": True,
                "message": f"Session not found: {session_id}"
            }, indent=2))]
        
        definition = builder.get_definition()
        
        result = {
            "session_id": session_id,
            "definition": definition,
            "summary": {
                "sources": len(builder.definition["sources"]),
                "streams": len(builder.definition["streams"]),
                "destinations": len(builder.definition["destinations"]),
                "operators": len(builder.definition["operators"])
            }
        }
        
        logger.info(f"Retrieved current definition (session: {session_id})")
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        logger.error(f"Error getting current definition: {e}")
        return [TextContent(type="text", text=json.dumps({
            "error": True,
            "message": f"Failed to get current definition: {str(e)}"
        }, indent=2))]


def eventstream_clear_definition(session_id: str) -> List[TextContent]:
    """
    Clear the current eventstream definition and start over.
    
    :param session_id: Builder session ID
    :return: Confirmation of clearing
    """
    try:
        service = get_eventstream_builder_service()
        
        if service.clear_session(session_id):
            result = {
                "success": True,
                "message": f"Cleared eventstream definition (session: {session_id})",
                "next_steps": [
                    "Start adding components again",
                    "Or use eventstream_start_definition() to begin fresh"
                ]
            }
        else:
            result = {
                "error": True,
                "message": f"Session not found: {session_id}"
            }
        
        logger.info(f"Cleared eventstream definition (session: {session_id})")
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        logger.error(f"Error clearing eventstream definition: {e}")
        return [TextContent(type="text", text=json.dumps({
            "error": True,
            "message": f"Failed to clear eventstream definition: {str(e)}"
        }, indent=2))]


def eventstream_list_available_components() -> List[TextContent]:
    """
    List available components for building eventstreams.
    
    :return: Available components
    """
    try:
        components = {
            "sources": {
                "SampleData": {
                    "description": "Sample data sources for testing",
                    "types": ["Bicycles", "Stock", "IoT", "WebLogs"],
                    "tool": "eventstream_add_sample_data_source"
                },
                "CustomEndpoint": {
                    "description": "Custom REST endpoint sources",
                    "tool": "eventstream_add_custom_endpoint_source"
                }
            },
            "streams": {
                "DefaultStream": {
                    "description": "Default stream from sources",
                    "tool": "eventstream_add_default_stream"
                },
                "DerivedStream": {
                    "description": "Derived stream from operators",
                    "tool": "eventstream_add_derived_stream"
                }
            },
            "destinations": {
                "Eventhouse": {
                    "description": "Fabric Eventhouse (KQL Database)",
                    "tool": "eventstream_add_eventhouse_destination"
                },
                "CustomEndpoint": {
                    "description": "Custom REST endpoint destinations",
                    "tool": "eventstream_add_custom_endpoint_destination"
                }
            }
        }
        
        result = {
            "available_components": components,
            "workflow": [
                "1. Start with eventstream_start_definition()",
                "2. Add sources using source tools",
                "3. Add streams using stream tools",
                "4. Add destinations using destination tools",
                "5. Validate with eventstream_validate_definition()",
                "6. Create with eventstream_create_from_definition()"
            ]
        }
        
        logger.info("Listed available eventstream components")
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        logger.error(f"Error listing available components: {e}")
        return [TextContent(type="text", text=json.dumps({
            "error": True,
            "message": f"Failed to list available components: {str(e)}"
        }, indent=2))]
