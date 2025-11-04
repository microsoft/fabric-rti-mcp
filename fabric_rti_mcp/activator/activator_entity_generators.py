import uuid
from typing import Any, Dict, List, Optional

# Shared constants
TEMPLATE_VERSION = "1.2.2"


ALLOWED_POLLING_FREQUENCIES_MINUTES = {5, 15, 60, 180, 360, 720, 1440}


def validate_polling_frequency(polling_frequency_minutes: int) -> int:
    """
    Validate and convert polling frequency from minutes to seconds.
    
    :param polling_frequency_minutes: Polling frequency in minutes
    :return: Polling frequency in seconds
    :raises ValueError: If the polling frequency is not allowed
    """
    if polling_frequency_minutes not in ALLOWED_POLLING_FREQUENCIES_MINUTES:
        allowed_values = sorted(ALLOWED_POLLING_FREQUENCIES_MINUTES)
        raise ValueError(f"Polling frequency must be one of {allowed_values} minutes. Got: {polling_frequency_minutes}")
    
    return polling_frequency_minutes * 60


def generate_teams_binding(alert_recipient: str, headline: str, message: str) -> str:
    """
    Generate the Teams binding configuration for activator rules.
    
    Args:
        alert_recipient: Email address of the alert recipient
        headline: Alert headline text
        message: Alert message text
    
    Returns:
        JSON string representation of the Teams binding configuration
    """
    return f'{{\"name\":\"TeamsBinding\",\"kind\":\"TeamsMessage\",\"arguments\":[{{\"name\":\"messageLocale\",\"type\":\"string\",\"value\":\"\"}},{{\"name\":\"recipients\",\"type\":\"array\",\"values\":[{{\"type\":\"string\",\"value\":\"{alert_recipient}\"}}]}},{{\"name\":\"headline\",\"type\":\"array\",\"values\":[{{\"type\":\"string\",\"value\":\"{headline}\"}}]}},{{\"name\":\"optionalMessage\",\"type\":\"array\",\"values\":[{{\"type\":\"string\",\"value\":\"{message}\"}}]}},{{\"name\":\"additionalInformation\",\"type\":\"array\",\"values\":[]}}]}}'


def generate_email_binding(alert_recipient: str, headline: str, message: str) -> str:
    """
    Generate the Email binding configuration for activator rules.
    
    Args:
        alert_recipient: Email address of the alert recipient
        headline: Alert headline text
        message: Alert message text
    
    Returns:
        JSON string representation of the Email binding configuration
    """
    return f'{{\"name\":\"EmailBinding\",\"kind\":\"EmailMessage\",\"arguments\":[{{\"name\":\"messageLocale\",\"type\":\"string\",\"value\":\"\"}},{{\"name\":\"sentTo\",\"type\":\"array\",\"values\":[{{\"type\":\"string\",\"value\":\"{alert_recipient}\"}}]}},{{\"name\":\"copyTo\",\"type\":\"array\",\"values\":[]}},{{\"name\":\"bCCTo\",\"type\":\"array\",\"values\":[]}},{{\"name\":\"subject\",\"type\":\"array\",\"values\":[{{\"type\":\"string\",\"value\":\"{headline}\"}}]}},{{\"name\":\"headline\",\"type\":\"array\",\"values\":[{{\"type\":\"string\",\"value\":\"{headline}\"}}]}},{{\"name\":\"optionalMessage\",\"type\":\"array\",\"values\":[{{\"type\":\"string\",\"value\":\"{message}\"}}]}},{{\"name\":\"additionalInformation\",\"type\":\"array\",\"values\":[]}}]}}'

def create_container_entity(trigger_name: str) -> tuple[Dict[str, Any], str]:
    container_guid = str(uuid.uuid4())
    container: Dict[str, Any] = {
        "uniqueIdentifier": container_guid,
        "payload": {
            "name": f"{trigger_name}",
            "type": "unconstrained"
            },
            "type": "container-v1"
    }

    return (container, container_guid)

