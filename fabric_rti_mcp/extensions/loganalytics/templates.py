"""
KQL Templates for Log Analytics.
"""


class LogAnalyticsKQLTemplates:
    """
    Collection of KQL query templates for log analytics.
    """

    def get_failed_logins_query(
        self,
        table_name: str,
        user_column: str,
        ip_column: str,
        timestamp_column: str,
        status_column: str,
        hours: int,
    ) -> str:
        """
        Generate KQL query for analyzing failed login attempts.

        Args:
            table_name: Name of the log table
            user_column: Column containing usernames
            ip_column: Column containing IP addresses
            timestamp_column: Column containing timestamps
            status_column: Column containing login status
            hours: Number of hours to analyze

        Returns:
            str: KQL query for failed login analysis
        """
        return f"""
{table_name}
| where {timestamp_column} >= ago({hours}h)
| where {status_column} has_any ("failed", "failure", "error", "denied", "401", "403")
| summarize
    FailedAttempts = count(),
    UniqueUsers = dcount({user_column}),
    FirstFailure = min({timestamp_column}),
    LastFailure = max({timestamp_column}),
    Users = make_set({user_column}, 10)
    by {ip_column}
| where FailedAttempts >= 3
| extend
    AttackDuration = LastFailure - FirstFailure,
    RiskScore = case(
        FailedAttempts >= 50, "Critical",
        FailedAttempts >= 20, "High",
        FailedAttempts >= 10, "Medium",
        "Low"
    )
| project
    IP = {ip_column},
    FailedAttempts,
    UniqueUsers,
    RiskScore,
    AttackDuration,
    FirstFailure,
    LastFailure,
    Users
| order by FailedAttempts desc
"""

    def get_suspicious_ips_query(
        self,
        table_name: str,
        ip_column: str,
        timestamp_column: str,
        activity_column: str,
        threshold: int,
        hours: int,
    ) -> str:
        """
        Generate KQL query for detecting suspicious IP addresses.

        Args:
            table_name: Name of the log table
            ip_column: Column containing IP addresses
            timestamp_column: Column containing timestamps
            activity_column: Column containing activity type
            threshold: Minimum number of activities to be considered suspicious
            hours: Number of hours to analyze

        Returns:
            str: KQL query for suspicious IP detection
        """
        return f"""
{table_name}
| where {timestamp_column} >= ago({hours}h)
| summarize
    ActivityCount = count(),
    UniqueActivities = dcount({activity_column}),
    Activities = make_set({activity_column}, 20),
    FirstSeen = min({timestamp_column}),
    LastSeen = max({timestamp_column}),
    RequestsPerHour = count() / {hours}
    by {ip_column}
| where ActivityCount >= {threshold}
| extend
    SuspicionLevel = case(
        RequestsPerHour >= 1000, "Very High",
        RequestsPerHour >= 500, "High",
        RequestsPerHour >= 100, "Medium",
        "Low"
    ),
    ActivitySpan = LastSeen - FirstSeen
| project
    IP = {ip_column},
    ActivityCount,
    RequestsPerHour,
    UniqueActivities,
    SuspicionLevel,
    ActivitySpan,
    FirstSeen,
    LastSeen,
    Activities
| order by RequestsPerHour desc
"""

    def get_error_patterns_query(
        self,
        table_name: str,
        error_column: str,
        timestamp_column: str,
        service_column: str,
        hours: int,
    ) -> str:
        """
        Generate KQL query for analyzing error patterns.

        Args:
            table_name: Name of the log table
            error_column: Column containing error messages
            timestamp_column: Column containing timestamps
            service_column: Column containing service names
            hours: Number of hours to analyze

        Returns:
            str: KQL query for error pattern analysis
        """
        return f"""
{table_name}
| where {timestamp_column} >= ago({hours}h)
| where isnotempty({error_column})
| extend ErrorType = case(
    {error_column} has_any ("timeout", "connection", "network"), "Network",
    {error_column} has_any ("memory", "out of memory", "heap"), "Memory",
    {error_column} has_any ("sql", "database", "connection pool"), "Database",
    {error_column} has_any ("permission", "access denied", "forbidden"), "Permission",
    {error_column} has_any ("null", "nullpointer", "reference"), "NullReference",
    "Other"
)
| summarize
    ErrorCount = count(),
    ErrorRate = count() / ({hours} * 60),  // Errors per minute
    UniqueErrors = dcount({error_column}),
    FirstOccurrence = min({timestamp_column}),
    LastOccurrence = max({timestamp_column}),
    SampleErrors = take_any({error_column}, 3)
    by {service_column}, ErrorType
| extend
    Severity = case(
        ErrorRate >= 10, "Critical",
        ErrorRate >= 5, "High",
        ErrorRate >= 1, "Medium",
        "Low"
    )
| project
    Service = {service_column},
    ErrorType,
    ErrorCount,
    ErrorRate,
    Severity,
    UniqueErrors,
    FirstOccurrence,
    LastOccurrence,
    SampleErrors
| order by ErrorRate desc
"""

    def get_performance_metrics_query(
        self,
        table_name: str,
        response_time_column: str,
        timestamp_column: str,
        endpoint_column: str,
        hours: int,
    ) -> str:
        """
        Generate KQL query for performance monitoring.

        Args:
            table_name: Name of the log table
            response_time_column: Column containing response times
            timestamp_column: Column containing timestamps
            endpoint_column: Column containing API endpoints
            hours: Number of hours to analyze

        Returns:
            str: KQL query for performance monitoring
        """
        return f"""
{table_name}
| where {timestamp_column} >= ago({hours}h)
| where isnotnull({response_time_column})
| summarize
    RequestCount = count(),
    AvgResponseTime = avg({response_time_column}),
    MedianResponseTime = percentile({response_time_column}, 50),
    P95ResponseTime = percentile({response_time_column}, 95),
    P99ResponseTime = percentile({response_time_column}, 99),
    MaxResponseTime = max({response_time_column}),
    SlowRequests = countif({response_time_column} > 5000),  // > 5 seconds
    RequestsPerMinute = count() / ({hours} * 60)
    by {endpoint_column}
| extend
    SlowRequestPercent = (SlowRequests * 100.0) / RequestCount,
    PerformanceRating = case(
        AvgResponseTime <= 100, "Excellent",
        AvgResponseTime <= 500, "Good",
        AvgResponseTime <= 2000, "Fair",
        "Poor"
    )
| project
    Endpoint = {endpoint_column},
    RequestCount,
    RequestsPerMinute,
    AvgResponseTime,
    MedianResponseTime,
    P95ResponseTime,
    P99ResponseTime,
    MaxResponseTime,
    SlowRequests,
    SlowRequestPercent,
    PerformanceRating
| order by AvgResponseTime desc
"""

    def get_security_summary_query(
        self,
        table_name: str,
        user_column: str,
        ip_column: str,
        action_column: str,
        timestamp_column: str,
        hours: int,
    ) -> str:
        """
        Generate KQL query for security summary report.

        Args:
            table_name: Name of the log table
            user_column: Column containing usernames
            ip_column: Column containing IP addresses
            action_column: Column containing actions/activities
            timestamp_column: Column containing timestamps
            hours: Number of hours to analyze

        Returns:
            str: KQL query for security summary
        """
        return f"""
let timeRange = {hours}h;
let suspiciousActions = dynamic(["login_failed", "access_denied", "permission_error", "brute_force"]);
let summary = {table_name}
| where {timestamp_column} >= ago(timeRange)
| extend IsSuspicious = {action_column} has_any (suspiciousActions)
| summarize
    TotalEvents = count(),
    SuspiciousEvents = countif(IsSuspicious),
    UniqueUsers = dcount({user_column}),
    UniqueIPs = dcount({ip_column}),
    UniqueActions = dcount({action_column})
| extend SuspiciousPercentage = (SuspiciousEvents * 100.0) / TotalEvents;
let topSuspiciousIPs = {table_name}
| where {timestamp_column} >= ago(timeRange)
| extend IsSuspicious = {action_column} has_any (suspiciousActions)
| where IsSuspicious
| summarize SuspiciousCount = count() by {ip_column}
| top 5 by SuspiciousCount desc;
let topActiveUsers = {table_name}
| where {timestamp_column} >= ago(timeRange)
| summarize ActivityCount = count() by {user_column}
| top 5 by ActivityCount desc;
let actionDistribution = {table_name}
| where {timestamp_column} >= ago(timeRange)
| summarize ActionCount = count() by {action_column}
| order by ActionCount desc;
summary
| extend ReportType = "SecuritySummary"
| project ReportType, TotalEvents, SuspiciousEvents, SuspiciousPercentage, UniqueUsers, UniqueIPs, UniqueActions
| union (
    topSuspiciousIPs | extend ReportType = "TopSuspiciousIPs" | project ReportType, IP = {ip_column}, SuspiciousCount
)
| union (
    topActiveUsers | extend ReportType = "TopActiveUsers" | project ReportType, User = {user_column}, ActivityCount
)
| union (
    actionDistribution | extend ReportType = "ActionDistribution"
    | project ReportType, Action = {action_column}, ActionCount
)
"""
