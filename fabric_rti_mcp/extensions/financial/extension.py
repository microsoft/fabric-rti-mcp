"""
Financial Analytics Extension implementation.
"""

from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from fabric_rti_mcp.extensions.base import ExtensionBase
from fabric_rti_mcp.kusto import kusto_service
from .services import FinancialAnalyticsService
from .templates import FinancialKQLTemplates


class FinancialAnalyticsExtension(ExtensionBase):
    """
    Extension providing financial analytics tools and KQL templates.
    """
    
    def __init__(self):
        self.service = FinancialAnalyticsService()
        self.templates = FinancialKQLTemplates()
    
    @property
    def name(self) -> str:
        return "financial-analytics"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Financial analytics tools and KQL templates for financial data analysis"
    
    def get_dependencies(self) -> List[str]:
        return ["azure-kusto-data", "pandas", "numpy"]
    
    def register_tools(self, mcp: FastMCP) -> None:
        """Register all financial analytics tools."""
        
        # Moving averages
        @mcp.tool(
            annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False)
        )
        def calculate_moving_average(
            table_name: str,
            value_column: str,
            time_column: str,
            window_size: int,
            cluster_uri: str,
            database: Optional[str] = None
        ) -> List[Dict[str, Any]]:
            """
            Calculate moving average for financial data.
            
            Args:
                table_name: Name of the table containing financial data
                value_column: Column containing the values to average
                time_column: Column containing timestamps
                window_size: Number of periods for the moving average
                cluster_uri: Kusto cluster URI
                database: Optional database name
                
            Returns:
                List[Dict[str, Any]]: Results with moving averages
            """
            query = self.templates.get_moving_average_query(
                table_name, value_column, time_column, window_size
            )
            return kusto_service._execute(query, cluster_uri, database=database)
        
        @mcp.tool(
            annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False)
        )
        def analyze_financial_trends(
            table_name: str,
            price_column: str,
            time_column: str,
            symbol_column: str,
            days: int,
            cluster_uri: str,
            database: Optional[str] = None
        ) -> List[Dict[str, Any]]:
            """
            Analyze financial trends over a specified time period.
            
            Args:
                table_name: Name of the table containing financial data
                price_column: Column containing price data
                time_column: Column containing timestamps
                symbol_column: Column containing financial symbols
                days: Number of days to analyze
                cluster_uri: Kusto cluster URI
                database: Optional database name
                
            Returns:
                List[Dict[str, Any]]: Trend analysis results
            """
            query = self.templates.get_trend_analysis_query(
                table_name, price_column, time_column, symbol_column, days
            )
            return kusto_service._execute(query, cluster_uri, database=database)
        
        @mcp.tool(
            annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False)
        )
        def calculate_volatility(
            table_name: str,
            price_column: str,
            time_column: str,
            symbol_column: str,
            period_days: int,
            cluster_uri: str,
            database: Optional[str] = None
        ) -> List[Dict[str, Any]]:
            """
            Calculate volatility for financial instruments.
            
            Args:
                table_name: Name of the table containing financial data
                price_column: Column containing price data
                time_column: Column containing timestamps
                symbol_column: Column containing financial symbols
                period_days: Number of days for volatility calculation
                cluster_uri: Kusto cluster URI
                database: Optional database name
                
            Returns:
                List[Dict[str, Any]]: Volatility calculations
            """
            query = self.templates.get_volatility_query(
                table_name, price_column, time_column, symbol_column, period_days
            )
            return kusto_service._execute(query, cluster_uri, database=database)
        
        @mcp.tool(
            annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False)
        )
        def generate_financial_report(
            table_name: str,
            price_column: str,
            volume_column: str,
            time_column: str,
            symbol_column: str,
            start_date: str,
            end_date: str,
            cluster_uri: str,
            database: Optional[str] = None
        ) -> List[Dict[str, Any]]:
            """
            Generate a comprehensive financial report.
            
            Args:
                table_name: Name of the table containing financial data
                price_column: Column containing price data
                volume_column: Column containing volume data
                time_column: Column containing timestamps
                symbol_column: Column containing financial symbols
                start_date: Start date for the report (ISO format)
                end_date: End date for the report (ISO format)
                cluster_uri: Kusto cluster URI
                database: Optional database name
                
            Returns:
                List[Dict[str, Any]]: Comprehensive financial report
            """
            query = self.templates.get_financial_report_query(
                table_name, price_column, volume_column, time_column, 
                symbol_column, start_date, end_date
            )
            return kusto_service._execute(query, cluster_uri, database=database)
        
        @mcp.tool(
            annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False)
        )
        def detect_price_anomalies(
            table_name: str,
            price_column: str,
            time_column: str,
            symbol_column: str,
            threshold_multiplier: float,
            cluster_uri: str,
            database: Optional[str] = None
        ) -> List[Dict[str, Any]]:
            """
            Detect price anomalies using statistical methods.
            
            Args:
                table_name: Name of the table containing financial data
                price_column: Column containing price data
                time_column: Column containing timestamps
                symbol_column: Column containing financial symbols
                threshold_multiplier: Multiplier for standard deviation threshold
                cluster_uri: Kusto cluster URI
                database: Optional database name
                
            Returns:
                List[Dict[str, Any]]: Detected anomalies
            """
            query = self.templates.get_anomaly_detection_query(
                table_name, price_column, time_column, symbol_column, threshold_multiplier
            )
            return kusto_service._execute(query, cluster_uri, database=database)
    
    def get_configuration_schema(self) -> Optional[Dict[str, Any]]:
        """
        Get configuration schema for the financial analytics extension.
        
        Returns:
            Dict containing JSON schema for configuration
        """
        return {
            "type": "object",
            "properties": {
                "market_data_source": {
                    "type": "string",
                    "description": "Source for market data (e.g., 'bloomberg', 'yahoo', 'alpha_vantage')",
                    "default": "yahoo"
                },
                "default_currency": {
                    "type": "string",
                    "description": "Default currency for calculations",
                    "default": "USD"
                },
                "risk_free_rate": {
                    "type": "number",
                    "description": "Default risk-free rate for calculations",
                    "default": 0.02
                },
                "cache_duration": {
                    "type": "integer",
                    "description": "Cache duration in seconds for market data",
                    "default": 3600
                }
            }
        }
