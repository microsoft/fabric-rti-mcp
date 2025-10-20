"""
Manual integration test for activator service.
"""
import argparse
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add the project root to the path so we can import the service
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fabric_rti_mcp.activator.activator_service import DEFAULT_ACTIVATOR_SERVICE, KqlSource


def create_email_trigger_new_artifact(
    workspace_id: str, 
    kql_cluster_url: str, 
    kql_database: str, 
    kql_query: str,
    timestamp: str,
    alert_recipient: str,
    polling_frequency_in_minutes: int
) -> str:
    """
    Create an email trigger in a new artifact.
    
    Args:
        workspace_id: The Fabric workspace ID
        kql_cluster_url: The KQL cluster URL
        kql_database: The KQL database name
        kql_query: The KQL query to use for the trigger
        timestamp: Timestamp string for naming
        alert_recipient: Email address for alerts
        polling_frequency_in_minutes: Polling frequency in minutes
        
    Returns:
        The artifact ID of the created artifact
        
    Raises:
        Exception: If trigger creation fails
    """
    print("=" * 50)
    print("STEP 1: Creating email trigger (new artifact)")
    print("=" * 50)
    
    email_trigger_name = f"EmailTrigger_{timestamp}"
    email_alert_message = "Email alert from activator integration test"
    email_alert_headline = "Test Email Activator Alert"
    
    print(f"Trigger name: {email_trigger_name}")
    print(f"Alert type: email")
    print(f"Alert recipient: {alert_recipient}")
    print(f"Polling frequency: {polling_frequency_in_minutes} minutes")
    print(f"Creating new artifact...")
    print()
    
    try:
        # Create KQL source model
        kql_source = KqlSource(
            cluster_url=kql_cluster_url,
            database=kql_database,
            query=kql_query,
            polling_frequency_minutes=polling_frequency_in_minutes
        )
        
        email_result = DEFAULT_ACTIVATOR_SERVICE.activator_create_trigger(
            workspace_id=workspace_id,
            trigger_name=email_trigger_name,
            source=kql_source,
            alert_recipient=alert_recipient,
            alert_type="email",
            artifact_id=None,  # Create new artifact
            alert_message=email_alert_message,
            alert_headline=email_alert_headline
        )
        
        print("✅ Email trigger creation completed successfully!")
        print(f"Email trigger result: {email_result}")
        
        # Extract the artifact ID from the result
        if email_result.get("error"):
            raise Exception(f"Failed to create email trigger: {email_result.get('error')}")
        
        # Get the artifact ID - try different possible locations
        artifact_id = email_result.get("id") or email_result.get("artifactId") or email_result.get("artifact_id")
        if not artifact_id:
            print(f"⚠️  Could not extract artifact ID from result. Available keys: {list(email_result.keys())}")
            print(f"Full result: {email_result}")
            raise Exception("Could not extract artifact ID from email trigger creation result")
        
        print(f"✅ Created artifact ID: {artifact_id}")
        print()
        
        return artifact_id
        
    except Exception as e:
        print(f"❌ Error creating email trigger: {e}")
        raise


def create_teams_trigger_existing_artifact(
    workspace_id: str, 
    kql_cluster_url: str, 
    kql_database: str, 
    kql_query: str,
    timestamp: str,
    alert_recipient: str,
    polling_frequency_in_minutes: int,
    artifact_id: str
) -> Dict[str, Any]:
    """
    Create a teams trigger in an existing artifact.
    
    Args:
        workspace_id: The Fabric workspace ID
        kql_cluster_url: The KQL cluster URL
        kql_database: The KQL database name
        kql_query: The KQL query to use for the trigger
        timestamp: Timestamp string for naming
        alert_recipient: Email address for alerts
        polling_frequency_in_minutes: Polling frequency in minutes
        artifact_id: Existing artifact ID to add trigger to
        
    Returns:
        The result dictionary from trigger creation
        
    Raises:
        Exception: If trigger creation fails
    """
    print("=" * 50)
    print("STEP 2: Creating teams trigger (existing artifact)")
    print("=" * 50)
    
    teams_trigger_name = f"TeamsTrigger_{timestamp}"
    teams_alert_message = "Teams alert from activator integration test"
    teams_alert_headline = "Test Teams Activator Alert"
    
    print(f"Trigger name: {teams_trigger_name}")
    print(f"Alert type: teams")
    print(f"Alert recipient: {alert_recipient}")
    print(f"Polling frequency: {polling_frequency_in_minutes} minutes")
    print(f"Adding to existing artifact: {artifact_id}")
    print()
    
    try:
        # Create KQL source model
        kql_source = KqlSource(
            cluster_url=kql_cluster_url,
            database=kql_database,
            query=kql_query,
            polling_frequency_minutes=polling_frequency_in_minutes
        )
        
        teams_result = DEFAULT_ACTIVATOR_SERVICE.activator_create_trigger(
            workspace_id=workspace_id,
            trigger_name=teams_trigger_name,
            source=kql_source,
            alert_recipient=alert_recipient,
            alert_type="teams",
            artifact_id=artifact_id,  # Add to existing artifact
            alert_message=teams_alert_message,
            alert_headline=teams_alert_headline
        )
        
        print("✅ Teams trigger creation completed successfully!")
        print(f"Teams trigger result: {teams_result}")
        print()
        
        return teams_result
        
    except Exception as e:
        print(f"❌ Error creating teams trigger: {e}")
        raise


