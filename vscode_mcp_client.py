#!/usr/bin/env python3
"""
Simple MCP client for VS Code
Run this script in VS Code terminal to interact with Fabric RTI MCP server

Usage:
  python vscode_mcp_client.py                    # Interactive mode
  python vscode_mcp_client.py "list eventstreams in workspace abc-123 with token xyz"
  python vscode_mcp_client.py "query kusto cluster https://example.kusto.windows.net with 'MyTable | take 10'"
  python vscode_mcp_client.py "list databases in cluster https://example.kusto.windows.net"
"""

import asyncio
import json
import sys
import re
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.append(str(Path(__file__).parent))

async def main():
    """Main interface for MCP operations"""
    # Check if prompt was provided as command line argument
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
        print(f"🚀 Processing prompt: {prompt}")
        await process_prompt(prompt)
        return
    
    # Interactive mode
    print("🚀 Fabric RTI MCP Client")
    print("=" * 50)
    print("💡 You can also use natural language prompts!")
    print("   Example: 'list eventstreams in workspace abc-123 with token xyz'")
    print("   Example: 'query kusto cluster https://example.kusto.windows.net MyTable | take 10'")
    
    while True:
        print("\nAvailable operations:")
        print("1. List Eventstreams")
        print("2. Query Kusto") 
        print("3. List Kusto Databases")
        print("4. Get Eventstream Definition")
        print("5. List Eventstreams (Interactive Auth)")
        print("6. Get Eventstream Definition (Interactive Auth)")
        print("7. Natural Language Prompt")
        print("8. Show Prompt Examples")
        print("9. Test Prompt Parsing (Dry Run)")
        print("10. Get Fabric API Base URL")
        print("11. Set Fabric API Base URL")
        print("12. Reset Fabric API Base URL")
        print("13. Exit")
        
        choice = input("\nSelect operation (1-13): ").strip()
        
        if choice == "1":
            await list_eventstreams()
        elif choice == "2":
            await query_kusto()
        elif choice == "3":
            await list_kusto_databases()
        elif choice == "4":
            await get_eventstream_definition()
        elif choice == "5":
            await list_eventstreams_with_auth()
        elif choice == "6":
            await get_eventstream_definition_with_auth()
        elif choice == "7":
            prompt = input("\nEnter your prompt: ").strip()
            await process_prompt(prompt)
        elif choice == "8":
            show_prompt_examples()
        elif choice == "9":
            await test_prompt_parsing()
        elif choice == "10":
            await get_fabric_api_base()
        elif choice == "11":
            await set_fabric_api_base()
        elif choice == "12":
            await reset_fabric_api_base()
        elif choice == "13":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please select 1-13.")

async def list_eventstreams():
    """List eventstreams in a workspace"""
    print("\n📋 List Eventstreams")
    workspace_id = input("Enter workspace ID: ").strip()
    auth_token = input("Enter auth token (Bearer xxx): ").strip()
    
    if not auth_token.startswith("Bearer "):
        auth_token = f"Bearer {auth_token}"
    
    try:
        # Use the direct service import instead of MCP for simplicity
        from fabric_rti_mcp.eventstream.eventstream_service import eventstream_list
        
        result = eventstream_list(workspace_id, auth_token)
        print("\n✅ Results:")
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"❌ Error: {e}")

async def query_kusto():
    """Execute a Kusto query"""
    print("\n🔍 Query Kusto")
    cluster_uri = input("Enter cluster URI: ").strip()
    query = input("Enter KQL query: ").strip()
    database = input("Enter database (optional): ").strip() or None
    
    try:
        from fabric_rti_mcp.kusto.kusto_service import kusto_query
        
        result = kusto_query(query, cluster_uri, database)
        print("\n✅ Results:")
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"❌ Error: {e}")

async def list_kusto_databases():
    """List databases in a Kusto cluster"""
    print("\n📊 List Kusto Databases")
    cluster_uri = input("Enter cluster URI: ").strip()
    
    try:
        from fabric_rti_mcp.kusto.kusto_service import kusto_list_databases
        
        result = kusto_list_databases(cluster_uri)
        print("\n✅ Results:")
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"❌ Error: {e}")

