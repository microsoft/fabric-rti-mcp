from unittest.mock import MagicMock, Mock, patch

from azure.kusto.data import ClientRequestProperties
from azure.kusto.data.response import KustoResponseDataSet

from fabric_rti_mcp import __version__
from fabric_rti_mcp.kusto.kusto_service import kusto_query


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
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["TestColumn"] == "TestValue"
