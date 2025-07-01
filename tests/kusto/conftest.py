from typing import Any, Dict, List
from unittest.mock import Mock, patch

import pytest
from azure.kusto.data import KustoClient
from azure.kusto.data.response import KustoResponseDataSetV1

from fabric_rti_mcp.kusto.kusto_connection import KustoConnection


@pytest.fixture
def mock_kusto_response() -> KustoResponseDataSetV1:
    """Create a minimal KustoResponseDataSet for testing."""
    json_response: Dict[str, List[Dict[str, Any]]] = {
        "Tables": [
            {
                "TableName": "Table_0",
                "Columns": [{"ColumnName": "TestColumn", "DataType": "string"}],
                "Rows": [["TestValue"]],
            }
        ]
    }
    return KustoResponseDataSetV1(json_response)


@pytest.fixture
def mock_query_client() -> Mock:
    """Mock Kusto query client that returns predictable responses."""
    client = Mock(spec=KustoClient)
    # Mock response format matches Kusto table format
    client.execute.return_value = [
        {
            "TableName": "TestTable",
            "Columns": [{"ColumnName": "TestColumn", "DataType": "string"}],
            "Rows": [["TestValue"]],
        }
    ]
    return client


@pytest.fixture
def mock_kusto_connection(mock_query_client: Mock) -> KustoConnection:
    """Mock KustoConnection with configured query client."""
    with patch("fabric_rti_mcp.kusto.kusto_connection.KustoConnectionStringBuilder"):
        connection = KustoConnection("https://test.kusto.windows.net")
        connection.query_client = mock_query_client
        return connection


@pytest.fixture
def mock_kusto_cache(mock_kusto_connection: KustoConnection) -> Mock:
    """Mock the global KUSTO_CONNECTION_CACHE."""
    with patch("fabric_rti_mcp.kusto.kusto_service.KUSTO_CONNECTION_CACHE") as cache:
        cache.__getitem__.return_value = mock_kusto_connection
        return cache


@pytest.fixture
def sample_cluster_uri() -> str:
    """Sample cluster URI for tests."""
    return "https://test.kusto.windows.net"
