import base64
import json
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from fabric_rti_mcp.utils.fabric_api_http_client import FabricHttpClientCache
from fabric_rti_mcp.common import GlobalFabricRTIConfig, logger
from fabric_rti_mcp.activator.activator_entity_generators import *

# Microsoft Fabric API configuration
FABRIC_CONFIG = GlobalFabricRTIConfig.from_env()


# Pydantic models for source types
class SourceBase(BaseModel):
    """Base class for all activator source types."""
    source_type: str = Field(..., description="The type of source (e.g., 'kql', 'eventstream')")


class KqlSource(SourceBase):
    """KQL source configuration for activator triggers."""
    source_type: str = Field(default="kql", description="Source type identifier")
    cluster_url: str = Field(..., description="The KQL cluster URL") 
    database: str = Field(..., description="The KQL database name")
    query: str = Field(..., description="The KQL query to monitor. The query MUST be appropriate for the schema of the underlying data, otherwise the alert will not function correctly")
    polling_frequency_minutes: int = Field(
        default=5, 
        description="Polling frequency in minutes. Must be one of: 5, 15, 60, 180, 360, 720, 1440 (defaults to 5)",
        ge=1,
        le=1440
    )

    class Config:
        extra = "forbid"


# Union type for all supported source types (extensible for future source types)
TriggerSource = Union[KqlSource]


class ActivatorService:
    """Service class for Fabric Activator operations."""

    def activator_list_artifacts(self, workspace_id: str) -> List[Dict[str, Any]]:
        """
        Use this tool to list all Activator artifacts in a workspace.
        
        :param workspace_id: The workspace ID (UUID)
        :return: List of activator artifacts
        """
        endpoint = f"/workspaces/{workspace_id}/items"
        result = FabricHttpClientCache.get_client().make_request("GET", endpoint)
        
        # Filter only Reflex (Activator) items if the result contains a list
        if isinstance(result, dict) and "value" in result and isinstance(result["value"], list):
            activators = [
                item
                for item in result["value"]
                if isinstance(item, dict) and item.get("type") == "Reflex"
            ]
            return activators
        elif isinstance(result, list):
            activators = [
                item
                for item in result
                if isinstance(item, dict) and item.get("type") == "Reflex"
            ]
            return activators
            
        return [result]

    def activator_create_trigger(
        self,
        workspace_id: str,
        trigger_name: str,
        source: TriggerSource,
        alert_recipient: str,
        alert_message: str,
        alert_headline: str,
        alert_type: str = "teams",
        artifact_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Use this tool create an alert that will fire when the source generates data.
        
        :param workspace_id: The workspace ID (UUID)
        :param trigger_name: Name of the trigger
        :param source: Source configuration (e.g., KqlSource)
        :param alert_recipient: Email address of the alert recipient
        :param alert_type: Type of alert - "teams" or "email" (defaults to "teams")
        :param alert_message: Alert message for the trigger
        :param alert_headline: Alert headline for the trigger
        :param artifact_id: If specified, the trigger will be created in the specified Activator artifact. If left blank, a new Activator artifact will be created.
        :return: Created trigger details:
            * url: URL back to the trigger in Fabric UI for further management
            * id: Artifact ID if a new one was created
            * displayName: Name of newly created trigger

        Critical:
        * This API call will NOT tell the caller if a KQL query is used which does not match the source data schema, so any KQL query should be double-checked upfront.
        """
        (container_entity, container_guid) = create_container_entity(trigger_name)
        
        # Handle different source types
        if isinstance(source, KqlSource):
            (source_entity, source_guid) = create_kql_source_entity(
                trigger_name,
                polling_frequency_minutes=source.polling_frequency_minutes,
                kql_query=source.query,
                database=source.database,
                cluster_hostname=source.cluster_url,
                container_id=container_guid,
                workspace_id=workspace_id
            )
        else:
            raise ValueError(f"Unsupported source type: {type(source)}")

        return self._create_trigger_with_source(
            workspace_id=workspace_id,
            trigger_name=trigger_name,
            container_entity=container_entity,
            container_guid=container_guid,
            source_entity=source_entity,
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
        alert_message: str,
        alert_headline: str,
        artifact_id: Optional[str] = None
    ) -> Dict[str, Any]:
        event_and_rule_entities = create_simple_event_rule_entities(
            trigger_name,
            container_id=container_guid,
            source_id=source_guid,
            message=alert_message,
            headline=alert_headline,
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
        # Get the existing artifact definition
        get_definition_endpoint = f"/workspaces/{workspace_id}/reflexes/{artifact_id}/getDefinition"
        existing_definition_response = FabricHttpClientCache.get_client().make_request(
            "POST", get_definition_endpoint, {}
        )
        
        if existing_definition_response.get("error"):
            raise Exception(f"Failed to get existing definition: {existing_definition_response.get('error')}")
            
        return existing_definition_response

    def _create_combined_entities(self, new_entities: List[Dict[str, Any]], api_response: Dict[str, Any]) -> List[Dict[str, Any]]:
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
        result = FabricHttpClientCache.get_client().make_request("POST", update_endpoint, update_payload)
        
        if result.get("error"):
            raise Exception(f"Failed to update artifact: {result.get('error')}")
        
        # augment result with a url back to the artifact
        result["url"] = f"{FABRIC_CONFIG.fabric_base_url}/groups/{workspace_id}/reflexes/{artifact_id}"
        
        return result

    def _create_new_artifact(self, workspace_id: str, full_payload: Dict[str, Any]) -> Dict[str, Any]:
        endpoint = f"/workspaces/{workspace_id}/reflexes"

        result = FabricHttpClientCache.get_client().make_request("POST", endpoint, full_payload)

        if not result.get("error"):
            # augment result with a url back to the artifact
            result["url"] = f"{FABRIC_CONFIG.fabric_base_url}/groups/{workspace_id}/reflexes/{result.get('id', '')}"
        
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
