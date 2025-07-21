"""
Integrated from external MCP server: fabric_eventstream_mcp\run_agent.py
Adapted for fabric-rti-mcp
"""

#!/usr/bin/env python3
"""
Example usage of the Fabric Eventstream AI Agent.

This script demonstrates how to use the AI agent to interact with Microsoft Fabric Eventstreams
through natural language. The agent uses the MCP server for authentication and API calls.

Usage:
    python run_agent.py                    # Interactive mode
    python run_agent.py --example          # Run example conversations
    python run_agent.py --test             # Test agent functionality
    python run_agent.py --demo             # Run in demo mode (no Azure OpenAI required)
    python run_agent.py --help             # Show help

Environment Variables (Required for Azure OpenAI):
    AZURE_OPENAI_ENDPOINT: Your Azure OpenAI endpoint URL
    AZURE_OPENAI_API_KEY: Your Azure OpenAI API key
    AZURE_OPENAI_DEPLOYMENT: Your deployment name (default: gpt-4)
    MCP_SERVER_URL: MCP server URL (default: http://localhost:8000)
"""
import os
import sys
from .ai_agent_openai import FabricEventstreamAgent

# Configuration - you can set these as environment variables
# or uncomment and set them here for testing
# os.environ["AZURE_OPENAI_ENDPOINT"] = "https://your-resource-name.openai.azure.com/"
# os.environ["AZURE_OPENAI_API_KEY"] = "your-azure-openai-key"
# os.environ["AZURE_OPENAI_DEPLOYMENT"] = "gpt-4"  # or your deployment name
# os.environ["MCP_SERVER_URL"] = "http://localhost:8000"

def test_agent():
    """Test the agent functionality and server connection."""
    print("🧪 Testing Fabric Eventstream AI Agent")
    print("=" * 50)
    
    # Check environment variables
    required_vars = ["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY"]
    missing_vars = []
    demo_mode = False
    
    for var in required_vars:
        if not os.getenv(var) or "<your-" in os.getenv(var, ""):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Missing environment variables: {missing_vars}")
        print("The agent will run in demo mode with simulated responses.")
        print("For full functionality, please set these environment variables.\n")
        demo_mode = True
    
    try:
        # Create the agent
        print("Creating AI agent...")
        agent = FabricEventstreamAgent(demo_mode=demo_mode)
        print("✅ Agent created successfully")
        
        # Test MCP server connection
        if agent.auth_token:
            print("✅ Authentication token acquired from MCP server")
        else:
            print("⚠️  No authentication token (MCP server may be offline)")
        
        # Test a simple conversation
        print("\n--- Testing basic conversation ---")
        test_message = "What can you help me with regarding Eventstreams?"
        print(f"User: {test_message}")
        
        response = agent.chat(test_message)
        print(f"🤖 Assistant: {response}")
        
        print("\n✅ Agent test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        print("\nPlease ensure:")
        print("1. MCP server is running (uvicorn main:app --reload)")
        print("2. Azure OpenAI credentials are properly set (or use demo mode)")
        print("3. All required packages are installed")

def example_conversation():
    """Example of programmatic conversation with the AI agent."""
    print("🤖 Example: Programmatic AI Agent Usage")
    print("=" * 50)
    
    # Check if we should use demo mode
    demo_mode = False
    if (not os.getenv("AZURE_OPENAI_API_KEY") or 
        "<your-" in os.getenv("AZURE_OPENAI_API_KEY", "") or
        not os.getenv("AZURE_OPENAI_ENDPOINT") or
        "<your-" in os.getenv("AZURE_OPENAI_ENDPOINT", "")):
        demo_mode = True
        print("Running examples in demo mode (simulated responses)\n")
    
    try:
        # Create the agent
        agent = FabricEventstreamAgent(demo_mode=demo_mode)
        print("Agent initialized successfully!\n")
        
        # Example conversations - using realistic workspace IDs
        examples = [
            "What are Microsoft Fabric Eventstreams and how can you help me manage them?",
            "Can you explain the main components of an Eventstream?",
            "List all Eventstreams in workspace 12345678-1234-1234-1234-123456789012",
            "Show me details of Eventstream abc123def-4567-8901-2345-678901234567 in workspace 12345678-1234-1234-1234-123456789012",
            "Help me create a simple Eventstream for IoT data processing in workspace 12345678-1234-1234-1234-123456789012"
        ]
        
        for i, user_message in enumerate(examples, 1):
            print(f"\n--- Example {i} ---")
            print(f"User: {user_message}")
            
            try:
                response = agent.chat(user_message)
                print(f"🤖 Assistant: {response}")
            except Exception as e:
                print(f"❌ Error: {e}")
            
            if i < len(examples):  # Don't wait after the last example
                input("\nPress Enter to continue to next example...")
        
        print("\n✅ All examples completed!")
        
    except Exception as e:
        print(f"❌ Error initializing agent: {e}")
        print("Please ensure the MCP server is running.")

def interactive_mode():
    """Run the agent in interactive mode."""
    # Check if we should use demo mode
    demo_mode = False
    if (not os.getenv("AZURE_OPENAI_API_KEY") or 
        "<your-" in os.getenv("AZURE_OPENAI_API_KEY", "") or
        not os.getenv("AZURE_OPENAI_ENDPOINT") or
        "<your-" in os.getenv("AZURE_OPENAI_ENDPOINT", "")):
        demo_mode = True
        print("🔧 Starting in demo mode (Azure OpenAI credentials not configured)")
    
    try:
        agent = FabricEventstreamAgent(demo_mode=demo_mode)
        agent.start_conversation()
    except Exception as e:
        print(f"❌ Error starting interactive mode: {e}")
        print("Please ensure the MCP server is running.")

def show_help():
    """Show help information."""
    print(__doc__)

def demo_mode():
    """Run the agent in demo mode (no Azure OpenAI required)."""
    print("🔧 Starting Fabric Eventstream AI Agent in Demo Mode")
    print("=" * 60)
    print("This mode demonstrates the agent functionality without requiring Azure OpenAI credentials.")
    print("The agent will provide simulated responses and still connect to the MCP server.\n")
    
    try:
        agent = FabricEventstreamAgent(demo_mode=True)
        agent.start_conversation()
    except Exception as e:
        print(f"❌ Error starting demo mode: {e}")
        print("Please ensure the MCP server is running.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "--example":
            example_conversation()
        elif command == "--test":
            test_agent()
        elif command == "--demo":
            demo_mode()
        elif command == "--help" or command == "-h":
            show_help()
        else:
            print(f"Unknown command: {command}")
            print("Use --help to see available commands.")
    else:
        interactive_mode()
