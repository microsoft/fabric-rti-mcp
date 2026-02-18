import csv
import json
import os
import tempfile
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import pytest
from azure.kusto.data.response import KustoResponseDataSet

from fabric_rti_mcp.services.kusto.kusto_config import KustoConfig, KustoEnvVarNames
from fabric_rti_mcp.services.kusto.kusto_file_writer import (
    CsvFileWriter,
    JsonlFileWriter,
    estimate_token_count,
    get_file_writer,
    should_write_to_file,
    write_to_file,
)
from fabric_rti_mcp.services.kusto.kusto_service import kusto_query


class TestFileWriters:
    def test_csv_writer_extension(self) -> None:
        writer = CsvFileWriter()
        assert writer.extension == "csv"

    def test_jsonl_writer_extension(self) -> None:
        writer = JsonlFileWriter()
        assert writer.extension == "jsonl"

    def test_csv_writer_writes_data(self, tmp_path: Any) -> None:
        writer = CsvFileWriter()
        rows = [{"Name": "Alice", "Age": 30}, {"Name": "Bob", "Age": 25}]
        path = str(tmp_path / "test.csv")

        writer.write(rows, path)

        with open(path) as f:
            reader = csv.DictReader(f)
            result = list(reader)
        assert len(result) == 2
        assert result[0]["Name"] == "Alice"
        assert result[0]["Age"] == "30"
        assert result[1]["Name"] == "Bob"

    def test_csv_writer_writes_empty(self, tmp_path: Any) -> None:
        writer = CsvFileWriter()
        path = str(tmp_path / "empty.csv")

        writer.write([], path)

        with open(path) as f:
            assert f.read() == ""

    def test_jsonl_writer_writes_data(self, tmp_path: Any) -> None:
        writer = JsonlFileWriter()
        rows = [{"Name": "Alice", "Age": 30}, {"Name": "Bob", "Age": 25}]
        path = str(tmp_path / "test.jsonl")

        writer.write(rows, path)

        with open(path) as f:
            lines = f.readlines()
        assert len(lines) == 2
        assert json.loads(lines[0]) == {"Name": "Alice", "Age": 30}
        assert json.loads(lines[1]) == {"Name": "Bob", "Age": 25}

    def test_jsonl_writer_writes_empty(self, tmp_path: Any) -> None:
        writer = JsonlFileWriter()
        path = str(tmp_path / "empty.jsonl")

        writer.write([], path)

        with open(path) as f:
            assert f.read() == ""

    def test_get_file_writer_csv(self) -> None:
        writer = get_file_writer("csv")
        assert isinstance(writer, CsvFileWriter)

    def test_get_file_writer_jsonl(self) -> None:
        writer = get_file_writer("jsonl")
        assert isinstance(writer, JsonlFileWriter)

    def test_get_file_writer_unsupported(self) -> None:
        with pytest.raises(ValueError, match="Unsupported file format"):
            get_file_writer("xml")


class TestEstimateTokenCount:
    def test_small_response(self) -> None:
        response: dict[str, Any] = {"format": "columnar", "data": {"col": [1]}}
        count = estimate_token_count(response)
        assert count > 0

    def test_larger_response_higher_count(self) -> None:
        small: dict[str, Any] = {"format": "columnar", "data": {"col": [1]}}
        large: dict[str, Any] = {"format": "columnar", "data": {"col": list(range(1000))}}
        assert estimate_token_count(large) > estimate_token_count(small)


class TestShouldWriteToFile:
    def test_small_response_returns_false(self) -> None:
        response: dict[str, Any] = {"format": "columnar", "data": {"Name": ["Alice"], "Age": [30]}}
        assert should_write_to_file(response, threshold=100000) is False

    def test_large_response_returns_true(self) -> None:
        large_data = {"Name": [f"User{i}" for i in range(500)], "Age": list(range(500))}
        response: dict[str, Any] = {"format": "columnar", "data": large_data}
        assert should_write_to_file(response, threshold=10) is True

    def test_empty_response_returns_false(self) -> None:
        response: dict[str, Any] = {"format": "columnar", "data": {}}
        assert should_write_to_file(response, threshold=0) is False


class TestWriteToFile:
    def test_writes_jsonl_by_default(self, tmp_path: Any) -> None:
        large_data = {"Name": [f"User{i}" for i in range(500)], "Age": list(range(500))}
        response: dict[str, Any] = {"format": "columnar", "data": large_data}

        result = write_to_file(response, output_dir=str(tmp_path))

        assert result["format"] == "file"
        assert result["file_format"] == "jsonl"
        assert result["row_count"] == 500
        assert os.path.exists(result["path"])

        with open(result["path"]) as f:
            lines = f.readlines()
        assert len(lines) == 500

    def test_writes_csv_format(self, tmp_path: Any) -> None:
        large_data = {"Name": [f"User{i}" for i in range(50)], "Age": list(range(50))}
        response: dict[str, Any] = {"format": "columnar", "data": large_data}

        result = write_to_file(response, output_dir=str(tmp_path), file_format="csv")

        assert result["format"] == "file"
        assert result["file_format"] == "csv"
        assert result["row_count"] == 50
        assert result["path"].endswith(".csv")
        assert os.path.exists(result["path"])

    def test_empty_response_returned_as_is(self) -> None:
        response: dict[str, Any] = {"format": "columnar", "data": {}}
        result = write_to_file(response)
        assert result is response

    def test_custom_output_dir_created(self, tmp_path: Any) -> None:
        output_dir = str(tmp_path / "nested" / "output")
        large_data = {"Name": [f"User{i}" for i in range(100)]}
        response: dict[str, Any] = {"format": "columnar", "data": large_data}

        result = write_to_file(response, output_dir=output_dir)

        assert os.path.isdir(output_dir)
        assert os.path.exists(result["path"])

    def test_uses_temp_dir_by_default(self) -> None:
        large_data = {"Name": [f"User{i}" for i in range(100)]}
        response: dict[str, Any] = {"format": "columnar", "data": large_data}

        result = write_to_file(response)

        assert result["format"] == "file"
        assert tempfile.gettempdir() in result["path"]
        # cleanup
        os.remove(result["path"])


