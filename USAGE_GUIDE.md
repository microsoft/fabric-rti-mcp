# 📖 Usage Guide - Fabric RTI MCP Server

## Quick Start

### 1. Installation
```bash
# Via pip (recommended)
pip install microsoft-fabric-rti-mcp

# Or via uvx
uvx microsoft-fabric-rti-mcp
```

### 2. VS Code Configuration
Add to your VS Code `settings.json`:
```json
{
    "mcp": {
        "servers": {
            "fabric-rti-mcp": {
                "command": "uvx",
                "args": ["microsoft-fabric-rti-mcp"],
                "env": {
                    "KUSTO_SERVICE_URI": "https://your-cluster.region.kusto.windows.net/",
                    "KUSTO_DATABASE": "YourDatabase",
                    "FABRIC_API_BASE_URL": "https://api.fabric.microsoft.com/v1"
                }
            }
        }
    }
}
```

### 3. Authentication
The server automatically uses your existing Azure credentials:
- Azure CLI: `az login`
- Azure PowerShell: `Connect-AzAccount`
- Visual Studio: Sign in to Azure
- Interactive browser: Fallback option

## Available Services

## 🏢 Eventhouse (Kusto) Operations

### List Databases
```
@copilot /agent mode

List all databases in my Eventhouse cluster
```

**What it does**: Enumerates all databases you have access to in the configured Kusto cluster.

### List Tables
```
Show me all tables in the 'SampleData' database
```

**What it does**: Lists all tables within a specific database, including table names and basic metadata.

### Get Table Schema
```
What's the schema of the 'StormEvents' table?
```

**What it does**: Returns detailed schema information including column names, data types, and descriptions.

### Sample Data
```
Show me 10 sample rows from the 'StormEvents' table
```

**What it does**: Retrieves sample data from any table to help understand the data structure and content.

### Execute KQL Queries
```
Run this KQL query: StormEvents | where State == "TEXAS" | summarize count() by EventType
```

**What it does**: Executes any KQL (Kusto Query Language) query against your databases.

**Advanced Examples**:
```kql
// Time series analysis
StormEvents 
| where StartTime > ago(365d)
| summarize Events = count() by bin(StartTime, 1d), State
| render timechart

// Top 10 analysis
StormEvents 
| summarize TotalDamage = sum(DamageProperty) by State
| top 10 by TotalDamage
```

### Ingest CSV Data
```
Ingest this CSV data into the 'MyTable' table:
Name,Age,City
John,25,Seattle
Jane,30,Portland
```

**What it does**: Uploads CSV data directly into Kusto tables for analysis.

## 🌊 Eventstream Operations

### List Eventstreams
```
Show me all Eventstreams in my workspace
```

**What it does**: Lists all Eventstreams in your configured Fabric workspace with basic information.

### Get Eventstream Details
```
Tell me about the 'IoT-Sensor-Stream' Eventstream
```

**What it does**: Provides detailed information about a specific Eventstream including configuration and status.

### Create Eventstream
```
Create a new Eventstream called 'Sales-Events' for processing e-commerce data
```

**What it does**: Creates a new Eventstream with basic configuration. You can specify:
- Name and description
- Initial configuration
- Workspace location

### Update Eventstream
```
Update my 'IoT-Sensor-Stream' to add a new destination for processed data
```

**What it does**: Modifies existing Eventstream configuration, destinations, or processing logic.

### Delete Eventstream
```
Delete the 'Test-Stream' Eventstream - it's no longer needed
```

**What it does**: Removes an Eventstream and all its associated resources.

### Get Eventstream Definition
```
Show me the complete definition of my 'Production-Stream' Eventstream
```

**What it does**: Returns the full JSON definition including all sources, destinations, and transformations.

## Real-World Usage Scenarios

### 📊 Data Analysis Workflows

#### Storm Data Analysis
```
1. "List all tables in the SampleData database"
2. "Show me the schema of the StormEvents table"
3. "What can you tell me about the StormEvents data?"
4. "Analyze storm patterns in Texas over the last 5 years"
```

#### Performance Monitoring
```
1. "Sample 100 rows from the PerformanceCounters table"
2. "Show me CPU usage trends over the last 24 hours"
3. "Find all servers with CPU usage above 80%"
```

### 🔄 Real-Time Data Processing

