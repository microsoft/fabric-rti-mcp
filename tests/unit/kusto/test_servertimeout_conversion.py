"""Test servertimeout conversion in client_request_properties."""

from datetime import timedelta
from unittest.mock import Mock, patch

import pytest
from azure.kusto.data import ClientRequestProperties

from fabric_rti_mcp.services.kusto.kusto_service import _parse_timespan_to_timedelta, kusto_query


def test_parse_timespan_hh_mm_ss() -> None:
    """Test that 'HH:MM:SS' string is converted to timedelta."""
    assert _parse_timespan_to_timedelta("00:03:00") == timedelta(minutes=3)


def test_parse_timespan_int_seconds() -> None:
    """Test that integer seconds are converted to timedelta."""
    assert _parse_timespan_to_timedelta(180) == timedelta(seconds=180)


def test_parse_timespan_timedelta_passthrough() -> None:
    """Test that timedelta values pass through unchanged."""
    td = timedelta(minutes=3)
    assert _parse_timespan_to_timedelta(td) == td


def test_parse_timespan_invalid_raises() -> None:
    """Test that unsupported formats raise ValueError."""
    with pytest.raises(ValueError, match="Cannot parse servertimeout"):
        _parse_timespan_to_timedelta("3m")


@patch("fabric_rti_mcp.services.kusto.kusto_service.get_kusto_connection")
def test_servertimeout_string_converted_end_to_end(mock_get_connection: Mock) -> None:
    """Test that servertimeout string in client_request_properties is converted to timedelta through kusto_query."""
    mock_connection = Mock()
    mock_connection.default_database = "TestDB"
    mock_client = Mock()
    mock_result = Mock()
    mock_result.primary_results = None
    mock_client.execute.return_value = mock_result
    mock_connection.query_client = mock_client
    mock_get_connection.return_value = mock_connection

    with patch("fabric_rti_mcp.services.kusto.kusto_service.CONFIG") as mock_config:
        mock_config.timeout_seconds = None
        kusto_query(
            "TestQuery",
            "https://test.kusto.windows.net",
            client_request_properties={"servertimeout": "00:03:00"},
        )

    crp = mock_client.execute.call_args[0][2]
    assert isinstance(crp, ClientRequestProperties)
    assert crp._options["servertimeout"] == timedelta(minutes=3)
