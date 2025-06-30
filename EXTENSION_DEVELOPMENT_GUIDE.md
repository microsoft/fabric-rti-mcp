# Extension Development Guide

This guide shows how to create domain-specific extensions for the Fabric RTI MCP Server.

## Quick Start

### Extension Structure

```text
fabric_rti_mcp/extensions/your_extension/
├── __init__.py              # Package exports
├── extension.py             # Main extension class (required)
├── services.py              # Business logic
├── templates.py             # KQL query templates
└── test_your_extension.py   # Unit tests (required)
```

### Prerequisites

- Python 3.8+, pytest, azure-kusto-data
- Basic KQL knowledge

## Implementation Guide

### Step 1: Create Extension Class

```python
# fabric_rti_mcp/extensions/your_extension/extension.py
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from fabric_rti_mcp.extensions.base import ExtensionBase
from fabric_rti_mcp.kusto import kusto_service

class YourExtension(ExtensionBase):
    @property
    def name(self) -> str:
        return "your-extension"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Your extension description"
    
    def register_tools(self, mcp: FastMCP) -> None:
        @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False))
        def your_tool(
            table_name: str,
            cluster_uri: str,
            database: Optional[str] = None
        ) -> List[Dict[str, Any]]:
            """Your tool description."""
            query = f"{table_name} | take 10"
            return kusto_service._execute(query, cluster_uri, database=database)
```

### Step 2: Create Supporting Files

```python
# fabric_rti_mcp/extensions/your_extension/services.py
class YourExtensionService:
    def validate_inputs(self, table_name: str) -> bool:
        return bool(table_name and table_name.isalnum())

# fabric_rti_mcp/extensions/your_extension/templates.py
class YourExtensionKQLTemplates:
    def get_basic_query(self, table_name: str) -> str:
        return f"{table_name} | summarize count() by bin(timestamp, 1h)"

# fabric_rti_mcp/extensions/your_extension/__init__.py
from .extension import YourExtension
__all__ = ["YourExtension"]
```

### Step 3: Create Tests

```python
# fabric_rti_mcp/extensions/your_extension/test_your_extension.py
import pytest
from unittest.mock import Mock, patch
from .extension import YourExtension

class TestYourExtension:
    def test_extension_properties(self):
        extension = YourExtension()
        assert extension.name == "your-extension"
        assert extension.version == "1.0.0"
    
    @patch('fabric_rti_mcp.kusto.kusto_service._execute')
    def test_register_tools(self, mock_execute):
        extension = YourExtension()
        mock_mcp = Mock()
        mock_execute.return_value = [{"result": "success"}]
        
        extension.register_tools(mock_mcp)
        assert mock_mcp.tool.called
```

## Testing & CLI Commands

### Essential Commands

```bash
# List all discovered extensions
python test_extensions.py list

# Discover extension tests
python test_extensions.py discover-tests

# Run tests for specific extension
python test_extensions.py run-tests your-extension

# Run all extension tests
python test_extensions.py run-tests

# Validate test coverage
python test_extensions.py validate-coverage

# Test extension loading
python test_extensions.py test

# Display extension configuration
python test_extensions.py config your-extension
```

### Development Workflow

```bash
# 1. Create your extension files
# 2. Verify discovery
python test_extensions.py list

# 3. Test your extension
python test_extensions.py run-tests your-extension

# 4. Run all tests
python test_extensions.py run-tests

# 5. Validate coverage
python test_extensions.py validate-coverage
```

## Configuration (Optional)

Create `extension_configs/your-extension.json`:

```json
{
  "setting1": "value1",
  "setting2": 42,
  "nested_settings": {
    "enabled": true,
    "threshold": 0.5
  }
}
```

## Best Practices

### Tool Design

- **Single Responsibility**: Each tool does one thing well
- **Clear Documentation**: Comprehensive docstrings
- **Parameter Validation**: Validate inputs in service layer
- **Error Handling**: Use try-catch blocks

### KQL Templates

- **Parameterized Queries**: Avoid string concatenation
- **Performance**: Consider query performance
- **Security**: Avoid SQL injection

### Testing

- **Unit Tests**: Test each component independently
- **Mock Dependencies**: Use mocks for external services
- **Integration Tests**: Test complete workflows

## Deployment

### Development Setup

```bash
# Install in development mode
pip install -e ".[dev]"

# Verify extension discovery
python test_extensions.py list

# Run comprehensive tests
python test_extensions.py run-tests
python test_extensions.py validate-coverage
```

### Production Checklist

1. ✅ All unit tests pass
2. ✅ Test coverage adequate  
3. ✅ Extension loads correctly
4. ✅ Configuration valid
5. ✅ Documentation complete

## Examples

Check existing extensions for reference:

- `financial` - Financial analytics tools
- `loganalytics` - Log analysis tools

## Getting Help

- Review base classes in `fabric_rti_mcp/extensions/base.py`
- Run `python test_extensions.py` for debugging
- Ensure all tests pass before deployment

Your extension will be automatically discovered and loaded when the MCP server starts!
