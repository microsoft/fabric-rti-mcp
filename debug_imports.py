#!/usr/bin/env python3
"""Minimal test to isolate the eventstream_builder_service import issue."""


def test_step_by_step():
    """Test imports step by step to find where it fails."""

    print("Step 1: Testing basic imports...")
    try:
        import json
        import uuid
        from datetime import datetime
        from typing import Any, Dict, List, Optional, Union

        print("✓ Basic imports successful")
    except Exception as e:
        print(f"✗ Basic imports failed: {e}")
        return False

    print("Step 2: Testing fabric_rti_mcp.common...")
    try:
        from fabric_rti_mcp.common import logger

        print("✓ Common module import successful")
    except Exception as e:
        print(f"✗ Common module import failed: {e}")
        return False

    print("Step 3: Testing eventstream_service import...")
    try:
        from fabric_rti_mcp.eventstream import eventstream_service

        print("✓ eventstream_service module import successful")
    except Exception as e:
        print(f"✗ eventstream_service module import failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    print("Step 4: Testing specific function import...")
    try:
        from fabric_rti_mcp.eventstream.eventstream_service import eventstream_create

        print("✓ eventstream_create function import successful")
    except Exception as e:
        print(f"✗ eventstream_create function import failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    print("Step 5: Testing eventstream_builder_service import...")
    try:
        from fabric_rti_mcp.eventstream import eventstream_builder_service

        print("✓ eventstream_builder_service module import successful")
    except Exception as e:
        print(f"✗ eventstream_builder_service module import failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    print("Step 6: Testing specific function access...")
    try:
        func = eventstream_builder_service.eventstream_start_definition
        print(f"✓ eventstream_start_definition function found: {func}")
        return True
    except Exception as e:
        print(f"✗ eventstream_start_definition function not found: {e}")
        print(f"Available attributes: {dir(eventstream_builder_service)}")
        return False


if __name__ == "__main__":
    print("=== Eventstream Builder Service Import Test ===")
    success = test_step_by_step()
    if success:
        print("\n✅ All imports successful!")
    else:
        print("\n❌ Import test failed!")
