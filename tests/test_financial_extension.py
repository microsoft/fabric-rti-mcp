"""
Tests for Financial Analytics Extension.
"""

from unittest.mock import Mock, patch

from mcp.server.fastmcp import FastMCP

from fabric_rti_mcp.extensions.financial import FinancialAnalyticsExtension
from fabric_rti_mcp.extensions.financial.services import FinancialAnalyticsService
from fabric_rti_mcp.extensions.financial.templates import FinancialKQLTemplates


class TestFinancialAnalyticsExtension:
    """Test cases for Financial Analytics Extension."""

    def test_extension_properties(self) -> None:
        """Test financial extension properties."""
        extension = FinancialAnalyticsExtension()

        assert extension.name == "financial-analytics"
        assert extension.version == "1.0.0"
        assert "financial analytics" in extension.description.lower()
        assert "azure-kusto-data" in extension.get_dependencies()

    @patch("fabric_rti_mcp.kusto.kusto_service._execute")
    def test_register_tools(self, mock_execute: Mock) -> None:
        """Test that financial tools are registered correctly."""
        extension = FinancialAnalyticsExtension()
        mock_mcp = Mock(spec=FastMCP)

        # Mock the _execute function to return sample data
        mock_execute.return_value = [{"symbol": "AAPL", "moving_average": 150.0}]

        extension.register_tools(mock_mcp)

        # Verify that mcp.tool was called (tools were registered)
        assert mock_mcp.tool.called
        assert mock_mcp.tool.call_count >= 5  # We registered 5 tools


class TestFinancialAnalyticsService:
    """Test cases for Financial Analytics Service."""

    def test_validate_financial_data_valid(self) -> None:
        """Test validation of valid financial data."""
        service = FinancialAnalyticsService()
        valid_data = [
            {"price": 100.0, "symbol": "AAPL", "timestamp": "2023-01-01"},
            {"price": 101.0, "symbol": "MSFT", "timestamp": "2023-01-02"},
        ]

        assert service.validate_financial_data(valid_data) is True

    def test_validate_financial_data_invalid(self) -> None:
        """Test validation of invalid financial data."""
        service = FinancialAnalyticsService()

        # Test empty data
        assert service.validate_financial_data([]) is False

        # Test missing required fields
        invalid_data = [{"price": 100.0, "symbol": "AAPL"}]  # Missing timestamp
        assert service.validate_financial_data(invalid_data) is False

    def test_calculate_returns(self) -> None:
        """Test returns calculation."""
        service = FinancialAnalyticsService()
        prices = [100.0, 105.0, 102.0, 108.0]

        returns = service.calculate_returns(prices)

        # Expected approximate values: [0.05, -0.0285714, 0.0588235]
        assert len(returns) == 3
        assert abs(returns[0] - 0.05) < 0.001

    def test_calculate_returns_insufficient_data(self) -> None:
        """Test returns calculation with insufficient data."""
        service = FinancialAnalyticsService()

        assert service.calculate_returns([]) == []
        assert service.calculate_returns([100.0]) == []

    def test_format_financial_report(self) -> None:
        """Test financial report formatting."""
        service = FinancialAnalyticsService()
        data = {"symbol": "AAPL", "price": 150.0, "volume": 1000000}

        formatted = service.format_financial_report(data)

        assert '"symbol": "AAPL"' in formatted
        assert '"price": 150.0' in formatted


class TestFinancialKQLTemplates:
    """Test cases for Financial KQL Templates."""

    def test_get_moving_average_query(self) -> None:
        """Test moving average KQL query generation."""
        templates = FinancialKQLTemplates()

        query = templates.get_moving_average_query(
            "StockPrices", "price", "timestamp", 5
        )

        assert "StockPrices" in query
        assert "price" in query
        assert "timestamp" in query
        assert "MovingAverage" in query
        assert "series_fir" in query

    def test_get_trend_analysis_query(self) -> None:
        """Test trend analysis KQL query generation."""
        templates = FinancialKQLTemplates()

        query = templates.get_trend_analysis_query(
            "StockPrices", "price", "timestamp", "symbol", 30
        )

        assert "StockPrices" in query
        assert "price" in query
        assert "timestamp" in query
        assert "symbol" in query
        assert "30d" in query
        assert "TotalReturn" in query
        assert "TrendDirection" in query

    def test_get_volatility_query(self) -> None:
        """Test volatility calculation KQL query generation."""
        templates = FinancialKQLTemplates()

        query = templates.get_volatility_query(
            "StockPrices", "price", "timestamp", "symbol", 252
        )

        assert "StockPrices" in query
        assert "price" in query
        assert "Volatility" in query
        assert "DailyReturn" in query
        assert "sqrt(252)" in query

    def test_get_financial_report_query(self) -> None:
        """Test financial report KQL query generation."""
        templates = FinancialKQLTemplates()

        query = templates.get_financial_report_query(
            "StockPrices",
            "price",
            "volume",
            "timestamp",
            "symbol",
            "2023-01-01",
            "2023-12-31",
        )

        assert "StockPrices" in query
        assert "price" in query
        assert "volume" in query
        assert "2023-01-01" in query
        assert "2023-12-31" in query
        assert "OpenPrice" in query
        assert "ClosePrice" in query

    def test_get_anomaly_detection_query(self) -> None:
        """Test anomaly detection KQL query generation."""
        templates = FinancialKQLTemplates()

        query = templates.get_anomaly_detection_query(
            "StockPrices", "price", "timestamp", "symbol", 2.0
        )

        assert "StockPrices" in query
        assert "price" in query
        assert "ZScore" in query
        assert "IsAnomaly" in query
        assert "2.0" in query
