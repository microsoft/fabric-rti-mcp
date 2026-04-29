# Release History

## Unreleased
### Features
- Added `kusto_deeplink_from_query` tool to generate deeplink URLs for opening KQL queries in the appropriate web explorer UI (Azure Data Explorer Web Explorer or Microsoft Fabric query workbench). Auto-detects cluster type from URI with `.show version` fallback.

### Other Changes
- Use docstring as tool description
- Add annotations (readonly, destructive)
- Add Attach to proc id + tracing pid on start so we can debug locally
- Gate PyPI publishing on required read-only Kusto query checks
- Rename and test schema simplification for broader MCP client compatibility
- Add underscore variant of console script entry point for uvx compatibility
- Add external table support for OneLake Shortcuts
- Add GitHub Copilot CLI installation instructions
- Dependency updates (fastmcp, starlette, azure-core, urllib3, cryptography, python-multipart, requests, pyjwt, authlib)

## 0.4.0
### Features
- Add Map service and tools
- AI Foundry compatibility schema (behind toggle)

### Other Changes
- Add usage header to Activator API requests
- Update Activator tool descriptions
- Switch to ruff for formatting and linting
- Fix PyPI publishing

## 0.3.0
### Features
- Add Eventstream builder tools
- Add initial support for Activator service and tools
- Add server.json metadata for MCP registry

### Bugs Fixed
- Fix hostname parsing when pasting from Fabric portal with https:// prefix

### Other Changes
- Refactor EventStreamConnection to FabricApiHttpClient
- Add Private Shots notebook
- Updated instructions for HTTP mode and remote deployment

## 0.2.0
### Features
- Generalized kusto tools with graph_query support
- Compact kusto response format
- HTTP transport support
- OBO flow with user managed identity credentials
- Kusto-specific timeout configuration
- Client request properties support
- Correlation ID tracing for Kusto error handling

### Other Changes
- Add live tests
- Fix auto-versioning package name lookup

## 0.1.0
### Features
- Add core Eventstream service and MCP tools
- Add kusto_get_shots tool for semantic search
- Explicit kusto cluster management

### Bugs Fixed
- Fix shots table column names (EmbeddingText, AugmentedText, EmbeddingVector)

### Other Changes
- Refactor kusto connection cache and known service URIs
- Add authority ID support for Kusto

