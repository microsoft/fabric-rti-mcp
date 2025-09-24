import base64
import json
from typing import Any, Dict, List, Optional

from fabric_rti_mcp.utils import FabricConnection, run_async_operation
from fabric_rti_mcp.common import GlobalFabricRTIConfig, logger
from fabric_rti_mcp.activator.activator_entity_generators import *

# Microsoft Fabric API configuration
FABRIC_BASE_URL = "https://fabric.microsoft.com"
DEFAULT_TIMEOUT = 30
FABRIC_CONFIG = GlobalFabricRTIConfig.from_env()


class ActivatorConnectionCache:
    """Simple connection cache for Activator API clients using Azure Identity."""

    def __init__(self) -> None:
        self._connection: Optional[FabricConnection] = None

    def get_connection(self) -> FabricConnection:
        """Get or create an Activator connection using the configured API base URL."""
        if self._connection is None:
            api_base = FABRIC_CONFIG.fabric_api_base
            self._connection = FabricConnection(api_base, service_name="Activator")
            logger.info(f"Created Activator connection for API base: {api_base}")

        return self._connection


ACTIVATOR_CONNECTION_CACHE = ActivatorConnectionCache()


def get_activator_connection() -> FabricConnection:
    """Get or create an Activator connection using the configured API base URL."""
    return ACTIVATOR_CONNECTION_CACHE.get_connection()

