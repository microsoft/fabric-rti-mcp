"""
Log Analytics Services.
"""

import re
from ipaddress import AddressValueError, ip_address
from typing import List


class LogAnalyticsService:
    """
    Service class for log analytics operations.
    """

    def __init__(self):
        self.common_attack_patterns = [
            r"(?i)(sql injection|script injection|xss|csrf)",
            r"(?i)(union select|drop table|exec|execute)",
            r"(?i)(<script|javascript:|onload=|onerror=)",
            r"(?i)(cmd\.exe|powershell|/bin/sh|wget|curl)",
        ]

    def extract_ip_addresses(self, text: str) -> List[str]:
        """
        Extract IP addresses from log text.

        Args:
            text: Log text to extract IPs from

        Returns:
            List[str]: List of valid IP addresses found
        """
        ip_pattern = r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"
        potential_ips = re.findall(ip_pattern, text)

        valid_ips = []
        for ip in potential_ips:
            try:
                ip_address(ip)
                valid_ips.append(ip)
            except (AddressValueError, ValueError):
                continue

        return valid_ips

    def detect_attack_patterns(self, log_entry: str) -> List[str]:
        """
        Detect potential attack patterns in log entries.

        Args:
            log_entry: Log entry to analyze

        Returns:
            List[str]: List of detected attack patterns
        """
        detected_patterns = []

        for pattern in self.common_attack_patterns:
            if re.search(pattern, log_entry):
                detected_patterns.append(pattern)

        return detected_patterns

    def classify_error_severity(self, error_message: str) -> str:
        """
        Classify error severity based on error message.

        Args:
            error_message: Error message to classify

        Returns:
            str: Severity level (Critical, High, Medium, Low)
        """
        error_lower = error_message.lower()

        critical_keywords = [
            "fatal",
            "critical",
            "emergency",
            "system failure",
            "crash",
        ]
        high_keywords = ["error", "exception", "failure", "timeout", "unavailable"]
        medium_keywords = ["warning", "deprecated", "retry", "slow"]

        for keyword in critical_keywords:
            if keyword in error_lower:
                return "Critical"

        for keyword in high_keywords:
            if keyword in error_lower:
                return "High"

        for keyword in medium_keywords:
            if keyword in error_lower:
                return "Medium"

        return "Low"

    def calculate_error_rate(self, total_requests: int, error_count: int) -> float:
        """
        Calculate error rate percentage.

        Args:
            total_requests: Total number of requests
            error_count: Number of error requests

        Returns:
            float: Error rate as percentage
        """
        if total_requests == 0:
            return 0.0

        return (error_count / total_requests) * 100.0

    def is_private_ip(self, ip: str) -> bool:
        """
        Check if an IP address is private/internal.

        Args:
            ip: IP address string

        Returns:
            bool: True if IP is private, False otherwise
        """
        try:
            ip_obj = ip_address(ip)
            return ip_obj.is_private
        except (AddressValueError, ValueError):
            return False
