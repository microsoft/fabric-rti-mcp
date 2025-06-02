---
applyTo: "**"
---
# Project Coding Guidelines

This document outlines the coding standards, architectural patterns, and best practices for this Project's codebase. 
It's designed to help new engineers quickly understand our approach and contribute effectively to the project.

## Project Overview

Fabric RTI MCP is an MCP server that exposes Fabric RTI functionality as tools that can be used by agents.


## Code Style and Formatting

### Python Version

- Python 3.10 is required for this project

### Formatting

- We use [Black](https://black.readthedocs.io/) for code formatting with a line length of 120 characters
- Run `black .` before committing to ensure consistent formatting

### Imports

- Group imports in the following order:
  1. Standard library imports
  2. Third-party library imports
  3. Project imports
- Within each group, use alphabetical ordering
- Use absolute imports for project modules

Example:
```python
import abc
from dataclasses import dataclass
from typing import List, Optional, Dict

import numpy as np
from termcolor import colored

from fabric_rti_mcp.kusto import KustoService
```

### Type Annotations

- Use type hints for all function parameters and return values
- Use generics (TypeVar) when appropriate
- Prefer composition of simple types over complex nested types

Example:
```python
from typing import Dict, List, Optional, TypeVar

T = TypeVar("T")

def get_tasks_with_status(status_type: str, project_id: Optional[str] = None) -> List[int]:
    """Get tasks with a specific status type."""
    # Implementation
```

### Naming Conventions

- **Classes**: `PascalCase`
- **Functions/Methods**: `snake_case`
- **Variables**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private members**: Prefix with underscore (`_private_method`)
- **Type variables**: Single uppercase letter or `PascalCase` with descriptive name

### Comments and TODOs

- Use TODOs to mark areas that need improvement, but include specific details about what needs to be done
- For complex algorithms or non-obvious code, include explanatory comments
- Avoid commented-out code in the main branch


## Architecture

### Tool Development Guidelines
- At the moment, there is no service discovery mechanism for Fabric workspaces. As such, when creating a service, use the service's globally unique name such as FQN or URI.
- Make sure to properly document each tool's function, its arguments, and expected output. If the output is complex, show an example of the output format.
- Avoid using @tool decorator, prefer a bootstrapping function (`service_module.register_service(mcp_instance)`). This allow for better flexibility and decoupling.
- Minimize the number of tools. Too many tools confuse agents. Make sure each tool has a clear purpose and is not redundant with others.
- 

### Complex Design decisions
- When faced with a complex design decision, document the reasoning behind the chosen approach
- Be clear about the trade-offs and alternatives considered
- Make sure to review common practices in similar projects, and patterns that can be adopted from other languages (like Rust) that can be applied to Python
- If the decision isn't clear-cut, make sure to consult with the owner, present the options and pros/cons, and suggest at least 3 options to choose from

## Testing Guidelines

### Test Structure
- Use pytest for all tests
- Group tests by module/functionality in the `tests/` directory
- Follow the Arrange-Act-Assert pattern for test structure
- Focus on testing specific service code (e.g. kusto). No need to test common code.
- Use `MagicMock` for mocking external dependencies. Mock all IO calls in unit tests.
