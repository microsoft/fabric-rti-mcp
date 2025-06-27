"""
Integrated from external MCP server: fabric_eventstream_mcp\example_usage.py
Adapted for fabric-rti-mcp
"""

#!/usr/bin/env python3
"""
Complete example of using the Fabric Eventstream AI Agent.

This example demonstrates:
1. Basic agent setup and configuration
2. Demo mode for testing without Azure OpenAI
3. Real MCP server interactions
4. Error handling and best practices
"""
import os
from .ai_agent_openai import FabricEventstreamAgent
from .config import config

def setup_demo_environment():
    """Set up environment for demo purposes."""
    print("🔧 Setting up environment...")
    
    # Check if configuration is already loaded
    is_valid, missing = config.validate()
    
    if is_valid:
        print("✅ Environment already configured from config file or environment variables")
    else:
        print(f"⚠️  Missing configuration: {', '.join(missing)}")
        print("💡 Create config_local.py with your actual credentials or set environment variables")
        print("   See config_local_template.py for the expected format")
    
    # Display current configuration (without sensitive data)
    print(f"🔗 MCP Server URL: {config.MCP_SERVER_URL}")
    print(f"🌐 Azure OpenAI Endpoint: {config.AZURE_OPENAI_ENDPOINT or 'Not configured'}")
    print(f"🔑 API Key configured: {'Yes' if config.AZURE_OPENAI_API_KEY else 'No'}")
    print(f"🚀 Deployment: {config.AZURE_OPENAI_DEPLOYMENT}")
    print(f"📁 Default Workspace ID: {config.DEFAULT_WORKSPACE_ID or 'Not configured'}")
    
    return is_valid

