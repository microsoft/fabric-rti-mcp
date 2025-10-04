"""
Integrated from external MCP server: fabric_eventstream_mcp\test_integration.py
Adapted for fabric-rti-mcp
"""

#!/usr/bin/env python3
"""
Comprehensive integration test for Fabric Eventstream MCP Server and AI Agent
"""
import sys
import os
import json
import requests
import time
from typing import Dict, Any

# Add current directory to path
sys.path.append('.')
from ai_agent_openai import FabricEventstreamAgent

# Test workspace ID
WORKSPACE_ID = '7cb96f67-9cdb-4398-ae4e-bddb6f69b08f'
MCP_SERVER_URL = 'http://localhost:8000'

class IntegrationTester:
    def __init__(self):
        self.agent = FabricEventstreamAgent(demo_mode=True)
        self.test_results = []
    
    def log_test(self, test_name: str, success: bool, message: str = ""):
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if message:
            print(f"   {message}")
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message
        })
    
    def test_mcp_server_health(self):
        """Test if MCP server is responsive"""
        try:
            response = requests.get(f"{MCP_SERVER_URL}/docs", timeout=5)
            success = response.status_code == 200
            message = f"Server responded with status {response.status_code}"
            self.log_test("MCP Server Health Check", success, message)
            return success
        except Exception as e:
            self.log_test("MCP Server Health Check", False, f"Connection failed: {e}")
            return False
    
    def test_direct_api_call(self):
        """Test direct API call to MCP server"""
        try:
            response = requests.get(f"{MCP_SERVER_URL}/eventstream/{WORKSPACE_ID}", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                items = data.get('value', [])
                eventstreams = [item for item in items if item.get('type') == 'Eventstream']
                message = f"Found {len(items)} total items, {len(eventstreams)} Eventstreams"
            else:
                message = f"API call failed with status {response.status_code}: {response.text}"
            
            self.log_test("Direct API Call", success, message)
            return success, data if success else None
        except Exception as e:
            self.log_test("Direct API Call", False, f"Exception: {e}")
            return False, None
    
    def test_agent_mcp_integration(self):
        """Test agent's MCP tool integration"""
        try:
            result = self.agent._call_mcp_tool('list_eventstreams', {'workspace_id': WORKSPACE_ID})
            success = 'value' in result and not 'error' in result
            
            if success:
                items = result['value']
                eventstreams = [item for item in items if item.get('type') == 'Eventstream']
                message = f"Agent retrieved {len(items)} items, {len(eventstreams)} Eventstreams"
            else:
                message = f"Agent call failed: {result.get('error', 'Unknown error')}"
            
            self.log_test("Agent MCP Integration", success, message)
            return success, result if success else None
        except Exception as e:
            self.log_test("Agent MCP Integration", False, f"Exception: {e}")
            return False, None
    
    def test_agent_conversation(self):
        """Test agent conversation capabilities"""
        try:
            # Test workspace listing
            message1 = f"List all eventstreams in workspace {WORKSPACE_ID}"
            response1 = self.agent.chat(message1)
            success1 = WORKSPACE_ID in response1 and 'Eventstream' in response1
            
            # Test general help
            message2 = "What can you help me with?"
            response2 = self.agent.chat(message2)
            success2 = 'Eventstream' in response2 and 'help' in response2.lower()
            
            success = success1 and success2
            message = f"Conversation tests: List={success1}, Help={success2}"
            
            self.log_test("Agent Conversation", success, message)
            return success
        except Exception as e:
            self.log_test("Agent Conversation", False, f"Exception: {e}")
            return False
    
    def test_eventstream_details(self, eventstream_data):
        """Test getting specific Eventstream details"""
        if not eventstream_data or 'value' not in eventstream_data:
            self.log_test("Eventstream Details", False, "No data available")
            return False
        
        eventstreams = [item for item in eventstream_data['value'] if item.get('type') == 'Eventstream']
        if not eventstreams:
            self.log_test("Eventstream Details", False, "No Eventstreams found")
            return False
        
        try:
            first_eventstream = eventstreams[0]
            item_id = first_eventstream['id']
            
            result = self.agent._call_mcp_tool('get_eventstream', {
                'workspace_id': WORKSPACE_ID,
                'item_id': item_id
            })
            
            success = 'id' in result and result['id'] == item_id
            message = f"Retrieved details for '{first_eventstream.get('displayName', 'Unknown')}'"
            
            self.log_test("Eventstream Details", success, message)
            return success
        except Exception as e:
            self.log_test("Eventstream Details", False, f"Exception: {e}")
            return False
    
    def run_all_tests(self):
        """Run comprehensive integration tests"""
        print("🧪 Fabric Eventstream MCP Integration Tests")
        print("=" * 60)
        print(f"Testing workspace: {WORKSPACE_ID}")
        print()
        
        # Test 1: MCP Server Health
        server_healthy = self.test_mcp_server_health()
        
        # Test 2: Direct API Call
        api_success, api_data = self.test_direct_api_call()
        
        # Test 3: Agent MCP Integration
        agent_success, agent_data = self.test_agent_mcp_integration()
        
        # Test 4: Agent Conversation
        conversation_success = self.test_agent_conversation()
        
        # Test 5: Eventstream Details (if we have data)
        details_success = False
        if api_data:
            details_success = self.test_eventstream_details(api_data)
        
        # Summary
        print()
        print("📊 Test Summary")
        print("-" * 30)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}")
        
        print()
        print(f"Overall Result: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 All tests passed! MCP/Agent integration is fully functional.")
        elif passed_tests >= total_tests * 0.8:
            print("⚠️  Most tests passed. Minor issues may exist.")
        else:
            print("🚨 Multiple test failures. Integration needs attention.")
        
        return passed_tests == total_tests

def main():
    """Main test runner"""
    tester = IntegrationTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
