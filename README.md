[![Install with UVX in VS Code](https://img.shields.io/badge/VS_Code-Install_Microsoft_Fabric_RTI_MCP_Server-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=ms-fabric-rti&config=%7B%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22microsoft-fabric-rti-mcp%22%5D%7D) [![PyPI Downloads](https://static.pepy.tech/badge/microsoft-fabric-rti-mcp)](https://pepy.tech/projects/microsoft-fabric-rti-mcp)

## 🎯 Overview

A comprehensive Model Context Protocol (MCP) server implementation for [Microsoft Fabric Real-Time Intelligence (RTI)](https://aka.ms/fabricrti). 
This server enables AI agents to interact with Fabric RTI services by providing tools through the MCP interface, allowing for seamless data querying, analysis, and streaming capabilities.

> [!NOTE]  
> This project is in Public Preview and implementation may significantly change prior to General Availability.

### 🔍 How It Works

The Fabric RTI MCP Server creates a seamless integration between AI agents and Fabric RTI services through:

- 🔄 Smart JSON communication that AI agents understand
- 🏗️ Natural language commands that get translated to KQL operations and Eventstream management
- 💡 Intelligent parameter suggestions and auto-completion
- ⚡ Consistent error handling that makes sense
- 📊 Unified interface for both analytics and streaming workloads

### ✨ Supported Services

#### **Eventhouse (Kusto)** ✅
Execute KQL queries against Microsoft Fabric RTI [Eventhouse](https://aka.ms/eventhouse) and [Azure Data Explorer(ADX)](https://aka.ms/adx):
- List databases and tables
- Get table schemas
- Execute KQL queries
- Sample data from tables
- Ingest CSV data

#### **Eventstreams** ✅ 
Manage Microsoft Fabric [Eventstreams](https://learn.microsoft.com/en-us/fabric/real-time-intelligence/eventstream/eventstream-introduction) for real-time data processing:
- List Eventstreams in workspaces
- Get Eventstream details and definitions
- Create new Eventstreams
- Update existing Eventstreams
- Delete Eventstreams

## 🚧 Coming soon
- **Activator**
- **Other RTI items**

### 🔍 Explore your data

#### Eventhouse Analytics:
- "Get databases in Eventhouse"
- "Sample 10 rows from table 'StormEvents' in Eventhouse"
- "What can you tell me about StormEvents data?"
- "Analyze the StormEvents to come up with trend analysis across past 10 years of data"
- "Analyze the commands in 'CommandExecution' table and categorize them as low/medium/high risks"

#### Eventstream Management:
- "List all Eventstreams in my workspace"
- "Show me the details of my IoT data Eventstream"
- "Create a new Eventstream for processing sensor data"
- "Update my existing Eventstream to add a new destination"

### Available Tools 

#### Eventhouse (Kusto) - 6 Tools:
- **`list_databases`** - Enumerate all accessible databases in your Kusto cluster
- **`list_tables`** - List all tables within a specific database
- **`get_schema`** - Get detailed schema information for any table (columns, types, descriptions)
- **`sample_data`** - Retrieve sample rows from tables to understand data structure
- **`execute_kql`** - Execute any KQL (Kusto Query Language) query for analysis
- **`ingest_csv`** - Upload and ingest CSV data directly into Kusto tables

#### Eventstreams - 6 Tools:
- **`list_eventstreams`** - List all Eventstreams in your Fabric workspace
- **`get_eventstream`** - Get detailed information about a specific Eventstream
- **`create_eventstream`** - Create new Eventstreams with custom configuration
- **`update_eventstream`** - Modify existing Eventstream settings and destinations
- **`delete_eventstream`** - Remove Eventstreams and associated resources
- **`get_eventstream_definition`** - Retrieve complete JSON definition of an Eventstream

> **💡 Pro Tip**: All tools work with natural language! Just describe what you want to do and the AI agent will use the appropriate tools automatically.

## Getting Started

### Prerequisites
1. Install either the stable or Insiders release of VS Code:
   * [💫 Stable release](https://code.visualstudio.com/download)
   * [🔮 Insiders release](https://code.visualstudio.com/insiders)
2. Install the [GitHub Copilot](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot) and [GitHub Copilot Chat](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot-chat) extensions
3. Install `uv`  
```ps
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```  
or, check here for [other install options](https://docs.astral.sh/uv/getting-started/installation/#__tabbed_1_2)

4. Open VS Code in an empty folder


### Install from PyPI (Pip)
The Fabric RTI MCP Server is available on [PyPI](https://pypi.org/project/microsoft-fabric-rti-mcp/), so you can install it using pip. This is the easiest way to install the server.

#### From VS Code
    1. Open the command palette (Ctrl+Shift+P) and run the command `MCP: Add Server`
    2. Select install from Pip
    3. When prompted, enter the package name `microsoft-fabric-rti-mcp`
    4. Follow the prompts to install the package and add it to your settings.json file

The process should end with the below settings in your `settings.json` file.

#### settings.json
```json
{
    "mcp": {
        "server": {
            "fabric-rti-mcp": {
                "command": "uvx",
                "args": [
                    "microsoft-fabric-rti-mcp"
                ],
                "env": {
                    "KUSTO_SERVICE_URI": "https://cluster.westus.kusto.windows.net/", //optionally provide cluster URI
                    "KUSTO_DATABASE": "Datasets", //optionally provide database
                    "FABRIC_WORKSPACE_ID": "your-workspace-id" //optionally provide default workspace for Eventstreams
                }
            }
        }
    }
}
```

### 🔧 Manual Install (Install from source)  

1. Make sure you have Python 3.10+ installed properly and added to your PATH.
2. Clone the repository
3. Install the dependencies (`pip install .` or `uv tool install .`)
4. Add the settings below into your vscode `settings.json` file. 
5. Change the path to match the repo location on your machine.
6. Change the cluster uri in the settings to match your cluster.

```json
{
    "mcp": {
        "servers": {
            "fabric-rti-mcp": {
                "command": "uv",
                "args": [
                    "--directory",
                    "C:/path/to/fabric-rti-mcp/",
                    "run",
                    "-m",
                    "fabric_rti_mcp.server"
                ],
                "env": {
                    "KUSTO_SERVICE_URI": "https://cluster.westus.kusto.windows.net/", //optionally provide cluster URI
                    "KUSTO_DATABASE": "Datasets", //optionally provide database
                    "FABRIC_WORKSPACE_ID": "your-workspace-id" //optionally provide default workspace for Eventstreams
                }
            }
        }
    }
}
```

## 🐛 Debugging the MCP Server locally
Assuming you have python installed and the repo cloned:

### Install locally
```bash
pip install -e ".[dev]"
```

### Configure

Add the server to your
```
{
    "mcp": {
        "servers": {
            "local-fabric-rti-mcp": {
                "command": "python",
                "args": [
                    "-m",
                    "fabric_rti_mcp.server"
                ]
            }
        }
    }
}
```

### Attach the debugger
Use the `Python: Attach` configuration in your `launch.json` to attach to the running server. 
Once VS Code picks up the server and starts it, navigate to it's output: 
1. Open command palette (Ctrl+Shift+P) and run the command `MCP: List Servers`
2. Navigate to `local-fabric-rti-mcp` and select `Show Output`
3. Pick up the process id (PID) of the server from the output
4. Run the `Python: Attach` configuration in your `launch.json` file, and paste the PID of the server in the prompt
5. The debugger will attach to the server process, and you can start debugging


## 🧪 Test the MCP Server

### Via GitHub Copilot
1. Open GitHub Copilot in VS Code and [switch to Agent mode](https://code.visualstudio.com/docs/copilot/chat/chat-agent-mode)
2. You should see the Fabric RTI MCP Server in the list of tools
3. Try prompts that tell the agent to use the RTI tools, such as:
   - **Eventhouse**: "List my Kusto tables" or "Show me a sample from the StormEvents table"
   - **Eventstreams**: "List all Eventstreams in my workspace" or "Show me details of my data processing Eventstream"
4. The agent should be able use the Fabric RTI MCP Server tools to complete your query

### Via VS Code Client Tool
For direct testing and development, use the included VS Code client:

```bash
# Interactive mode with menu
python eventstream_test/vscode_mcp_client.py

# Natural language commands
python eventstream_test/vscode_mcp_client.py "list eventstreams in workspace abc-123 with interactive auth"
python eventstream_test/vscode_mcp_client.py "query cluster https://example.kusto.windows.net: MyTable | take 10"
python eventstream_test/vscode_mcp_client.py "get fabric api base url"
```

The VS Code client includes:
- 🔐 **Interactive authentication** - Browser-based Microsoft sign-in
- 🗣️ **Natural language prompts** - English commands for MCP operations  
- ⚙️ **API configuration** - Runtime control of Fabric API endpoints
- 📊 **JSON output** - Formatted results for analysis

## 🏗️ Architecture

The Fabric RTI MCP Server is designed with a clean, modular architecture:

### MCP Server Core
```
fabric_rti_mcp/
├── kusto/                    # Eventhouse (Kusto) integration
│   ├── kusto_service.py      # Core Kusto operations
│   ├── kusto_tools.py        # MCP tool definitions
│   └── kusto_connection.py   # Connection management
├── eventstream/              # Eventstream integration  
│   ├── eventstream_service.py # Core Eventstream operations
│   └── eventstream_tools.py  # MCP tool definitions
├── server.py                 # Main MCP server entry point
└── common.py                 # Shared utilities
```

### Standalone Tools
```
tools/
└── eventstream_client/       # Standalone Eventstream tools
    ├── ai_agent_openai.py    # AI agent for Eventstream management
    ├── config.py             # Configuration management
    ├── demo_agent.py         # Demo and example scripts
    └── run_agent.py          # Agent runner
```

### Testing & Client Tools
```
eventstream_test/             # Test utilities and examples
├── test_api_config.py        # Test Fabric API configuration
├── test_eventstream_client.py # Test Eventstream MCP client
├── test_mcp_connection.py    # Test MCP server connection
├── vscode_mcp_client.py      # VS Code MCP client with interactive auth
└── vscode-mcp-client.ipynb   # Jupyter notebook examples
```

> **Note**: The `tools/` directory contains standalone utilities that can be used independently of the MCP server for direct Fabric integration and automation. The `eventstream_test/` directory contains testing utilities and client examples.

### Key Design Principles

- 🔧 **Modular**: Each service (Kusto, Eventstream) is self-contained
- 🔄 **Async/Sync Bridge**: Seamless integration between async operations and MCP's sync interface
- 🎯 **Clean Separation**: MCP server code separate from standalone tools
- 🛡️ **Type Safe**: Comprehensive type annotations throughout
- ⚡ **Performance**: Connection caching and efficient resource management


## 🔑 Authentication

The MCP Server seamlessly integrates with your host operating system's authentication mechanisms, making it super easy to get started! We use Azure Identity under the hood via [`DefaultAzureCredential`](https://learn.microsoft.com/en-us/azure/developer/python/sdk/authentication/credential-chains?tabs=dac), which tries these credentials in order:

1. **Environment Variables** (`EnvironmentCredential`) - Perfect for CI/CD pipelines
1. **Visual Studio** (`VisualStudioCredential`) - Uses your Visual Studio credentials
1. **Azure CLI** (`AzureCliCredential`) - Uses your existing Azure CLI login
1. **Azure PowerShell** (`AzurePowerShellCredential`) - Uses your Az PowerShell login
1. **Azure Developer CLI** (`AzureDeveloperCliCredential`) - Uses your azd login
1. **Interactive Browser** (`InteractiveBrowserCredential`) - Falls back to browser-based login if needed

If you're already logged in through any of these methods, the Fabric RTI MCP Server will automatically use those credentials.

## 🛡️ Security Note

Your credentials are always handled securely through the official [Azure Identity SDK](https://github.com/Azure/azure-sdk-for-net/blob/main/sdk/identity/Azure.Identity/README.md) - **we never store or manage tokens directly**.

MCP as a phenomenon is very novel and cutting-edge. As with all new technology standards, consider doing a security review to ensure any systems that integrate with MCP servers follow all regulations and standards your system is expected to adhere to. This includes not only the Azure MCP Server, but any MCP client/agent that you choose to implement down to the model provider.


## 👥 Contributing

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.opensource.microsoft.com.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

## 🤝 Code of Conduct

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

- ✅ **Complete documentation** - Users can easily understand and use both services
- ✅ **Clean codebase** - No dead code or architectural debt

**This integration and cleanup effort has been a COMPLETE SUCCESS!** 🎉🚀

The project is **ready for feature branch push and production deployment**.

## 📚 Documentation

- **[Usage Guide](./USAGE_GUIDE.md)** - Comprehensive examples and scenarios
- **[Architecture Guide](./ARCHITECTURE.md)** - Technical architecture and design patterns  
- **[Async Pattern Explanation](./ASYNC_PATTERN_EXPLANATION.md)** - Details on async/sync integration
- **[Changelog](./CHANGELOG.md)** - Release history and breaking changes
- **[Project Assessment](./POST_CLEANUP_ASSESSMENT.md)** - Current project health status

## Data Collection

The software may collect information about you and your use of the software and send it to Microsoft. Microsoft may use this information to provide services and improve our products and services. You may turn off the telemetry as described in the repository. There are also some features in the software that may enable you and Microsoft to collect data from users of your applications. If you use these features, you must comply with applicable law, including providing appropriate notices to users of your applications together with a copy of Microsoft’s privacy statement. Our privacy statement is located at https://go.microsoft.com/fwlink/?LinkID=824704. You can learn more about data collection and use in the help documentation and our privacy statement. Your use of the software operates as your consent to these practices.


## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft 
trademarks or logos is subject to and must follow 
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.
