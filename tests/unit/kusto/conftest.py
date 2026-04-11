from typing import Any
from unittest.mock import Mock, patch

import pytest
from azure.kusto.data import KustoClient
from azure.kusto.data.response import KustoResponseDataSetV1

from fabric_rti_mcp.services.kusto.kusto_connection import KustoConnection


@pytest.fixture
def mock_kusto_response() -> KustoResponseDataSetV1:
    """Create a minimal KustoResponseDataSet for testing."""
    json_response: dict[str, list[dict[str, Any]]] = {
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
    with patch("fabric_rti_mcp.services.kusto.kusto_connection.KustoConnectionStringBuilder"):
        connection = KustoConnection("https://test.kusto.windows.net")
        connection.query_client = mock_query_client
        return connection


@pytest.fixture
def mock_kusto_cache(mock_kusto_connection: KustoConnection) -> Mock:
    """Mock the global KUSTO_CONNECTION_CACHE."""
    with patch("fabric_rti_mcp.services.kusto.kusto_service.KUSTO_CONNECTION_CACHE") as cache:
        cache.__getitem__.return_value = mock_kusto_connection
        return cache


@pytest.fixture
def sample_cluster_uri() -> str:
    """Sample cluster URI for tests."""
    return "https://test.kusto.windows.net"


@pytest.fixture
def mock_queryplan_response() -> KustoResponseDataSetV1:
    """Create a mock .show queryplan response for testing."""
    import json

    physical_plan = json.dumps(
        {
            "TotalRowCount": 59066,
            "RootOperator": {
                "Operators": [
                    {
                        "Source": {
                            "Source": {
                                "StrategyHint": {"Concurrency": 1, "Spread": 1},
                                "Operands": [{"TotalRowCount": 59066, "HasSelection": False}],
                            }
                        }
                    }
                ]
            },
        }
    )
    json_response: dict[str, list[dict[str, Any]]] = {
        "Tables": [
            {
                "TableName": "Table_0",
                "Columns": [
                    {"ColumnName": "ResultType", "DataType": "string"},
                    {"ColumnName": "Format", "DataType": "string"},
                    {"ColumnName": "Content", "DataType": "string"},
                ],
                "Rows": [
                    ["QueryText", "text", "StormEvents | count"],
                    [
                        "RelopTree",
                        "json",
                        '{"type":"CrossTableUnionOperator","output":["Count:Int64"]}',
                    ],
                    ["QueryPlan", "json", physical_plan],
                    [
                        "Stats",
                        "json",
                        '{"Duration":"00:00:00.001","PlanSize":9487,"RelopSize":229}',
                    ],
                ],
            }
        ]
    }
    return KustoResponseDataSetV1(json_response)
