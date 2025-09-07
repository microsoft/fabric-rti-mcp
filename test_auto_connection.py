#!/usr/bin/env python3
"""
Quick test to verify auto-connection logic works as expected
"""

def test_auto_connection_logic():
    """Test the auto-connection logic in isolation"""
    
    # Simulate the condition from our function
    input_nodes = []  # Empty list passed from MCP
    stream_names = ["TestFinalFix-stream"]  # One default stream exists
    operator_names = []  # No operators
    
    print(f"Initial state:")
    print(f"  input_nodes: {input_nodes}")
    print(f"  stream_names: {stream_names}")
    print(f"  operator_names: {operator_names}")
    print()
    
    # Test the auto-connection logic
    if not input_nodes:  # This handles both None and empty list []
        print("Auto-connection check triggered (input_nodes is falsy)")
        
        # Auto-connect logic: if only one stream and no operators, connect to that stream
        if len(stream_names) == 1 and len(operator_names) == 0:
            input_nodes = stream_names.copy()  # Use copy to avoid reference issues
            print(f"Auto-connecting to default stream '{stream_names[0]}'")
        else:
            print(f"Multiple streams/operators exist - auto-connection not allowed")
            
    print(f"Final input_nodes: {input_nodes}")
    
    # Test the inputNodes creation
    final_input_nodes = [{"name": node} for node in input_nodes]
    print(f"Final inputNodes structure: {final_input_nodes}")
    
    return final_input_nodes

if __name__ == "__main__":
    print("Testing auto-connection logic...")
    result = test_auto_connection_logic()
    print(f"\nExpected result: [{'name': 'TestFinalFix-stream'}]")
    print(f"Actual result: {result}")
    print(f"Test {'PASSED' if result == [{'name': 'TestFinalFix-stream'}] else 'FAILED'}!")
