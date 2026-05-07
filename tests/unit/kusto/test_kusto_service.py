import json
from unittest.mock import MagicMock, Mock, patch

import pytest
from azure.kusto.data import ClientRequestProperties
from azure.kusto.data.response import KustoResponseDataSet

from fabric_rti_mcp import __version__
from fabric_rti_mcp.services.kusto.kusto_service import (
    KustoConnectionManager,
    kusto_command,
    kusto_diagnostics,
    kusto_query,
    kusto_show_queryplan,
)


@patch.dict(
    "os.environ",
    {
        "KUSTO_SERVICE_URI": "https://demo11.westus.kusto.windows.net/",
        "KUSTO_SERVICE_DEFAULT_DB": "ML",
        "KUSTO_KNOWN_SERVICES": json.dumps(
            [
                {"service_uri": "https://demo11.westus.kusto.windows.net/", "default_database": "ML"},
                {"service_uri": "https://demo12.westus.kusto.windows.net/", "default_database": "Datasets"},
                {"service_uri": "https://kuskus.kusto.windows.net/", "default_database": "Kuskus"},
            ]
        ),
        "KUSTO_ALLOW_UNKNOWN_SERVICES": "true",
    },
    clear=False,
)
@patch("fabric_rti_mcp.services.kusto.kusto_service.KustoConnection")
def test_connection_manager_uses_known_service_default_database(mock_kusto_connection: MagicMock) -> None:
    manager = KustoConnectionManager()

    manager.get("HTTPS://DEMO12.WESTUS.KUSTO.WINDOWS.NET/")

    mock_kusto_connection.assert_called_once_with(
        "HTTPS://DEMO12.WESTUS.KUSTO.WINDOWS.NET",
        default_database="Datasets",
    )


@patch("fabric_rti_mcp.services.kusto.kusto_service.CONFIG")
@patch("fabric_rti_mcp.services.kusto.kusto_service.get_kusto_connection")
def test_execute_basic_query(
    mock_get_kusto_connection: Mock,
    mock_config: MagicMock,
    sample_cluster_uri: str,
    mock_kusto_response: KustoResponseDataSet,
) -> None:
    """Test that _execute properly calls the Kusto client with correct parameters."""
    # Arrange
    mock_config.response_format = "columnar"
    mock_config.timeout_seconds = None

    mock_client = MagicMock()
    mock_client.execute.return_value = mock_kusto_response

    mock_connection = MagicMock()
    mock_connection.query_client = mock_client
    mock_connection.default_database = "default_db"
    mock_connection.timeout_seconds = None
    mock_get_kusto_connection.return_value = mock_connection

    query = "  TestTable | take 10  "  # Added whitespace to test stripping
    database = "test_db"

    # Act
    result = kusto_query(query, sample_cluster_uri, database=database)

    # Assert
    mock_get_kusto_connection.assert_called_once_with(sample_cluster_uri)
    mock_client.execute.assert_called_once()

    # Verify database and stripped query
    args = mock_client.execute.call_args[0]
    assert args[0] == database
    assert args[1] == "TestTable | take 10"

    # Verify ClientRequestProperties settings
    crp = mock_client.execute.call_args[0][2]
    assert isinstance(crp, ClientRequestProperties)
    assert crp.application == f"fabric-rti-mcp{{{__version__}}}"
    assert crp.client_request_id.startswith("KFRTI_MCP.kusto_query:")  # type: ignore
    assert crp.has_option("request_readonly")

    # Verify result format
    assert result["format"] == "columnar"
    assert result["data"]["TestColumn"][0] == "TestValue"


