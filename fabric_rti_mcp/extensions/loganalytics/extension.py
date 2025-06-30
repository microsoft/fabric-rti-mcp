"""
Log Analytics Extension implementation.
"""

from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from fabric_rti_mcp.extensions.base import ExtensionBase
from fabric_rti_mcp.kusto import kusto_service

from .services import LogAnalyticsService
from .templates import LogAnalyticsKQLTemplates


class LogAnalyticsExtension(ExtensionBase):
    """
    Extension providing log analytics tools and KQL templates.
    """

    def __init__(self) -> None:
        self.service = LogAnalyticsService()
        self.templates = LogAnalyticsKQLTemplates()

    @property
    def name(self) -> str:
        return "log-analytics"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Log analytics tools for security monitoring and performance analysis"

    def get_dependencies(self) -> List[str]:
        return ["azure-kusto-data", "re", "ipaddress"]

    def register_tools(self, mcp: FastMCP) -> None:
        """Register all log analytics tools."""

        @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False))
        def analyze_failed_logins(
            table_name: str,
            user_column: str,
            ip_column: str,
            timestamp_column: str,
            status_column: str,
            hours: int,
            cluster_uri: str,
            database: Optional[str] = None,
        ) -> List[Dict[str, Any]]:
            """
            Analyze failed login attempts for security monitoring.

            Args:
                table_name: Name of the log table
                user_column: Column containing usernames
                ip_column: Column containing IP addresses
                timestamp_column: Column containing timestamps
                status_column: Column containing login status
                hours: Number of hours to analyze
                cluster_uri: Kusto cluster URI
                database: Optional database name

            Returns:
                List[Dict[str, Any]]: Failed login analysis results
            """
            query = self.templates.get_failed_logins_query(
                table_name,
                user_column,
                ip_column,
                timestamp_column,
                status_column,
                hours,
            )
            return kusto_service._execute(query, cluster_uri, database=database)

        @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False))
        def detect_suspicious_ips(
            table_name: str,
            ip_column: str,
            timestamp_column: str,
            activity_column: str,
            threshold: int,
            hours: int,
            cluster_uri: str,
            database: Optional[str] = None,
        ) -> List[Dict[str, Any]]:
            """
            Detect suspicious IP addresses based on activity patterns.

            Args:
                table_name: Name of the log table
                ip_column: Column containing IP addresses
                timestamp_column: Column containing timestamps
                activity_column: Column containing activity type
                threshold: Minimum number of activities to be considered suspicious
                hours: Number of hours to analyze
                cluster_uri: Kusto cluster URI
                database: Optional database name

            Returns:
                List[Dict[str, Any]]: Suspicious IP analysis results
            """
            query = self.templates.get_suspicious_ips_query(
                table_name,
                ip_column,
                timestamp_column,
                activity_column,
                threshold,
                hours,
            )
            return kusto_service._execute(query, cluster_uri, database=database)

        @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False))
        def analyze_error_patterns(
            table_name: str,
            error_column: str,
            timestamp_column: str,
            service_column: str,
            hours: int,
            cluster_uri: str,
            database: Optional[str] = None,
        ) -> List[Dict[str, Any]]:
            """
            Analyze error patterns and trends in application logs.

            Args:
                table_name: Name of the log table
                error_column: Column containing error messages
                timestamp_column: Column containing timestamps
                service_column: Column containing service names
                hours: Number of hours to analyze
                cluster_uri: Kusto cluster URI
                database: Optional database name

            Returns:
                List[Dict[str, Any]]: Error pattern analysis results
            """
            query = self.templates.get_error_patterns_query(
                table_name, error_column, timestamp_column, service_column, hours
            )
            return kusto_service._execute(query, cluster_uri, database=database)

        @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False))
        def monitor_performance_metrics(
            table_name: str,
            response_time_column: str,
            timestamp_column: str,
            endpoint_column: str,
            hours: int,
            cluster_uri: str,
            database: Optional[str] = None,
        ) -> List[Dict[str, Any]]:
            """
            Monitor application performance metrics.

            Args:
                table_name: Name of the log table
                response_time_column: Column containing response times
                timestamp_column: Column containing timestamps
                endpoint_column: Column containing API endpoints
                hours: Number of hours to analyze
                cluster_uri: Kusto cluster URI
                database: Optional database name

            Returns:
                List[Dict[str, Any]]: Performance monitoring results
            """
            query = self.templates.get_performance_metrics_query(
                table_name,
                response_time_column,
                timestamp_column,
                endpoint_column,
                hours,
            )
            return kusto_service._execute(query, cluster_uri, database=database)

        @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False))
        def generate_security_summary(
            table_name: str,
            user_column: str,
            ip_column: str,
            action_column: str,
            timestamp_column: str,
            hours: int,
            cluster_uri: str,
            database: Optional[str] = None,
        ) -> List[Dict[str, Any]]:
            """
            Generate a comprehensive security summary report.

            Args:
                table_name: Name of the log table
                user_column: Column containing usernames
                ip_column: Column containing IP addresses
                action_column: Column containing actions/activities
                timestamp_column: Column containing timestamps
                hours: Number of hours to analyze
                cluster_uri: Kusto cluster URI
                database: Optional database name

            Returns:
                List[Dict[str, Any]]: Security summary report
            """
            query = self.templates.get_security_summary_query(
                table_name,
                user_column,
                ip_column,
                action_column,
                timestamp_column,
                hours,
            )
            return kusto_service._execute(query, cluster_uri, database=database)

    def get_configuration_schema(self) -> Optional[Dict[str, Any]]:
        """
        Get configuration schema for the log analytics extension.

        Returns:
            Dict containing JSON schema for configuration
        """
        return {
            "type": "object",
            "properties": {
                "log_retention_days": {
                    "type": "integer",
                    "description": "Number of days to retain logs for analysis",
                    "default": 30,
                },
                "alert_threshold": {
                    "type": "integer",
                    "description": "Threshold for triggering security alerts",
                    "default": 5,
                },
                "ip_whitelist": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of whitelisted IP addresses",
                    "default": [],
                },
                "enable_geo_lookup": {
                    "type": "boolean",
                    "description": "Enable geographic lookup for IP addresses",
                    "default": True,
                },
                "performance_baseline": {
                    "type": "object",
                    "properties": {
                        "cpu_threshold": {"type": "number", "default": 80.0},
                        "memory_threshold": {"type": "number", "default": 85.0},
                        "disk_threshold": {"type": "number", "default": 90.0},
                    },
                },
            },
        }
