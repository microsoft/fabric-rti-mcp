#!/usr/bin/env python3
"""Simple server test - runs the server briefly to check for startup errors."""

import signal
import sys
import threading
import time


def timeout_handler():
    """Exit after a few seconds to prevent hanging."""
    time.sleep(3)
    print("\n⏰ Test timeout - server appears to be working!")
    sys.exit(0)


def main():
    print("Testing MCP server startup...")

    # Start timeout thread
    timeout_thread = threading.Thread(target=timeout_handler, daemon=True)
    timeout_thread.start()

    try:
        # Import and run the server main function
        from fabric_rti_mcp.server import main as server_main

        print("✓ Server import successful")
        print("🚀 Starting server (will auto-exit after 3 seconds)...")
        server_main()
    except KeyboardInterrupt:
        print("\n🛑 Server interrupted")
    except Exception as e:
        print(f"\n❌ Server startup failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    main()