@patch("fabric_rti_mcp.services.kusto.kusto_service.CONFIG")
@patch("fabric_rti_mcp.services.kusto.kusto_service.get_kusto_connection")
def test_execute_with_custom_client_request_properties(
    mock_get_kusto_connection: Mock,
    mock_config: MagicMock,
    sample_cluster_uri: str,
    mock_kusto_response: KustoResponseDataSet,
) -> None:
    """Test that custom client request properties are properly applied."""
    # Arrange
    mock_config.response_format = "columnar"
    mock_config.timeout_seconds = None

    mock_client = MagicMock()
    mock_client.execute.return_value = mock_kusto_response

    mock_connection = MagicMock()
    mock_connection.query_client = mock_client
    mock_connection.default_database = "default_db"
    mock_get_kusto_connection.return_value = mock_connection

    query = "TestTable | take 5"
    database = "test_db"
    custom_properties = {
        "request_timeout": "00:10:00",
        "max_memory_consumption_per_query_per_node": 1073741824,
        "custom_property": "custom_value",
    }

    # Act
    result = kusto_query(query, sample_cluster_uri, database=database, client_request_properties=custom_properties)

    # Assert
    mock_get_kusto_connection.assert_called_once_with(sample_cluster_uri)
    mock_client.execute.assert_called_once()

    # Verify database and query
    args = mock_client.execute.call_args[0]
    assert args[0] == database
    assert args[1] == query

    # Verify ClientRequestProperties settings
    crp = mock_client.execute.call_args[0][2]
    assert isinstance(crp, ClientRequestProperties)

    # Verify default properties are still set
    assert crp.application == f"fabric-rti-mcp{{{__version__}}}"
    assert crp.client_request_id.startswith("KFRTI_MCP.kusto_query:")  # type: ignore
    assert crp.has_option("request_readonly")

    # Verify custom properties are set
    assert crp.has_option("request_timeout")
    assert crp.has_option("max_memory_consumption_per_query_per_node")
    assert crp.has_option("custom_property")

    # Verify result format
    assert isinstance(result, dict)
    assert result["format"] == "columnar"
    assert "data" in result
    assert result["data"]["TestColumn"] == ["TestValue"]


@patch("fabric_rti_mcp.services.kusto.kusto_service.CONFIG")
@patch("fabric_rti_mcp.services.kusto.kusto_service.get_kusto_connection")
def test_execute_without_client_request_properties_preserves_behavior(
    mock_get_kusto_connection: Mock,
    mock_config: MagicMock,
    sample_cluster_uri: str,
    mock_kusto_response: KustoResponseDataSet,
) -> None:
    """Test that behavior is unchanged when no custom client request properties are provided."""
    # Arrange
    mock_config.response_format = "columnar"
    mock_config.timeout_seconds = None

    mock_client = MagicMock()
    mock_client.execute.return_value = mock_kusto_response

    mock_connection = MagicMock()
    mock_connection.query_client = mock_client
    mock_connection.default_database = "default_db"
    mock_get_kusto_connection.return_value = mock_connection

    query = "TestTable | take 10"
    database = "test_db"

    # Act
    result = kusto_query(query, sample_cluster_uri, database=database)

    # Assert
    mock_get_kusto_connection.assert_called_once_with(sample_cluster_uri)
    mock_client.execute.assert_called_once()

    # Verify ClientRequestProperties contains only default settings
    crp = mock_client.execute.call_args[0][2]
    assert isinstance(crp, ClientRequestProperties)
    assert crp.application == f"fabric-rti-mcp{{{__version__}}}"
    assert crp.client_request_id.startswith("KFRTI_MCP.kusto_query:")  # type: ignore
    assert crp.has_option("request_readonly")

    # Verify result format
    assert isinstance(result, dict)
    assert result["format"] == "columnar"
    assert "data" in result
    assert result["data"]["TestColumn"] == ["TestValue"]


