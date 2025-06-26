from typing import cast
from unittest.mock import MagicMock, Mock, patch

from azure.kusto.data import ClientRequestProperties
from azure.kusto.data.response import KustoResponseDataSet

from fabric_rti_mcp import __version__
from fabric_rti_mcp.kusto.kusto_service import (
    KUSTO_CONNECTION_CACHE,
    KustoConnectionWrapper,
    add_kusto_cluster,
    kusto_connect,
    kusto_get_clusters,
    kusto_query,
)


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
    assert cast(str, crp.client_request_id).startswith("KFRTI_MCP.kusto_query:")
    assert crp.has_option("request_readonly")

    # Verify result format
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["TestColumn"] == "TestValue"


def test_add_kusto_cluster_new_cluster() -> None:
    """Test adding a new cluster to the cache."""
    cluster_uri = "https://test-cluster.kusto.windows.net"
    description = "Test cluster description"

    # Clear cache for clean test
    KUSTO_CONNECTION_CACHE.clear()

    # Act
    add_kusto_cluster(cluster_uri, description=description)

    # Assert
    assert cluster_uri in KUSTO_CONNECTION_CACHE
    connection_wrapper = KUSTO_CONNECTION_CACHE[cluster_uri]
    assert isinstance(connection_wrapper, KustoConnectionWrapper)
    assert connection_wrapper.description == description


def test_add_kusto_cluster_strips_trailing_slash() -> None:
    """Test that trailing slashes are stripped from cluster URIs."""
    cluster_uri_with_slash = "https://test-cluster.kusto.windows.net/"
    cluster_uri_clean = "https://test-cluster.kusto.windows.net"
    description = "Test cluster"

    # Clear cache for clean test
    KUSTO_CONNECTION_CACHE.clear()

    # Act
    add_kusto_cluster(cluster_uri_with_slash, description=description)

    # Assert
    assert cluster_uri_clean in KUSTO_CONNECTION_CACHE
    assert cluster_uri_with_slash not in KUSTO_CONNECTION_CACHE


def test_add_kusto_cluster_strips_whitespace() -> None:
    """Test that whitespace is stripped from cluster URIs."""
    cluster_uri_with_spaces = "  https://test-cluster.kusto.windows.net  "
    cluster_uri_clean = "https://test-cluster.kusto.windows.net"
    description = "Test cluster"

    # Clear cache for clean test
    KUSTO_CONNECTION_CACHE.clear()

    # Act
    add_kusto_cluster(cluster_uri_with_spaces, description=description)

    # Assert
    assert cluster_uri_clean in KUSTO_CONNECTION_CACHE
    assert cluster_uri_with_spaces not in KUSTO_CONNECTION_CACHE


def test_add_kusto_cluster_existing_cluster() -> None:
    """Test that adding an existing cluster doesn't overwrite it."""
    cluster_uri = "https://test-cluster.kusto.windows.net"
    original_description = "Original description"
    new_description = "New description"

    # Clear cache and add initial cluster
    KUSTO_CONNECTION_CACHE.clear()
    add_kusto_cluster(cluster_uri, description=original_description)

    # Act - try to add same cluster with different description
    add_kusto_cluster(cluster_uri, description=new_description)

    # Assert - original description should be preserved
    connection_wrapper = KUSTO_CONNECTION_CACHE[cluster_uri]
    assert connection_wrapper.description == original_description


def test_add_kusto_cluster_no_description() -> None:
    """Test adding a cluster without a description uses URI as description."""
    cluster_uri = "https://test-cluster.kusto.windows.net"

    # Clear cache for clean test
    KUSTO_CONNECTION_CACHE.clear()

    # Act
    add_kusto_cluster(cluster_uri)

    # Assert
    connection_wrapper = KUSTO_CONNECTION_CACHE[cluster_uri]
    assert connection_wrapper.description == cluster_uri


def test_kusto_connect() -> None:
    """Test kusto_connect function wraps add_kusto_cluster correctly."""
    cluster_uri = "https://connect-test.kusto.windows.net"
    description = "Connect test cluster"
    default_db = "TestDB"

    # Clear cache for clean test
    KUSTO_CONNECTION_CACHE.clear()

    # Act
    kusto_connect(cluster_uri, default_database=default_db, description=description)

    # Assert
    assert cluster_uri in KUSTO_CONNECTION_CACHE
    connection_wrapper = KUSTO_CONNECTION_CACHE[cluster_uri]
    assert connection_wrapper.description == description
    assert connection_wrapper.default_database == default_db


def test_kusto_get_clusters_empty_cache() -> None:
    """Test getting clusters when cache is empty."""
    # Clear cache for clean test
    KUSTO_CONNECTION_CACHE.clear()

    # Act
    clusters = kusto_get_clusters()

    # Assert
    assert clusters == []


def test_kusto_get_clusters_single_cluster() -> None:
    """Test getting clusters with one cluster in cache."""
    cluster_uri = "https://single-test.kusto.windows.net"
    description = "Single test cluster"

    # Clear cache and add one cluster
    KUSTO_CONNECTION_CACHE.clear()
    add_kusto_cluster(cluster_uri, description=description)

    # Act
    clusters = kusto_get_clusters()

    # Assert
    assert len(clusters) == 1
    assert clusters[0] == (cluster_uri, description)


def test_kusto_get_clusters_multiple_clusters() -> None:
    """Test getting clusters with multiple clusters in cache."""
    cluster1_uri = "https://cluster1.kusto.windows.net"
    cluster1_desc = "First cluster"
    cluster2_uri = "https://cluster2.kusto.windows.net"
    cluster2_desc = "Second cluster"
    cluster3_uri = "https://cluster3.kusto.windows.net"
    cluster3_desc = "Third cluster"

    # Clear cache and add multiple clusters
    KUSTO_CONNECTION_CACHE.clear()
    add_kusto_cluster(cluster1_uri, description=cluster1_desc)
    add_kusto_cluster(cluster2_uri, description=cluster2_desc)
    add_kusto_cluster(cluster3_uri, description=cluster3_desc)

    # Act
    clusters = kusto_get_clusters()

    # Assert
    assert len(clusters) == 3
    cluster_dict = dict(clusters)
    assert cluster_dict[cluster1_uri] == cluster1_desc
    assert cluster_dict[cluster2_uri] == cluster2_desc
    assert cluster_dict[cluster3_uri] == cluster3_desc


def test_kusto_get_clusters_returns_tuples() -> None:
    """Test that kusto_get_clusters returns list of tuples with correct structure."""
    cluster_uri = "https://tuple-test.kusto.windows.net"
    description = "Tuple test cluster"

    # Clear cache and add cluster
    KUSTO_CONNECTION_CACHE.clear()
    add_kusto_cluster(cluster_uri, description=description)

    # Act
    clusters = kusto_get_clusters()

    # Assert
    assert isinstance(clusters, list)
    assert len(clusters) == 1
    cluster_tuple = clusters[0]
    assert isinstance(cluster_tuple, tuple)
    assert len(cluster_tuple) == 2
    assert cluster_tuple[0] == cluster_uri
    assert cluster_tuple[1] == description
