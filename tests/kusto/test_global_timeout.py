"""Test global timeout configuration for Kusto tools."""

import os
from unittest.mock import Mock, patch

from azure.kusto.data import ClientRequestProperties

from fabric_rti_mcp.common import Config, config
from fabric_rti_mcp.kusto.kusto_service import kusto_query


def test_config_loads_timeout_from_env() -> None:
    """Test that Config loads timeout from FABRIC_RTI_KUSTO_TIMEOUT environment variable."""
    with patch.dict(os.environ, {"FABRIC_RTI_KUSTO_TIMEOUT": "300"}):
        test_config = Config()
        assert test_config.kusto_timeout_seconds == 300


def test_config_handles_invalid_timeout() -> None:
    """Test that Config handles invalid timeout values gracefully."""
    with patch.dict(os.environ, {"FABRIC_RTI_KUSTO_TIMEOUT": "invalid"}):
        test_config = Config()
        assert test_config.kusto_timeout_seconds is None


def test_config_no_timeout_env() -> None:
    """Test that Config handles missing environment variable."""
    with patch.dict(os.environ, {}, clear=True):
        test_config = Config()
        assert test_config.kusto_timeout_seconds is None


@patch("fabric_rti_mcp.kusto.kusto_service.get_kusto_connection")
@patch("fabric_rti_mcp.kusto.kusto_service.format_results")
def test_global_timeout_applied_to_query(mock_format_results: Mock, mock_get_connection: Mock) -> None:
    """Test that global timeout is applied to Kusto queries."""
    # Mock connection
    mock_connection = Mock()
    mock_connection.default_database = "TestDB"
    mock_client = Mock()
    mock_connection.query_client = mock_client
    mock_get_connection.return_value = mock_connection

    # Mock format_results to return expected result
    mock_format_results.return_value = [{"test": "result"}]

    # Mock config with timeout
    with patch.object(config, 'kusto_timeout_seconds', 600):
        kusto_query("TestQuery", "https://test.kusto.windows.net")

    # Verify that execute was called with ClientRequestProperties
    mock_client.execute.assert_called_once()
    call_args = mock_client.execute.call_args
    crp = call_args[0][2]  # Third argument should be ClientRequestProperties

    assert isinstance(crp, ClientRequestProperties)
    # The timeout should be set as server timeout option in HH:MM:SS format
    # 600 seconds = 10 minutes = 00:10:00
    expected_timeout = "00:10:00"
    assert crp._options.get("servertimeout") == expected_timeout


@patch("fabric_rti_mcp.kusto.kusto_service.get_kusto_connection")
@patch("fabric_rti_mcp.kusto.kusto_service.format_results")
def test_no_timeout_when_not_configured(mock_format_results: Mock, mock_get_connection: Mock) -> None:
    """Test that no timeout is set when not configured."""
    # Mock connection
    mock_connection = Mock()
    mock_connection.default_database = "TestDB"
    mock_client = Mock()
    mock_connection.query_client = mock_client
    mock_get_connection.return_value = mock_connection

    # Mock format_results to return expected result
    mock_format_results.return_value = [{"test": "result"}]

    # Mock config without timeout
    with patch.object(config, 'kusto_timeout_seconds', None):
        kusto_query("TestQuery", "https://test.kusto.windows.net")

    # Verify that execute was called with ClientRequestProperties
    mock_client.execute.assert_called_once()
    call_args = mock_client.execute.call_args
    crp = call_args[0][2]  # Third argument should be ClientRequestProperties

    assert isinstance(crp, ClientRequestProperties)
    # No timeout should be set
    assert "servertimeout" not in crp._options