@patch("fabric_rti_mcp.services.kusto.kusto_service.CONFIG")
@patch("fabric_rti_mcp.services.kusto.kusto_service.get_kusto_connection")
def test_destructive_operation_with_custom_client_request_properties(
    mock_get_kusto_connection: Mock,
    mock_config: MagicMock,
    sample_cluster_uri: str,
    mock_kusto_response: KustoResponseDataSet,
) -> None:
    """Test that destructive operations correctly handle custom client request properties."""
    # Arrange
    mock_config.response_format = "columnar"
    mock_config.timeout_seconds = None

    mock_client = MagicMock()
    mock_client.execute.return_value = mock_kusto_response

    mock_connection = MagicMock()
    mock_connection.query_client = mock_client
    mock_connection.default_database = "default_db"
    mock_get_kusto_connection.return_value = mock_connection

    command = ".create table TestTable (Column1: string)"
    database = "test_db"
    custom_properties = {"request_timeout": "00:05:00", "async_mode": True}

    # Act
    result = kusto_command(command, sample_cluster_uri, database=database, client_request_properties=custom_properties)

    # Assert
    mock_get_kusto_connection.assert_called_once_with(sample_cluster_uri)
    mock_client.execute.assert_called_once()

    # Verify database and command
    args = mock_client.execute.call_args[0]
    assert args[0] == database
    assert args[1] == command

    # Verify ClientRequestProperties settings for destructive operation
    crp = mock_client.execute.call_args[0][2]
    assert isinstance(crp, ClientRequestProperties)

    # Verify default properties are still set
    assert crp.application == f"fabric-rti-mcp{{{__version__}}}"
    assert crp.client_request_id.startswith("KFRTI_MCP.kusto_command:")  # type: ignore

    # For destructive operations, request_readonly should NOT be set
    assert not crp.has_option("request_readonly")

    # Verify custom properties are set
    assert crp.has_option("request_timeout")
    assert crp.has_option("async_mode")

    # Verify result format
    assert isinstance(result, dict)
    assert result["format"] == "columnar"
    assert "data" in result
    assert result["data"]["TestColumn"] == ["TestValue"]


@patch("fabric_rti_mcp.services.kusto.kusto_service.CONFIG")
@patch("fabric_rti_mcp.services.kusto.kusto_service.get_kusto_connection")
def test_blocked_crp_keys_raise_error(
    mock_get_kusto_connection: Mock,
    mock_config: MagicMock,
    sample_cluster_uri: str,
) -> None:
    """Test that security-sensitive CRP keys are rejected."""
    mock_config.timeout_seconds = None

    blocked_keys = [
        "request_readonly",
        "request_readonly_hardline",
    ]

    for key in blocked_keys:
        with pytest.raises(ValueError, match="security-sensitive"):
            kusto_query("T | take 1", sample_cluster_uri, database="db", client_request_properties={key: False})

    # Also verify case-insensitive matching
    with pytest.raises(ValueError, match="security-sensitive"):
        kusto_query(
            "T | take 1", sample_cluster_uri, database="db", client_request_properties={"Request_Readonly": False}
        )


@patch("fabric_rti_mcp.services.kusto.kusto_service.get_kusto_connection")
def test_execute_error_includes_correlation_id(
    mock_get_kusto_connection: Mock,
    sample_cluster_uri: str,
) -> None:
    """Test that errors include correlation ID for easier debugging."""
    # Arrange
    mock_client = MagicMock()
    mock_client.execute.side_effect = Exception("Kusto execution failed")

    mock_connection = MagicMock()
    mock_connection.query_client = mock_client
    mock_connection.default_database = "default_db"
    mock_get_kusto_connection.return_value = mock_connection

    query = "TestTable | take 10"
    database = "test_db"

    # Act & Assert
    with pytest.raises(RuntimeError) as exc_info:
        kusto_query(query, sample_cluster_uri, database=database)

    error_message = str(exc_info.value)

    # Verify the error message includes correlation ID and operation name
    assert "correlation ID:" in error_message
    assert "KFRTI_MCP.kusto_query:" in error_message
    assert "kusto_query" in error_message
    assert "Kusto execution failed" in error_message


@patch("fabric_rti_mcp.services.kusto.kusto_service.get_kusto_connection")
def test_execute_json_parse_error_includes_correlation_id(
    mock_get_kusto_connection: Mock,
    sample_cluster_uri: str,
) -> None:
    """Test that JSON parsing errors include correlation ID for easier debugging."""
    # Arrange - simulate the kind of error that was happening in the issue
    mock_client = MagicMock()
    mock_client.execute.side_effect = json.JSONDecodeError("Expecting value", "", 0)

    mock_connection = MagicMock()
    mock_connection.query_client = mock_client
    mock_connection.default_database = "default_db"
    mock_get_kusto_connection.return_value = mock_connection

    command = ".show version"

    # Act & Assert
    with pytest.raises(RuntimeError) as exc_info:
        kusto_command(command, sample_cluster_uri)

    error_message = str(exc_info.value)

    # Verify the error message includes correlation ID and operation name
    assert "correlation ID:" in error_message
    assert "KFRTI_MCP.kusto_command:" in error_message
    assert "kusto_command" in error_message
    assert "Expecting value" in error_message