def test_azure_openai_connection():
    """Test Azure OpenAI connection."""
    print("\n" + "="*60)
    print("🔍 TESTING: Azure OpenAI Connection")
    print("="*60)
    
    if config.is_demo_mode():
        print("⚠️  Azure OpenAI not configured - skipping connection test")
        return False
    
    from openai import AzureOpenAI
    
    # Get credentials from config
    try:
        client = AzureOpenAI(
            api_key=config.AZURE_OPENAI_API_KEY,
            api_version=config.AZURE_OPENAI_API_VERSION,
            azure_endpoint=config.AZURE_OPENAI_ENDPOINT
        )
        print("✅ Client created successfully")
        print(f"🔗 Testing endpoint: {config.AZURE_OPENAI_ENDPOINT}")
    except Exception as e:
        print(f"❌ Failed to create client: {e}")
        return False
    
    # Test the configured deployment
    print(f"\n🔄 Testing deployment: {config.AZURE_OPENAI_DEPLOYMENT}")
    
    try:
        response = client.chat.completions.create(
            model=config.AZURE_OPENAI_DEPLOYMENT,
            messages=[{"role": "user", "content": "Hello, test message"}],
            max_tokens=50
        )
        print(f"✅ SUCCESS! Deployment '{config.AZURE_OPENAI_DEPLOYMENT}' works!")
        print(f"💬 Response: {response.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"❌ Deployment '{config.AZURE_OPENAI_DEPLOYMENT}' failed: {e}")
        print("\n📋 Please check your Azure OpenAI configuration:")
        print("1. Verify your deployment name in Azure OpenAI Studio")
        print("2. Make sure the deployment is active and not paused")
        print("3. Update the deployment name in config_local.py")
        return False
    print("\n🔧 For now, the agent will run in demo mode.")
    return None

def demo_basic_conversation():
    """Demonstrate basic conversation with the agent."""
    print("\n" + "="*60)
    print("🤖 DEMO: Basic Conversation with Azure OpenAI")
    print("="*60)
    
    # Test Azure OpenAI connection first
    working_deployment = test_azure_openai_connection()
    
    if working_deployment:
        print(f"\n✅ Using working deployment: {working_deployment}")
        demo_mode = False
    else:
        print("\n🔧 Falling back to demo mode")
        demo_mode = True
    
    # Create agent 
    agent = FabricEventstreamAgent(demo_mode=demo_mode)
    
    # Example conversations
    conversations = [
        "What can you help me with regarding Microsoft Fabric Eventstreams?",
        "Explain what Microsoft Fabric Eventstreams are and their main components",
        "How do I create an Eventstream for IoT data processing?",
    ]
    
    for i, message in enumerate(conversations, 1):
        print(f"\n--- Conversation {i} ---")
        print(f"👤 User: {message}")
        
        try:
            response = agent.chat(message)
            print(f"🤖 Agent: {response}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        if i < len(conversations):
            input("\nPress Enter to continue...")

def demo_mcp_integration():
    """Demonstrate MCP server integration."""
    print("\n" + "="*60)
    print("🔗 DEMO: MCP Server Integration")
    print("="*60)
    
    agent = FabricEventstreamAgent(demo_mode=True)
    
    # Test MCP calls with fake but realistic IDs
    mcp_examples = [
        "List all Eventstreams in workspace 12345678-1234-1234-1234-123456789012",
        "Get details of Eventstream abc12345-6789-0123-4567-890123456789 in workspace 12345678-1234-1234-1234-123456789012",
        "Create an Eventstream for IoT data in workspace 12345678-1234-1234-1234-123456789012"
    ]
    
    for i, message in enumerate(mcp_examples, 1):
        print(f"\n--- MCP Example {i} ---")
        print(f"👤 User: {message}")
        print("🔄 Calling MCP server...")
        
        response = agent.chat(message)
        print(f"🤖 Agent: {response}")
        
        if i < len(mcp_examples):
            input("\nPress Enter to continue...")

def demo_real_workspace():
    """Example with real workspace ID from configuration."""
    print("\n" + "="*60)
    print("🏢 DEMO: Real Workspace Example")
    print("="*60)
    
    workspace_id = config.get_workspace_id()
    
    if not workspace_id:
        print("⚠️  No workspace ID configured")
        print("   1. Set FABRIC_WORKSPACE_ID environment variable, or")
        print("   2. Add FABRIC_WORKSPACE_ID to config_local.py")
        print("\n   Skipping real workspace demo...")
        return
    
    agent = FabricEventstreamAgent(demo_mode=config.is_demo_mode())
    
    print(f"🔍 Testing with workspace: {workspace_id}")
    print("📋 Attempting to list Eventstreams...")
    
    response = agent.chat(f"List all Eventstreams in workspace {workspace_id}")
    print(f"🤖 Agent: {response}")
    
    # Also test the help functionality
    print("\n📖 Testing help functionality...")
    help_response = agent.chat("What can you help me with?")
    print(f"🤖 Agent: {help_response}")

def demo_error_handling():
    """Demonstrate error handling capabilities."""
    print("\n" + "="*60)
    print("⚠️  DEMO: Error Handling")
    print("="*60)
    
    agent = FabricEventstreamAgent(demo_mode=True)
    
    # Test various error scenarios
    error_examples = [
        "List Eventstreams without workspace ID",
        "Get details without proper IDs",
        "List Eventstreams in workspace invalid-id-format",
    ]
    
    for i, message in enumerate(error_examples, 1):
        print(f"\n--- Error Test {i} ---")
        print(f"👤 User: {message}")
        
        response = agent.chat(message)
        print(f"🤖 Agent: {response}")
        
        if i < len(error_examples):
            input("\nPress Enter to continue...")

def main():
    """Run the complete demo."""
    print("🎯 Fabric Eventstream AI Agent - Complete Demo")
    print("="*70)
    print("This demo will test your configuration and demonstrate all agent capabilities.")
    print("\nPress Enter to start...")
    input()
    
    # Setup and validate configuration
    config_valid = setup_demo_environment()
    
    # Test Azure OpenAI if configured
    if config_valid and not config.is_demo_mode():
        print("\n🔄 Testing Azure OpenAI connection...")
        test_azure_openai_connection()
    
    # Run demos
    try:
        demo_basic_conversation()
        demo_mcp_integration() 
        demo_error_handling()
        demo_real_workspace()
        
        print("\n" + "="*70)
        print("✅ Demo completed successfully!")
        print("="*70)
        print("\n🎯 Next Steps:")
        if config.is_demo_mode():
            print("1. Configure Azure OpenAI credentials in config_local.py for full AI capabilities")
        else:
            print("1. Azure OpenAI is configured - you have full AI capabilities!")
        print("2. Use 'python ai_agent_openai.py' for interactive mode")
        print("3. Modify config_local.py to update workspace IDs and other settings")
        
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        print("Please ensure the MCP server is running: uvicorn main:app --reload")

if __name__ == "__main__":
    main()
