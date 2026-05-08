"""Tests for ``servertimeout`` conversion in user-supplied client_request_properties."""

from datetime import timedelta
from unittest.mock import Mock, patch

import pytest
from azure.kusto.data import ClientRequestProperties

from fabric_rti_mcp.services.kusto.kusto_service import _parse_servertimeout, kusto_query


def test_parse_servertimeout_hh_mm_ss() -> None:
    """An 'HH:MM:SS' string is converted to the corresponding timedelta."""
    assert _parse_servertimeout("00:03:00") == timedelta(minutes=3)


def test_parse_servertimeout_combines_hours_minutes_seconds() -> None:
    """All three components contribute to the resulting timedelta in the right order."""
    assert _parse_servertimeout("01:30:45") == timedelta(hours=1, minutes=30, seconds=45)


def test_parse_servertimeout_strips_whitespace() -> None:
    """Leading/trailing whitespace around the timespan is tolerated."""
    assert _parse_servertimeout("  00:03:00  ") == timedelta(minutes=3)


def test_parse_servertimeout_rejects_non_string() -> None:
    """Non-string values are rejected — agents must produce 'HH:MM:SS' strings."""
    with pytest.raises(ValueError, match="must be a string"):
        _parse_servertimeout(180)  # type: ignore[arg-type]


def test_parse_servertimeout_rejects_invalid_format() -> None:
    """Strings that are not in 'HH:MM:SS' form are rejected."""
    with pytest.raises(ValueError, match="HH:MM:SS"):
        _parse_servertimeout("3m")


@patch("fabric_rti_mcp.services.kusto.kusto_service.get_kusto_connection")
def test_servertimeout_string_converted_end_to_end(mock_get_connection: Mock) -> None:
    """servertimeout in client_request_properties is converted to a timedelta on the CRP."""
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


@patch("fabric_rti_mcp.services.kusto.kusto_service.get_kusto_connection")
def test_user_servertimeout_overrides_global_timeout(mock_get_connection: Mock) -> None:
    """User-supplied servertimeout wins over CONFIG.timeout_seconds."""
    mock_connection = Mock()
    mock_connection.default_database = "TestDB"
    mock_client = Mock()
    mock_result = Mock()
    mock_result.primary_results = None
    mock_client.execute.return_value = mock_result
    mock_connection.query_client = mock_client
    mock_get_connection.return_value = mock_connection

    with patch("fabric_rti_mcp.services.kusto.kusto_service.CONFIG") as mock_config:
        mock_config.timeout_seconds = 600  # 10 minutes
        kusto_query(
            "TestQuery",
            "https://test.kusto.windows.net",
            client_request_properties={"servertimeout": "00:01:00"},
        )

    crp = mock_client.execute.call_args[0][2]
    assert crp._options["servertimeout"] == timedelta(minutes=1)
