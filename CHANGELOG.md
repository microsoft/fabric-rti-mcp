# Release History

## 0.0.10 (Unreleased)
### Features
- **Kusto query statistics**: Add optional `show_stats` parameter to `kusto_query` and `kusto_graph_query`. When `True`, the response includes a top-level `statistics` key with execution time, CPU, memory, cache, network, extents/rows scanned, result size, and per-cluster cross-cluster breakdown — extracted from the `QueryCompletionInformation` tables returned by the SDK.

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

