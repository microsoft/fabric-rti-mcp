import json
import os
from unittest.mock import MagicMock, Mock, patch

from azure.kusto.data.response import KustoResponseDataSet

from fabric_rti_mcp.services.kusto.kusto_service import kusto_query
from fabric_rti_mcp.services.kusto.kusto_watermark import (
    CUSTOM_WATERMARK_ENV_VAR,
    _resolve_custom_watermark,
    _sanitize_value,
    add_watermark,
    build_watermark,
)


class TestSanitizeValue:
    def test_removes_newlines(self) -> None:
        assert _sanitize_value("hello\nworld") == "hello world"

    def test_removes_carriage_returns(self) -> None:
        assert _sanitize_value("hello\r\nworld") == "hello world"

    def test_strips_whitespace(self) -> None:
        assert _sanitize_value("  hello  ") == "hello"

    def test_plain_string_unchanged(self) -> None:
        assert _sanitize_value("hello") == "hello"


class TestResolveCustomWatermark:
    def test_resolves_env_vars(self) -> None:
        with patch.dict(os.environ, {"TEAM_NAME": "data-platform", "REQ_ID": "abc123"}):
            result = _resolve_custom_watermark('{"team": "env:TEAM_NAME", "request_id": "env:REQ_ID"}')
            assert result == {"team": "data-platform", "request_id": "abc123"}

    def test_literal_values_used_as_is(self) -> None:
        result = _resolve_custom_watermark('{"team": "my-team", "app": "my-app"}')
        assert result == {"team": "my-team", "app": "my-app"}

    def test_mixed_literal_and_env(self) -> None:
        with patch.dict(os.environ, {"MY_APP_ID": "cool-app-123"}):
            result = _resolve_custom_watermark('{"team": "data-eng", "app_id": "env:MY_APP_ID"}')
            assert result == {"team": "data-eng", "app_id": "cool-app-123"}

    def test_skips_missing_env_vars(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            result = _resolve_custom_watermark('{"missing": "env:NONEXISTENT_VAR"}')
            assert result == {}

    def test_invalid_json_returns_empty(self) -> None:
        result = _resolve_custom_watermark("not-json")
        assert result == {}

    def test_non_dict_json_returns_empty(self) -> None:
        result = _resolve_custom_watermark('["a", "b"]')
        assert result == {}

    def test_non_string_value_skipped(self) -> None:
        result = _resolve_custom_watermark('{"key": 123}')
        assert result == {}

    def test_sanitizes_resolved_values(self) -> None:
        with patch.dict(os.environ, {"DIRTY_VAR": "hello\nworld"}):
            result = _resolve_custom_watermark('{"key": "env:DIRTY_VAR"}')
            assert result == {"key": "hello world"}

    def test_sanitizes_literal_values(self) -> None:
        result = _resolve_custom_watermark('{"key": "hello\\nworld"}')
        assert result == {"key": "hello world"}


class TestBuildWatermark:
    def test_default_watermark_contains_version(self) -> None:
        watermark = build_watermark()
        assert watermark.startswith("// ")
        assert watermark.endswith("\n")
        data = json.loads(watermark[3:].strip())
        assert "fabric_rti_mcp_version" in data

    def test_default_watermark_contains_user(self) -> None:
        with patch.dict(os.environ, {"USER": "testuser"}):
            watermark = build_watermark()
            data = json.loads(watermark[3:].strip())
            assert data["user"] == "testuser"

    def test_watermark_without_user_env(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            watermark = build_watermark()
            data = json.loads(watermark[3:].strip())
            assert "user" not in data

    def test_custom_watermark_entries(self) -> None:
        with patch.dict(
            os.environ,
            {
                "USER": "testuser",
                "TEAM_NAME": "data-platform",
                CUSTOM_WATERMARK_ENV_VAR: '{"team": "env:TEAM_NAME"}',
            },
        ):
            watermark = build_watermark()
            data = json.loads(watermark[3:].strip())
            assert data["team"] == "data-platform"
            assert data["user"] == "testuser"
            assert "fabric_rti_mcp_version" in data

    def test_custom_watermark_literal_entries(self) -> None:
        with patch.dict(
            os.environ,
            {
                "USER": "testuser",
                CUSTOM_WATERMARK_ENV_VAR: '{"team": "my-team"}',
            },
        ):
            watermark = build_watermark()
            data = json.loads(watermark[3:].strip())
            assert data["team"] == "my-team"
            assert data["user"] == "testuser"

    def test_custom_watermark_keys_sorted(self) -> None:
        with patch.dict(
            os.environ,
            {
                "USER": "testuser",
                "VAR_Z": "z_value",
                "VAR_A": "a_value",
                CUSTOM_WATERMARK_ENV_VAR: '{"z_key": "env:VAR_Z", "a_key": "env:VAR_A"}',
            },
        ):
            watermark = build_watermark()
            data = json.loads(watermark[3:].strip())
            keys = list(data.keys())
            # Default keys come first
            assert keys[0] == "fabric_rti_mcp_version"
            assert keys[1] == "user"
            # Custom keys are sorted alphabetically after default keys
            assert keys.index("a_key") < keys.index("z_key")


class TestAddWatermark:
    def test_prepends_watermark_to_query(self) -> None:
        query = "TestTable | take 10"
        with patch.dict(os.environ, {CUSTOM_WATERMARK_ENV_VAR: "{}"}):
            result = add_watermark(query)
        lines = result.split("\n", 1)
        assert lines[0].startswith("// ")
        assert lines[1] == query

    def test_watermark_is_valid_json_comment(self) -> None:
        query = "TestTable | take 10"
        with patch.dict(os.environ, {CUSTOM_WATERMARK_ENV_VAR: "{}"}):
            result = add_watermark(query)
        first_line = result.split("\n", 1)[0]
        json_str = first_line[3:]
        data = json.loads(json_str)
        assert isinstance(data, dict)
        assert "fabric_rti_mcp_version" in data

    def test_opt_out_when_env_var_unset(self) -> None:
        query = "TestTable | take 10"
        with patch.dict(os.environ, {}, clear=True):
            result = add_watermark(query)
        assert result == query

    def test_opt_in_with_empty_json(self) -> None:
        query = "TestTable | take 10"
        with patch.dict(os.environ, {CUSTOM_WATERMARK_ENV_VAR: "{}"}, clear=True):
            result = add_watermark(query)
        assert result.startswith("// ")
        assert result.endswith(query)

    def test_control_command_unchanged_even_when_enabled(self) -> None:
        command = ".show tables"
        with patch.dict(os.environ, {CUSTOM_WATERMARK_ENV_VAR: "{}"}):
            result = add_watermark(command)
        assert result == command


class TestWatermarkIntegration:
    @patch("fabric_rti_mcp.services.kusto.kusto_service.get_kusto_connection")
    def test_query_includes_watermark_when_enabled(
        self,
        mock_get_kusto_connection: Mock,
        sample_cluster_uri: str,
        mock_kusto_response: KustoResponseDataSet,
    ) -> None:
        """Test that executed queries include the watermark comment when opt-in env var is set."""
        mock_client = MagicMock()
        mock_client.execute.return_value = mock_kusto_response

        mock_connection = MagicMock()
        mock_connection.query_client = mock_client
        mock_connection.default_database = "default_db"
        mock_get_kusto_connection.return_value = mock_connection

        query = "TestTable | take 10"

        with patch.dict(os.environ, {CUSTOM_WATERMARK_ENV_VAR: "{}"}):
            kusto_query(query, sample_cluster_uri, database="test_db")

        executed_query = mock_client.execute.call_args[0][1]
        assert executed_query.startswith("// ")
        watermark_line = executed_query.split("\n", 1)[0]
        watermark_data = json.loads(watermark_line[3:])
        assert "fabric_rti_mcp_version" in watermark_data
        assert executed_query.endswith(query)

    @patch("fabric_rti_mcp.services.kusto.kusto_service.get_kusto_connection")
    def test_query_unwatermarked_by_default(
        self,
        mock_get_kusto_connection: Mock,
        sample_cluster_uri: str,
        mock_kusto_response: KustoResponseDataSet,
    ) -> None:
        """Test that executed queries are not watermarked when the opt-in env var is unset."""
        mock_client = MagicMock()
        mock_client.execute.return_value = mock_kusto_response

        mock_connection = MagicMock()
        mock_connection.query_client = mock_client
        mock_connection.default_database = "default_db"
        mock_get_kusto_connection.return_value = mock_connection

        query = "TestTable | take 10"

        env = {k: v for k, v in os.environ.items() if k != CUSTOM_WATERMARK_ENV_VAR}
        with patch.dict(os.environ, env, clear=True):
            kusto_query(query, sample_cluster_uri, database="test_db")

        executed_query = mock_client.execute.call_args[0][1]
        assert executed_query == query
