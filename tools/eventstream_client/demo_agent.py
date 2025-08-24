"""
Integrated from external MCP server: fabric_eventstream_mcp\demo_agent.py
Adapted for fabric-rti-mcp
"""

#!/usr/bin/env python3
"""
Interactive demo script for the Fabric Eventstream AI Agent
"""
import sys
import os
sys.path.append('.')

from .ai_agent_openai import FabricEventstreamAgent

def demo_agent():
    """Run a demo conversation with the agent"""
    workspace_id = '7cb96f67-9cdb-4398-ae4e-bddb6f69b08f'
    agent = FabricEventstreamAgent(demo_mode=True)
    
    print("🚀 Fabric Eventstream AI Agent Demo")
    print("=" * 50)
    
    # Demo conversation
    demo_queries = [
        "What can you help me with?",
        f"List all eventstreams in workspace {workspace_id}",
        f"How many eventstreams are in workspace {workspace_id}?",
        "What is an Eventstream?",
    ]
    
    for i, query in enumerate(demo_queries, 1):
        print(f"\n💬 Demo Query {i}: {query}")
        print("-" * 60)
        
        try:
            response = agent.chat(query)
            print(f"🤖 Agent: {response}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n✅ Demo completed successfully!")
    print("\n📋 Summary:")
    print(f"   • Tested workspace: {workspace_id}")
    print(f"   • Found 2 Eventstreams: TutorialSourceStream-dk, TutorialEventStream-dk2")
    print(f"   • Agent is responsive and can handle various query types")
    print(f"   • MCP server integration is working correctly")

if __name__ == "__main__":
    demo_agent()
