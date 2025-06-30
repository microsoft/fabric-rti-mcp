"""
Unit tests for the Financial Analytics Extension.
"""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any

from mcp.server.fastmcp import FastMCP

from fabric_rti_mcp.extensions.financial.extension import FinancialAnalyticsExtension
from fabric_rti_mcp.extensions.financial.services import FinancialAnalyticsService
from fabric_rti_mcp.extensions.financial.templates import FinancialKQLTemplates


class TestFinancialAnalyticsExtension:
    """Test cases for FinancialAnalyticsExtension."""
    
    def test_extension_properties(self):
        """Test extension properties."""
        extension = FinancialAnalyticsExtension()
        
        assert extension.name == "financial-analytics"
        assert extension.version == "1.0.0"
        assert "financial analytics" in extension.description.lower()
        
        dependencies = extension.get_dependencies()
        assert "azure-kusto-data" in dependencies
        assert "pandas" in dependencies
        assert "numpy" in dependencies
    
    def test_register_tools(self):
        """Test tool registration."""
        extension = FinancialAnalyticsExtension()
        mock_mcp = Mock(spec=FastMCP)
        
        # Mock the tool decorator
        mock_mcp.tool.return_value = lambda func: func
        
        extension.register_tools(mock_mcp)
        
        # Verify tool decorator was called for each tool
        assert mock_mcp.tool.call_count >= 3  # Should have multiple tools
    
    def test_configuration_schema(self):
        """Test configuration schema."""
        extension = FinancialAnalyticsExtension()
        schema = extension.get_configuration_schema()
        
        assert schema is not None
        assert "type" in schema
        assert schema["type"] == "object"
        assert "properties" in schema


class TestFinancialAnalyticsService:
    """Test cases for FinancialAnalyticsService."""
    
    def test_validate_financial_data_valid(self):
        """Test validation of valid financial data."""
        service = FinancialAnalyticsService()
        
        # Test with valid data
        data = [
            {"price": 100.0, "symbol": "AAPL", "timestamp": "2023-01-01"},
            {"price": 102.0, "symbol": "AAPL", "timestamp": "2023-01-02"}
        ]
        
        assert service.validate_financial_data(data) is True
    
    def test_validate_financial_data_empty(self):
        """Test validation with empty data."""
        service = FinancialAnalyticsService()
        
        assert service.validate_financial_data([]) is False
    
    def test_validate_financial_data_missing_fields(self):
        """Test validation with missing required fields."""
        service = FinancialAnalyticsService()
        
        # Missing 'symbol' field
        data = [{"price": 100.0, "timestamp": "2023-01-01"}]
        
        assert service.validate_financial_data(data) is False
    
    def test_calculate_returns(self):
        """Test returns calculation."""
        service = FinancialAnalyticsService()
        
        prices = [100.0, 102.0, 98.0, 105.0]
        returns = service.calculate_returns(prices)
        
        assert len(returns) == 3
        assert abs(returns[0] - 0.02) < 0.001  # (102-100)/100 = 0.02
        assert abs(returns[1] - (-0.0392)) < 0.001  # (98-102)/102 ≈ -0.0392
    
    def test_calculate_returns_insufficient_data(self):
        """Test returns calculation with insufficient data."""
        service = FinancialAnalyticsService()
        
        assert service.calculate_returns([]) == []
        assert service.calculate_returns([100]) == []
    
    def test_calculate_returns_zero_price(self):
        """Test returns calculation with zero price."""
        service = FinancialAnalyticsService()
        
        prices = [0.0, 100.0, 102.0]
        returns = service.calculate_returns(prices)
        
        assert len(returns) == 2
        assert returns[0] == 0.0  # Handle division by zero
        assert abs(returns[1] - 0.02) < 0.001
    
    def test_format_financial_report(self):
        """Test financial report formatting."""
        service = FinancialAnalyticsService()
        
        data = {
            "symbol": "AAPL",
            "price": 150.25,
            "change": 2.5
        }
        
        report = service.format_financial_report(data)
        
        assert isinstance(report, str)
        assert "AAPL" in report
        assert "150.25" in report


class TestFinancialKQLTemplates:
    """Test cases for FinancialKQLTemplates."""
    
    def test_get_moving_average_query(self):
        """Test moving average query template."""
        templates = FinancialKQLTemplates()
        
        query = templates.get_moving_average_query(
            "StockPrices", "Price", "Timestamp", 10
        )
        
        assert isinstance(query, str)
        assert "StockPrices" in query
        assert "Price" in query
        assert "Timestamp" in query
        assert "MovingAverage" in query
        assert "10" in query
    
    def test_get_trend_analysis_query(self):
        """Test trend analysis query template."""
        templates = FinancialKQLTemplates()
        
        query = templates.get_trend_analysis_query(
            "StockPrices", "Price", "Timestamp", "Symbol", 30
        )
        
        assert isinstance(query, str)
        assert "StockPrices" in query
        assert "Price" in query
        assert "Symbol" in query
        assert "30" in query


@pytest.fixture
def financial_extension():
    """Fixture for financial analytics extension."""
    return FinancialAnalyticsExtension()


@pytest.fixture
def financial_service():
    """Fixture for financial analytics service."""
    return FinancialAnalyticsService()


@pytest.fixture
def financial_templates():
    """Fixture for financial KQL templates."""
    return FinancialKQLTemplates()