@patch("fabric_rti_mcp.services.kusto.kusto_service.logger")
@patch("fabric_rti_mcp.services.kusto.kusto_service.get_kusto_connection")
def test_successful_operations_do_not_log_correlation_id(
    mock_get_kusto_connection: Mock,
    mock_logger: Mock,
    sample_cluster_uri: str,
    mock_kusto_response: KustoResponseDataSet,
) -> None:
    """Test that successful operations do not log correlation IDs (only errors do)."""
    # Arrange
    mock_client = MagicMock()
    mock_client.execute.return_value = mock_kusto_response

    mock_connection = MagicMock()
    mock_connection.query_client = mock_client
    mock_connection.default_database = "default_db"
    mock_get_kusto_connection.return_value = mock_connection

    query = "TestTable | take 10"

    # Act
    kusto_query(query, sample_cluster_uri)

    # Assert - verify no info or debug logging occurs for successful operations
    assert not mock_logger.info.called
    assert not mock_logger.debug.called


@patch("fabric_rti_mcp.services.kusto.kusto_service.CONFIG")
@patch("fabric_rti_mcp.services.kusto.kusto_service.get_kusto_connection")
def test_execute_respects_response_format_config(
    mock_get_kusto_connection: Mock,
    mock_config: MagicMock,
    sample_cluster_uri: str,
    mock_kusto_response: KustoResponseDataSet,
) -> None:
    """Test that _execute uses the configured response format."""
    mock_client = MagicMock()
    mock_client.execute.return_value = mock_kusto_response

    mock_connection = MagicMock()
    mock_connection.query_client = mock_client
    mock_connection.default_database = "default_db"
    mock_get_kusto_connection.return_value = mock_connection

    mock_config.response_format = "json"
    mock_config.timeout_seconds = None

    result = kusto_query("TestTable | take 10", sample_cluster_uri, database="test_db")

    assert result["format"] == "json"


@patch("fabric_rti_mcp.services.kusto.kusto_service.CONFIG")
@patch("fabric_rti_mcp.services.kusto.kusto_service.get_kusto_connection")
def test_execute_columnar_format(
    mock_get_kusto_connection: Mock,
    mock_config: MagicMock,
    sample_cluster_uri: str,
    mock_kusto_response: KustoResponseDataSet,
) -> None:
    """Test that _execute returns columnar format when configured."""
    mock_client = MagicMock()
    mock_client.execute.return_value = mock_kusto_response

    mock_connection = MagicMock()
    mock_connection.query_client = mock_client
    mock_connection.default_database = "default_db"
    mock_get_kusto_connection.return_value = mock_connection

    mock_config.response_format = "columnar"
    mock_config.timeout_seconds = None

    result = kusto_query("TestTable | take 10", sample_cluster_uri, database="test_db")

    assert result["format"] == "columnar"
    assert result["data"]["TestColumn"][0] == "TestValue"


@patch("fabric_rti_mcp.services.kusto.kusto_service.CONFIG")
@patch("fabric_rti_mcp.services.kusto.kusto_service.get_kusto_connection")
def test_execute_kusto_response_format(
    mock_get_kusto_connection: Mock,
    mock_config: MagicMock,
    sample_cluster_uri: str,
    mock_kusto_response: KustoResponseDataSet,
) -> None:
    """Test that _execute returns kusto_response format with raw columns and rows."""
    mock_client = MagicMock()
    mock_client.execute.return_value = mock_kusto_response

    mock_connection = MagicMock()
    mock_connection.query_client = mock_client
    mock_connection.default_database = "default_db"
    mock_get_kusto_connection.return_value = mock_connection

    mock_config.response_format = "kusto_response"
    mock_config.timeout_seconds = None

    result = kusto_query("TestTable | take 10", sample_cluster_uri, database="test_db")

    assert result["format"] == "kusto_response"
    assert "columns" in result["data"]
    assert "rows" in result["data"]
    assert isinstance(result["data"]["columns"], list)
    assert isinstance(result["data"]["rows"], list)


