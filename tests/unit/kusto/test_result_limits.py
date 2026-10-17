from collections.abc import Iterator
from datetime import timedelta
from unittest.mock import Mock, patch

import pytest
from azure.kusto.data import ClientRequestProperties
from azure.kusto.data.exceptions import KustoServiceError
from azure.kusto.data.response import KustoResponseDataSetV1

from fabric_rti_mcp.services.kusto.kusto_config import KustoConfig, KustoEnvVarNames
from fabric_rti_mcp.services.kusto.kusto_service import kusto_graph_query, kusto_query, kusto_sample_entity


@pytest.fixture(autouse=True)
def clear_kusto_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in KustoEnvVarNames.all():
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def query_client(mock_kusto_response: KustoResponseDataSetV1) -> Iterator[Mock]:
    with patch("fabric_rti_mcp.services.kusto.kusto_service.get_kusto_connection") as get_connection:
        client = get_connection.return_value.query_client
        client.execute.return_value = mock_kusto_response
        get_connection.return_value.default_database = "TestDB"
        yield client


@pytest.mark.parametrize(("size", "records"), [(None, None), (1048576, None), (None, 1000), (1048576, 1000), (1, 1)])
def test_result_limits_from_env_reach_sdk(
    monkeypatch: pytest.MonkeyPatch, query_client: Mock, size: int | None, records: int | None
) -> None:
    if size is not None:
        monkeypatch.setenv(KustoEnvVarNames.max_result_size_bytes, str(size))
    if records is not None:
        monkeypatch.setenv(KustoEnvVarNames.max_records, str(records))

    config = KustoConfig.from_env()
    assert config.max_result_size_bytes == size
    assert config.max_records == records
    with patch("fabric_rti_mcp.services.kusto.kusto_service.CONFIG", config):
        result = kusto_query("TestTable", "https://test.kusto.windows.net")

    crp: ClientRequestProperties = query_client.execute.call_args.args[2]
    for option, expected in (("truncationmaxsize", size), ("truncationmaxrecords", records)):
        assert crp.has_option(option) is (expected is not None)
        if expected is not None:
            assert crp.get_option(option, None) == expected
    assert result["format"] == "kusto_response"
    assert crp.get_option("request_readonly", None) is True
    assert crp.get_option("request_readonly_hardline", None) is True
    assert crp.get_option("request_is_agentic", None) is True


@pytest.mark.parametrize("name", [KustoEnvVarNames.max_result_size_bytes, KustoEnvVarNames.max_records])
@pytest.mark.parametrize("value", ["", "invalid", "1.5", "0", "-1"])
def test_invalid_result_limit_fails_configuration(monkeypatch: pytest.MonkeyPatch, name: str, value: str) -> None:
    monkeypatch.setenv(name, value)
    with pytest.raises(ValueError, match=f"{name}=.*positive integer"):
        KustoConfig.from_env()


def test_result_limit_environment_variables_are_discoverable(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (KustoEnvVarNames.max_result_size_bytes, KustoEnvVarNames.max_records):
        monkeypatch.setenv(name, "1")
        assert name in KustoConfig.existing_env_vars()


@pytest.mark.parametrize("option", ["truncationmaxsize", "truncationmaxrecords"])
def test_per_request_limit_overrides_only_matching_default(query_client: Mock, option: str) -> None:
    config = KustoConfig(max_result_size_bytes=1048576, max_records=1000, timeout_seconds=60)
    properties = {option: 2000, "queryconsistency": "strongconsistency"}
    with patch("fabric_rti_mcp.services.kusto.kusto_service.CONFIG", config):
        kusto_query("TestTable", "https://test.kusto.windows.net", client_request_properties=properties)

    crp: ClientRequestProperties = query_client.execute.call_args.args[2]
    expected = {"truncationmaxsize": 1048576, "truncationmaxrecords": 1000, option: 2000}
    for key, value in expected.items():
        assert crp.get_option(key, None) == value
    assert crp.get_option("servertimeout", None) == timedelta(seconds=60)
    assert crp.get_option("queryconsistency", None) == "strongconsistency"
    assert properties == {option: 2000, "queryconsistency": "strongconsistency"}


@pytest.mark.parametrize("tool", ["graph", "sample"])
def test_other_query_tools_receive_result_limits(query_client: Mock, tool: str) -> None:
    config = KustoConfig(max_result_size_bytes=1048576, max_records=1000)
    with patch("fabric_rti_mcp.services.kusto.kusto_service.CONFIG", config):
        if tool == "graph":
            kusto_graph_query("TestGraph", "| graph-match (n) project n", "https://test.kusto.windows.net", "db")
        else:
            kusto_sample_entity("TestTable", "table", "https://test.kusto.windows.net")

    crp: ClientRequestProperties = query_client.execute.call_args.args[2]
    assert crp.get_option("truncationmaxsize", None) == 1048576
    assert crp.get_option("truncationmaxrecords", None) == 1000


def test_truncation_error_is_not_returned_as_success(query_client: Mock) -> None:
    query_client.execute.side_effect = KustoServiceError("E_QUERY_RESULT_SET_TOO_LARGE")
    with (
        patch("fabric_rti_mcp.services.kusto.kusto_service.CONFIG", KustoConfig(max_records=1000)),
        pytest.raises(RuntimeError, match="E_QUERY_RESULT_SET_TOO_LARGE"),
    ):
        kusto_query("TestTable", "https://test.kusto.windows.net")
