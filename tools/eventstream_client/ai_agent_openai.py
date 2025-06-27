"""
Integrated from external MCP server: fabric_eventstream_mcp\ai_agent_openai.py
Adapted for fabric-rti-mcp
"""

"""
AI Agent for Microsoft Fabric Eventstream using MCP Server
This agent can help users manage Eventstreams through natural language interactions.
"""
import os
import json
import requests
from openai import AzureOpenAI
from typing import Dict, Any, List, Optional
import sys
from .config import config

class FabricEventstreamAgent:
    """
    AI Agent for Microsoft Fabric Eventstream management using MCP Server.
    """
    
    def __init__(self, demo_mode: bool = False):
        """Initialize the AI agent with OpenAI client and MCP tools.
        
        Args:
            demo_mode: If True, runs in demo mode without requiring Azure OpenAI credentials
        """
        self.demo_mode = demo_mode
        
        if not demo_mode:
            self.client = AzureOpenAI(
                api_key=config.AZURE_OPENAI_API_KEY,
                api_version=config.AZURE_OPENAI_API_VERSION,
                azure_endpoint=config.AZURE_OPENAI_ENDPOINT
            )
        else:
            self.client = None
            print("🔧 Running in demo mode (Azure OpenAI not required)")
        
        # Initialize conversation history
        self.conversation_history = [
            {
                "role": "system",
                "content": """You are a helpful AI assistant specialized in Microsoft Fabric Eventstream management. 
                You can help users create, manage, and monitor Eventstreams using the Microsoft Fabric API through an MCP server.
                
                Available capabilities:
                - List Eventstreams in a workspace
                - Get details of specific Eventstreams
                - Create new Eventstreams
                - Update existing Eventstreams
                - Delete Eventstreams
                
                When users ask about Eventstreams, use the appropriate tools to help them. 
                Always explain what you're doing and provide helpful context about the results.
                
                The MCP server handles authentication automatically, so you don't need to worry about tokens.
                """
            }
        ]
        
        # Get authentication token automatically
        self.auth_token = self._get_auth_token()
        
        # Define MCP tools for OpenAI function calling
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "list_eventstreams",
                    "description": "List all Eventstream items in a Microsoft Fabric workspace.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "workspace_id": {
                                "type": "string",
                                "description": "The workspace ID (UUID) where to list Eventstreams"
                            }
                        },
                        "required": ["workspace_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_eventstream",
                    "description": "Get details of a specific Eventstream item by workspace and item ID.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "workspace_id": {
                                "type": "string",
                                "description": "The workspace ID (UUID)"
                            },
                            "item_id": {
                                "type": "string",
                                "description": "The Eventstream item ID (UUID)"
                            }
                        },
                        "required": ["workspace_id", "item_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_eventstream",
                    "description": "Create a new Eventstream item in Microsoft Fabric.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "workspaceId": {
                                "type": "string",
                                "description": "The workspace ID (UUID) where to create the Eventstream"
                            },
                            "definition": {
                                "type": "object",
                                "description": "The Eventstream definition with sources, destinations, operators, streams",
                                "properties": {
                                    "sources": {
                                        "type": "array", 
                                        "description": "List of data sources",
                                        "items": {"type": "object"}
                                    },
                                    "destinations": {
                                        "type": "array", 
                                        "description": "List of data destinations",
                                        "items": {"type": "object"}
                                    },
                                    "operators": {
                                        "type": "array", 
                                        "description": "List of stream operators",
                                        "items": {"type": "object"}
                                    },
                                    "streams": {
                                        "type": "array", 
                                        "description": "List of data streams",
                                        "items": {"type": "object"}
                                    },
                                    "compatibilityLevel": {"type": "string", "default": "1.0"}
                                },
                                "required": ["sources", "destinations", "operators", "streams"]
                            }
                        },
                        "required": ["workspaceId", "definition"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_eventstream",
                    "description": "Delete an Eventstream item from Microsoft Fabric.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "workspace_id": {
                                "type": "string",
                                "description": "The workspace ID (UUID)"
                            },
                            "item_id": {
                                "type": "string",
                                "description": "The Eventstream item ID (UUID) to delete"
                            }
                        },
                        "required": ["workspace_id", "item_id"]
                    }
                }
            }
        ]
    
    def _get_auth_token(self) -> str:
        """Get authentication token from MCP server."""
        try:
            response = requests.post(f"{config.MCP_SERVER_URL}/auth/get-token")
            if response.status_code == 200:
                data = response.json()
                return f"Bearer {data['access_token']}"
            else:
                print(f"Warning: Could not get auth token. Status: {response.status_code}")
                return None
        except Exception as e:
            print(f"Warning: Could not connect to MCP server for authentication: {e}")
            return None
    
    def _call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call the MCP server with the specified tool and arguments."""
        headers = {}
        if self.auth_token:
            headers["Authorization"] = self.auth_token
        
        try:
            if tool_name == "list_eventstreams":
                workspace_id = arguments["workspace_id"]
                response = requests.get(
                    f"{config.MCP_SERVER_URL}/eventstream/{workspace_id}",
                    headers=headers
                )
            
            elif tool_name == "get_eventstream":
                workspace_id = arguments["workspace_id"]
                item_id = arguments["item_id"]
                response = requests.get(
                    f"{config.MCP_SERVER_URL}/eventstream/{workspace_id}/{item_id}",
                    headers=headers
                )
            
            elif tool_name == "create_eventstream":
                response = requests.post(
                    f"{config.MCP_SERVER_URL}/eventstream/create",
                    json=arguments,
                    headers={**headers, "Content-Type": "application/json"}
                )
            
            elif tool_name == "delete_eventstream":
                workspace_id = arguments["workspace_id"]
                item_id = arguments["item_id"]
                response = requests.delete(
                    f"{config.MCP_SERVER_URL}/eventstream/{workspace_id}/{item_id}",
                    headers=headers
                )
            
            else:
                return {"error": f"Unknown tool: {tool_name}"}
            
            # Parse response
            if response.status_code in [200, 201, 204]:
                if response.content:
                    return response.json()
                else:
                    return {"success": True, "message": "Operation completed successfully"}
            else:
                return {
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "status_code": response.status_code
                }
                
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON response: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
    
    def _simulate_ai_response(self, user_message: str) -> str:
        """Simulate AI responses for demo mode."""
        user_lower = user_message.lower()
        
        # Handle different types of requests
        if "what" in user_lower and ("eventstream" in user_lower or "help" in user_lower):
            return """I'm an AI assistant specialized in Microsoft Fabric Eventstream management! I can help you with:

🔹 **List Eventstreams** - Show all Eventstreams in a workspace
🔹 **Get Eventstream Details** - View specific Eventstream information
🔹 **Create Eventstreams** - Set up new data streaming pipelines
🔹 **Delete Eventstreams** - Remove Eventstreams when no longer needed

I work through the MCP server which handles authentication with Microsoft Fabric automatically. Just tell me what you'd like to do with your Eventstreams!

*Note: Currently running in demo mode. For full functionality, configure Azure OpenAI credentials.*"""

        elif "list" in user_lower and "eventstream" in user_lower:
            # Extract workspace ID if present
            import re
            workspace_match = re.search(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', user_message)
            
            if workspace_match:
                workspace_id = workspace_match.group(0)
                # Call the MCP tool to actually list Eventstreams
                result = self._call_mcp_tool("list_eventstreams", {"workspace_id": workspace_id})
                
                if "error" in result:
                    return f"I tried to list Eventstreams in workspace {workspace_id}, but encountered an error: {result['error']}"
                else:
                    return f"Here are the Eventstreams in workspace {workspace_id}:\n\n{result}"
            else:
                return "I'd be happy to list Eventstreams! Please provide a workspace ID (UUID format) so I can fetch the information."

        elif "create" in user_lower and "eventstream" in user_lower:
            return """I can help you create an Eventstream! To create one, I'll need:

1. **Workspace ID** - The UUID of your Fabric workspace
2. **Eventstream Configuration** - Including:
   - Data sources (where data comes from)
   - Destinations (where data goes)
   - Operators (any transformations)
   - Streams (data flow paths)

For example, for IoT data processing, I might create an Eventstream with:
- Source: IoT Hub or Event Hub
- Operators: Filter, Transform, Aggregate
- Destination: Lakehouse, KQL Database, or another Event Hub

Please provide the workspace ID and describe what kind of data processing you need!

