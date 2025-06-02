from typing import cast
from unittest.mock import MagicMock, Mock, patch

from azure.kusto.data import ClientRequestProperties
from azure.kusto.data.response import KustoResponseDataSet

from fabric_rti_mcp import __version__
from fabric_rti_mcp.kusto.kusto_service import kusto_query


@patch("fabric_rti_mcp.kusto.kusto_service.get_kusto_query_client")
def test_execute_basic_query(
    mock_get_query_client: Mock,
    sample_cluster_uri: str,
    mock_kusto_response: KustoResponseDataSet,
) -> None:
    """Test that _execute properly calls the Kusto client with correct parameters."""
    # Arrange
    mock_client = MagicMock()
    mock_client.execute.return_value = mock_kusto_response
    mock_get_query_client.return_value = mock_client

    query = "  TestTable | take 10  "  # Added whitespace to test stripping
    database = "test_db"

    # Act
    result = kusto_query(query, sample_cluster_uri, database=database)

    # Assert
    mock_get_query_client.assert_called_once_with(sample_cluster_uri)
    mock_client.execute.assert_called_once()

    # Verify database and stripped query
    args = mock_client.execute.call_args[0]
    assert args[0] == database
    assert args[1] == "TestTable | take 10"

    # Verify ClientRequestProperties settings
    crp = mock_client.execute.call_args[0][2]
    assert isinstance(crp, ClientRequestProperties)
    assert crp.application == f"fabric-rti-mcp{{{__version__}}}"
    assert cast(str, crp.client_request_id).startswith("KFRTI_MCP.kusto_query:")
    assert crp.has_option("request_readonly")

    # Verify result format
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["TestColumn"] == "TestValue"
