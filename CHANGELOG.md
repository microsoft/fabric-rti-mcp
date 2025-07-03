# Release History

## 0.1.0 (Ready for Release)
### Features Added
- **Eventstream Support**: Added comprehensive Microsoft Fabric Eventstream integration
  - List Eventstreams in workspaces
  - Get Eventstream details and definitions
  - Create, update, and delete Eventstreams
  - Full MCP tool integration alongside existing Kusto functionality

### Other Changes
- **Architecture Overhaul**: Clean separation between MCP server and standalone tools
  - Moved AI agents and demo tools to `tools/eventstream_client/` directory
  - Improved modular design with clear boundaries
- **Async Pattern Standardization**: Implemented centralized async/sync bridge pattern
  - Resolves event loop conflicts
  - Consistent error handling across all async operations
  - Better resource management and performance
- **Configuration Cleanup**: Enhanced configuration management
  - Proper type annotations throughout
  - Improved error handling for missing config files
  - Support for both Kusto and Eventstream configuration
- **Type Safety Improvements**: Comprehensive type checking support
- **Documentation Updates**: Updated README to reflect dual Kusto + Eventstream functionality
- **Dead Code Removal**: Cleaned up empty and unused files

### Breaking Changes
- Server name changed from "kusto-mcp-server" to "fabric-rti-mcp-server" to reflect expanded functionality
- Non-MCP tools moved from `fabric_rti_mcp/eventstream/` to `tools/eventstream_client/`

## 0.0.10 (Previous)
### Other Changes
- Use docstring as tool description
- Add annotations (readonly, destructive)
- Add Attach to proc id + tracing pid on start so we can debug locally

## 0.0.9
### Other Changes
- Removed bloat around deployment. Publishing regular package to PyPI
- Fixed PyPI pipeline

## 0.0.8 
### Other Changes
- Cleanup pyproject.toml
- Add logger that uses the stderr so that it could be seen in the MCP server logs
- Strip whitespaces from agent parameters 

## 0.0.7
### Features
- Executable installed via pip
- Main functionality of the Kusto MCP server is implemented.
- Readme includes instructions for manual installation of the server (and PyPI depending on python environment correctly set up)


## template (not yet released / release date)
### Breaking Changes
- ...
### Features
- ...
### Bugs Fixed
- ...
### Other Changes
- ...

