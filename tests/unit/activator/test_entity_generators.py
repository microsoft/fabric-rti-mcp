import json
import pytest
from unittest.mock import patch, MagicMock

from fabric_rti_mcp.activator.activator_entity_generators import (
    create_container_entity,
    create_kql_source_entity,
    create_simple_event_rule_entities,
    generate_teams_binding,
    generate_email_binding,
    validate_polling_frequency,
    ALLOWED_POLLING_FREQUENCIES_MINUTES,
)


class TestEntityGenerators:
    """Unit tests for activator entity generator functions."""

    def test_validate_polling_frequency_valid_values(self):
        """Test that valid polling frequency values are accepted."""
        for minutes in ALLOWED_POLLING_FREQUENCIES_MINUTES:
            expected_seconds = minutes * 60
            result = validate_polling_frequency(minutes)
            assert result == expected_seconds

    def test_validate_polling_frequency_invalid_value(self):
        """Test that invalid polling frequency values raise ValueError."""
        with pytest.raises(ValueError, match="Polling frequency must be one of"):
            validate_polling_frequency(10)  # Invalid value

    def test_create_container_entity(self):
        """Test container entity creation."""
        trigger_name = "test_trigger"
        
        container_entity, container_guid = create_container_entity(trigger_name)
        
        # Verify structure
        assert isinstance(container_entity, dict)
        assert isinstance(container_guid, str)
        assert len(container_guid) > 0
        
        # Verify container entity content
        assert container_entity["type"] == "container-v1"
        assert container_entity["payload"]["name"] == trigger_name
        assert container_entity["payload"]["type"] == "unconstrained"
        assert container_entity["uniqueIdentifier"] == container_guid

    def test_create_kql_source_entity(self):
        """Test KQL source entity creation."""
        trigger_name = "test_kql_trigger"
        polling_frequency_minutes = 5
        kql_query = "MyTable | count"
        database = "TestDB"
        cluster_hostname = "https://test.kusto.windows.net"
        container_id = "container-123"
        workspace_id = "workspace-456"
        
        source_entity, source_guid = create_kql_source_entity(
            trigger_name=trigger_name,
            polling_frequency_minutes=polling_frequency_minutes,
            kql_query=kql_query,
            database=database,
            cluster_hostname=cluster_hostname,
            container_id=container_id,
            workspace_id=workspace_id
        )
        
        # Verify structure
        assert isinstance(source_entity, dict)
        assert isinstance(source_guid, str)
        assert len(source_guid) > 0
        
        # Verify source entity content
        assert source_entity["type"] == "kqlSource-v1"
        assert source_entity["payload"]["name"] == f"{trigger_name} source"
        assert source_entity["uniqueIdentifier"] == source_guid
        
        # Verify payload properties
        payload = source_entity["payload"]
        assert payload["runSettings"]["executionIntervalInSeconds"] == 300  # 5 minutes = 300 seconds
        assert payload["query"]["queryString"] == kql_query
        assert payload["eventhouseItem"]["databaseName"] == database
        assert payload["eventhouseItem"]["clusterHostName"] == cluster_hostname
        assert payload["parentContainer"]["targetUniqueIdentifier"] == container_id
        assert payload["metadata"]["workspaceId"] == workspace_id

    def test_create_kql_source_entity_with_long_polling_frequency(self):
        """Test KQL source entity creation with longer polling frequency."""
        polling_frequency_minutes = 60  # 1 hour
        
        source_entity, _ = create_kql_source_entity(
            trigger_name="test",
            polling_frequency_minutes=polling_frequency_minutes,
            kql_query="test",
            database="test",
            cluster_hostname="test",
            container_id="test",
            workspace_id="test"
        )
        
        # Verify polling frequency is stored correctly (60 minutes = 3600 seconds)
        payload = source_entity["payload"]
        assert payload["runSettings"]["executionIntervalInSeconds"] == 3600

    def test_generate_teams_binding(self):
        """Test Teams alert binding generation."""
        teams_recipient = "user@example.com"
        headline = "Test Headline"
        message = "Test Message"
        
        binding = generate_teams_binding(teams_recipient, headline, message)
        
        # Verify it's a JSON string
        assert isinstance(binding, str)
        
        # Parse the JSON to verify structure
        binding_data = json.loads(binding)
        assert binding_data["name"] == "TeamsBinding"
        assert binding_data["kind"] == "TeamsMessage"
        
        # Verify arguments contain recipient, headline, and message
        args = binding_data["arguments"]
        recipients_arg = next(arg for arg in args if arg["name"] == "recipients")
        assert recipients_arg["values"][0]["value"] == teams_recipient
        
        headline_arg = next(arg for arg in args if arg["name"] == "headline")
        assert headline_arg["values"][0]["value"] == headline
        
        message_arg = next(arg for arg in args if arg["name"] == "optionalMessage")
        assert message_arg["values"][0]["value"] == message

    def test_generate_email_binding(self):
        """Test email alert binding generation."""
        email_recipient = "user@example.com"
        headline = "Test Headline" 
        message = "Test Message"
        
        binding = generate_email_binding(email_recipient, headline, message)
        
        # Verify it's a JSON string
        assert isinstance(binding, str)
        
        # Parse the JSON to verify structure
        binding_data = json.loads(binding)
        assert binding_data["name"] == "EmailBinding"
        assert binding_data["kind"] == "EmailMessage"
        
        # Verify arguments contain recipient, headline, and message
        args = binding_data["arguments"]
        sentto_arg = next(arg for arg in args if arg["name"] == "sentTo")
        assert sentto_arg["values"][0]["value"] == email_recipient
        
        subject_arg = next(arg for arg in args if arg["name"] == "subject")
        assert subject_arg["values"][0]["value"] == headline

    def test_create_simple_event_rule_entities_with_teams_alert(self):
        """Test event and rule entities creation with Teams alert."""
        trigger_name = "test_teams_trigger"
        container_id = "container-123"
        source_id = "source-456"
        message = "Test alert message"
        headline = "Test Alert"
        alert_recipient = "user@example.com"
        alert_type = "teams"
        
        entities = create_simple_event_rule_entities(
            trigger_name=trigger_name,
            container_id=container_id,
            source_id=source_id,
            message=message,
            headline=headline,
            alert_recipient=alert_recipient,
            alert_type=alert_type
        )
        
        # Verify we get 2 entities (event and rule)
        assert isinstance(entities, list)
        assert len(entities) == 2
        
        # Both entities should be timeSeriesView-v1 type
        event_entity, rule_entity = entities[0], entities[1]
        
        assert event_entity["type"] == "timeSeriesView-v1"
        assert rule_entity["type"] == "timeSeriesView-v1"
        
        # Verify event entity
        assert event_entity["payload"]["name"] == f"{trigger_name} event"
        assert event_entity["payload"]["parentContainer"]["targetUniqueIdentifier"] == container_id
        assert event_entity["payload"]["definition"]["type"] == "Event"
        
        # Verify rule entity
        assert rule_entity["payload"]["name"] == f"{trigger_name} rule"
        assert rule_entity["payload"]["parentContainer"]["targetUniqueIdentifier"] == container_id
        assert rule_entity["payload"]["definition"]["type"] == "Rule"
        
        # Verify the rule definition contains Teams binding
        rule_instance = rule_entity["payload"]["definition"]["instance"]
        assert "TeamsBinding" in rule_instance
        assert alert_recipient in rule_instance

    def test_create_simple_event_rule_entities_with_email_alert(self):
        """Test event and rule entities creation with email alert."""
        trigger_name = "test_email_trigger"
        container_id = "container-123"
        source_id = "source-456"
        message = "Test email alert"
        headline = "Test Email Alert"
        alert_recipient = "user@example.com"
        alert_type = "email"
        
        entities = create_simple_event_rule_entities(
            trigger_name=trigger_name,
            container_id=container_id,
            source_id=source_id,
            message=message,
            headline=headline,
            alert_recipient=alert_recipient,
            alert_type=alert_type
        )
        
        # Verify we get 2 entities (event and rule)
        assert len(entities) == 2
        
        # Verify rule entity contains email binding
        rule_entity = entities[1]
        rule_instance = rule_entity["payload"]["definition"]["instance"]
        assert "EmailBinding" in rule_instance
        assert alert_recipient in rule_instance

    def test_create_simple_event_rule_entities_default_alert_type(self):
        """Test that default alert type is teams."""
        entities = create_simple_event_rule_entities(
            trigger_name="test",
            container_id="container",
            source_id="source",
            message="message",
            headline="headline",
            alert_recipient="user@example.com"
            # No alert_type specified - should default to teams
        )
        
        rule_entity = entities[1]
        rule_instance = rule_entity["payload"]["definition"]["instance"]
        assert "TeamsBinding" in rule_instance

    def test_entity_ids_are_unique(self):
        """Test that generated entity IDs are unique across multiple calls."""
        # Create multiple entities and collect their IDs
        ids = set()
        
        for i in range(10):
            container_entity, container_guid = create_container_entity(f"trigger_{i}")
            source_entity, source_guid = create_kql_source_entity(
                trigger_name=f"trigger_{i}",
                polling_frequency_minutes=5,
                kql_query="test",
                database="test",
                cluster_hostname="test",
                container_id=container_guid,
                workspace_id="test"
            )
            event_rule_entities = create_simple_event_rule_entities(
                trigger_name=f"trigger_{i}",
                container_id=container_guid,
                source_id=source_guid,
                message="test",
                headline="test",
                alert_recipient="test@example.com",
                alert_type="email"
            )
            
            # Collect all IDs
            ids.add(container_entity["uniqueIdentifier"])
            ids.add(source_entity["uniqueIdentifier"])
            for entity in event_rule_entities:
                ids.add(entity["uniqueIdentifier"])
        
        # Verify all IDs are unique (should have 40 unique IDs: 10 * (container + source + event + rule))
        assert len(ids) == 40

    def test_entity_structure_consistency(self):
        """Test that entities have consistent required fields."""
        container_entity, container_guid = create_container_entity("test")
        source_entity, source_guid = create_kql_source_entity(
            trigger_name="test",
            polling_frequency_minutes=5,
            kql_query="test",
            database="test", 
            cluster_hostname="test",
            container_id=container_guid,
            workspace_id="test"
        )
        event_rule_entities = create_simple_event_rule_entities(
            trigger_name="test",
            container_id=container_guid,
            source_id=source_guid,
            message="test",
            headline="test", 
            alert_recipient="test@example.com",
            alert_type="teams"
        )
        
        all_entities = [container_entity, source_entity] + event_rule_entities
        
        # Verify all entities have required fields
        for entity in all_entities:
            assert "uniqueIdentifier" in entity
            assert "type" in entity
            assert "payload" in entity
            assert isinstance(entity["uniqueIdentifier"], str)
            assert isinstance(entity["type"], str)
            assert isinstance(entity["payload"], dict)
            
            # All payloads should have a name
            assert "name" in entity["payload"]
            assert isinstance(entity["payload"]["name"], str)

    def test_kql_source_metadata_structure(self):
        """Test that KQL source metadata has expected structure."""
        source_entity, _ = create_kql_source_entity(
            trigger_name="test",
            polling_frequency_minutes=5,
            kql_query="test query",
            database="testdb",
            cluster_hostname="https://test.kusto.windows.net",
            container_id="container-123",
            workspace_id="workspace-456"
        )
        
        metadata = source_entity["payload"]["metadata"]
        assert metadata["workspaceId"] == "workspace-456"
        assert "measureName" in metadata
        assert "querySetId" in metadata  
        assert "queryId" in metadata

    def test_event_rule_definition_structure(self):
        """Test that event and rule definitions have proper JSON structure."""
        entities = create_simple_event_rule_entities(
            trigger_name="test",
            container_id="container-123",
            source_id="source-456", 
            message="test message",
            headline="test headline",
            alert_recipient="test@example.com",
            alert_type="teams"
        )
        
        event_entity, rule_entity = entities[0], entities[1]
        
        # Verify event definition instance is valid JSON
        event_instance = event_entity["payload"]["definition"]["instance"]
        event_data = json.loads(event_instance)
        assert event_data["templateId"] == "SourceEvent"
        assert "templateVersion" in event_data
        assert "steps" in event_data
        
        # Verify rule definition instance is valid JSON
        rule_instance = rule_entity["payload"]["definition"]["instance"]  
        rule_data = json.loads(rule_instance)
        assert rule_data["templateId"] == "EventTrigger"
        assert "templateVersion" in rule_data
        assert "steps" in rule_data
