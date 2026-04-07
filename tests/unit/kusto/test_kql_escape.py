import pytest

from fabric_rti_mcp.services.kusto.kusto_service import (
    _find_first_statement,
    kql_escape_entity_name,
    kql_escape_string,
    kusto_command,
    kusto_query,
)

from unittest.mock import MagicMock, patch


class TestKqlEscapeEntityName:
    def test_plain_name_gets_escaped(self) -> None:
        assert kql_escape_entity_name("StormEvents") == "['StormEvents']"

    def test_already_single_quote_escaped(self) -> None:
        assert kql_escape_entity_name("['my-table']") == "['my-table']"

    def test_already_double_quote_escaped(self) -> None:
        assert kql_escape_entity_name('["my-table"]') == '["my-table"]'

    def test_special_chars_in_plain_name(self) -> None:
        assert kql_escape_entity_name("sys.logs_v2-prod") == "['sys.logs_v2-prod']"

    def test_whitespace_stripped(self) -> None:
        assert kql_escape_entity_name("  StormEvents  ") == "['StormEvents']"

    def test_standalone_brackets_allowed(self) -> None:
        assert kql_escape_entity_name("table[0]") == "['table[0]']"

    def test_standalone_quote_allowed(self) -> None:
        assert kql_escape_entity_name("it's a table") == "['it's a table']"

    def test_partial_escape_inside_raises(self) -> None:
        with pytest.raises(ValueError, match="escape sequences"):
            kql_escape_entity_name("table['inner']value")

    def test_query_appending_attempt_raises(self) -> None:
        """Entity name that appends a sub-query to exfiltrate schema info."""
        with pytest.raises(ValueError, match="escape sequences"):
            kql_escape_entity_name("['StormEvents'] | project SecretColumn | ")


class TestKqlEscapeString:
    def test_no_quotes(self) -> None:
        assert kql_escape_string("normal") == "normal"

    def test_single_quote(self) -> None:
        assert kql_escape_string("it's") == "it''s"

    def test_empty(self) -> None:
        assert kql_escape_string("") == ""


class TestFindFirstStatement:
    def test_plain_query(self) -> None:
        assert _find_first_statement("StormEvents | take 10") == "StormEvents | take 10"

    def test_plain_command(self) -> None:
        assert _find_first_statement(".show tables") == ".show tables"

    def test_skips_line_comment(self) -> None:
        assert _find_first_statement("// this is a comment\nStormEvents | take 10") == "StormEvents | take 10"

    def test_skips_directive(self) -> None:
        assert _find_first_statement("#connect cluster\n.show tables") == ".show tables"

    def test_skips_set_hint(self) -> None:
        assert _find_first_statement("set notruncation;\nStormEvents | take 10") == "StormEvents | take 10"

    def test_skips_all_three(self) -> None:
        text = "// comment\n#directive\nset querytrace;\n.show tables"
        assert _find_first_statement(text) == ".show tables"

    def test_comment_then_set_then_query(self) -> None:
        text = "// get storm data\nset notruncation;\nStormEvents | take 10"
        assert _find_first_statement(text) == "StormEvents | take 10"

    def test_multiple_comments_then_directive_then_command(self) -> None:
        text = "// first comment\n// second comment\n#connect mydb\nset querytrace;\n.show tables"
        assert _find_first_statement(text) == ".show tables"

    def test_set_then_comment_then_query(self) -> None:
        text = "set notruncation;\n// sample query\nStormEvents | sample 5"
        assert _find_first_statement(text) == "StormEvents | sample 5"

    def test_blank_lines_between_prefixes(self) -> None:
        text = "// comment\n\nset notruncation;\n\n.show version"
        assert _find_first_statement(text) == ".show version"

    def test_empty_returns_empty(self) -> None:
        assert _find_first_statement("") == ""

    def test_only_comments_returns_empty(self) -> None:
        assert _find_first_statement("// comment\n// another") == ""