def create_kql_source_entity(
    trigger_name: str,
    polling_frequency_minutes: int,
    kql_query: str,
    database: str,
    cluster_hostname: Optional[str],
    container_id: str,
    workspace_id: str,
) -> tuple[Dict[str, Any], str]:
    # Validate and convert polling frequency to seconds
    polling_frequency_seconds = validate_polling_frequency(polling_frequency_minutes)
    
    kql_source_id = str(uuid.uuid4())

    # Strip newlines from KQL query as the API does not handle it properly
    kql_query = kql_query.replace("\n", " ").replace(" ", " ")

    source: Dict[str, Any] = {
            "uniqueIdentifier": kql_source_id,
            "payload": {
                "name": f"{trigger_name} source",
                "runSettings": {
                    "executionIntervalInSeconds": polling_frequency_seconds
                },
                "query": {
                    "queryString": kql_query
                },
                "eventhouseItem": {
                    "databaseName": database,
                    "clusterHostName": cluster_hostname
                },
                "queryParameters": [],
                "metadata": {
                    "workspaceId": workspace_id,
                    "measureName": "",
                    "querySetId": "",
                    "queryId": ""
                },
                "parentContainer": {
                    "targetUniqueIdentifier": container_id
                }
            },
            "type": "kqlSource-v1"
        }

    return (source, kql_source_id)

def create_simple_event_rule_entities(
    trigger_name: str,
    container_id: str,
    source_id: str,
    message: str,
    headline: str,
    alert_recipient: str,
    alert_type: str = "teams"
):
    event_entity_guid = str(uuid.uuid4())
    rule_id = str(uuid.uuid4())
    
    # Choose the appropriate binding based on alert_type
    if alert_type.lower() == "email":
        binding_config = generate_email_binding(alert_recipient, headline, message)
    else:  # default to teams
        binding_config = generate_teams_binding(alert_recipient, headline, message)
    
    event_entity: Dict[str, Any] = {
        "uniqueIdentifier": event_entity_guid,
        "payload": {
            "name": f"{trigger_name} event",
            "parentContainer": {
                "targetUniqueIdentifier": container_id
            },
            "definition": {
                "type": "Event",
                "instance": f'{{\"templateId\":\"SourceEvent\",\"templateVersion\":\"{TEMPLATE_VERSION}\",\"steps\":[{{\"name\":\"SourceEventStep\",\"id\":\"{str(uuid.uuid4())}\",\"rows\":[{{\"name\":\"SourceSelector\",\"kind\":\"SourceReference\",\"arguments\":[{{\"name\":\"entityId\",\"type\":\"string\",\"value\":\"{source_id}\"}}]}}]}}]}}'
            }
        },
        "type": "timeSeriesView-v1"
    }

    event_rule_entity: Dict[str, Any] = {
            "uniqueIdentifier": rule_id,
            "payload": {
                "name": f"{trigger_name} rule",
                "parentContainer": {
                    "targetUniqueIdentifier": container_id
                },
                "definition": {
                    "type": "Rule",
                    "instance": f'{{\"templateId\":\"EventTrigger\",\"templateVersion\":\"{TEMPLATE_VERSION}\",\"steps\":[{{\"name\":\"FieldsDefaultsStep\",\"id\":\"{str(uuid.uuid4())}\",\"rows\":[{{\"name\":\"EventSelector\",\"kind\":\"Event\",\"arguments\":[{{\"kind\":\"EventReference\",\"type\":\"complex\",\"arguments\":[{{\"name\":\"entityId\",\"type\":\"string\",\"value\":\"{event_entity_guid}\"}}],\"name\":\"event\"}}]}}]}},{{\"name\":\"EventDetectStep\",\"id\":\"{str(uuid.uuid4())}\",\"rows\":[{{\"name\":\"OnEveryValue\",\"kind\":\"OnEveryValue\",\"arguments\":[]}}]}},{{\"name\":\"ActStep\",\"id\":\"{str(uuid.uuid4())}\",\"rows\":[{binding_config}]}}]}}',
                    "settings": {
                        "shouldRun": True,  # Enable the rule
                        "shouldApplyRuleOnUpdate": False
                    }
                }
            },
            "type": "timeSeriesView-v1"
        }

    return [event_entity, event_rule_entity]
