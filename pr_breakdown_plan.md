# PR Breakdown Execution Plan

## Current State
- Branch: `feature/eventstream-integration`
- Target: Multiple smaller PRs to main

## Step-by-Step Process

### Step 1: Create PR 1 - Core Eventstream Service
```bash
# Create new branch for core service
git checkout main
git pull
git checkout -b feature/eventstream-core-service

# Cherry-pick only the core service commits/files
git checkout feature/eventstream-integration -- fabric_rti_mcp/eventstream/__init__.py
git checkout feature/eventstream-integration -- fabric_rti_mcp/eventstream/eventstream_service.py  
git checkout feature/eventstream-integration -- fabric_rti_mcp/eventstream/eventstream_tools.py

# Manually edit fabric_rti_mcp/server.py to include only eventstream tool registration
# Manually edit pyproject.toml to include only essential eventstream dependencies

git add .
git commit -m "feat: Add core Eventstream service and tools

- Add basic Eventstream CRUD operations
- Add 6 core MCP tools for eventstream management
- Register eventstream tools in MCP server
- Add minimal dependencies for eventstream functionality"

git push fork feature/eventstream-core-service
```

### Step 2: Create PR 2 - Documentation
```bash
git checkout main
git checkout -b feature/eventstream-documentation

git checkout feature/eventstream-integration -- ARCHITECTURE.md
git checkout feature/eventstream-integration -- ASYNC_PATTERN_EXPLANATION.md
git checkout feature/eventstream-integration -- USAGE_GUIDE.md
git checkout feature/eventstream-integration -- CHANGELOG.md
# Edit README.md to include only documentation changes

git add .
git commit -m "docs: Add comprehensive Eventstream documentation

- Add architecture guide explaining service patterns
- Add async/sync bridge pattern documentation  
- Add usage guide with examples
- Update changelog and README"

git push fork feature/eventstream-documentation
```

### Step 3: Create PR 3 - Testing Infrastructure
```bash
git checkout main  
git checkout -b feature/eventstream-testing

git checkout feature/eventstream-integration -- eventstream_test/
git checkout feature/eventstream-integration -- tests/validate_final.py

git add .
git commit -m "test: Add Eventstream testing infrastructure

- Add integration tests for eventstream functionality
- Add validation script for PR readiness
- Add test configuration and setup"

git push fork feature/eventstream-testing
```

### Step 4: Create PR 4 - Client Tools
```bash
git checkout main
git checkout -b feature/eventstream-client-tools

git checkout feature/eventstream-integration -- tools/eventstream_client/
git checkout feature/eventstream-integration -- vscode-extension/
git checkout feature/eventstream-integration -- uv.lock

git add .
git commit -m "feat: Add Eventstream client tools and VS Code extension

- Add standalone eventstream client tools
- Add VS Code extension for MCP integration
- Add configuration templates and examples"

git push fork feature/eventstream-client-tools
```

## Merge Order
1. PR 1 (Core Service) - **Must go first** 
2. PR 2 (Documentation) - Can go in parallel with PR 1
3. PR 3 (Testing) - Should go after PR 1
4. PR 4 (Client Tools) - Can go last, depends on PR 1

## Benefits
- **Easier review**: Each PR focuses on one concern
- **Faster approval**: Reviewers can approve parts incrementally  
- **Lower risk**: Issues in one area don't block others
- **Cleaner history**: Each merge represents a logical feature