def verify_artifact_in_list(workspace_id: str, artifact_id: str) -> None:
    """
    Verify that the created artifact appears in the list of activator artifacts.
    
    Args:
        workspace_id: The Fabric workspace ID
        artifact_id: The artifact ID to verify
        
    Raises:
        Exception: If verification fails
    """
    print("=" * 50)
    print("STEP 3: Verifying artifact in list")
    print("=" * 50)
    
    print(f"Listing activator artifacts in workspace: {workspace_id}")
    print(f"Looking for artifact ID: {artifact_id}")
    print()
    
    try:
        artifacts_list = DEFAULT_ACTIVATOR_SERVICE.activator_list_artifacts(workspace_id=workspace_id)
        
        print(f"✅ Successfully retrieved artifacts list")
        print(f"Found {len(artifacts_list)} activator artifacts in workspace")
        
        # Look for our artifact ID in the list
        found_artifact = None
        for artifact in artifacts_list:
            if artifact.get("id") == artifact_id:
                found_artifact = artifact
                break
        
        if found_artifact:
            print(f"✅ Successfully found our artifact in the list!")
            print(f"Artifact details:")
            print(f"  - ID: {found_artifact.get('id')}")
            print(f"  - Display Name: {found_artifact.get('displayName', 'N/A')}")
            print(f"  - Description: {found_artifact.get('description', 'N/A')}")
            print(f"  - Type: {found_artifact.get('type', 'N/A')}")
            print(f"  - Workspace ID: {found_artifact.get('workspaceId', 'N/A')}")
        else:
            print(f"❌ Artifact {artifact_id} not found in the list!")
            print(f"Available artifact IDs:")
            for artifact in artifacts_list:
                print(f"  - {artifact.get('id', 'Unknown ID')}: {artifact.get('displayName', 'Unknown Name')}")
            raise Exception(f"Created artifact {artifact_id} was not found in the workspace artifacts list")
        
        print()
        
    except Exception as e:
        print(f"❌ Error verifying artifact in list: {e}")
        raise


def test_activator_triggers_sequence(workspace_id: str, kql_cluster_url: str, kql_database: str, kql_query: str):
    """
    Manual integration test for create_activator_trigger_on_kql_source.
    This test creates two triggers in sequence:
    1. First trigger with email alerts (creates new artifact)
    2. Second trigger with teams alerts (adds to the created artifact)
    
    Args:
        workspace_id: The Fabric workspace ID
        kql_cluster_url: The KQL cluster URL
        kql_database: The KQL database name
        kql_query: The KQL query to use for the trigger
    """
    print(f"Testing activator trigger creation sequence...")
    print(f"Workspace ID: {workspace_id}")
    print(f"KQL Cluster URL: {kql_cluster_url}")
    print(f"KQL Database: {kql_database}")
    print(f"KQL Query: {kql_query}")
    print()
    
    # Use sensible default values for other parameters
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    alert_recipient = "test@example.com"
    polling_frequency_in_minutes = 5  # 5 minutes
    
    # Step 1: Create email trigger in new artifact
    artifact_id = create_email_trigger_new_artifact(
        workspace_id=workspace_id,
        kql_cluster_url=kql_cluster_url,
        kql_database=kql_database,
        kql_query=kql_query,
        timestamp=timestamp,
        alert_recipient=alert_recipient,
        polling_frequency_in_minutes=polling_frequency_in_minutes
    )
    
    # Step 2: Create teams trigger in existing artifact
    create_teams_trigger_existing_artifact(
        workspace_id=workspace_id,
        kql_cluster_url=kql_cluster_url,
        kql_database=kql_database,
        kql_query=kql_query,
        timestamp=timestamp,
        alert_recipient=alert_recipient,
        polling_frequency_in_minutes=polling_frequency_in_minutes,
        artifact_id=artifact_id
    )
    
    # Step 3: Verify the artifact exists in the list
    verify_artifact_in_list(workspace_id=workspace_id, artifact_id=artifact_id)
    
    # Summary
    print("=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"✅ Success")
    print()
    print("🎉 Integration test completed successfully!")


def main():
    """Main entry point for the test."""
    parser = argparse.ArgumentParser(description="Test activator trigger creation sequence")
    parser.add_argument("--workspace-id", required=True, 
                       help="The Fabric workspace ID (UUID)")
    parser.add_argument("--kql-cluster-url", required=True,
                       help="The KQL cluster URL (e.g., https://mycluster.kusto.windows.net)")
    parser.add_argument("--kql-database", required=True,
                       help="The KQL database name")
    parser.add_argument("--kql-query", required=True,
                       help="The KQL query to use for the trigger")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Fabric RTI MCP - Activator Service Integration Test")
    print("=" * 60)
    print("This test will:")
    print("1. Create an email trigger in a new artifact")
    print("2. Add a teams trigger to the same artifact")
    print("3. Verify the artifact appears in the list of activator artifacts")
    print("=" * 60)
    print()
    
    test_activator_triggers_sequence(
        workspace_id=args.workspace_id,
        kql_cluster_url=args.kql_cluster_url,
        kql_database=args.kql_database,
        kql_query=args.kql_query
    )


if __name__ == "__main__":
    main()