async def get_eventstream_definition():
    """Get eventstream definition"""
    print("\n📝 Get Eventstream Definition")
    workspace_id = input("Enter workspace ID: ").strip()
    item_id = input("Enter eventstream item ID: ").strip()
    auth_token = input("Enter auth token (Bearer xxx): ").strip()
    
    if not auth_token.startswith("Bearer "):
        auth_token = f"Bearer {auth_token}"
    
    try:
        from fabric_rti_mcp.eventstream.eventstream_service import eventstream_get_definition
        
        result = eventstream_get_definition(workspace_id, item_id, auth_token)
        print("\n✅ Results:")
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"❌ Error: {e}")

async def process_prompt(prompt: str):
    """Process natural language prompts and execute appropriate operations"""
    prompt_lower = prompt.lower()
    
    try:
        # Parse eventstream operations
        if "eventstream" in prompt_lower and "list" in prompt_lower:
            await parse_and_list_eventstreams(prompt)
        elif "eventstream" in prompt_lower and ("get" in prompt_lower or "definition" in prompt_lower):
            await parse_and_get_eventstream_definition(prompt)
        
        # Parse kusto operations
        elif "kusto" in prompt_lower and "query" in prompt_lower:
            await parse_and_query_kusto(prompt)
        elif "kusto" in prompt_lower and ("database" in prompt_lower or "list" in prompt_lower):
            await parse_and_list_kusto_databases(prompt)
        elif "cluster" in prompt_lower and "query" in prompt_lower:
            await parse_and_query_kusto(prompt)
        elif "cluster" in prompt_lower and ("database" in prompt_lower or "list" in prompt_lower):
            await parse_and_list_kusto_databases(prompt)
        
        else:
            print("❓ I didn't understand that prompt. Here are some examples:")
            print("   • 'list eventstreams in workspace abc-123 with token xyz'")
            print("   • 'get eventstream definition for item def-456 in workspace abc-123 with token xyz'")
            print("   • 'query kusto cluster https://example.kusto.windows.net: MyTable | take 10'")
            print("   • 'list databases in cluster https://example.kusto.windows.net'")
            
    except Exception as e:
        print(f"❌ Error processing prompt: {e}")


