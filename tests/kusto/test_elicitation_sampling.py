"""Tests for elicitation and sampling functionality in Kusto service."""

from unittest.mock import Mock, patch

import pytest

from fabric_rti_mcp.kusto.kusto_config import KustoServiceConfig
from fabric_rti_mcp.kusto.kusto_service import (
    KustoElicitationError,
    _elicit_cluster_selection,
    _elicit_database_selection,
    _sample_cluster_from_known_services,
    _sample_database_from_cluster,
    kusto_explore_with_elicitation,
    kusto_query_with_elicitation,
    kusto_sample_data_with_elicitation,
)


class TestClusterSampling:
    """Test cluster URI sampling functionality."""

    @patch("fabric_rti_mcp.kusto.kusto_service.KustoConfig.get_known_services")
    def test_sample_cluster_no_services(self, mock_get_services: Mock) -> None:
        """Test sampling when no services are configured."""
        mock_get_services.return_value = {}

        result = _sample_cluster_from_known_services()
        assert result is None

    @patch("fabric_rti_mcp.kusto.kusto_service.KustoConfig.get_known_services")
    def test_sample_cluster_single_service(self, mock_get_services: Mock) -> None:
        """Test sampling when only one service is available."""
        service = KustoServiceConfig("https://test.kusto.windows.net", "TestDB", "Test Service")
        mock_get_services.return_value = {"https://test.kusto.windows.net": service}

        result = _sample_cluster_from_known_services()
        assert result == "https://test.kusto.windows.net"

    @patch("fabric_rti_mcp.kusto.kusto_service.KustoConfig.get_known_services")
    @patch("fabric_rti_mcp.kusto.kusto_service.CONFIG")
    def test_sample_cluster_multiple_services_with_default(self, mock_config: Mock, mock_get_services: Mock) -> None:
        """Test sampling when multiple services are available and default is set."""
        service1 = KustoServiceConfig("https://test1.kusto.windows.net", "DB1", "Service 1")
        service2 = KustoServiceConfig("https://test2.kusto.windows.net", "DB2", "Service 2")
        mock_get_services.return_value = {
            "https://test1.kusto.windows.net": service1,
            "https://test2.kusto.windows.net": service2,
        }
        mock_config.default_service = service1

        result = _sample_cluster_from_known_services()
        assert result == "https://test1.kusto.windows.net"

    @patch("fabric_rti_mcp.kusto.kusto_service.KustoConfig.get_known_services")
    @patch("fabric_rti_mcp.kusto.kusto_service.CONFIG")
    def test_sample_cluster_context_based_selection(self, mock_config: Mock, mock_get_services: Mock) -> None:
        """Test context-based cluster selection."""
        service1 = KustoServiceConfig("https://prod.kusto.windows.net", "ProdDB", "Production")
        service2 = KustoServiceConfig("https://samples.kusto.windows.net", "SamplesDB", "Sample Data")
        mock_get_services.return_value = {
            "https://prod.kusto.windows.net": service1,
            "https://samples.kusto.windows.net": service2,
        }
        mock_config.default_service = None

        result = _sample_cluster_from_known_services("show me some sample data")
        assert result == "https://samples.kusto.windows.net"


class TestClusterElicitation:
    """Test cluster URI elicitation functionality."""

    @patch("fabric_rti_mcp.kusto.kusto_service.KustoConfig.get_known_services")
    def test_elicit_cluster_no_services(self, mock_get_services: Mock) -> None:
        """Test elicitation when no services are configured."""
        mock_get_services.return_value = {}

        with pytest.raises(KustoElicitationError) as exc_info:
            _elicit_cluster_selection()

        error = exc_info.value
        assert error.parameter_type == "cluster_uri"
        assert error.available_options == []
        assert "No Kusto cluster URI provided" in str(error)

    @patch("fabric_rti_mcp.kusto.kusto_service.KustoConfig.get_known_services")
    def test_elicit_cluster_with_services(self, mock_get_services: Mock) -> None:
        """Test elicitation when services are available."""
        service1 = KustoServiceConfig("https://test1.kusto.windows.net", "DB1", "Service 1")
        service2 = KustoServiceConfig("https://test2.kusto.windows.net", None, None)
        mock_get_services.return_value = {
            "https://test1.kusto.windows.net": service1,
            "https://test2.kusto.windows.net": service2,
        }

        with pytest.raises(KustoElicitationError) as exc_info:
            _elicit_cluster_selection()

        error = exc_info.value
        assert error.parameter_type == "cluster_uri"
        assert len(error.available_options) == 2
        assert error.available_options[0]["service_uri"] == "https://test1.kusto.windows.net"
        assert error.available_options[0]["description"] == "Service 1"
        assert error.available_options[1]["description"] == "No description"


