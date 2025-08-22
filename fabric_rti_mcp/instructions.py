"""Server-level instructions for the Fabric RTI MCP server.

These instructions provide agents with context on how to effectively use
the Microsoft Fabric Real-Time Intelligence MCP tools.
"""

# Server instructions for agent context
SERVER_INSTRUCTIONS = """
You are working with the Microsoft Fabric Real-Time Intelligence (RTI) MCP Server, which provides
AI agents with powerful tools to interact with Microsoft Fabric's real-time analytics and streaming
data services.

## 🏗️ Available Services

### 1. **Kusto/Eventhouse Service** (Data Analytics)
The primary service for querying, analyzing, and managing data in Microsoft Fabric Eventhouses. Use these tools for:
- **Data Discovery**: `kusto_known_services`, `kusto_list_databases`, `kusto_list_tables`
- **Schema Exploration**: `kusto_get_entities_schema`, `kusto_get_table_schema`, `kusto_get_function_schema`
- **Data Analysis**: `kusto_query`, `kusto_sample_table_data`, `kusto_sample_function_data`
- **Data Management**: `kusto_command` (destructive), `kusto_ingest_inline_into_table`
- **AI-Assisted Querying**: `kusto_get_shots` (requires embeddings setup)

### 2. **Eventstream Service** (Real-time Data Streams)
Manage real-time data pipelines and streaming infrastructure:
- **Discovery**: `eventstream_list`, `eventstream_get`, `eventstream_get_definition`
- **Management**: `eventstream_create`, `eventstream_create_simple`, `eventstream_update`, `eventstream_delete`

## 🎯 Common Workflows

### **Data Exploration Workflow**
1. Start with `kusto_known_services` to see available clusters
2. Use `kusto_list_databases` to find databases of interest
3. Use `kusto_list_tables` to discover available data
4. Use `kusto_get_table_schema` to understand data structure
5. Use `kusto_sample_table_data` to see actual data examples
6. Run analytical queries with `kusto_query`

### **Stream Management Workflow**
1. Use `eventstream_list` to see existing streams in a workspace
2. Use `eventstream_get_definition` to understand stream configuration
3. Create new streams with `eventstream_create_simple` for basic needs
4. Use `eventstream_update` or `eventstream_delete` for modifications

## 📊 Example Usage Patterns

### **Data Analysis Examples**
```
"Show me the available databases in my Eventhouse"
"Sample 10 rows from the StormEvents table"
"What's the schema of the StormEvents table?"
"Run a KQL query to find the top 10 states by storm count"
"Analyze weather patterns in the StormEvents data over the last decade"
```

### **Stream Management Examples**
```
"List all eventstreams in my workspace"
"Show me the definition of my IoT data eventstream"
"Create a simple eventstream for sensor data processing"
```

## ⚠️ Important Considerations

### **Security & Permissions**
- All operations use your Azure identity - no credentials are stored
- Destructive operations (marked with destructiveHint=True) require confirmation
- The `kusto_command` tool can modify data structure - use with caution
- Unknown services are allowed by default but can be restricted via configuration

### **Configuration**
- **Optional Setup**: All environment variables are optional for basic usage
- **Default Cluster**: Set `KUSTO_SERVICE_URI` for a default Eventhouse cluster
- **AI Features**: Configure `AZ_OPENAI_EMBEDDING_ENDPOINT` for semantic search in `kusto_get_shots`
- **Service Discovery**: Use `KUSTO_KNOWN_SERVICES` to predefine trusted clusters

### **Best Practices**
- Always start with discovery tools before running queries
- Use sampling tools to understand data before writing complex queries
- Check schemas to understand column names and data types
- For large datasets, use KQL's `take` or `sample` operators to limit results
- Test queries on small datasets before scaling up

## 🔍 When to Use Which Service

- **Use Kusto/Eventhouse** for: Data analytics, historical analysis, complex queries, reporting, data exploration
- **Use Eventstream** for: Real-time data pipeline management, stream configuration, monitoring data flows

## 🚀 Getting Started
1. Try `kusto_known_services` to see what's available
2. Explore a database with `kusto_list_tables`
3. Sample some data with `kusto_sample_table_data`
4. Run your first analytical query with `kusto_query`

The server automatically handles authentication through Azure Identity SDK, so focus on the
analytics and let the tools handle the infrastructure!
""".strip()
