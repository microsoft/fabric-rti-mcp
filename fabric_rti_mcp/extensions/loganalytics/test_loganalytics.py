"""
Unit tests for the Log Analytics Extension.
"""

import pytest
from unittest.mock import Mock
from typing import Dict, Any

from mcp.server.fastmcp import FastMCP

from fabric_rti_mcp.extensions.loganalytics.extension import LogAnalyticsExtension
from fabric_rti_mcp.extensions.loganalytics.services import LogAnalyticsService
from fabric_rti_mcp.extensions.loganalytics.templates import LogAnalyticsKQLTemplates


class TestLogAnalyticsExtension:
    """Test cases for LogAnalyticsExtension."""
    
    def test_extension_properties(self):
        """Test extension properties."""
        extension = LogAnalyticsExtension()
        
        assert extension.name == "log-analytics"
        assert extension.version == "1.0.0"
        assert "log analytics" in extension.description.lower()
        
        dependencies = extension.get_dependencies()
        assert "azure-kusto-data" in dependencies
        assert "re" in dependencies
        assert "ipaddress" in dependencies
    
    def test_register_tools(self):
        """Test tool registration."""
        extension = LogAnalyticsExtension()
        mock_mcp = Mock(spec=FastMCP)
        
        # Mock the tool decorator
        mock_mcp.tool.return_value = lambda func: func
        
        extension.register_tools(mock_mcp)
        
        # Verify tool decorator was called for each tool
        assert mock_mcp.tool.call_count >= 3  # Should have multiple tools
    
    def test_configuration_schema(self):
        """Test configuration schema."""
        extension = LogAnalyticsExtension()
        schema = extension.get_configuration_schema()
        
        assert schema is not None
        assert "type" in schema
        assert schema["type"] == "object"
        assert "properties" in schema


class TestLogAnalyticsService:
    """Test cases for LogAnalyticsService."""
    
    def test_extract_ip_addresses_valid(self):
        """Test extraction of valid IP addresses."""
        service = LogAnalyticsService()
        
        text = "Connection from 192.168.1.100 failed, retry from 10.0.0.1"
        ips = service.extract_ip_addresses(text)
        
        assert isinstance(ips, list)
        assert "192.168.1.100" in ips
        assert "10.0.0.1" in ips
    
    def test_extract_ip_addresses_invalid(self):
        """Test extraction with invalid IP addresses."""
        service = LogAnalyticsService()
        
        text = "No valid IPs here: 999.999.999.999 and not.an.ip"
        ips = service.extract_ip_addresses(text)
        
        assert isinstance(ips, list)
        assert len(ips) == 0
    
    def test_extract_ip_addresses_empty(self):
        """Test extraction from empty text."""
        service = LogAnalyticsService()
        
        ips = service.extract_ip_addresses("")
        
        assert isinstance(ips, list)
        assert len(ips) == 0
    
    def test_detect_attack_patterns_sql_injection(self):
        """Test detection of SQL injection patterns."""
        service = LogAnalyticsService()
        
        log_entry = "User input: ' union select * from users"
        patterns = service.detect_attack_patterns(log_entry)
        
        assert isinstance(patterns, list)
        assert len(patterns) > 0
    
    def test_detect_attack_patterns_xss(self):
        """Test detection of XSS patterns."""
        service = LogAnalyticsService()
        
        log_entry = "Request contains: <script>alert('xss')</script>"
        patterns = service.detect_attack_patterns(log_entry)
        
        assert isinstance(patterns, list)
        assert len(patterns) > 0
    
    def test_detect_attack_patterns_clean(self):
        """Test detection with clean log entry."""
        service = LogAnalyticsService()
        
        log_entry = "Normal user login from IP 192.168.1.100"
        patterns = service.detect_attack_patterns(log_entry)
        
        assert isinstance(patterns, list)
        assert len(patterns) == 0
    
    def test_classify_error_severity_critical(self):
        """Test classification of critical errors."""
        service = LogAnalyticsService()
        
        error_messages = [
            "Fatal system crash detected",
            "Critical database failure",
            "Emergency shutdown initiated"
        ]
        
        for message in error_messages:
            severity = service.classify_error_severity(message)
            assert severity == "Critical"
    
    def test_classify_error_severity_high(self):
        """Test classification of high severity errors."""
        service = LogAnalyticsService()
        
        error_messages = [
            "Database connection error",
            "Unhandled exception occurred",
            "Service timeout failure"
        ]
        
        for message in error_messages:
            severity = service.classify_error_severity(message)
            assert severity == "High"
    
    def test_classify_error_severity_medium(self):
        """Test classification of medium severity errors."""
        service = LogAnalyticsService()
        
        error_messages = [
            "Deprecated API usage warning",
            "Slow query performance",
            "Retry attempt failed"
        ]
        
        for message in error_messages:
            severity = service.classify_error_severity(message)
            assert severity == "Medium"
    
    def test_classify_error_severity_low(self):
        """Test classification of low severity errors."""
        service = LogAnalyticsService()
        
        error_message = "Info message about user login"
        severity = service.classify_error_severity(error_message)
        
        assert severity == "Low"
    
    def test_calculate_error_rate_normal(self):
        """Test error rate calculation."""
        service = LogAnalyticsService()
        
        rate = service.calculate_error_rate(1000, 50)
        
        assert abs(rate - 5.0) < 0.001  # 50/1000 * 100 = 5%
    
    def test_calculate_error_rate_zero_requests(self):
        """Test error rate calculation with zero requests."""
        service = LogAnalyticsService()
        
        rate = service.calculate_error_rate(0, 0)
        
        assert rate == 0.0
    
    def test_calculate_error_rate_no_errors(self):
        """Test error rate calculation with no errors."""
        service = LogAnalyticsService()
        
        rate = service.calculate_error_rate(1000, 0)
        
        assert rate == 0.0
    
    def test_is_private_ip_private(self):
        """Test identification of private IP addresses."""
        service = LogAnalyticsService()
        
        private_ips = ["192.168.1.1", "10.0.0.1", "172.16.0.1"]
        
        for ip in private_ips:
            assert service.is_private_ip(ip) is True
    
    def test_is_private_ip_public(self):
        """Test identification of public IP addresses."""
        service = LogAnalyticsService()
        
        public_ips = ["8.8.8.8", "1.1.1.1", "208.67.222.222"]
        
        for ip in public_ips:
            assert service.is_private_ip(ip) is False
    
    def test_is_private_ip_invalid(self):
        """Test with invalid IP addresses."""
        service = LogAnalyticsService()
        
        invalid_ips = ["not.an.ip", "256.256.256.256", ""]
        
        for ip in invalid_ips:
            assert service.is_private_ip(ip) is False


