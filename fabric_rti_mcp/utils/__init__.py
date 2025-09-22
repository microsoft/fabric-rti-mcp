import asyncio
from typing import Any, Coroutine

from .fabric_connection import FabricConnection


def run_async_operation(coro: Coroutine[Any, Any, Any]) -> Any:
    """
    Helper function to run async operations in sync context.
    Handles event loop management gracefully.
    """
    try:
        # Try to get the existing event loop
        asyncio.get_running_loop()
        # If we're already in an event loop, we need to run in a thread
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()

    except RuntimeError:
        # No event loop running, we can run directly
        return asyncio.run(coro)


__all__ = ["FabricConnection", "run_async_operation"]
