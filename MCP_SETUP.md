# MCP Configuration Setup

This document explains how to configure the Microsoft Fabric RTI MCP server with VS Code.

## Configuration File Setup

1. **Copy the template configuration:**
   ```bash
   cp mcp.json.template ~/.config/Code/User/mcp.json
   # Or on Windows: copy mcp.json.template "%APPDATA%\Code\User\mcp.json"
   ```

2. **Update the path in mcp.json:**
   Replace `<PATH_TO_FABRIC_RTI_MCP_DIRECTORY>` with the actual path to your fabric-rti-mcp directory.

   Example:
   ```json
   "args": [
     "--directory",
     "/home/user/projects/fabric-rti-mcp",  // Linux/Mac
     // or "C:/Users/username/Sources/fabric-rti-mcp",  // Windows
     "run",
     "-m",
     "fabric_rti_mcp.server"
   ]
   ```

## Environment Variables

The following environment variables can be configured:

- `KUSTO_SERVICE_URI`: URI for Kusto cluster (default: https://help.kusto.windows.net/)
- `KUSTO_DATABASE`: Default Kusto database (default: Samples)
- `FABRIC_API_BASE_URL`: Microsoft Fabric API base URL (default: https://api.fabric.microsoft.com/v1)

## Security Settings

The configuration includes security settings to enable eventstream builder tools:

- `allowDangerous: true` - Allows potentially destructive operations
- `enableModificationTools: true` - Enables tools that modify data/resources
- `trustLevel: "full"` - Full trust level for the MCP server

## Testing the Configuration

After setting up the configuration:

1. Restart VS Code
2. Open Copilot Chat
3. Try: `@workspace List available MCP tools`
4. You should see both Kusto and Eventstream tools available

## Troubleshooting

If tools don't appear:
- Check the file path in mcp.json is correct
- Ensure uv is installed and in PATH
- Check VS Code logs for MCP connection errors
- Verify the fabric_rti_mcp package is properly installed
