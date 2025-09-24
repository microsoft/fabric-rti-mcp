#!/usr/bin/env python3
"""Test each import step by step to find the hanging point."""

import sys


def test_import_chain():
    """Test the import chain step by step."""

    try:
        print("1. Testing basic imports...")
        import uuid
        from datetime import datetime
        from typing import Any, Dict, List, Optional

        print("   ✓ Basic imports OK")

        print("2. Testing fabric_rti_mcp.common...")
        from fabric_rti_mcp.common import logger

        print("   ✓ Common module OK")

        print("3. Testing other eventstream modules...")

        print("3a. Testing eventstream_connection...")
        from fabric_rti_mcp.eventstream import eventstream_connection

        print("   ✓ eventstream_connection OK")

        print("3b. Testing eventstream_service...")
        from fabric_rti_mcp.eventstream import eventstream_service

        print("   ✓ eventstream_service OK")

        print("4. Testing eventstream_builder_service directly...")
        # Let's try to import the file content step by step
        sys.path.insert(0, "fabric_rti_mcp/eventstream")

        print("4a. Trying direct import...")
        import eventstream_builder_service

        print("   ✓ Direct import OK")

        print("4b. Checking for function...")
        has_func = hasattr(eventstream_builder_service, "eventstream_start_definition")
        print(f"   Has function: {has_func}")

        if not has_func:
            print("   Available attributes:")
            for attr in dir(eventstream_builder_service):
                if not attr.startswith("_") and callable(getattr(eventstream_builder_service, attr)):
                    print(f"     - {attr}")

        return has_func

    except Exception as e:
        print(f"ERROR at step: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=== Import Chain Test ===")
    test_import_chain()