# ── kusto_show_queryplan tests ───────────────────────────────────────────────────


@patch("fabric_rti_mcp.services.kusto.kusto_service.CONFIG")
@patch("fabric_rti_mcp.services.kusto.kusto_service.get_kusto_connection")
def test_show_queryplan_constructs_correct_command(
    mock_get_kusto_connection: Mock,
    mock_config: MagicMock,
    sample_cluster_uri: str,
    mock_queryplan_response: KustoResponseDataSet,
) -> None:
    """Test that kusto_show_queryplan wraps the query in .show queryplan <| syntax."""
    mock_config.response_format = "kusto_response"
    mock_config.timeout_seconds = None

    mock_client = MagicMock()
    mock_client.execute.return_value = mock_queryplan_response

    mock_connection = MagicMock()
    mock_connection.query_client = mock_client
    mock_connection.default_database = "default_db"
    mock_get_kusto_connection.return_value = mock_connection

    result = kusto_show_queryplan("StormEvents | count", sample_cluster_uri, database="test_db")

    mock_client.execute.assert_called_once()
    args = mock_client.execute.call_args[0]
    assert args[0] == "test_db"
    assert args[1] == ".show queryplan <| StormEvents | count"

    crp = args[2]
    assert isinstance(crp, ClientRequestProperties)
    assert crp.client_request_id.startswith("KFRTI_MCP.kusto_show_queryplan:")

    assert result["query_text"] == "StormEvents | count"
    assert result["stats"]["PlanSize"] == 9487
    assert result["stats"]["RelopSize"] == 229
    assert result["relop_tree"]["type"] == "CrossTableUnionOperator"

    # Verify execution hints extracted from physical plan
    hints = result["execution_hints"]
    assert hints["estimated_rows"] == 59066
    assert hints["concurrency"] == 1
    assert hints["spread"] == 1
    assert len(hints["shard_scans"]) == 1
    assert hints["shard_scans"][0]["total_rows"] == 59066
    assert hints["shard_scans"][0]["has_selection"] is False


@patch("fabric_rti_mcp.services.kusto.kusto_service.CONFIG")
@patch("fabric_rti_mcp.services.kusto.kusto_service.get_kusto_connection")
def test_show_queryplan_strips_query_whitespace(
    mock_get_kusto_connection: Mock,
    mock_config: MagicMock,
    sample_cluster_uri: str,
    mock_queryplan_response: KustoResponseDataSet,
) -> None:
    """Test that leading/trailing whitespace in the query is stripped before wrapping."""
    mock_config.response_format = "kusto_response"
    mock_config.timeout_seconds = None

    mock_client = MagicMock()
    mock_client.execute.return_value = mock_queryplan_response

    mock_connection = MagicMock()
    mock_connection.query_client = mock_client
    mock_connection.default_database = "default_db"
    mock_get_kusto_connection.return_value = mock_connection

    kusto_show_queryplan("  StormEvents | take 10  ", sample_cluster_uri, database="test_db")

    args = mock_client.execute.call_args[0]
    assert args[1] == ".show queryplan <| StormEvents | take 10"


@patch("fabric_rti_mcp.services.kusto.kusto_service.CONFIG")
@patch("fabric_rti_mcp.services.kusto.kusto_service.get_kusto_connection")
def test_show_queryplan_uses_default_database(
    mock_get_kusto_connection: Mock,
    mock_config: MagicMock,
    sample_cluster_uri: str,
    mock_queryplan_response: KustoResponseDataSet,
) -> None:
    """Test that kusto_show_queryplan falls back to default database when none provided."""
    mock_config.response_format = "kusto_response"
    mock_config.timeout_seconds = None

    mock_client = MagicMock()
    mock_client.execute.return_value = mock_queryplan_response

    mock_connection = MagicMock()
    mock_connection.query_client = mock_client
    mock_connection.default_database = "my_default_db"
    mock_get_kusto_connection.return_value = mock_connection

    kusto_show_queryplan("T | count", sample_cluster_uri)

    args = mock_client.execute.call_args[0]
    assert args[0] == "my_default_db"


# ── kusto_diagnostics tests ──────────────────────────────────────────────────────


