"""
Eventstream Builder Service - Core builder logic for Microsoft Fabric Eventstreams
Provides a fluent interface for building Fabric-compliant eventstream definitions
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Coroutine
import concurrent.futures

from fabric_rti_mcp.common import logger
from fabric_rti_mcp.eventstream.eventstream_service import eventstream_create


def _run_async_operation(coro: Coroutine[Any, Any, Any]) -> Any:
    """
    Helper function to run async operations in sync context.
    Handles event loop management gracefully.
    """
    try:
        # Try to get the existing event loop
        asyncio.get_running_loop()
        # If we're already in an event loop, we need to run in a thread
        
        def run_in_thread() -> Any:
            # Create a new event loop for this thread
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(coro)
            finally:
                new_loop.close()
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_in_thread)
            return future.result()
            
    except RuntimeError:
        # No event loop running, we can use asyncio.run
        return asyncio.run(coro)


class EventstreamDefinitionBuilder:
    """
    Core builder class for creating Fabric-compliant eventstream definitions.
    Manages session state and provides methods to build eventstream components.
    """
    
    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize a new eventstream definition builder.
        
        :param session_id: Optional session ID. If not provided, generates a new UUID.
        """
        self.session_id = session_id or str(uuid.uuid4())
        self.metadata: Dict[str, Any] = {
            "name": None,
            "description": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "session_id": self.session_id
        }
        self.definition: Dict[str, Any] = {
            "sources": [],
            "destinations": [],
            "operators": [],
            "streams": [],
            "compatibilityLevel": "1.0"
        }
        self.validation_errors: List[str] = []
        logger.info(f"Created eventstream builder with session ID: {self.session_id}")
    
    def set_metadata(self, name: str, description: Optional[str] = None) -> None:
        """
        Set metadata for the eventstream definition.
        
        :param name: Name of the eventstream
        :param description: Optional description
        """
        self.metadata["name"] = name
        self.metadata["description"] = description
        logger.info(f"Set eventstream metadata: name={name}")
    
    def add_source(self, source_config: Dict[str, Any]) -> None:
        """
        Add a source to the eventstream definition.
        
        :param source_config: Source configuration in Fabric API format
        """
        self.definition["sources"].append(source_config)
        logger.info(f"Added source: {source_config.get('name', 'unnamed')}")
    
    def add_destination(self, destination_config: Dict[str, Any]) -> None:
        """
        Add a destination to the eventstream definition.
        
        :param destination_config: Destination configuration in Fabric API format
        """
        self.definition["destinations"].append(destination_config)
        logger.info(f"Added destination: {destination_config.get('name', 'unnamed')}")
    
    def add_stream(self, stream_config: Dict[str, Any]) -> None:
        """
        Add a stream to the eventstream definition.
        
        :param stream_config: Stream configuration in Fabric API format
        """
        self.definition["streams"].append(stream_config)
        logger.info(f"Added stream: {stream_config.get('name', 'unnamed')}")
    
    def add_operator(self, operator_config: Dict[str, Any]) -> None:
        """
        Add an operator to the eventstream definition.
        
        :param operator_config: Operator configuration in Fabric API format
        """
        self.definition["operators"].append(operator_config)
        logger.info(f"Added operator: {operator_config.get('name', 'unnamed')}")
    
    def get_definition(self) -> Dict[str, Any]:
        """
        Get the current eventstream definition.
        
        :return: Complete definition including metadata
        """
        return {
            "metadata": self.metadata,
            "definition": self.definition
        }
    
    def validate(self) -> List[str]:
        """
        Validate the current eventstream definition.
        
        :return: List of validation errors (empty if valid)
        """
        errors = []
        
        # Basic validation
        if not self.metadata.get("name"):
            errors.append("Eventstream name is required")
        
        if not self.definition["sources"]:
            errors.append("At least one source is required")
        
        if not self.definition["destinations"]:
            errors.append("At least one destination is required")
        
        if not self.definition["streams"]:
            errors.append("At least one stream is required")
        
        # Validate source/destination connectivity
        source_names = {source.get("name") for source in self.definition["sources"]}
        destination_names = {dest.get("name") for dest in self.definition["destinations"]}
        stream_names = {stream.get("name") for stream in self.definition["streams"]}
        operator_names = {op.get("name") for op in self.definition["operators"]}
        
        # All available node names that can be referenced
        all_node_names = source_names | stream_names | operator_names
        
        for stream in self.definition["streams"]:
            input_nodes = stream.get("inputNodes", [])
            for node in input_nodes:
                # Handle both string and object formats for inputNodes
                node_name = node.get("name") if isinstance(node, dict) else node
                if node_name not in all_node_names:
                    errors.append(f"Stream '{stream.get('name')}' references unknown input node: {node_name}")
        
        self.validation_errors = errors
        return errors
    
    def clear(self) -> None:
        """
        Clear the current definition and start fresh.
        """
        self.definition = {
            "sources": [],
            "destinations": [],
            "operators": [],
            "streams": [],
            "compatibilityLevel": "1.0"
        }
        self.validation_errors = []
        logger.info(f"Cleared eventstream definition for session: {self.session_id}")
    
    def create_sample_data_source(self, name: str, sample_type: str = "Bicycles") -> Dict[str, Any]:
        """
        Create a sample data source configuration.
        
        :param name: Name of the source
        :param sample_type: Type of sample data (Bicycles, Stock, etc.)
        :return: Source configuration
        """
        return {
            "name": name,
            "type": "SampleData",
            "properties": {
                "type": sample_type
            }
        }
    
    def create_custom_endpoint_source(self, name: str, endpoint_url: str) -> Dict[str, Any]:
        """
        Create a custom endpoint source configuration.
        
        :param name: Name of the source
        :param endpoint_url: Custom endpoint URL
        :return: Source configuration
        """
        return {
            "name": name,
            "type": "CustomEndpoint",
            "properties": {
                "endpointUrl": endpoint_url
            }
        }
    
    def create_eventhouse_destination(
        self,
        name: str,
        workspace_id: str,
        item_id: str,
        database_name: str,
        table_name: str,
        input_nodes: List[str],
        data_ingestion_mode: str = "ProcessedIngestion",
        encoding: str = "UTF8"
    ) -> Dict[str, Any]:
        """
        Create an Eventhouse destination configuration.
        
        :param name: Name of the destination
        :param workspace_id: Fabric workspace ID
        :param item_id: Eventhouse item ID
        :param database_name: Target database name
        :param table_name: Target table name
        :param input_nodes: List of input node names (stream names that feed this destination)
        :param data_ingestion_mode: Ingestion mode (ProcessedIngestion or DirectIngestion)
        :param encoding: Input encoding
        :return: Destination configuration
        """
        return {
            "name": name,
            "type": "Eventhouse",
            "properties": {
                "dataIngestionMode": data_ingestion_mode,
                "workspaceId": workspace_id,
                "itemId": item_id,
                "databaseName": database_name,
                "tableName": table_name,
                "inputSerialization": {
                    "type": "Json",
                    "properties": {
                        "encoding": encoding
                    }
                }
            },
            "inputNodes": [{"name": node} for node in input_nodes],
        }
    
    def create_custom_endpoint_destination(
        self,
        name: str,
        endpoint_url: str,
        input_nodes: List[str],
        method: str = "POST",
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create a custom endpoint destination configuration.
        
        :param name: Name of the destination
        :param endpoint_url: Custom endpoint URL
        :param input_nodes: List of input node names (stream names that feed this destination)
        :param method: HTTP method
        :param headers: Optional HTTP headers
        :return: Destination configuration
        """
        return {
            "name": name,
            "type": "CustomEndpoint",
            "properties": {},
            "inputNodes": [{"name": node} for node in input_nodes]
        }
    
    def create_default_stream(self, name: str, input_nodes: List[str]) -> Dict[str, Any]:
        """
        Create a default stream configuration. All Eventstreams must have
        one default stream that connects sources to destinations, derived streams or 
        operators.
        
        :param name: Name of the stream
        :param input_nodes: List of input node names
        :return: Stream configuration
        """
        return {
            "name": name+"-stream",
            "type": "DefaultStream",
            "properties": {},
            "inputNodes": [{"name": node} for node in input_nodes]
        }
    
    def create_derived_stream(self, name: str, input_nodes: List[str]) -> Dict[str, Any]:
        """
        Create a derived stream configuration. Derived streams are optional. But if 
        present, they must be connected to either a default stream or another derived stream
        or an operator as input
        
        :param name: Name of the stream
        :param input_nodes: List of input node names
        :return: Stream configuration
        """
        return {
            "name": name,
            "type": "DerivedStream",
            "properties": { "inputSerialization": { "type": "Json", "properties": { "encoding": "UTF8" } } },
            "inputNodes": [{"name": node} for node in input_nodes]
        }


class EventstreamBuilderService:
    """
    Service class for managing eventstream builder sessions.
    Provides high-level operations for the eventstream builder.
    """
    
    def __init__(self):
        """Initialize the builder service."""
        self.sessions: Dict[str, EventstreamDefinitionBuilder] = {}
        logger.info("Initialized eventstream builder service")
    
    def create_session(self, name: str, description: Optional[str] = None) -> str:
        """
        Create a new builder session.
        
        :param name: Name of the eventstream
        :param description: Optional description
        :return: Session ID
        """
        builder = EventstreamDefinitionBuilder()
        builder.set_metadata(name, description)
        self.sessions[builder.session_id] = builder
        logger.info(f"Created new builder session: {builder.session_id}")
        return builder.session_id
    
    def get_session(self, session_id: str) -> Optional[EventstreamDefinitionBuilder]:
        """
        Get a builder session by ID.
        
        :param session_id: Session ID
        :return: Builder instance or None if not found
        """
        return self.sessions.get(session_id)
    
    def clear_session(self, session_id: str) -> bool:
        """
        Clear a builder session.
        
        :param session_id: Session ID
        :return: True if session was cleared, False if not found
        """
        if session_id in self.sessions:
            self.sessions[session_id].clear()
            return True
        return False
    
    def remove_session(self, session_id: str) -> bool:
        """
        Remove a builder session.
        
        :param session_id: Session ID
        :return: True if session was removed, False if not found
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Removed builder session: {session_id}")
            return True
        return False
    
    async def create_eventstream_from_definition(
        self,
        session_id: str,
        workspace_id: str
    ) -> Dict[str, Any]:
        """
        Create an eventstream in Fabric from a builder session.
        
        :param session_id: Builder session ID
        :param workspace_id: Target workspace ID
        :return: Creation result
        """
        builder = self.get_session(session_id)
        if not builder:
            return {"error": True, "message": f"Session not found: {session_id}"}
        
        # Validate definition
        errors = builder.validate()
        if errors:
            return {"error": True, "message": "Validation failed", "errors": errors}
        
        # Create eventstream using existing service
        try:
            result = eventstream_create(
                workspace_id=workspace_id,
                eventstream_name=builder.metadata["name"],
                definition=builder.definition,
                description=builder.metadata.get("description")
            )
            
            # Clean up session after successful creation
            self.remove_session(session_id)
            
            return {
                "success": True,
                "message": f"Eventstream '{builder.metadata['name']}' created successfully",
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Error creating eventstream: {e}")
            return {"error": True, "message": f"Failed to create eventstream: {str(e)}"}


# Global service instance
EVENTSTREAM_BUILDER_SERVICE = EventstreamBuilderService()


def get_eventstream_builder_service() -> EventstreamBuilderService:
    """Get the global eventstream builder service instance."""
    return EVENTSTREAM_BUILDER_SERVICE