class TestDatabaseSampling:
    """Test database sampling functionality."""

    @patch("fabric_rti_mcp.kusto.kusto_service._execute")
    def test_sample_database_no_databases(self, mock_execute: Mock) -> None:
        """Test sampling when no databases are found."""
        mock_execute.return_value = []

        result = _sample_database_from_cluster("https://test.kusto.windows.net")
        assert result is None

    @patch("fabric_rti_mcp.kusto.kusto_service._execute")
    def test_sample_database_single_database(self, mock_execute: Mock) -> None:
        """Test sampling when only one database exists."""
        mock_execute.return_value = [{"DatabaseName": "TestDB"}]

        result = _sample_database_from_cluster("https://test.kusto.windows.net")
        assert result == "TestDB"

    @patch("fabric_rti_mcp.kusto.kusto_service._execute")
    def test_sample_database_context_based_selection(self, mock_execute: Mock) -> None:
        """Test context-based database selection."""
        mock_execute.return_value = [
            {"DatabaseName": "ProdDB"},
            {"DatabaseName": "SamplesDB"},
            {"DatabaseName": "TestDB"},
        ]

        result = _sample_database_from_cluster("https://test.kusto.windows.net", "query with samples data")
        assert result == "SamplesDB"

    @patch("fabric_rti_mcp.kusto.kusto_service._execute")
    def test_sample_database_query_mentions_db(self, mock_execute: Mock) -> None:
        """Test selection when query mentions specific database."""
        mock_execute.return_value = [
            {"DatabaseName": "ProdDB"},
            {"DatabaseName": "TestDB"},
        ]

        result = _sample_database_from_cluster("https://test.kusto.windows.net", "TestDB.MyTable | take 10")
        assert result == "TestDB"

    @patch("fabric_rti_mcp.kusto.kusto_service._execute")
    def test_sample_database_exception_handling(self, mock_execute: Mock) -> None:
        """Test exception handling during database sampling."""
        mock_execute.side_effect = Exception("Connection failed")

        result = _sample_database_from_cluster("https://test.kusto.windows.net")
        assert result is None


class TestDatabaseElicitation:
    """Test database elicitation functionality."""

    @patch("fabric_rti_mcp.kusto.kusto_service._execute")
    def test_elicit_database_with_available_databases(self, mock_execute: Mock) -> None:
        """Test elicitation when databases are available."""
        mock_execute.return_value = [
            {"DatabaseName": "DB1", "TotalExtentSize": 1000},
            {"DatabaseName": "DB2", "TotalExtentSize": 2000},
        ]

        with pytest.raises(KustoElicitationError) as exc_info:
            _elicit_database_selection("https://test.kusto.windows.net")

        error = exc_info.value
        assert error.parameter_type == "database"
        assert len(error.available_options) == 2
        assert error.available_options[0]["database_name"] == "DB1"
        assert error.available_options[0]["size_mb"] == 1000

    @patch("fabric_rti_mcp.kusto.kusto_service._execute")
    def test_elicit_database_no_databases(self, mock_execute: Mock) -> None:
        """Test elicitation when no databases are found."""
        mock_execute.return_value = []

        with pytest.raises(KustoElicitationError) as exc_info:
            _elicit_database_selection("https://test.kusto.windows.net")

        error = exc_info.value
        assert error.parameter_type == "database"
        assert error.available_options == []

    @patch("fabric_rti_mcp.kusto.kusto_service._execute")
    def test_elicit_database_connection_failure(self, mock_execute: Mock) -> None:
        """Test elicitation when connection fails."""
        mock_execute.side_effect = Exception("Connection failed")

        with pytest.raises(KustoElicitationError) as exc_info:
            _elicit_database_selection("https://test.kusto.windows.net")

        error = exc_info.value
        assert error.parameter_type == "database"
        assert error.available_options == []


class TestElicitationTools:
    """Test the new tool functions that use elicitation."""

    @patch("fabric_rti_mcp.kusto.kusto_service._execute_with_elicitation")
    def test_kusto_query_with_elicitation(self, mock_execute: Mock) -> None:
        """Test kusto_query_with_elicitation function."""
        mock_execute.return_value = [{"TestColumn": "TestValue"}]

        result = kusto_query_with_elicitation("TestTable | take 10", "https://test.kusto.windows.net", "TestDB")

        mock_execute.assert_called_once_with("TestTable | take 10", "https://test.kusto.windows.net", database="TestDB")
        assert result == [{"TestColumn": "TestValue"}]

    @patch("fabric_rti_mcp.kusto.kusto_service._execute_with_elicitation")
    def test_kusto_sample_data_with_elicitation(self, mock_execute: Mock) -> None:
        """Test kusto_sample_data_with_elicitation function."""
        mock_execute.return_value = [{"TestColumn": "TestValue"}]

        result = kusto_sample_data_with_elicitation("MyTable", "https://test.kusto.windows.net", 5, "TestDB")

        mock_execute.assert_called_once_with("MyTable | sample 5", "https://test.kusto.windows.net", database="TestDB")
        assert result == [{"TestColumn": "TestValue"}]

    @patch("fabric_rti_mcp.kusto.kusto_service._execute_with_elicitation")
    def test_kusto_explore_with_elicitation(self, mock_execute: Mock) -> None:
        """Test kusto_explore_with_elicitation function."""
        mock_execute.return_value = [{"TableName": "MyTable"}]

        result = kusto_explore_with_elicitation("https://test.kusto.windows.net", "TestDB")

        mock_execute.assert_called_once_with(".show tables", "https://test.kusto.windows.net", database="TestDB")
        assert result == [{"TableName": "MyTable"}]

    @patch("fabric_rti_mcp.kusto.kusto_service._sample_cluster_from_known_services")
    @patch("fabric_rti_mcp.kusto.kusto_service._elicit_cluster_selection")
    def test_elicitation_with_no_cluster_uri(self, mock_elicit: Mock, mock_sample: Mock) -> None:
        """Test that elicitation is triggered when no cluster_uri is provided."""
        mock_sample.return_value = None
        mock_elicit.side_effect = KustoElicitationError("No cluster", [], "cluster_uri")

        with pytest.raises(KustoElicitationError):
            kusto_query_with_elicitation("TestTable | take 10")

        mock_sample.assert_called_once()
        mock_elicit.assert_called_once()