#### IoT Data Pipeline
```
1. "List all my Eventstreams"
2. "Create a new Eventstream for IoT sensor data processing"
3. "Show me details of my IoT-Processing-Stream"
4. "Update the stream to add a new analytics destination"
```

#### E-commerce Event Processing
```
1. "Create an Eventstream for tracking purchase events"
2. "Configure the stream to process payment data"
3. "Add a destination for real-time analytics"
```

## Advanced Tips

### 🧠 Working with AI Agent

#### Natural Language Queries
The AI agent understands natural language and can help with:
```
"Find all high-severity events in the last week"
"What are the top 5 states by storm damage?"
"Create a summary of web traffic patterns"
"Show me trends in user engagement"
```

#### Complex Analysis
```
"Analyze the StormEvents data and create a risk assessment by state"
"Compare performance metrics between different server groups"
"Create a report on seasonal patterns in the weather data"
```

### 🔧 Configuration Tips

#### Multiple Clusters
```json
{
    "mcp": {
        "servers": {
            "fabric-rti-prod": {
                "command": "uvx",
                "args": ["microsoft-fabric-rti-mcp"],
                "env": {
                    "KUSTO_SERVICE_URI": "https://prod-cluster.region.kusto.windows.net/",
                    "KUSTO_DATABASE": "Production",
                    "FABRIC_API_BASE_URL": "https://api.fabric.microsoft.com/v1"
                }
            },
            "fabric-rti-dev": {
                "command": "uvx", 
                "args": ["microsoft-fabric-rti-mcp"],
                "env": {
                    "KUSTO_SERVICE_URI": "https://dev-cluster.region.kusto.windows.net/",
                    "KUSTO_DATABASE": "Development",
                    "FABRIC_API_BASE_URL": "https://api.fabric.microsoft.com/v1"
                }
            }
        }
    }
}
```

#### Environment-Specific Settings
```bash
# Production
export KUSTO_SERVICE_URI="https://prod.westus.kusto.windows.net/"
export KUSTO_DATABASE="ProductionData"
export FABRIC_API_BASE_URL="https://api.fabric.microsoft.com/v1"

# Development  
export KUSTO_SERVICE_URI="https://dev.westus.kusto.windows.net/"
export KUSTO_DATABASE="TestData"
export FABRIC_API_BASE_URL="https://api.fabric.microsoft.com/v1"
```

## Troubleshooting

### Common Issues

#### Authentication Problems
```
❌ Error: "Authentication failed"
✅ Solution: Run `az login` or ensure you're signed into Azure in VS Code
```

#### Connection Issues
```
❌ Error: "Cannot connect to Kusto cluster"
✅ Solution: Verify KUSTO_SERVICE_URI is correct and accessible
```

#### Permission Issues
```
❌ Error: "Access denied to database"
✅ Solution: Ensure your account has appropriate permissions in Fabric
```

### Debug Mode
Enable debug logging by setting:
```json
{
    "mcp": {
        "servers": {
            "fabric-rti-mcp": {
                "command": "uvx",
                "args": ["microsoft-fabric-rti-mcp"],
                "env": {
                    "LOG_LEVEL": "DEBUG"
                }
            }
        }
    }
}
```

### Getting Help
1. Check the [GitHub Issues](https://github.com/microsoft/fabric-rti-mcp/issues)
2. Review the [Architecture Guide](./ARCHITECTURE.md)
3. Check VS Code MCP server logs:
   - Command Palette → "MCP: List Servers"
   - Select "fabric-rti-mcp" → "Show Output"

## Best Practices

### 🔐 Security
- Use environment variables for sensitive configuration
- Regularly rotate Azure credentials
- Follow principle of least privilege for database access

### 📈 Performance
- Use specific database names to avoid unnecessary enumeration
- Limit result sets with KQL `take` operator for large queries
- Cache frequently accessed schema information

### 🛠️ Development
- Test queries in Azure Data Explorer before using in agent
- Use descriptive names for Eventstreams and resources
- Document complex KQL queries for team reference

### 🔄 Monitoring
- Monitor MCP server logs for errors
- Set up alerts for failed authentication attempts
- Track query performance and optimize as needed

This guide should help you get the most out of the Fabric RTI MCP Server. The AI agent can assist with all these operations using natural language, making complex data operations accessible and intuitive!