class TestAdaptiveQueryConfig:
    def test_config_loads_adaptive_query_results_from_env(self) -> None:
        with patch.dict(os.environ, {KustoEnvVarNames.adaptive_query_results: "true"}):
            config = KustoConfig.from_env()
            assert config.adaptive_query_results is True

    def test_config_adaptive_query_results_default_false(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            config = KustoConfig.from_env()
            assert config.adaptive_query_results is False

    def test_config_loads_adaptive_query_results_path(self) -> None:
        with patch.dict(
            os.environ,
            {
                KustoEnvVarNames.adaptive_query_results: "true",
                KustoEnvVarNames.adaptive_query_results_path: "/custom/path",
            },
        ):
            config = KustoConfig.from_env()
            assert config.adaptive_query_results is True
            assert config.adaptive_query_results_path == "/custom/path"

    def test_config_adaptive_query_results_path_default_none(self) -> None:
        with patch.dict(os.environ, {KustoEnvVarNames.adaptive_query_results: "true"}):
            config = KustoConfig.from_env()
            assert config.adaptive_query_results_path is None

    def test_env_var_names_include_adaptive(self) -> None:
        all_vars = KustoEnvVarNames.all()
        assert KustoEnvVarNames.adaptive_query_results in all_vars
        assert KustoEnvVarNames.adaptive_query_results_path in all_vars


class TestAdaptiveQueryInService:
    @patch("fabric_rti_mcp.services.kusto.kusto_service.get_kusto_connection")
    @patch("fabric_rti_mcp.services.kusto.kusto_service.CONFIG")
    def test_adaptive_results_writes_large_response_to_file(
        self,
        mock_config: Mock,
        mock_get_kusto_connection: Mock,
        sample_cluster_uri: str,
        tmp_path: Any,
    ) -> None:
        mock_config.adaptive_query_results = True
        mock_config.adaptive_query_results_path = str(tmp_path)
        mock_config.timeout_seconds = None

        # Create a response large enough to trigger file writing
        large_rows = [[f"val{i}"] for i in range(500)]
        mock_column = Mock()
        mock_column.column_name = "Data"
        mock_primary_result = Mock()
        mock_primary_result.columns = [mock_column]
        mock_primary_result.rows = large_rows
        mock_result_set = Mock(spec=KustoResponseDataSet)
        mock_result_set.primary_results = [mock_primary_result]

        mock_client = MagicMock()
        mock_client.execute.return_value = mock_result_set
        mock_connection = MagicMock()
        mock_connection.query_client = mock_client
        mock_connection.default_database = "default_db"
        mock_get_kusto_connection.return_value = mock_connection

        result = kusto_query("TestTable | take 500", sample_cluster_uri, database="test_db")

        assert result["format"] == "file"
        assert result["row_count"] == 500
        assert os.path.exists(result["path"])

    @patch("fabric_rti_mcp.services.kusto.kusto_service.get_kusto_connection")
    @patch("fabric_rti_mcp.services.kusto.kusto_service.CONFIG")
    def test_adaptive_results_disabled_returns_inline(
        self,
        mock_config: Mock,
        mock_get_kusto_connection: Mock,
        sample_cluster_uri: str,
        mock_kusto_response: KustoResponseDataSet,
    ) -> None:
        mock_config.adaptive_query_results = False
        mock_config.timeout_seconds = None

        mock_client = MagicMock()
        mock_client.execute.return_value = mock_kusto_response
        mock_connection = MagicMock()
        mock_connection.query_client = mock_client
        mock_connection.default_database = "default_db"
        mock_get_kusto_connection.return_value = mock_connection

        result = kusto_query("TestTable | take 10", sample_cluster_uri, database="test_db")

        assert result["format"] == "columnar"
        assert "data" in result

    @patch("fabric_rti_mcp.services.kusto.kusto_service.get_kusto_connection")
    @patch("fabric_rti_mcp.services.kusto.kusto_service.CONFIG")
    def test_adaptive_results_small_response_stays_inline(
        self,
        mock_config: Mock,
        mock_get_kusto_connection: Mock,
        sample_cluster_uri: str,
        mock_kusto_response: KustoResponseDataSet,
    ) -> None:
        mock_config.adaptive_query_results = True
        mock_config.adaptive_query_results_path = None
        mock_config.timeout_seconds = None

        mock_client = MagicMock()
        mock_client.execute.return_value = mock_kusto_response
        mock_connection = MagicMock()
        mock_connection.query_client = mock_client
        mock_connection.default_database = "default_db"
        mock_get_kusto_connection.return_value = mock_connection

        result = kusto_query("TestTable | take 1", sample_cluster_uri, database="test_db")

        # Small response should stay inline even with adaptive enabled
        assert result["format"] == "columnar"