async def parse_and_list_eventstreams(prompt: str):
    """Parse prompt for eventstream listing"""
    import re
    
    # Extract workspace ID (UUID pattern)
    workspace_match = re.search(r'workspace\s+([a-f0-9\-]{36}|[\w\-]+)', prompt, re.IGNORECASE)
    if not workspace_match:
        print("❌ Could not find workspace ID in prompt. Use format: 'workspace abc-123'")
        return
    
    workspace_id = workspace_match.group(1)
    
    # Check if user wants interactive auth
    if "interactive" in prompt.lower() or "auth" in prompt.lower():
        print(f"📋 Listing eventstreams in workspace: {workspace_id} (with interactive auth)")
        auth_token = await get_interactive_fabric_token()
        if not auth_token:
            print("❌ Authentication failed, cannot proceed")
            return
    else:
        # Extract token
        token_match = re.search(r'(?:token|bearer)\s+(\S+)', prompt, re.IGNORECASE)
        if not token_match:
            print("❌ Could not find token in prompt. Use format: 'token xyz' or 'bearer xyz'")
            print("💡 Or add 'with interactive auth' to use browser authentication")
            return
        
        auth_token = token_match.group(1)
        if not auth_token.startswith("Bearer "):
            auth_token = f"Bearer {auth_token}"
        
        print(f"📋 Listing eventstreams in workspace: {workspace_id}")
    
    try:
        from fabric_rti_mcp.eventstream.eventstream_service import eventstream_list
        result = eventstream_list(workspace_id, auth_token)
        print("\n✅ Results:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"❌ Error: {e}")


async def parse_and_get_eventstream_definition(prompt: str):
    """Parse prompt for eventstream definition"""
    import re
    
    # Extract workspace ID
    workspace_match = re.search(r'workspace\s+([a-f0-9\-]{36}|[\w\-]+)', prompt, re.IGNORECASE)
    if not workspace_match:
        print("❌ Could not find workspace ID in prompt")
        return
    
    workspace_id = workspace_match.group(1)
    
    # Extract item ID
    item_match = re.search(r'(?:item|eventstream)\s+([a-f0-9\-]{36}|[\w\-]+)', prompt, re.IGNORECASE)
    if not item_match:
        print("❌ Could not find item ID in prompt. Use format: 'item def-456'")
        return
    
    item_id = item_match.group(1)
    
    # Extract token
    token_match = re.search(r'(?:token|bearer)\s+(\S+)', prompt, re.IGNORECASE)
    if not token_match:
        print("❌ Could not find token in prompt")
        return
    
    auth_token = token_match.group(1)
    if not auth_token.startswith("Bearer "):
        auth_token = f"Bearer {auth_token}"
    
    print(f"📝 Getting eventstream definition for item: {item_id}")
    
    try:
        from fabric_rti_mcp.eventstream.eventstream_service import eventstream_get_definition
        result = eventstream_get_definition(workspace_id, item_id, auth_token)
        print("\n✅ Results:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"❌ Error: {e}")


async def parse_and_query_kusto(prompt: str):
    """Parse prompt for kusto query"""
    import re
    
    # Extract cluster URI
    cluster_match = re.search(r'cluster\s+(https?://[\w\.-]+)', prompt, re.IGNORECASE)
    if not cluster_match:
        print("❌ Could not find cluster URI in prompt. Use format: 'cluster https://example.kusto.windows.net'")
        return
    
    cluster_uri = cluster_match.group(1)
    
    # Extract query - look for text after colon or quotes
    query_patterns = [
        r':\s*(.+)$',  # After colon
        r"'([^']+)'",  # Single quotes
        r'"([^"]+)"',  # Double quotes
        r'query\s+(.+?)(?:\s+(?:database|db)\s+|$)',  # After 'query' keyword
    ]
    
    query = None
    for pattern in query_patterns:
        query_match = re.search(pattern, prompt, re.IGNORECASE | re.DOTALL)
        if query_match:
            query = query_match.group(1).strip()
            break
    
    if not query:
        print("❌ Could not find query in prompt. Use format: 'query: MyTable | take 10' or 'query \"MyTable | take 10\"'")
        return
    
    # Extract database (optional)
    db_match = re.search(r'(?:database|db)\s+(\w+)', prompt, re.IGNORECASE)
    database = db_match.group(1) if db_match else None
    
    print(f"🔍 Querying cluster: {cluster_uri}")
    print(f"📝 Query: {query}")
    if database:
        print(f"🗃️  Database: {database}")
    
    try:
        from fabric_rti_mcp.kusto.kusto_service import kusto_query
        result = kusto_query(query, cluster_uri, database)
        print("\n✅ Results:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"❌ Error: {e}")


async def parse_and_list_kusto_databases(prompt: str):
    """Parse prompt for kusto database listing"""
    import re
    
    # Extract cluster URI
    cluster_match = re.search(r'cluster\s+(https?://[\w\.-]+)', prompt, re.IGNORECASE)
    if not cluster_match:
        print("❌ Could not find cluster URI in prompt. Use format: 'cluster https://example.kusto.windows.net'")
        return
    
    cluster_uri = cluster_match.group(1)
    
    print(f"📊 Listing databases in cluster: {cluster_uri}")
    
    try:
        from fabric_rti_mcp.kusto.kusto_service import kusto_list_databases
        result = kusto_list_databases(cluster_uri)
        print("\n✅ Results:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"❌ Error: {e}")

def show_prompt_examples():
    """Show example prompts"""
    print("\n💡 Example Prompts:")
    print("=" * 50)
    print("\n🔸 Eventstream Operations:")
    print("   list eventstreams in workspace 12345678-1234-1234-1234-123456789012 with token abc123")
    print("   list eventstreams in workspace 12345678-1234-1234-1234-123456789012 with interactive auth")
    print("   get eventstream definition for item def456 in workspace 12345678-1234-1234-1234-123456789012 with bearer xyz789")
    
    print("\n🔸 Kusto Operations:")
    print("   query kusto cluster https://mycluster.kusto.windows.net: MyTable | take 10")
    print("   query cluster https://mycluster.kusto.windows.net: 'StormEvents | where State == \"TEXAS\" | take 5'")
    print("   list databases in cluster https://mycluster.kusto.windows.net")
    print("   query cluster https://mycluster.kusto.windows.net database SampleDB: MyTable | summarize count() by Category")
    
    print("\n🔸 Configuration Operations:")
    print("   get fabric api base url")
    print("   set fabric api base url https://custom.fabric.api.com/v1")
    print("   reset fabric api base url")
    
    print("\n🔸 Command Line Usage:")
    print('   python vscode_mcp_client.py "list eventstreams in workspace abc-123 with token xyz"')
    print('   python vscode_mcp_client.py "list eventstreams in workspace abc-123 with interactive auth"')
    print('   python vscode_mcp_client.py "query cluster https://example.kusto.windows.net: MyTable | take 10"')
    print('   python vscode_mcp_client.py "get fabric api base url"')
    
    print("\n🔸 Interactive Authentication:")
    print("   • Uses Azure Interactive Browser Credential")
    print("   • Opens browser for Microsoft sign-in")
    print("   • Automatically gets Microsoft Fabric API token")
    print("   • No need to manually copy/paste tokens!")
    
    print("\n🔸 API Configuration:")
    print("   • Default API: https://api.fabric.microsoft.com/v1")
    print("   • Can be changed to custom endpoints")
    print("   • Useful for testing or custom Fabric instances")
    print("   • Configuration persists for the session")

async def test_prompt_parsing():
    """Test prompt parsing without making actual API calls"""
    test_prompts = [
        "list eventstreams in workspace 12345678-1234-1234-1234-123456789012 with token abc123",
        "query cluster https://example.kusto.windows.net: MyTable | take 10",
        "list databases in cluster https://example.kusto.windows.net"
    ]
    
    print("🧪 Testing Prompt Parsing (No API Calls)")
    print("=" * 50)
    
    for prompt in test_prompts:
        print(f"\n📝 Testing: {prompt}")
        await process_prompt_dry_run(prompt)

async def process_prompt_dry_run(prompt: str):
    """Process prompts without making API calls (for testing)"""
    prompt_lower = prompt.lower()
    
    # Parse eventstream operations
    if "eventstream" in prompt_lower and "list" in prompt_lower:
        await parse_and_list_eventstreams_dry_run(prompt)
    elif "cluster" in prompt_lower and "query" in prompt_lower:
        await parse_and_query_kusto_dry_run(prompt)
    elif "cluster" in prompt_lower and ("database" in prompt_lower or "list" in prompt_lower):
        await parse_and_list_kusto_databases_dry_run(prompt)

async def parse_and_list_eventstreams_dry_run(prompt: str):
    """Parse eventstream listing prompt without API call"""
    import re
    
    workspace_match = re.search(r'workspace\s+([a-f0-9\-]{36}|[\w\-]+)', prompt, re.IGNORECASE)
    token_match = re.search(r'(?:token|bearer)\s+(\S+)', prompt, re.IGNORECASE)
    
    if workspace_match and token_match:
        workspace_id = workspace_match.group(1)
        auth_token = token_match.group(1)
        print(f"   ✅ Would list eventstreams in workspace: {workspace_id}")
        print(f"   ✅ Using token: {auth_token[:10]}...")
    else:
        print("   ❌ Could not parse workspace ID or token")

async def parse_and_query_kusto_dry_run(prompt: str):
    """Parse kusto query prompt without API call"""
    import re
    
    cluster_match = re.search(r'cluster\s+(https?://[\w\.-]+)', prompt, re.IGNORECASE)
    query_match = re.search(r':\s*(.+)$', prompt, re.IGNORECASE | re.DOTALL)
    
    if cluster_match and query_match:
        cluster_uri = cluster_match.group(1)
        query = query_match.group(1).strip()
        print(f"   ✅ Would query cluster: {cluster_uri}")
        print(f"   ✅ Query: {query}")
    else:
        print("   ❌ Could not parse cluster URI or query")

async def parse_and_list_kusto_databases_dry_run(prompt: str):
    """Parse kusto database listing prompt without API call"""
    import re
    
    cluster_match = re.search(r'cluster\s+(https?://[\w\.-]+)', prompt, re.IGNORECASE)
    
    if cluster_match:
        cluster_uri = cluster_match.group(1)
        print(f"   ✅ Would list databases in cluster: {cluster_uri}")
    else:
        print("   ❌ Could not parse cluster URI")

async def get_interactive_fabric_token():
    """Get a Microsoft Fabric token using interactive browser authentication"""
    try:
        # Import the auth functions from the eventstream client tools
        from tools.eventstream_client.auth import get_fabric_token
        
        print("🔐 Starting interactive authentication...")
        print("   A browser window will open for you to sign in to Microsoft Fabric")
        
        token = get_fabric_token()
        
        if token:
            print("✅ Authentication successful!")
            return f"Bearer {token}"
        else:
            print("❌ Authentication failed")
            return None
            
    except ImportError:
        print("❌ Authentication module not found. Make sure the auth.py file is available in tools/eventstream_client/")
        return None
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None


async def list_eventstreams_with_auth():
    """List eventstreams with interactive authentication"""
    print("\n📋 List Eventstreams (with interactive auth)")
    
    # Get workspace ID
    workspace_id = input("Enter workspace ID: ").strip()
    
    # Offer interactive auth option
    use_interactive = input("Use interactive authentication? (y/n): ").strip().lower()
    
    if use_interactive in ['y', 'yes']:
        auth_token = await get_interactive_fabric_token()
        if not auth_token:
            print("❌ Authentication failed, cannot proceed")
            return
    else:
        auth_token = input("Enter auth token (Bearer xxx): ").strip()
        if not auth_token.startswith("Bearer "):
            auth_token = f"Bearer {auth_token}"
    
    try:
        from fabric_rti_mcp.eventstream.eventstream_service import eventstream_list
        
        result = eventstream_list(workspace_id, auth_token)
        print("\n✅ Results:")
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"❌ Error: {e}")


async def get_eventstream_definition_with_auth():
    """Get eventstream definition with interactive authentication"""
    print("\n📝 Get Eventstream Definition (with interactive auth)")
    
    # Get workspace and item IDs
    workspace_id = input("Enter workspace ID: ").strip()
    item_id = input("Enter eventstream item ID: ").strip()
    
    # Offer interactive auth option
    use_interactive = input("Use interactive authentication? (y/n): ").strip().lower()
    
    if use_interactive in ['y', 'yes']:
        auth_token = await get_interactive_fabric_token()
        if not auth_token:
            print("❌ Authentication failed, cannot proceed")
            return
    else:
        auth_token = input("Enter auth token (Bearer xxx): ").strip()
        if not auth_token.startswith("Bearer "):
            auth_token = f"Bearer {auth_token}"
    
    try:
        from fabric_rti_mcp.eventstream.eventstream_service import eventstream_get_definition
        
        result = eventstream_get_definition(workspace_id, item_id, auth_token)
        print("\n✅ Results:")
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"❌ Error: {e}")


async def get_fabric_api_base():
    """Get the current Fabric API base URL"""
    print("\n🔧 Get Fabric API Base URL")
    
    try:
        from fabric_rti_mcp.eventstream.eventstream_service import get_fabric_api_base
        
        result = get_fabric_api_base()
        print(f"\n✅ Current Fabric API Base URL: {result}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


async def set_fabric_api_base():
    """Set a custom Fabric API base URL"""
    print("\n🔧 Set Fabric API Base URL")
    print("💡 Default: https://api.fabric.microsoft.com/v1")
    
    api_base_url = input("Enter new API base URL: ").strip()
    
    if not api_base_url:
        print("❌ API base URL cannot be empty")
        return
    
    try:
        from fabric_rti_mcp.eventstream.eventstream_service import set_fabric_api_base
        
        result = set_fabric_api_base(api_base_url)
        print(f"\n✅ Fabric API Base URL updated to: {result}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


async def reset_fabric_api_base():
    """Reset Fabric API base URL to default"""
    print("\n🔧 Reset Fabric API Base URL")
    
    try:
        from fabric_rti_mcp.eventstream.eventstream_service import reset_fabric_api_base
        
        result = reset_fabric_api_base()
        print(f"\n✅ Fabric API Base URL reset to default: {result}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user. Goodbye!")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