*Note: In demo mode - would normally create via MCP server.*"""

        elif "get" in user_lower or "detail" in user_lower or "show" in user_lower:
            # Extract IDs if present
            import re
            ids = re.findall(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', user_message)
            
            if len(ids) >= 2:
                workspace_id, item_id = ids[0], ids[1]
                # Call the MCP tool to get Eventstream details
                result = self._call_mcp_tool("get_eventstream", {"workspace_id": workspace_id, "item_id": item_id})
                
                if "error" in result:
                    return f"I tried to get details for Eventstream {item_id} in workspace {workspace_id}, but encountered an error: {result['error']}"
                else:
                    return f"Here are the details for Eventstream {item_id}:\n\n{result}"
            else:
                return "To get Eventstream details, please provide both the workspace ID and Eventstream item ID (both in UUID format)."

        else:
            return f"""I received your message: "{user_message}"

I'm specialized in Microsoft Fabric Eventstream management. You can ask me to:
- List Eventstreams in a workspace
- Get details of a specific Eventstream  
- Create new Eventstreams
- Delete Eventstreams

Try asking something like:
- "List all Eventstreams in workspace [workspace-id]"
- "What can you help me with?"
- "Create an Eventstream for IoT data"

*Running in demo mode - configure Azure OpenAI for full AI capabilities.*"""

    def chat(self, user_message: str) -> str:
        """
        Process a user message and return the assistant's response.
        
        Args:
            user_message: The user's input message
            
        Returns:
            The assistant's response as a string
        """
        # Add user message to conversation history
        self.conversation_history.append({"role": "user", "content": user_message})
        
        # If in demo mode, use simulated responses
        if self.demo_mode:
            response = self._simulate_ai_response(user_message)
            self.conversation_history.append({"role": "assistant", "content": response})
            return response
        
        try:
            if self.demo_mode:
                # Simulate a demo response
                demo_response = f"Demo response to: {user_message}"
                self.conversation_history.append({"role": "assistant", "content": demo_response})
                return demo_response
            
            # Call OpenAI with tools
            response = self.client.chat.completions.create(
                model=config.AZURE_OPENAI_DEPLOYMENT,
                messages=self.conversation_history,
                tools=self.tools,
                tool_choice="auto"
            )
            
            message = response.choices[0].message
            
            # Handle function calls
            if message.tool_calls:
                # Add assistant message with tool calls to history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": tool_call.type,
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments
                            }
                        }
                        for tool_call in message.tool_calls
                    ]
                })
                
                # Execute tool calls
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        arguments = {}
                    
                    # Call the MCP server
                    tool_result = self._call_mcp_tool(tool_name, arguments)
                    
                    # Add tool result to conversation history
                    self.conversation_history.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(tool_result)
                    })
                
                # Get final response after tool execution
                final_response = self.client.chat.completions.create(
                    model=config.AZURE_OPENAI_DEPLOYMENT,
                    messages=self.conversation_history
                )
                
                final_message = final_response.choices[0].message.content
                self.conversation_history.append({"role": "assistant", "content": final_message})
                return final_message
                
            else:
                # No tool calls, just return the response
                self.conversation_history.append({"role": "assistant", "content": message.content})
                return message.content
                
        except Exception as e:
            error_msg = f"Sorry, I encountered an error: {str(e)}"
            self.conversation_history.append({"role": "assistant", "content": error_msg})
            return error_msg
    
    def start_conversation(self):
        """Start an interactive conversation with the AI agent."""
        print("🤖 Fabric Eventstream AI Agent")
        print("=" * 50)
        print("I can help you manage Microsoft Fabric Eventstreams!")
        print("Ask me to list, create, get details, or delete Eventstreams.")
        
        if self.demo_mode:
            print("🔧 Running in demo mode (limited functionality)")
        
        print("Type 'exit' to quit.\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print("👋 Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                # Get response from agent
                response = self.chat(user_input)
                print(f"🤖 Assistant: {response}\n")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}\n")

def main():
    """Main function to run the AI agent."""
    # Check if required environment variables are set
    demo_mode = config.is_demo_mode()
    
    if demo_mode:
        print("⚠️  Azure OpenAI credentials not configured")
        print("Running in demo mode with simulated responses...")
    
    # Create and start the agent
    agent = FabricEventstreamAgent(demo_mode=demo_mode)
    agent.start_conversation()

if __name__ == "__main__":
    main()
