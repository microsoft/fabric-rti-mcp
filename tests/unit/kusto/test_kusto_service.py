import json
from unittest.mock import MagicMock, Mock, patch

import pytest
from azure.kusto.data import ClientRequestProperties
from azure.kusto.data.response import KustoResponseDataSet

from fabric_rti_mcp import __version__
from fabric_rti_mcp.kusto.kusto_service import kusto_command, kusto_query


@patch("fabric_rti_mcp.kusto.kusto_service.get_kusto_connection")
def test_execute_basic_query(
    mock_get_kusto_connection: Mock,
    sample_cluster_uri: str,
    mock_kusto_response: KustoResponseDataSet,
) -> None:
    """Test that _execute properly calls the Kusto client with correct parameters."""
    # Arrange
    mock_client = MagicMock()
    mock_client.execute.return_value = mock_kusto_response

    mock_connection = MagicMock()
    mock_connection.query_client = mock_client
    mock_connection.default_database = "default_db"
    mock_connection.timeout_seconds = None  # Add timeout_seconds attribute
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


@patch("fabric_rti_mcp.kusto.kusto_service.get_kusto_connection")
def test_execute_with_custom_client_request_properties(
    mock_get_kusto_connection: Mock,
    sample_cluster_uri: str,
    mock_kusto_response: KustoResponseDataSet,
) -> None:
    """Test that custom client request properties are properly applied."""
    # Arrange
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


@patch("fabric_rti_mcp.kusto.kusto_service.get_kusto_connection")
def test_execute_without_client_request_properties_preserves_behavior(
    mock_get_kusto_connection: Mock,
    sample_cluster_uri: str,
    mock_kusto_response: KustoResponseDataSet,
) -> None:
    """Test that behavior is unchanged when no custom client request properties are provided."""
    # Arrange
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


@patch("fabric_rti_mcp.kusto.kusto_service.get_kusto_connection")
def test_destructive_operation_with_custom_client_request_properties(
    mock_get_kusto_connection: Mock,
    sample_cluster_uri: str,
    mock_kusto_response: KustoResponseDataSet,
) -> None:
    """Test that destructive operations correctly handle custom client request properties."""
    # Arrange
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


@patch("fabric_rti_mcp.kusto.kusto_service.get_kusto_connection")
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


@patch("fabric_rti_mcp.kusto.kusto_service.get_kusto_connection")
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


@patch("fabric_rti_mcp.kusto.kusto_service.logger")
@patch("fabric_rti_mcp.kusto.kusto_service.get_kusto_connection")
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
