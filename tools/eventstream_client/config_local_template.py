"""
Integrated from external MCP server: fabric_eventstream_mcp\config_local_template.py
Adapted for fabric-rti-mcp
"""

"""
Local configuration file - DO NOT COMMIT TO GIT
Copy this file to config_local.py and fill in your actual values
"""

# This is a template file - create config_local.py with your actual values
LOCAL_CONFIG = {
    # Azure OpenAI Configuration
    "AZURE_OPENAI_ENDPOINT": "https://your-resource-name.openai.azure.com/",
    "AZURE_OPENAI_API_KEY": "your-azure-openai-api-key-here",
    "AZURE_OPENAI_DEPLOYMENT": "gpt-4",
    "AZURE_OPENAI_API_VERSION": "2024-02-15-preview",
    
    # Microsoft Fabric Configuration
    "FABRIC_WORKSPACE_ID": "your-workspace-id-here",
    
    # MCP Server Configuration (optional)
    "MCP_SERVER_URL": "http://localhost:8000",
}
