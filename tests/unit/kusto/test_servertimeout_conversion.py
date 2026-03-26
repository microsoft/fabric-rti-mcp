"""Tests for servertimeout timedelta conversion in client_request_properties."""

from datetime import timedelta
from unittest.mock import Mock, patch

import pytest
from azure.kusto.data import ClientRequestProperties

from fabric_rti_mcp.services.kusto.kusto_service import (
    _parse_timespan_to_timedelta,
    kusto_query,
)


class TestParseTimespanToTimedelta:
    """Tests for the _parse_timespan_to_timedelta helper."""

    def test_timedelta_passthrough(self) -> None:
        td = timedelta(minutes=3)
        assert _parse_timespan_to_timedelta(td) == td

    def test_int_seconds(self) -> None:
        assert _parse_timespan_to_timedelta(180) == timedelta(seconds=180)

    def test_float_seconds(self) -> None:
        assert _parse_timespan_to_timedelta(90.5) == timedelta(seconds=90.5)

    def test_hh_mm_ss_format(self) -> None:
        assert _parse_timespan_to_timedelta("00:03:00") == timedelta(minutes=3)

    def test_h_mm_ss_format(self) -> None:
        assert _parse_timespan_to_timedelta("1:30:00") == timedelta(hours=1, minutes=30)

    def test_shorthand_minutes(self) -> None:
        assert _parse_timespan_to_timedelta("3m") == timedelta(minutes=3)

    def test_shorthand_seconds(self) -> None:
        assert _parse_timespan_to_timedelta("180s") == timedelta(seconds=180)

    def test_shorthand_hours(self) -> None:
        assert _parse_timespan_to_timedelta("1h") == timedelta(hours=1)

    def test_shorthand_case_insensitive(self) -> None:
        assert _parse_timespan_to_timedelta("3M") == timedelta(minutes=3)

    def test_numeric_string(self) -> None:
        assert _parse_timespan_to_timedelta("180") == timedelta(seconds=180)

    def test_whitespace_stripped(self) -> None:
        assert _parse_timespan_to_timedelta("  00:03:00  ") == timedelta(minutes=3)

    def test_invalid_string_raises(self) -> None:
        with pytest.raises(ValueError, match="Cannot parse servertimeout"):
            _parse_timespan_to_timedelta("invalid")

    def test_none_raises(self) -> None:
        with pytest.raises((ValueError, TypeError)):
            _parse_timespan_to_timedelta(None)  # type: ignore


class TestCrpServertimeoutConversion:
    """Tests that servertimeout in client_request_properties is converted to timedelta."""

    @patch("fabric_rti_mcp.services.kusto.kusto_service.get_kusto_connection")
    def test_string_servertimeout_converted(self, mock_get_connection: Mock) -> None:
        """Passing servertimeout as a string should not crash — it should be converted to timedelta."""
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
        assert isinstance(crp._options["servertimeout"], timedelta)
        assert crp._options["servertimeout"] == timedelta(minutes=3)

    @patch("fabric_rti_mcp.services.kusto.kusto_service.get_kusto_connection")
    def test_shorthand_servertimeout_converted(self, mock_get_connection: Mock) -> None:
        """Shorthand format like '3m' should also work."""
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
                client_request_properties={"servertimeout": "3m"},
            )

        crp = mock_client.execute.call_args[0][2]
        assert crp._options["servertimeout"] == timedelta(minutes=3)

    @patch("fabric_rti_mcp.services.kusto.kusto_service.get_kusto_connection")
    def test_numeric_servertimeout_converted(self, mock_get_connection: Mock) -> None:
        """Numeric seconds should also work."""
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
                client_request_properties={"servertimeout": 180},
            )

        crp = mock_client.execute.call_args[0][2]
        assert crp._options["servertimeout"] == timedelta(seconds=180)

    @patch("fabric_rti_mcp.services.kusto.kusto_service.get_kusto_connection")
    def test_non_timeout_properties_unchanged(self, mock_get_connection: Mock) -> None:
        """Other properties should pass through without conversion."""
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
                client_request_properties={"truncationmaxsize": 51200},
            )

        crp = mock_client.execute.call_args[0][2]
        assert crp._options["truncationmaxsize"] == 51200