class ActivatorService:
    """Service class for Fabric Activator operations."""
    
    def __init__(self, connection_cache: Optional[ActivatorConnectionCache] = None) -> None:
        """
        Initialize the ActivatorService with a connection cache.
        
        :param connection_cache: Optional connection cache instance. If None, uses the global cache.
        """
        self._connection_cache = connection_cache or ACTIVATOR_CONNECTION_CACHE
    
    def _get_connection(self) -> FabricConnection:
        """Get the connection from the cache."""
        return self._connection_cache.get_connection()

    def activator_list_artifacts(self, workspace_id: str) -> List[Dict[str, Any]]:
        """
        List all Activator artifacts in a workspace.
        
        :param workspace_id: The workspace ID (UUID)
        :return: List of activator artifacts
        """
        connection = self._get_connection()
        
        result = run_async_operation(connection.list_artifacts_of_type(workspace_id, "Reflex"))
        return result

    def activator_create_trigger_on_kql_source(
        self,
        workspace_id: str,
        trigger_name: str,
        kql_cluster_url: str,
        kql_query: str,
        kql_database: str,
        alert_recipient: str,
        alert_type: str = "teams",
        polling_frequency_in_minutes: int = 5,
        artifact_id: Optional[str] = None,
        alert_message: Optional[str] = None,
        alert_headline: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a simple activator trigger on a KQL source. Users may wish to use this tool to get automatically notified about some condition they are interested in.
        The Kusto table can be explored using the Kusto tools, to help make sure the trigger being created has the correct column names etc.

        :param workspace_id: The workspace ID (UUID)
        :param trigger_name: Name of the trigger
        :param kql_cluster_url: The KQL cluster URL
        :param kql_query: The KQL query to monitor. DO NOT put new lines into the KQL query -- the API will fail if so.
        :param kql_database: The KQL database name
        :param alert_recipient: Email address of the alert recipient
        :param alert_type: Type of alert - "teams" or "email" (defaults to "teams")
        :param polling_frequency_in_minutes: Polling frequency in minutes. Must be one of: 5, 15, 60, 180, 360, 720, 1440 (defaults to 5)
        :param artifact_id: If specified, the trigger will be created in the specified Activator artifact. If left blank, a new Activator artifact will be created.
        :param alert_message: Optional alert message for the trigger
        :param alert_headline: Optional alert headline for the trigger
        :return: Created trigger details, including a URL back to the trigger
        """
        (container_entity, container_guid) = create_container_entity(trigger_name)
        (kql_source_entity, source_guid) = create_kql_source_entity(
            trigger_name,
            polling_frequency_minutes=polling_frequency_in_minutes,
            kql_query=kql_query,
            database=kql_database,
            cluster_hostname=kql_cluster_url,
            container_id=container_guid,
            workspace_id=workspace_id
        )

        return self._create_trigger_with_source(
            workspace_id=workspace_id,
            trigger_name=trigger_name,
            container_entity=container_entity,
            container_guid=container_guid,
            source_entity=kql_source_entity,
            source_guid=source_guid,
            alert_recipient=alert_recipient,
            alert_type=alert_type,
            artifact_id=artifact_id,
            alert_message=alert_message,
            alert_headline=alert_headline
        )


    def _create_trigger_with_source(
        self,
        workspace_id: str,
        trigger_name: str,
        container_entity: Dict[str, Any],
        container_guid: str,
        source_entity: Dict[str, Any],
        source_guid: str,
        alert_recipient: str,
        alert_type: str,
        artifact_id: Optional[str] = None,
        alert_message: Optional[str] = None,
        alert_headline: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Common logic for creating activator triggers with any source type. 
        
        :param workspace_id: The workspace ID (UUID)
        :param trigger_name: Name of the trigger
        :param container_entity: The container entity
        :param container_guid: The container GUID
        :param source_entity: The source entity (KQL, Event Stream, etc.)
        :param source_guid: The source GUID
        :param alert_recipient: Email address of the alert recipient
        :param alert_type: Type of alert - "teams" or "email"
        :param artifact_id: Optional artifact ID to associate with the trigger
        :param alert_message: Optional alert message for the trigger
        :param alert_headline: Optional alert headline for the trigger
        :return: Created trigger details, including a URL back to the trigger. Users can follow this URL to use more powerful Activator functionality, stop their trigger or see a history of its behaviour.
        """
        event_and_rule_entities = create_simple_event_rule_entities(
            trigger_name,
            container_id=container_guid,
            source_id=source_guid,
            message=alert_message or "Alert from Activator trigger",
            headline=alert_headline or f"Alert from {trigger_name}",
            alert_recipient=alert_recipient,
            alert_type=alert_type,
        )
        
        full_entity_list = [*event_and_rule_entities, container_entity, source_entity]

        if artifact_id is None:
            full_payload = self._get_full_payload(full_entity_list, trigger_name)
            return self._create_new_artifact(workspace_id, full_payload)
        else:
            return self._add_trigger_to_existing_artifact(workspace_id, artifact_id, full_entity_list)

    def _add_trigger_to_existing_artifact(self, workspace_id: str, artifact_id: str, entity_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Add a trigger to an existing activator artifact.
        
        :param workspace_id: The workspace ID (UUID)
        :param artifact_id: The existing artifact ID to add the trigger to
        :param entity_list: The list of entities to add to the existing artifact
        :return: Updated artifact details
        """
        try:
            # Step 1: Get existing payload
            existing_payload_result = self._get_existing_payload(workspace_id, artifact_id)
            
            # Step 2: Create combined entities
            combined_entities = self._create_combined_entities(entity_list, existing_payload_result)
            
            # Step 3: Update item with combined entities
            return self._update_item(workspace_id, artifact_id, combined_entities, existing_payload_result)
        except Exception as e:
            return {"error": str(e)}

    def _get_existing_payload(self, workspace_id: str, artifact_id: str) -> Dict[str, Any]:
        """
        Get the existing payload from an activator artifact.
        
        :param workspace_id: The workspace ID (UUID)
        :param artifact_id: The existing artifact ID
        :return: The raw API response
        :raises: Exception if unable to get existing payload
        """
        connection = self._get_connection()
        
        # Get the existing artifact definition
        get_definition_endpoint = f"/workspaces/{workspace_id}/reflexes/{artifact_id}/getDefinition"
        existing_definition_response = run_async_operation(
            connection.execute_operation_and_return_error_in_dict("POST", get_definition_endpoint, {})
        )
        
        if existing_definition_response.get("error"):
            raise Exception(f"Failed to get existing definition: {existing_definition_response.get('error')}")
            
        return existing_definition_response

    def _create_combined_entities(self, new_entities: List[Dict[str, Any]], api_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Create combined entities from new entities and API response.
        
        :param new_entities: The list of new entities to add
        :param api_response: The API response containing definition parts
        :return: Combined list of entities
        :raises: Exception if unable to decode existing entities
        """
        # Extract the ReflexEntities.json part from the API response
        existing_definition = api_response.get("definition", {})
        existing_parts = existing_definition.get("parts", [])
        
        reflex_entities_part = None
        for part in existing_parts:
            if part.get("path") == "ReflexEntities.json":
                reflex_entities_part = part
                break
                
        if not reflex_entities_part:
            raise Exception("ReflexEntities.json not found in API response")
            
        # Decode the existing base64 payload
        try:
            existing_payload_b64 = reflex_entities_part.get("payload", "")
            existing_entities_json = base64.b64decode(existing_payload_b64).decode('utf-8')
            existing_entities = json.loads(existing_entities_json)
        except Exception as e:
            raise Exception(f"Failed to decode existing entities: {str(e)}")
        
        # Combine the existing entities with the new entities
        combined_entities: List[Dict[str, Any]] = existing_entities + new_entities
        
        return combined_entities

    def _update_item(self, workspace_id: str, artifact_id: str, combined_entities: List[Dict[str, Any]], existing_payload_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an activator artifact with combined entities.
        
        :param workspace_id: The workspace ID (UUID)
        :param artifact_id: The artifact ID to update
        :param combined_entities: The combined list of entities
        :param existing_payload_result: The existing payload result from API
        :return: Updated artifact details
        :raises: Exception if unable to update the artifact
        """
        connection = self._get_connection()
        
        # Get the existing parts structure (we need this to preserve other parts like .platform)
        existing_definition = existing_payload_result.get("definition", {})
        existing_parts = existing_definition.get("parts", [])
        
        # Create the updated payload
        combined_entities_json = json.dumps(combined_entities)
        combined_entities_b64 = base64.b64encode(combined_entities_json.encode('utf-8')).decode('utf-8')
        
        # Update the ReflexEntities.json part with combined entities
        updated_parts: List[Dict[str, Any]] = []
        for part in existing_parts:
            if part.get("path") == "ReflexEntities.json":
                updated_part: Dict[str, Any] = part.copy()
                updated_part["payload"] = combined_entities_b64
                updated_parts.append(updated_part)
            else:
                updated_parts.append(part)
                
        # Create the update payload
        update_payload: Dict[str, Any] = {
            "definition": {
                "parts": updated_parts
            }
        }
        
        # Update the existing artifact
        update_endpoint = f"/workspaces/{workspace_id}/reflexes/{artifact_id}/updateDefinition"
        result = run_async_operation(
            connection.execute_operation_and_return_error_in_dict("POST", update_endpoint, update_payload)
        )
        
        if result.get("error"):
            raise Exception(f"Failed to update artifact: {result.get('error')}")
        
        # augment result with a url back to the artifact
        result["url"] = f"{FABRIC_BASE_URL}/groups/{workspace_id}/reflexes/{artifact_id}"
        
        return result

    def _create_new_artifact(self, workspace_id: str, full_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new activator artifact.
        
        :param workspace_id: The workspace ID (UUID)
        :param full_payload: The complete payload for creating the artifact
        :return: Created artifact details
        """
        endpoint = f"/workspaces/{workspace_id}/reflexes"

        connection = self._get_connection()
        result = run_async_operation(connection.execute_operation_and_return_error_in_dict("POST", endpoint, full_payload))

        if not result.get("error"):
            # augment result with a url back to the artifact
            result["url"] = f"{FABRIC_BASE_URL}/groups/{workspace_id}/reflexes/{result.get('id', '')}"
        
        return result

    def _get_full_payload(self, entity_list: List[Dict[str, Any]], trigger_name: str) -> Dict[str, Any]:
        reflex_json = json.dumps(entity_list)
        reflex_b64 = base64.b64encode(reflex_json.encode('utf-8')).decode('utf-8')

        platform_data: dict[str, Any] = {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
            "metadata": {
                "type": "Reflex",
                "displayName": f"{trigger_name}",
                "description": f"{trigger_name}"
            },
            "config": {
                "version": "2.0",
                "logicalId": "4042fb10-1349-b4c0-4361-514b6b19c1fe"
            }
        }
        platform_b64 = base64.b64encode(json.dumps(platform_data).encode('utf-8')).decode('utf-8')

        payload: Dict[str, Any] = {
            "displayName": trigger_name,
            "description": trigger_name,
            "definition": {
                "parts": [
                    {
                        "path": "ReflexEntities.json",
                        "payload": reflex_b64,
                        "payloadType": "InlineBase64"
                    },
                    {
                        "path": ".platform",
                        "payload": platform_b64,
                        "payloadType": "InlineBase64"
                    }
                ]
            }
        }

        return payload


DEFAULT_ACTIVATOR_SERVICE = ActivatorService()
