[![Install with UVX in VS Code](https://img.shields.io/badge/VS_Code-Install_Microsoft_Fabric_RTI_MCP_Server-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=ms-fabric-rti&config=%7B%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22microsoft-fabric-rti-mcp%22%5D%7D) [![PyPI Downloads](https://static.pepy.tech/badge/microsoft-fabric-rti-mcp)](https://pepy.tech/projects/microsoft-fabric-rti-mcp)
## 🎯 Overview

A Model Context Protocol (MCP) server implementation for [Microsoft Fabric Real-Time Intelligence (RTI)](https://aka.ms/fabricrti). 
This server enables AI agents to interact with Fabric RTI services by providing tools through the MCP interface, allowing for seamless data querying and analysis capabilities.

> [!NOTE]  
> This project is in Public Preview and implementation may significantly change prior to General Availability.

### 🔍 How It Works

The Fabric RTI MCP Server creates a seamless integration between AI agents and Fabric RTI services through:

- 🔄 Smart JSON communication that AI agents understand
- 🏗️ Natural language commands that get translated to Kql operations
- 💡 Intelligent parameter suggestions and auto-completion!
- ⚡ Consistent error handling that makes sense

### ✨ Supported Services
- **Eventhouse (Kusto)**: Execute KQL queries against Microsoft Fabric RTI [Eventhouse](https://aka.ms/eventhouse) and [Azure Data Explorer(ADX)](https://aka.ms/adx).

## 🚧 Coming soon
- **Activator**
- **Eventstreams**
- **Other RTI items**

### 🔍 Explore your data

- "Get databases in Eventhouse'"
- "Sample 10 rows from table 'StormEvents' in Eventhouse"
- "What can you tell me about StormEvents data?"
- "Analyze the StormEvents to come up with trend analysis ocross past 10 years of data"
- "Analyze the commands in 'CommandExecution' table and categorize them as low/medium/high risks"


### Available tools 
- List databases
- List tables
- Get schema for a table
- Sample rows from a table
- Execute query
- Ingest a csv
- Get shots
- Explain KQL results (takes a KQL query and returns a modified query that adds natural language descriptions for each row)

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
    4. Follow the prompts to install the package and add it to your settings.json or your mcp.json file

The process should end with the below settings in your `settings.json` or your `mcp.json` file.

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
                    "KUSTO_SERVICE_URI": "https://help.kusto.windows.net/", // optionally provide cluster URI
                    "KUSTO_SERVICE_DEFAULT_DB": "Samples", // optionally provide database
                    "AZ_OPENAI_EMBEDDING_ENDPOINT": "https://your-openai-resource.openai.azure.com/openai/deployments/text-embedding-ada-002/embeddings?api-version=2024-10-21;impersonate", // optionally provide Azure OpenAI embedding endpoint (used for semantic search in the get shots tool)
                    "AZ_OPENAI_COMPLETION_ENDPOINT": "https://your-openai-resource.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-10-21;impersonate" // optionally provide Azure OpenAI completion endpoint (used for explaining row data)
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
4. Add the settings below into your vscode `settings.json` or your `mcp.json` file. 
5. Modify the path to match the repo location on your machine.
6. Modify the cluster uri in the settings to match your cluster.
7. Modify the cluster default database in the settings to match your database.
8. Modify the embeddings endpoint in the settings to match yours. This step is optional and needed only in case you supply a shots table

```json
{
    "mcp": {
        "servers": {
            "kusto-mcp": {
                "command": "uv",
                "args": [
                    "--directory",
                    "C:/path/to/fabric-rti-mcp/",
                    "run",
                    "-m",
                    "fabric_rti_mcp.server"
                ],
                "env": {
                    "KUSTO_SERVICE_URI": "https://help.kusto.windows.net/", // optionally provide cluster URI
                    "KUSTO_SERVICE_DEFAULT_DB": "Samples", // optionally provide database
                    "AZ_OPENAI_EMBEDDING_ENDPOINT": "https://your-openai-resource.openai.azure.com/openai/deployments/text-embedding-ada-002/embeddings?api-version=2024-10-21;impersonate" // optionally provide Azure OpenAI embedding endpoint (used for semantic search in the get shots tool)
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

Follow the [Manual Install](#🔧-manual-install-install-from-source) instructions.

### Attach the debugger
Use the `Python: Attach` configuration in your `launch.json` to attach to the running server. 
Once VS Code picks up the server and starts it, navigate to it's output: 
1. Open command palette (Ctrl+Shift+P) and run the command `MCP: List Servers`
2. Navigate to `local-fabric-rti-mcp` and select `Show Output`
3. Pick up the process id (PID) of the server from the output
4. Run the `Python: Attach` configuration in your `launch.json` file, and paste the PID of the server in the prompt
5. The debugger will attach to the server process, and you can start debugging


## 🧪 Test the MCP Server

1. Open GitHub Copilot in VS Code and [switch to Agent mode](https://code.visualstudio.com/docs/copilot/chat/chat-agent-mode)
2. You should see the Fabric RTI MCP Server in the list of tools
3. Try a prompt that tells the agent to use the Eventhouse tools, such as "List my Kusto tables"
4. The agent should be able to use the Fabric RTI MCP Server tools to complete your query


## ⚙️ Configuration

The MCP server can be configured using the following environment variables:

### Required Environment Variables
None - the server will work with default settings for demo purposes.

### Optional Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `KUSTO_SERVICE_URI` | The URI of your Kusto cluster | `https://mycluster.westus.kusto.windows.net` |
| `KUSTO_SERVICE_DEFAULT_DB` | Default database name for queries | `MyDatabase` |
| `AZ_OPENAI_EMBEDDING_ENDPOINT` | Custom Azure OpenAI embedding endpoint for semantic search | `https://your-resource.openai.azure.com/openai/deployments/text-embedding-ada-002/embeddings?api-version=2024-10-21;impersonate` |
| `AZ_OPENAI_COMPLETION_ENDPOINT` | Custom Azure OpenAI completion endpoint for explaining row data | `https://your-resource.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-10-21;impersonate` |

### Embedding Endpoint Configuration

The `AZ_OPENAI_EMBEDDING_ENDPOINT` is used by the semantic search functionality (e.g., `kusto_get_shots` function) to find similar query examples. 

**Format Requirements:**
```
https://{your-openai-resource}.openai.azure.com/openai/deployments/{deployment-name}/embeddings?api-version={api-version};impersonate
```

**Components:**
- `{your-openai-resource}`: Your Azure OpenAI resource name
- `{deployment-name}`: Your text embedding deployment name (e.g., `text-embedding-ada-002`)
- `{api-version}`: API version (e.g., `2024-10-21`, `2023-05-15`)
- `;impersonate`: Authentication method (you might use managed identity)

**Authentication Requirements:**
- Your Azure identity must have access to the OpenAI resource
- In case using managed identity, the OpenAI resource must should be configured to accept managed identity authentication
- The deployment must exist and be accessible

### Configuration of Shots table
The `get shots` tool retrieves shots that are most similar to your prompt out of the shots table. This function requires configuration of:
- Shots table that should have "EmbeddingText" (string) column containing the natural language prompt, "AugmentedText" (string) column containing the respective KQL, and "EmbeddingVector" (dynamic) column containing the embedding vector of the EmbeddingText.
- Azure OpenAI embedding endpoint to create embedding vectors for your prompt. Note that this endpoint must embed using the same model that was used for creating the "EmbeddingVector" column in the Shots table.

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

## Data Collection

The software may collect information about you and your use of the software and send it to Microsoft. Microsoft may use this information to provide services and improve our products and services. You may turn off the telemetry as described in the repository. There are also some features in the software that may enable you and Microsoft to collect data from users of your applications. If you use these features, you must comply with applicable law, including providing appropriate notices to users of your applications together with a copy of Microsoft’s privacy statement. Our privacy statement is located at https://go.microsoft.com/fwlink/?LinkID=824704. You can learn more about data collection and use in the help documentation and our privacy statement. Your use of the software operates as your consent to these practices.


## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft 
trademarks or logos is subject to and must follow 
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.
