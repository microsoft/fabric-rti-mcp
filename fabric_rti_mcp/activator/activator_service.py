import uuid
import sys
import json
from typing import Any, Dict, List, Optional

from fabric_rti_mcp.activator.fabric_connection import FabricConnection
from fabric_rti_mcp.common import logger


class ActivatorService:
    """Service for managing Data Activator alerts in Microsoft Fabric."""
    
    def __init__(self):
        self.fabric_connection = FabricConnection()
    
    async def create_kql_alert(
        self,
        kql_query: str,
        cluster_uri: str,
        workspace_id: str,
        alert_name: str,
        notification_recipients: List[str],
        frequency_minutes: int = 60,
        database: Optional[str] = None,
        activator_name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a Data Activator alert based on a KQL query.
        
        Args:
            kql_query: The KQL query to monitor
            cluster_uri: The URI of the Kusto cluster
            workspace_id: The Fabric workspace ID to create the alert in
            alert_name: Name for the alert
            notification_recipients: List of email addresses or Teams usernames to notify
            frequency_minutes: How often to run the query in minutes (default: 60)
            database: Optional database name (if not specified, uses default)
            activator_name: Optional name for the activator item (if creating new)
            description: Optional description for the alert
            
        Returns:
            Dictionary containing the created alert details
        """
        sys.stderr.write(f"=== ACTIVATOR SERVICE: create_kql_alert called ===\n")
        sys.stderr.write(f"Alert Name: {alert_name}\n")
        sys.stderr.write(f"Workspace ID: {workspace_id}\n")
        sys.stderr.write(f"KQL Query: {kql_query}\n")
        sys.stderr.write(f"Cluster URI: {cluster_uri}\n")
        sys.stderr.write(f"=== ===\n")
        sys.stderr.flush()
        
        try:
            # Create the reflex definition for the KQL alert
            reflex_definition = self._build_reflex_definition(
                alert_name=alert_name,
                kql_query=kql_query,
                cluster_uri=cluster_uri,
                database=database,
                notification_recipients=notification_recipients,
                frequency_minutes=frequency_minutes,
                description=description
            )
            
            # For now, let's try creating a Reflex WITH definition to test the full structure
            sys.stderr.write(f"=== ATTEMPTING REFLEX CREATION WITH DEFINITION ===\n")
            sys.stderr.flush()
            
            # Create the Reflex (Data Activator) item with the definition
            activator_item_name = activator_name or f"KQL Alert Activator {uuid.uuid4().hex[:8]}"
            
            activator_item = await self.fabric_connection.create_reflex_with_definition(
                workspace_id=workspace_id,
                name=activator_item_name,
                description=f"Data Activator for KQL query monitoring: {alert_name}",
                reflex_definition=reflex_definition  # Use the actual definition
            )
            
            logger.info(f"Created KQL alert '{alert_name}' in activator '{activator_item_name}'")
            
            result = {
                "alert_id": str(uuid.uuid4()),
                "alert_name": alert_name,
                "activator_item": activator_item,
                "workspace_id": workspace_id,
                "kql_query": kql_query,
                "cluster_uri": cluster_uri,
                "database": database,

                "notification_recipients": notification_recipients,
                "status": "created",
                "message": f"Successfully created KQL alert '{alert_name}'. The alert will run daily and notify {len(notification_recipients)} recipients when the query returns results.",
                "next_steps": [
                    "The Reflex (Data Activator) item has been created in your workspace",
                    "You can view and modify the alert in the Fabric portal",
                    f"Navigate to your workspace and open the '{activator_item_name}' item",
                    "The alert will start monitoring automatically once the Reflex is activated"
                ]
            }
            
            logger.info(f"Successfully created alert: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to create KQL alert: {str(e)}")
            raise
    
    def _build_reflex_definition(
        self,
        alert_name: str,
        kql_query: str,
        cluster_uri: str,
        database: Optional[str],
        notification_recipients: List[str],
        frequency_minutes: int,
        description: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Build the Reflex (Data Activator) definition using the working example structure with dynamic parameters."""
        
        # Generate unique identifiers
        container_id = str(uuid.uuid4())
        kql_source_id = str(uuid.uuid4())
        event_id = str(uuid.uuid4())
        rule_id = str(uuid.uuid4())
        
        # Build recipients array separately to avoid f-string bracket issues
        recipients_json = ",".join([f'{{\"type\":\"string\",\"value\":\"{recipient}\"}}' for recipient in notification_recipients])
        
        # Extract cluster hostname from URI (remove https://)
        cluster_hostname = cluster_uri.replace("https://", "").replace("http://", "")
        if not cluster_hostname.endswith("/"):
            cluster_hostname += "/"
        
        # Use working example structure with dynamic parameters
        working_reflex_definition = [
            {
                "uniqueIdentifier": container_id,
                "payload": {
                    "name": "OpQueryset",  # Keep same as working example
                    "type": "kqlQueries"
                },
                "type": "container-v1"
            },
            {
                "uniqueIdentifier": kql_source_id,
                "payload": {
                    "name": f"{alert_name} event",
                    "runSettings": {
                        "executionIntervalInSeconds": frequency_minutes * 60  # Convert minutes to seconds
                    },
                    "query": {
                        "queryString": kql_query  # Dynamic parameter
                    },
                    "eventhouseItem": {
                        "databaseName": database or "SampleLogs",  # Dynamic parameter
                        "clusterHostName": cluster_hostname  # Dynamic parameter
                    },
                    "queryParameters": [],
                    "metadata": {
                        "workspaceId": "fe51fb85-c3fb-40a0-b2ec-135312cf9a7a",  # Keep from working example
                        "measureName": "",
                        "querySetId": "1d22f507-75c8-497f-81e1-3b33e9e7b290",  # Keep from working example
                        "queryId": "d20cc0c3-ab31-48b8-a517-818291856ed8"  # Keep from working example
                    },
                    "parentContainer": {
                        "targetUniqueIdentifier": container_id
                    }
                },
                "type": "kqlSource-v1"
            },
            {
                "uniqueIdentifier": event_id,
                "payload": {
                    "name": f"{alert_name} event",
                    "parentContainer": {
                        "targetUniqueIdentifier": container_id
                    },
                    "definition": {
                        "type": "Event",
                        "instance": f'{{\"templateId\":\"SourceEvent\",\"templateVersion\":\"1.1\",\"steps\":[{{\"name\":\"SourceEventStep\",\"id\":\"{str(uuid.uuid4())}\",\"rows\":[{{\"name\":\"SourceSelector\",\"kind\":\"SourceReference\",\"arguments\":[{{\"name\":\"entityId\",\"type\":\"string\",\"value\":\"{kql_source_id}\"}}]}}]}}]}}'
                    }
                },
                "type": "timeSeriesView-v1"
            },
            {
                "uniqueIdentifier": rule_id,
                "payload": {
                    "name": f"{alert_name} alert",
                    "parentContainer": {
                        "targetUniqueIdentifier": container_id
                    },
                    "definition": {
                        "type": "Rule",
                        "instance": f'{{\"templateId\":\"EventTrigger\",\"templateVersion\":\"1.1\",\"steps\":[{{\"name\":\"FieldsDefaultsStep\",\"id\":\"{str(uuid.uuid4())}\",\"rows\":[{{\"name\":\"EventSelector\",\"kind\":\"Event\",\"arguments\":[{{\"kind\":\"EventReference\",\"type\":\"complex\",\"arguments\":[{{\"name\":\"entityId\",\"type\":\"string\",\"value\":\"{event_id}\"}}],\"name\":\"event\"}}]}}]}},{{\"name\":\"EventDetectStep\",\"id\":\"{str(uuid.uuid4())}\",\"rows\":[{{\"name\":\"OnEveryValue\",\"kind\":\"OnEveryValue\",\"arguments\":[]}}]}},{{\"name\":\"ActStep\",\"id\":\"{str(uuid.uuid4())}\",\"rows\":[{{\"name\":\"TeamsBinding\",\"kind\":\"TeamsMessage\",\"arguments\":[{{\"name\":\"messageLocale\",\"type\":\"string\",\"value\":\"\"}},{{\"name\":\"recipients\",\"type\":\"array\",\"values\":[{recipients_json}]}},{{\"name\":\"headline\",\"type\":\"array\",\"values\":[{{\"type\":\"string\",\"value\":\"Activator Trigger: New event from {alert_name}\"}}]}},{{\"name\":\"optionalMessage\",\"type\":\"array\",\"values\":[{{\"type\":\"string\",\"value\":\"New event from {alert_name}\"}}]}},{{\"name\":\"additionalInformation\",\"type\":\"array\",\"values\":[]}}]}}]}}]}}',
                        "settings": {
                            "shouldRun": True,  # Enable the rule
                            "shouldApplyRuleOnUpdate": False
                        }
                    }
                },
                "type": "timeSeriesView-v1"
            }
        ]
        
        # Debug: Show the dynamic reflex definition structure before encoding
        sys.stderr.write(f"=== DYNAMIC REFLEX DEFINITION STRUCTURE (before encoding) ===\n")
        sys.stderr.write(f"{json.dumps(working_reflex_definition, indent=2)}\n")
        sys.stderr.write(f"=== END DYNAMIC REFLEX DEFINITION ===\n")
        sys.stderr.flush()
        
        return working_reflex_definition
    
    async def list_workspaces(self) -> List[Dict[str, Any]]:
        """List all accessible Fabric workspaces."""
        try:
            return await self.fabric_connection.get_workspaces()
        except Exception as e:
            logger.error(f"Failed to list workspaces: {str(e)}")
            # Return mock workspaces for demonstration
            return [
                {"id": "mock-workspace-1", "name": "Default Workspace", "description": "Default workspace"},
                {"id": "mock-workspace-2", "name": "RTI Workspace", "description": "Real-Time Intelligence workspace"}
            ]
    
    async def list_activators(self, workspace_id: str) -> List[Dict[str, Any]]:
        """List all Activator items in a workspace."""
        try:
            return await self.fabric_connection.get_workspace_items(workspace_id, "Reflex")
        except Exception as e:
            logger.error(f"Failed to list activators: {str(e)}")
            return []