class TestQueryCommandValidation:
    def test_query_rejects_command(self) -> None:
        with pytest.raises(ValueError, match="management commands"):
            kusto_query(".show tables", "https://help.kusto.windows.net")

    def test_query_rejects_command_after_comments(self) -> None:
        with pytest.raises(ValueError, match="management commands"):
            kusto_query("// list tables\n.show tables", "https://help.kusto.windows.net")

    def test_query_rejects_command_after_set_hint(self) -> None:
        with pytest.raises(ValueError, match="management commands"):
            kusto_query("set notruncation;\n.show tables", "https://help.kusto.windows.net")

    @patch("fabric_rti_mcp.services.kusto.kusto_service.CONFIG")
    @patch("fabric_rti_mcp.services.kusto.kusto_service.get_kusto_connection")
    def test_query_accepts_kql(self, mock_conn: MagicMock, mock_config: MagicMock, mock_kusto_response) -> None:
        mock_config.response_format = "kusto_response"
        mock_config.timeout_seconds = None
        mock_config.offload_enabled = False
        mock_client = MagicMock()
        mock_client.execute.return_value = mock_kusto_response
        connection = MagicMock()
        connection.query_client = mock_client
        connection.default_database = "db"
        mock_conn.return_value = connection

        result = kusto_query("StormEvents | take 10", "https://help.kusto.windows.net")
        assert result["format"] == "kusto_response"

    @patch("fabric_rti_mcp.services.kusto.kusto_service.CONFIG")
    @patch("fabric_rti_mcp.services.kusto.kusto_service.get_kusto_connection")
    def test_query_accepts_kql_with_comments(self, mock_conn: MagicMock, mock_config: MagicMock, mock_kusto_response) -> None:
        mock_config.response_format = "kusto_response"
        mock_config.timeout_seconds = None
        mock_config.offload_enabled = False
        mock_client = MagicMock()
        mock_client.execute.return_value = mock_kusto_response
        connection = MagicMock()
        connection.query_client = mock_client
        connection.default_database = "db"
        mock_conn.return_value = connection

        result = kusto_query("// fetch storms\nStormEvents | take 10", "https://help.kusto.windows.net")
        assert result["format"] == "kusto_response"

    def test_command_rejects_query(self) -> None:
        with pytest.raises(ValueError, match="management commands"):
            kusto_command("StormEvents | take 10", "https://help.kusto.windows.net")

    def test_command_rejects_query_after_directive(self) -> None:
        with pytest.raises(ValueError, match="management commands"):
            kusto_command("#connect cluster\nStormEvents | take 10", "https://help.kusto.windows.net")

    @patch("fabric_rti_mcp.services.kusto.kusto_service.CONFIG")
    @patch("fabric_rti_mcp.services.kusto.kusto_service.get_kusto_connection")
    def test_command_accepts_dot_command(self, mock_conn: MagicMock, mock_config: MagicMock, mock_kusto_response) -> None:
        mock_config.response_format = "kusto_response"
        mock_config.timeout_seconds = None
        mock_config.offload_enabled = False
        mock_client = MagicMock()
        mock_client.execute.return_value = mock_kusto_response
        connection = MagicMock()
        connection.query_client = mock_client
        connection.default_database = "db"
        mock_conn.return_value = connection

        result = kusto_command(".show tables", "https://help.kusto.windows.net")
        assert result["format"] == "kusto_response"

    @patch("fabric_rti_mcp.services.kusto.kusto_service.CONFIG")
    @patch("fabric_rti_mcp.services.kusto.kusto_service.get_kusto_connection")
    def test_command_accepts_dot_command_after_set(self, mock_conn: MagicMock, mock_config: MagicMock, mock_kusto_response) -> None:
        mock_config.response_format = "kusto_response"
        mock_config.timeout_seconds = None
        mock_config.offload_enabled = False
        mock_client = MagicMock()
        mock_client.execute.return_value = mock_kusto_response
        connection = MagicMock()
        connection.query_client = mock_client
        connection.default_database = "db"
        mock_conn.return_value = connection

        result = kusto_command("set notruncation;\n.show tables", "https://help.kusto.windows.net")
        assert result["format"] == "kusto_response"
