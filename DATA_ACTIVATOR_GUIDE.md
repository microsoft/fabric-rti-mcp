# Data Activator MCP Tools Guide

This guide explains how to use the Data Activator tools in the Microsoft Fabric RTI MCP Server.

## Overview

The Data Activator tools allow you to create alerts from KQL queries that monitor data and automatically send notifications via Teams messages and email when conditions are met.

## Available Tools

### 1. `create_data_activator_alert`

Creates a Data Activator alert that monitors a KQL query and sends notifications.

**Parameters:**
- `kql_query` (required): The KQL query to monitor for anomalies or conditions
- `cluster_uri` (required): The URI of the Kusto cluster (e.g., https://mycluster.westus.kusto.windows.net)
- `workspace_id` (required): The Fabric workspace ID where the alert should be created
- `alert_name` (required): A descriptive name for the alert
- `notification_recipients` (required): List of email addresses or Teams usernames to notify
- `frequency_minutes` (optional): How often to run the query in minutes (default: 60)
- `database` (optional): Database name. If not provided, uses the default database
- `activator_name` (optional): Name for the activator item. If not provided, generates one
- `description` (optional): Description for the alert

**Example Usage:**
```
Create an alert for anomaly detection on login failures that runs every hour and notifies the security team via email and Teams when the query returns results.

Parameters:
- KQL Query: "SecurityLogs | where EventID == 4625 | where TimeGenerated > ago(1h) | summarize FailedLogins = count() by Account | where FailedLogins > 10"
- Cluster URI: "https://mycompany.westus.kusto.windows.net"
- Workspace ID: "12345678-1234-1234-1234-123456789012"
- Alert Name: "High Failed Login Alert"
- Recipients: ["security@company.com", "teams_security_team"]
```

### 2. `list_fabric_workspaces`

Lists all accessible Microsoft Fabric workspaces.

**Parameters:** None

**Returns:** List of workspace information including IDs, names, and descriptions

**Example Usage:**
```
List all workspaces I have access to so I can find the correct workspace ID for creating alerts.
```

### 3. `list_workspace_activators`

Lists all Data Activator items in a specific workspace.

**Parameters:**
- `workspace_id` (required): The Fabric workspace ID to list activators from

**Returns:** List of activator items in the workspace

**Example Usage:**
```
Show me all existing Data Activator items in workspace "12345678-1234-1234-1234-123456789012".
```

## Common Use Cases

### 1. Security Monitoring
Create alerts for security events like failed logins, unauthorized access attempts, or suspicious activities.

```kql
SecurityLogs 
| where TimeGenerated > ago(5m)
| where EventID in (4625, 4648, 4771) // Failed logins
| summarize Count = count() by Account
| where Count > 5
```

### 2. Performance Monitoring
Monitor system performance metrics like CPU usage, memory consumption, or response times.

```kql
PerformanceCounters
| where TimeGenerated > ago(10m)
| where CounterName == "% Processor Time"
| where CounterValue > 80
| summarize AvgCPU = avg(CounterValue) by Computer
| where AvgCPU > 85
```

### 3. Application Error Monitoring
Track application errors and exceptions that require immediate attention.

```kql
AppLogs
| where TimeGenerated > ago(15m)
| where Level == "Error"
| where Message contains "OutOfMemoryException"
| count
| where Count > 0
```

### 4. Business Metrics Monitoring
Monitor business KPIs like transaction volumes, revenue, or customer activity.

```kql
TransactionLogs
| where TimeGenerated > ago(1h)
| summarize Revenue = sum(Amount)
| where Revenue < 1000 // Alert if hourly revenue drops below threshold
```

## Notification Types

### Email Notifications
- Specify email addresses in the `notification_recipients` list
- Format: `["user@company.com", "team@company.com"]`
- Recipients will receive email alerts with query details

### Teams Notifications  
- Specify Teams usernames (without @) in the `notification_recipients` list
- Format: `["teams_username", "security_team"]`
- Recipients will receive Teams messages with alert details

### Mixed Notifications
- You can combine both email and Teams notifications
- Format: `["user@company.com", "teams_username", "admin@company.com"]`

## Best Practices

1. **Query Optimization**: Write efficient KQL queries that return results only when action is needed
2. **Frequency Setting**: Choose appropriate frequencies (15-60 minutes) to balance responsiveness with resource usage
3. **Alert Naming**: Use descriptive names that clearly indicate what the alert monitors
4. **Recipient Management**: Include relevant team members and distribution lists
5. **Testing**: Test queries manually before creating alerts to ensure they work as expected

## Troubleshooting

### Common Issues

1. **Authentication Errors**: Ensure you have proper Azure credentials configured
2. **Workspace Access**: Verify you have contributor access to the target workspace
3. **Cluster URI**: Ensure the Kusto cluster URI is correct and accessible
4. **KQL Syntax**: Validate your KQL query syntax before creating the alert

### Error Messages

- `"Workspace ID cannot be empty"`: Provide a valid workspace ID
- `"KQL query cannot be empty"`: Ensure your query is not blank
- `"At least one notification recipient must be specified"`: Add email or Teams recipients
- `"KQL query contains potentially dangerous keyword"`: Avoid management commands in monitoring queries

## Next Steps

After creating an alert:
1. The Reflex (Data Activator) item will appear in your Fabric workspace
2. Navigate to the Fabric portal to view and modify the alert
3. The alert will start monitoring automatically once activated
4. View alert history and rule activations in the Activator interface

For more information, see the [Microsoft Fabric Data Activator documentation](https://learn.microsoft.com/en-us/fabric/real-time-intelligence/data-activator/activator-introduction).
