---
mode: agent
description: Adds the necessary files to turn a standard MCP server into an MCP server that runs on Azure Functions.
model: Claude Sonnet 4
tools: ['codebase', 'editFiles', 'fetch', 'problems', 'runCommands', 'search', 'searchResults', 'terminalLastCommand', 'usages']
---

Your goal is to take the MCP server in the current codebase and add the necessary files to turn it into an MCP server that runs on Azure Functions.

## Prerequisites

- Languages supported: Node.js (TypeScript, JavaScript), Python, C#
- Create the Azure Functions project structure in the root of the MCP server project (e.g., folder where `package.json`, or `*.csproj` is located). If you can't find the root, ask for it.

### Additional validations

**Important**: STOP if the MCP server does not meet the following requirements. **Do not attempt to fix the MCP server code, just inform the user that the MCP server does not meet the requirements and exit.**

1. The MCP server must use streamable HTTP transport, not stdio.
    - For Node.js, it must use `StreamableHTTPServerTransport`.
    - For Python, the FastMCP server must be run with `transport="streamable-http"`.

2. The MCP server must be stateless.
    - For Node.js, `StreamableHTTPServerTransport` must not have `sessionIdGenerator` configured.
    - For Python, the server FastMCP server must be created with `stateless_http=True`. The default value is `False`, so it must be explicitly set it to `True`.
    
Again, this is super important -- if the above conditions are not met, STOP and don't make any changes.

## Steps

Take these general steps to convert the MCP server into an Azure Functions app.

### Create the Azure Functions project structure

Add the necessary files to run the MCP server as a custom handler in Azure Functions.

1. Create a `host.json` file with the following content:
    ```json
    {
        "version": "2.0",
        "extensions": {
            "http": {
                "routePrefix": ""
            }
        },
        "customHandler": {
            "description": {
                "defaultExecutablePath": "",
                "workingDirectory": "",
                "arguments": []
            },
            "enableForwardingHttpRequest": true,
            "enableHttpProxyingRequest": true
        }
    }
    ```

    **IMPORTANT**: Do not remove the properties `enableForwardingHttpRequest` and `enableHttpProxyingRequest`, even if the property is not recognized in the JSON schema. They are required for the MCP server to work correctly with Azure Functions.

    Set `defaultExecutablePath` and (optionally) `arguments` to the correct command to run the MCP server.
        - For Node.js, this is typically `node` with an argument of the path to the compiled JavaScript file (e.g., `server.js`). Don't use `npm` in case it's not installed in the Azure Functions environment.
        - For Python, this would be `python` with the path to the main script. If it's unclear which script to use, look for one that initializes the MCP server (e.g., look for file using `FastMCP`) or ask for help.
        - For C#, this would be `dotnet` with the path to the compiled DLL (e.g., `MyMcpServer.dll`). You do not need to set `workingDirectory` for C#, assume the DLL will be compiled to the root of the project.

1. Create a folder named `mcp-handler` in the root of the MCP server project. Inside the folder, create a file named `function.json` with the following content:
    ```json
    {
        "bindings": [
            {
                "authLevel": "anonymous",
                "type": "httpTrigger",
                "direction": "in",
                "name": "req",
                "methods": ["get", "post", "put", "delete", "patch", "head", "options"],
                "route": "{*route}"
            },
            {
                "type": "http",
                "direction": "out",
                "name": "res"
            }
        ]
    }
    ```

1. Create a `local.settings.json` file with the following content (select the correct runtime):
    ```json
    {
        "IsEncrypted": false,
        "Values": {
            "FUNCTIONS_WORKER_RUNTIME": "<node|python|dotnet-isolated>",
        }
    }
    ```

1. Create a `.funcignore` file in the root of the MCP server project that is suitable for the MCP server's runtime.

### Update the MCP server code

Modify the MCP server code to listen for HTTP requests on the port specified by the Azure Functions environment variable `FUNCTIONS_CUSTOMHANDLER_PORT`. This is typically done by reading the environment variable in your server code and using it to set the port for the HTTP server.

**Important** additional language-specific instructions:
- **Python**:
    - If the server uses FastMCP, you can pass this port to the `FastMCP` constructor like: `mcp = FastMCP("my-mcp", port=mcp_port)`.

## Add AzD template

Create an `infra` folder and an `azure.yaml` file so that the MCP server can be deployed using the Azure Developer CLI (AzD).

First, use the terminal to download a zip of this repository: https://github.com/anthonychu/create-functions-mcp-server . Extract the zip into a folder named `unzip`. Copy the `azure.yaml` file and the `infra` folder to your MCP server project. Delete the zip file and `unzip` folder after copying the files.

Next, modify the `azure.yaml` file to match the runtime/language of the MCP server project.

In the Bicep files, change the function app's name to reflect the MCP server project name.

Also in the Bicep files, change the runtime and runtime version to based on the following rules:
- For Node.js, use `node` and `20` or `22`
- For Python, use `python` and `3.10`, `3.11`, `3.12`, or `3.13`
- For C#, use `dotnet-isolated` and `8.0`, `9.0`, or `10.0`

Additionally, for Python, add an app setting to the function app:
- `PYTHONPATH` = `/home/site/wwwroot/.python_packages/lib/site-packages`

Additionally, for C#, add an empty file named `empty.txt` in an `.azurefunctions` folder in the root of the MCP server project. Then update the csproj file to include the `.azurefunctions` folder in the output directory. This is necessary for the Azure Functions runtime to deploy the custom handler.

## Additional files

Don't worry about adding additional files like a README. Also don't worry about running in depth tests.

## Summarize the changes

Summarize the changes made and outline the next steps (`azd up`) for the user to deploy the MCP server on Azure Functions, but do not deploy it yet.