@patch("fabric_rti_mcp.services.kusto.kusto_service.CONFIG")
@patch("fabric_rti_mcp.services.kusto.kusto_service.get_kusto_connection")
def test_diagnostics_all_sections_succeed(
    mock_get_kusto_connection: Mock,
    mock_config: MagicMock,
    sample_cluster_uri: str,
    mock_kusto_response: KustoResponseDataSet,
) -> None:
    """Test that kusto_diagnostics returns all 5 sections as lists of row-dicts."""
    mock_config.response_format = "columnar"
    mock_config.timeout_seconds = None

    mock_client = MagicMock()
    mock_client.execute.return_value = mock_kusto_response

    mock_connection = MagicMock()
    mock_connection.query_client = mock_client
    mock_connection.default_database = "default_db"
    mock_get_kusto_connection.return_value = mock_connection

    result = kusto_diagnostics(sample_cluster_uri, database="test_db")

    expected_sections = {
        "capacity",
        "cluster",
        "principal_roles",
        "diagnostics",
        "workload_groups",
        "rowstores",
        "ingestion_failures",
    }
    assert set(result.keys()) == expected_sections

    for section in expected_sections:
        assert isinstance(result[section], list), f"Section '{section}' should be a list of row-dicts"
        assert len(result[section]) == 1
        assert result[section][0]["TestColumn"] == "TestValue"

    assert mock_client.execute.call_count == 7


@patch("fabric_rti_mcp.services.kusto.kusto_service.CONFIG")
@patch("fabric_rti_mcp.services.kusto.kusto_service.get_kusto_connection")
def test_diagnostics_partial_failure(
    mock_get_kusto_connection: Mock,
    mock_config: MagicMock,
    sample_cluster_uri: str,
    mock_kusto_response: KustoResponseDataSet,
) -> None:
    """Test that a failing command results in an error for that section while others succeed."""
    mock_config.response_format = "columnar"
    mock_config.timeout_seconds = None

    call_count = 0

    def execute_side_effect(database: str, query: str, crp: ClientRequestProperties) -> KustoResponseDataSet:
        nonlocal call_count
        call_count += 1
        if ".show cluster" in query and "| project" not in query:
            raise RuntimeError("Permission denied for .show cluster")
        return mock_kusto_response

    mock_client = MagicMock()
    mock_client.execute.side_effect = execute_side_effect

    mock_connection = MagicMock()
    mock_connection.query_client = mock_client
    mock_connection.default_database = "default_db"
    mock_get_kusto_connection.return_value = mock_connection

    result = kusto_diagnostics(sample_cluster_uri, database="test_db")

    assert "error" in result["cluster"]
    assert "Permission denied" in result["cluster"]["error"]

    for section in ["capacity", "principal_roles", "diagnostics", "workload_groups", "rowstores", "ingestion_failures"]:
        assert isinstance(result[section], list), f"Section '{section}' should have succeeded"


@patch("fabric_rti_mcp.services.kusto.kusto_service.CONFIG")
@patch("fabric_rti_mcp.services.kusto.kusto_service.get_kusto_connection")
def test_diagnostics_commands_are_correct(
    mock_get_kusto_connection: Mock,
    mock_config: MagicMock,
    sample_cluster_uri: str,
    mock_kusto_response: KustoResponseDataSet,
) -> None:
    """Test that the diagnostic sub-commands match expected command strings."""
    mock_config.response_format = "columnar"
    mock_config.timeout_seconds = None

    mock_client = MagicMock()
    mock_client.execute.return_value = mock_kusto_response

    mock_connection = MagicMock()
    mock_connection.query_client = mock_client
    mock_connection.default_database = "default_db"
    mock_get_kusto_connection.return_value = mock_connection

    kusto_diagnostics(sample_cluster_uri)

    executed_commands = [call[0][1] for call in mock_client.execute.call_args_list]

    assert ".show capacity | project Resource, Total, Consumed, Remaining" in executed_commands
    assert ".show cluster" in executed_commands
    assert ".show principal roles | project Scope, Role" in executed_commands
    assert ".show diagnostics" in executed_commands
    assert ".show workload_groups" in executed_commands
    assert ".show rowstores" in executed_commands
    assert any("ingestion failures" in cmd for cmd in executed_commands)
