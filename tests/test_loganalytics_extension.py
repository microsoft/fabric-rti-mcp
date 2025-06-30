"""
Tests for Log Analytics Extension.
"""

from unittest.mock import Mock, patch

from mcp.server.fastmcp import FastMCP

from fabric_rti_mcp.extensions.loganalytics import LogAnalyticsExtension
from fabric_rti_mcp.extensions.loganalytics.services import LogAnalyticsService
from fabric_rti_mcp.extensions.loganalytics.templates import LogAnalyticsKQLTemplates


class TestLogAnalyticsExtension:
    """Test cases for Log Analytics Extension."""
    
    def test_extension_properties(self):
        """Test log analytics extension properties."""
        extension = LogAnalyticsExtension()
        
        assert extension.name == "log-analytics"
        assert extension.version == "1.0.0"
        assert "log analytics" in extension.description.lower()
        assert "azure-kusto-data" in extension.get_dependencies()
    
    @patch('fabric_rti_mcp.kusto.kusto_service._execute')
    def test_register_tools(self, mock_execute):
        """Test that log analytics tools are registered correctly."""
        extension = LogAnalyticsExtension()
        mock_mcp = Mock(spec=FastMCP)
        
        # Mock the _execute function to return sample data
        mock_execute.return_value = [{"ip": "192.168.1.1", "failed_attempts": 5}]
        
        extension.register_tools(mock_mcp)
        
        # Verify that mcp.tool was called (tools were registered)
        assert mock_mcp.tool.called
        assert mock_mcp.tool.call_count >= 5  # We registered 5 tools


class TestLogAnalyticsService:
    """Test cases for Log Analytics Service."""
    
    def test_extract_ip_addresses(self):
        """Test IP address extraction from log text."""
        service = LogAnalyticsService()
        log_text = "Connection from 192.168.1.1 and 10.0.0.1 failed. Invalid IP: 999.999.999.999"
        
        ips = service.extract_ip_addresses(log_text)
        
        assert "192.168.1.1" in ips
        assert "10.0.0.1" in ips
        assert "999.999.999.999" not in ips  # Invalid IP should be filtered out
    
    def test_detect_attack_patterns(self):
        """Test attack pattern detection."""
        service = LogAnalyticsService()
        
        # Test SQL injection pattern
        sql_injection_log = "User attempted: SELECT * FROM users WHERE id = 1; DROP TABLE users"
        patterns = service.detect_attack_patterns(sql_injection_log)
        assert len(patterns) > 0
        
        # Test XSS pattern
        xss_log = "User input: <script>alert('xss')</script>"
        patterns = service.detect_attack_patterns(xss_log)
        assert len(patterns) > 0
        
        # Test normal log
        normal_log = "User logged in successfully"
        patterns = service.detect_attack_patterns(normal_log)
        assert len(patterns) == 0
    
    def test_classify_error_severity(self):
        """Test error severity classification."""
        service = LogAnalyticsService()
        
        assert service.classify_error_severity("Fatal system crash") == "Critical"
        assert service.classify_error_severity("Database connection error") == "High"
        assert service.classify_error_severity("Warning: deprecated method used") == "Medium"
        assert service.classify_error_severity("Info: user logged in") == "Low"
    
    def test_calculate_error_rate(self):
        """Test error rate calculation."""
        service = LogAnalyticsService()
        
        assert service.calculate_error_rate(100, 5) == 5.0
        assert service.calculate_error_rate(0, 0) == 0.0
        assert service.calculate_error_rate(1000, 25) == 2.5
    
    def test_is_private_ip(self):
        """Test private IP address detection."""
        service = LogAnalyticsService()
        
        assert service.is_private_ip("192.168.1.1") is True
        assert service.is_private_ip("10.0.0.1") is True
        assert service.is_private_ip("8.8.8.8") is False
        assert service.is_private_ip("invalid-ip") is False


class TestLogAnalyticsKQLTemplates:
    """Test cases for Log Analytics KQL Templates."""
    
    def test_get_failed_logins_query(self):
        """Test failed logins KQL query generation."""
        templates = LogAnalyticsKQLTemplates()
        
        query = templates.get_failed_logins_query(
            "SecurityLogs", "username", "source_ip", "timestamp", "status", 24
        )
        
        assert "SecurityLogs" in query
        assert "username" in query
        assert "source_ip" in query
        assert "24h" in query
        assert "FailedAttempts" in query
        assert "RiskScore" in query
    
    def test_get_suspicious_ips_query(self):
        """Test suspicious IPs KQL query generation."""
        templates = LogAnalyticsKQLTemplates()
        
        query = templates.get_suspicious_ips_query(
            "SecurityLogs", "source_ip", "timestamp", "activity", 100, 12
        )
        
        assert "SecurityLogs" in query
        assert "source_ip" in query
        assert "activity" in query
        assert "12h" in query
        assert "ActivityCount" in query
        assert "SuspicionLevel" in query
    
    def test_get_error_patterns_query(self):
        """Test error patterns KQL query generation."""
        templates = LogAnalyticsKQLTemplates()
        
        query = templates.get_error_patterns_query(
            "ApplicationLogs", "error_message", "timestamp", "service", 6
        )
        
        assert "ApplicationLogs" in query
        assert "error_message" in query
        assert "service" in query
        assert "6h" in query
        assert "ErrorType" in query
        assert "Severity" in query
    
    def test_get_performance_metrics_query(self):
        """Test performance metrics KQL query generation."""
        templates = LogAnalyticsKQLTemplates()
        
        query = templates.get_performance_metrics_query(
            "APILogs", "response_time", "timestamp", "endpoint", 1
        )
        
        assert "APILogs" in query
        assert "response_time" in query
        assert "endpoint" in query
        assert "1h" in query
        assert "AvgResponseTime" in query
        assert "P95ResponseTime" in query
    
    def test_get_security_summary_query(self):
        """Test security summary KQL query generation."""
        templates = LogAnalyticsKQLTemplates()
        
        query = templates.get_security_summary_query(
            "SecurityLogs", "username", "source_ip", "action", "timestamp", 24
        )
        
        assert "SecurityLogs" in query
        assert "username" in query
        assert "source_ip" in query
        assert "action" in query
        assert "24h" in query
        assert "SecuritySummary" in query
        assert "TopSuspiciousIPs" in query
