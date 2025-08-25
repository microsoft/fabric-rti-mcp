#!/usr/bin/env python3
"""Simple test to check module loading issues."""

try:
    print("Step 1: Importing the module...")
    import fabric_rti_mcp.eventstream.eventstream_builder_service as ebs
    print("SUCCESS: Module imported")
    
    print("Step 2: Checking for function...")
    has_func = hasattr(ebs, 'eventstream_start_definition')
    print(f"Has eventstream_start_definition: {has_func}")
    
    if has_func:
        print("Step 3: Getting function...")
        func = getattr(ebs, 'eventstream_start_definition')
        print(f"Function: {func}")
        print("SUCCESS: Function found!")
    else:
        print("Step 3: Listing available attributes...")
        attrs = [attr for attr in dir(ebs) if not attr.startswith('_')]
        print(f"Available attributes: {attrs}")
        
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