class TestLogAnalyticsKQLTemplates:
    """Test cases for LogAnalyticsKQLTemplates."""
    
    def test_get_failed_logins_query(self):
        """Test failed logins query template."""
        templates = LogAnalyticsKQLTemplates()
        
        query = templates.get_failed_logins_query(
            "AuthenticationLog", "User", "SourceIP", "Timestamp", "Status", 24
        )
        
        assert isinstance(query, str)
        assert "AuthenticationLog" in query
        assert "User" in query
        assert "SourceIP" in query
        assert "Status" in query
        assert "24h" in query
        assert any(word in query.lower() for word in ["failed", "failure", "error"])
    
    def test_get_suspicious_ips_query(self):
        """Test suspicious IPs query template."""
        templates = LogAnalyticsKQLTemplates()
        
        query = templates.get_suspicious_ips_query(
            "SecurityLog", "SourceIP", "Timestamp", "EventType", 10, 12
        )
        
        assert isinstance(query, str)
        assert "SecurityLog" in query
        assert "SourceIP" in query
        assert "EventType" in query
        assert "12h" in query
    
    def test_get_error_patterns_query(self):
        """Test error patterns query template."""
        templates = LogAnalyticsKQLTemplates()
        
        query = templates.get_error_patterns_query(
            "ApplicationLog", "ErrorMessage", "Component", "Timestamp", 6
        )
        
        assert isinstance(query, str)
        assert "ApplicationLog" in query
        assert "ErrorMessage" in query
        assert "Component" in query
        assert "6h" in query
        assert any(word in query.lower() for word in ["error", "exception", "pattern"])
    
    def test_get_performance_metrics_query(self):
        """Test performance metrics query template."""
        templates = LogAnalyticsKQLTemplates()
        
        query = templates.get_performance_metrics_query(
            "PerformanceLog", "Timestamp", "cpu", "Endpoint", 4
        )
        
        assert isinstance(query, str)
        assert "PerformanceLog" in query
        assert "Timestamp" in query
        assert "cpu" in query
        assert "Endpoint" in query
        assert "4h" in query
    
    def test_get_security_summary_query(self):
        """Test security summary query template."""
        templates = LogAnalyticsKQLTemplates()
        
        query = templates.get_security_summary_query(
            "SecurityLog", "EventType", "Severity", "SourceIP", "Timestamp", 24
        )
        
        assert isinstance(query, str)
        assert "SecurityLog" in query
        assert "EventType" in query
        assert "Severity" in query
        assert "SourceIP" in query
        assert "24h" in query
        assert any(word in query.lower() for word in ["security", "summary", "event"])


@pytest.fixture
def log_extension():
    """Fixture for log analytics extension."""
    return LogAnalyticsExtension()


@pytest.fixture
def log_service():
    """Fixture for log analytics service."""
    return LogAnalyticsService()


@pytest.fixture
def log_templates():
    """Fixture for log analytics KQL templates."""
    return LogAnalyticsKQLTemplates()
