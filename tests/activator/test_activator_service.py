"""
Tests for Data Activator functionality.
"""
import pytest
from unittest.mock import patch

from fabric_rti_mcp.activator.activator_service import ActivatorService


@pytest.fixture
def activator_service():
    """Create an ActivatorService instance for testing."""
    with patch("fabric_rti_mcp.activator.activator_service.FabricConnection"):
        return ActivatorService()


def test_build_reflex_definition(activator_service):
    """Test building a reflex definition."""
    definition = activator_service._build_reflex_definition(
        alert_name="Test Alert",
        kql_query="MyTable | count",
        cluster_uri="https://test.kusto.windows.net", 
        database="testdb",
        frequency_minutes=60,
        notification_recipients=["test@example.com", "teams_user"],
        description="Test alert description"
    )
    
    assert "streams" in definition
    assert "entities" in definition
    assert "rules" in definition
    
    # Check stream configuration
    stream = definition["streams"][0]
    assert stream["sourceType"] == "KQLQueryset"
    assert stream["sourceConfiguration"]["clusterUri"] == "https://test.kusto.windows.net"
    assert stream["sourceConfiguration"]["query"] == "MyTable | count"
    assert stream["sourceConfiguration"]["refreshFrequencyMinutes"] == 60
    
    # Check rule configuration
    rule = definition["rules"][0]
    assert rule["name"] == "Test Alert"
    assert rule["description"] == "Test alert description"
    assert rule["condition"]["type"] == "OnEachEvent"
    assert len(rule["actions"]) == 2  # Email and Teams notifications


def test_build_reflex_definition_email_action(activator_service):
    """Test that email actions are correctly configured."""
    definition = activator_service._build_reflex_definition(
        alert_name="Email Alert",
        kql_query="MyTable | count",
        cluster_uri="https://test.kusto.windows.net",
        database="testdb", 
        frequency_minutes=30,
        notification_recipients=["user@example.com"],
        description="Email test"
    )
    
    actions = definition["rules"][0]["actions"]
    email_action = actions[0]
    
    assert email_action["type"] == "Email"
    assert email_action["configuration"]["to"] == ["user@example.com"]
    assert "Email Alert" in email_action["configuration"]["subject"]


def test_build_reflex_definition_teams_action(activator_service):
    """Test that Teams actions are correctly configured."""
    definition = activator_service._build_reflex_definition(
        alert_name="Teams Alert",
        kql_query="MyTable | count",
        cluster_uri="https://test.kusto.windows.net",
        database="testdb",
        frequency_minutes=30,
        notification_recipients=["teams_user"],
        description="Teams test"
    )
    
    actions = definition["rules"][0]["actions"]
    teams_action = actions[0]
    
    assert teams_action["type"] == "Teams"
    assert teams_action["configuration"]["recipient"] == "teams_user"
    assert "Teams Alert" in teams_action["configuration"]["title"]
