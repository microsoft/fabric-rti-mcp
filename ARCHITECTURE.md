# 🏗️ Architecture Guide - Fabric RTI MCP Server

## Overview
The Fabric RTI MCP Server provides a unified interface for Microsoft Fabric Real-Time Intelligence services through the Model Context Protocol (MCP). This document outlines the architecture, design patterns, and integration approach.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Client (VS Code)                     │
│                   GitHub Copilot Chat                       │
└─────────────────┬───────────────────────────────────────────┘
                  │ MCP Protocol (JSON-RPC)
                  │
┌─────────────────▼───────────────────────────────────────────┐
│                 Fabric RTI MCP Server                       │
│                    (server.py)                              │
├─────────────────┬───────────────────────────────────────────┤
│                 │                                           │
│  ┌──────────────▼────────────┐    ┌─────────────────────────▼┐ │
│  │     Kusto Service         │    │   Eventstream Service   │ │
│  │   (kusto_service.py)      │    │ (eventstream_service.py) │ │
│  │                           │    │                         │ │
│  │ • Database queries        │    │ • Stream management     │ │
│  │ • KQL execution           │    │ • CRUD operations       │ │
│  │ • Schema introspection    │    │ • Workspace integration │ │
│  │ • Data ingestion          │    │ • Configuration mgmt    │ │
│  └───────────┬───────────────┘    └─────────────────────────┬┘ │
│              │                                              │   │
│  ┌───────────▼───────────────┐    ┌─────────────────────────▼┐ │
│  │     Kusto Tools           │    │   Eventstream Tools     │ │
│  │   (kusto_tools.py)        │    │ (eventstream_tools.py)  │ │
│  │                           │    │                         │ │
│  │ • list_databases          │    │ • list_eventstreams     │ │
│  │ • list_tables             │    │ • get_eventstream       │ │
│  │ • get_schema              │    │ • create_eventstream    │ │
│  │ • sample_data             │    │ • update_eventstream    │ │
│  │ • execute_kql             │    │ • delete_eventstream    │ │
│  │ • ingest_csv              │    │ • get_definition        │ │
│  └───────────────────────────┘    └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│              Azure Services                                  │
│                                                             │
│  ┌─────────────────────────┐    ┌─────────────────────────┐ │
│  │    Fabric Eventhouse    │    │   Fabric Eventstreams   │ │
│  │   (Kusto/Azure Data     │    │  (Real-time Streaming)  │ │
│  │     Explorer)           │    │                         │ │
│  └─────────────────────────┘    └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Module Structure

### Core MCP Server (`fabric_rti_mcp/`)

#### `server.py` - Main Entry Point
- Initializes MCP server with FastMCP
- Registers tools from both Kusto and Eventstream modules
- Handles authentication via Azure Identity
- Manages server lifecycle and error handling

#### `common.py` - Shared Utilities
- Async/sync bridging patterns
- Common error handling
- Shared type definitions
- Utility functions used across modules

### Kusto Module (`fabric_rti_mcp/kusto/`)

#### `kusto_service.py`
- **Purpose**: Core business logic for Kusto operations
- **Key Functions**:
  - Database and table enumeration
  - KQL query execution
  - Schema introspection
  - Data ingestion capabilities
- **Integration**: Uses Azure Kusto SDK for all operations

#### `kusto_tools.py`
- **Purpose**: MCP tool definitions for Kusto functionality
- **Pattern**: Each tool wraps a service function with MCP-compatible interface
- **Tools Provided**:
  - `list_databases` - Enumerate available databases
  - `list_tables` - List tables in a database
  - `get_schema` - Get table schema information
  - `sample_data` - Sample rows from tables
  - `execute_kql` - Execute arbitrary KQL queries
  - `ingest_csv` - Ingest CSV data into tables

#### `kusto_connection.py`
- **Purpose**: Connection management and authentication
- **Features**: Connection pooling, credential handling, retry logic

#### `kusto_response_formatter.py`
- **Purpose**: Format Kusto responses for MCP consumption
- **Functionality**: Converts Kusto data types to JSON-compatible formats

### Eventstream Module (`fabric_rti_mcp/eventstream/`)

#### `eventstream_service.py`
- **Purpose**: Core business logic for Eventstream operations
- **Key Functions**:
  - Eventstream CRUD operations (Create, Read, Update, Delete)
  - Workspace integration
  - Configuration management
  - Definition retrieval and parsing
- **Integration**: Uses Microsoft Fabric REST APIs via HTTPX

#### `eventstream_tools.py`
- **Purpose**: MCP tool definitions for Eventstream functionality
- **Pattern**: Each tool wraps a service function with MCP-compatible interface
- **Tools Provided**:
  - `list_eventstreams` - List all Eventstreams in workspace
  - `get_eventstream` - Get specific Eventstream details
  - `create_eventstream` - Create new Eventstreams
  - `update_eventstream` - Update existing Eventstreams
  - `delete_eventstream` - Delete Eventstreams
  - `get_eventstream_definition` - Get detailed configuration

## Standalone Tools (`tools/eventstream_client/`)

### Purpose
Non-MCP tools and utilities that can be used independently of the MCP server for direct Eventstream management and automation.

### Key Components

#### `ai_agent_openai.py`
- **Purpose**: AI-powered Eventstream management agent
- **Features**: Natural language interface for Eventstream operations
- **Integration**: Uses OpenAI API for natural language processing

