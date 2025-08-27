from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from fabric_rti_mcp.activator.activator_service import ActivatorService
from fabric_rti_mcp.common import logger


# Global service instance
_activator_service: ActivatorService | None = None


def get_activator_service() -> ActivatorService:
    """Get or create the global activator service instance."""
    global _activator_service
    if _activator_service is None:
        _activator_service = ActivatorService()
    return _activator_service


def register_tools(mcp: FastMCP) -> None:
    """Register Data Activator tools with the MCP server."""
    mcp.add_tool(
        create_data_activator_alert,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
    )
    mcp.add_tool(
        list_fabric_workspaces,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )
    mcp.add_tool(
        list_workspace_activators,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
    )


async def create_data_activator_alert(
    kql_query: str,
    cluster_uri: str,
    workspace_id: str,
    alert_name: str,
    notification_recipients: List[str],
    frequency_minutes: int = 60,
    database: str | None = None,
    activator_name: str | None = None,
    description: str | None = None
) -> List[Dict[str, Any]]:
    """
    Create a Data Activator alert that monitors a KQL query and sends notifications.
    
    This tool creates an alert in Microsoft Fabric Data Activator that:
    1. Runs the specified KQL query at regular intervals (default: every hour)
    2. Triggers notifications when the query returns results
    3. Sends Teams messages and/or emails to specified recipients
    
    :param kql_query: The KQL query to monitor for anomalies or conditions
    :param cluster_uri: The URI of the Kusto cluster (e.g., https://mycluster.westus.kusto.windows.net)
    :param workspace_id: The Fabric workspace ID where the alert should be created
    :param alert_name: A descriptive name for the alert
    :param notification_recipients: List of email addresses or Teams usernames to notify
    :param frequency_minutes: How often to run the query in minutes (default: 60)
    :param database: Optional database name. If not provided, uses the default database
    :param activator_name: Optional name for the activator item. If not provided, generates one
    :param description: Optional description for the alert
    :return: List containing the alert creation result
    """
    import sys
    # Try writing to a debug file as well as stderr
    try:
        with open("c:/temp/fabric_debug.log", "a") as f:
            f.write(f"=== ACTIVATOR TOOL: create_data_activator_alert called ===\n")
            f.write(f"Alert Name: {alert_name}\n")
            f.write(f"Workspace ID: {workspace_id}\n")
            f.write(f"Cluster URI: {cluster_uri}\n")
            f.flush()
    except:
        pass
    
    sys.stderr.write(f"=== ACTIVATOR TOOL: create_data_activator_alert called ===\n")
    sys.stderr.write(f"Alert Name: {alert_name}\n")
    sys.stderr.write(f"Workspace ID: {workspace_id}\n")
    sys.stderr.write(f"Cluster URI: {cluster_uri}\n")
    sys.stderr.flush()
    
    try:
        service = get_activator_service()
        
        # Validate inputs
        if not kql_query.strip():
            raise ValueError("KQL query cannot be empty")
        
        if not cluster_uri.strip():
            raise ValueError("Cluster URI cannot be empty")
        
        if not workspace_id.strip():
            raise ValueError("Workspace ID cannot be empty")
        
        if not alert_name.strip():
            raise ValueError("Alert name cannot be empty")
        
        if not notification_recipients:
            raise ValueError("At least one notification recipient must be specified")
        
        if frequency_minutes < 1:
            raise ValueError("Frequency must be at least 1 minute")
        
        # Validate KQL query is safe (basic validation)
        dangerous_keywords = ['.drop', '.delete', '.clear', '.set-or-replace', '.alter']
        query_lower = kql_query.lower()
        for keyword in dangerous_keywords:
            if keyword in query_lower:
                raise ValueError(f"KQL query contains potentially dangerous keyword: {keyword}")
        
        logger.info(f"Creating Data Activator alert '{alert_name}' for query: {kql_query[:100]}...")
        
        result = await service.create_kql_alert(
            kql_query=kql_query,
            cluster_uri=cluster_uri,
            workspace_id=workspace_id,
            alert_name=alert_name,
            notification_recipients=notification_recipients,
            frequency_minutes=frequency_minutes,
            database=database,
            activator_name=activator_name,
            description=description
        )
        
        return [result]
        
    except Exception as e:
        logger.error(f"Failed to create Data Activator alert: {str(e)}")
        return [{"error": str(e), "status": "failed"}]


async def list_fabric_workspaces() -> List[Dict[str, Any]]:
    """
    List all accessible Microsoft Fabric workspaces.
    
    This tool retrieves all Fabric workspaces that the current user has access to.
    Use this to find the workspace_id needed for creating alerts.
    
    :return: List of workspace information including IDs, names, and descriptions
    """
    try:
        service = get_activator_service()
        workspaces = await service.list_workspaces()
        
        logger.info(f"Retrieved {len(workspaces)} accessible workspaces")
        return workspaces
        
    except Exception as e:
        logger.error(f"Failed to list workspaces: {str(e)}")
        return [{"error": str(e), "status": "failed"}]


async def list_workspace_activators(workspace_id: str) -> List[Dict[str, Any]]:
    """
    List all Data Activator items in a specific workspace.
    
    This tool shows all existing Activator (Reflex) items in the specified workspace.
    
    :param workspace_id: The Fabric workspace ID to list activators from
    :return: List of activator items in the workspace
    """
    try:
        service = get_activator_service()
        
        if not workspace_id.strip():
            raise ValueError("Workspace ID cannot be empty")
        
        activators = await service.list_activators(workspace_id)
        
        logger.info(f"Retrieved {len(activators)} activators from workspace {workspace_id}")
        return activators
        
    except Exception as e:
        logger.error(f"Failed to list activators: {str(e)}")
        return [{"error": str(e), "status": "failed"}]