#### `config.py` & `setup_config.py`
- **Purpose**: Configuration management for standalone tools
- **Features**: Environment-based configuration, credential management

#### `demo_agent.py` & `run_agent.py`
- **Purpose**: Example implementations and agent runners
- **Use Cases**: Demonstrations, testing, automation scripts

#### `eventstream_server.py`
- **Purpose**: FastAPI server for HTTP-based Eventstream operations
- **Features**: REST API endpoints, web interface for Eventstream management

## Design Patterns

### 1. Async/Sync Bridge Pattern

```python
def _run_async_operation(coro: Coroutine[Any, Any, Any]) -> Any:
    """
    Centralized async/sync bridge handling event loop management.
    """
    try:
        loop = asyncio.get_running_loop()
        # Run in thread if event loop exists
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(lambda: asyncio.run(coro))
            return future.result()
    except RuntimeError:
        # No event loop, use asyncio.run
        return asyncio.run(coro)
```

**Benefits**:
- Eliminates event loop conflicts
- Consistent error handling
- Single point of async/sync translation

### 2. Service-Tool Separation Pattern

```python
# Service Layer (Business Logic)
class EventstreamService:
    async def create_eventstream(self, name: str, config: dict) -> dict:
        # Core implementation
        pass

# Tool Layer (MCP Interface)
def create_eventstream_tool(name: str, config: str) -> List[TextContent]:
    service = EventstreamService()
    result = _run_async_operation(
        service.create_eventstream(name, json.loads(config))
    )
    return [TextContent(type="text", text=json.dumps(result))]
```

**Benefits**:
- Clear separation of concerns
- Service layer reusable outside MCP
- Easy testing and maintenance

### 3. Modular Registration Pattern

```python
# In server.py
def register_tools(server: Server):
    """Register all tools from different modules."""
    from .kusto.kusto_tools import register_kusto_tools
    from .eventstream.eventstream_tools import register_eventstream_tools
    
    register_kusto_tools(server)
    register_eventstream_tools(server)
```

**Benefits**:
- Loose coupling between modules
- Easy to add/remove functionality
- Clear tool organization

## Authentication & Security

### Azure Identity Integration
- Uses `DefaultAzureCredential` for seamless authentication
- Supports multiple credential types (CLI, PowerShell, VS Code, etc.)
- No token storage - relies on Azure Identity SDK

### Security Best Practices
- All HTTP clients use proper TLS/SSL
- Credentials never logged or stored in plain text
- Proper error handling prevents credential leakage
- Type safety throughout to prevent injection attacks

## Configuration

### Environment Variables

#### Kusto Configuration
```env
KUSTO_SERVICE_URI=https://cluster.region.kusto.windows.net/
KUSTO_DATABASE=DatabaseName
```

#### Eventstream Configuration
```env
FABRIC_WORKSPACE_ID=12345678-1234-1234-1234-123456789012
```

### MCP Settings
```json
{
    "mcp": {
        "servers": {
            "fabric-rti-mcp": {
                "command": "uvx",
                "args": ["microsoft-fabric-rti-mcp"],
                "env": {
                    "KUSTO_SERVICE_URI": "https://cluster.westus.kusto.windows.net/",
                    "KUSTO_DATABASE": "Datasets",
                    "FABRIC_WORKSPACE_ID": "your-workspace-id"
                }
            }
        }
    }
}
```

## Error Handling

### Consistent Error Pattern
```python
try:
    result = await service_operation()
    return success_response(result)
except SpecificException as e:
    logger.error(f"Specific error: {e}")
    return error_response(f"Operation failed: {e}")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    return error_response("Unexpected error occurred")
```

### Error Categories
- **Authentication Errors**: Credential-related issues
- **Network Errors**: Connectivity and timeout issues
- **API Errors**: Microsoft Fabric API-specific errors
- **Validation Errors**: Input validation failures
- **Runtime Errors**: Unexpected runtime conditions

## Performance Considerations

### Connection Management
- HTTP connection pooling for Eventstream operations
- Kusto connection caching via Azure SDK
- Proper connection cleanup and resource management

### Async Optimization
- All I/O operations are async-first
- Centralized async/sync bridge minimizes overhead
- Efficient thread management for sync contexts

### Memory Management
- Streaming responses for large datasets
- Proper resource cleanup in error conditions
- Minimal memory footprint for service operations

## Testing Strategy

### Unit Testing
- Service layer functions tested independently
- Mock external dependencies (Azure APIs)
- Test both success and error conditions

### Integration Testing
- End-to-end MCP tool execution
- Real Azure service integration (when possible)
- Authentication flow validation

### Type Safety
- Comprehensive type annotations
- MyPy strict mode enabled
- Runtime type validation where critical

## Extending the Architecture

### Adding New Services
1. Create new module under `fabric_rti_mcp/`
2. Implement service class with async methods
3. Create tools module with MCP tool definitions
4. Register tools in `server.py`
5. Update documentation and tests

### Adding New Tools
1. Add method to appropriate service class
2. Create corresponding tool function in tools module
3. Update tool registration
4. Add documentation and examples

This architecture provides a robust, scalable foundation for expanding Microsoft Fabric RTI integration while maintaining clean separation of concerns and high maintainability.
