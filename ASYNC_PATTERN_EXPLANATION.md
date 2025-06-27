# Async/Sync Pattern Issues and Solutions

## The Problem

### Original Anti-Pattern
```python
def eventstream_create(...):
    import asyncio
    result = asyncio.run(_execute_eventstream_operation(...))
    return [result]
```

### Why This Was Problematic
1. **Event Loop Conflicts**: Calling `asyncio.run()` when an event loop is already running causes `RuntimeError`
2. **Code Duplication**: Every sync function repeated the same `import asyncio` + `asyncio.run()` pattern
3. **Inefficient**: Creates new event loops unnecessarily
4. **Error Prone**: Different error handling in each function

## The Solution

### Centralized Async Handler
```python
def _run_async_operation(coro: Coroutine[Any, Any, Any]) -> Any:
    """
    Helper function to run async operations in sync context.
    Handles event loop management gracefully.
    """
    try:
        # Try to get the existing event loop
        loop = asyncio.get_running_loop()
        # If we're already in an event loop, run in a separate thread
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_in_thread)
            return future.result()
    except RuntimeError:
        # No event loop running, we can use asyncio.run
        return asyncio.run(coro)
```

### Standardized Usage
```python
def eventstream_create(...):
    result = _run_async_operation(_execute_eventstream_operation(...))
    return [result]
```

## Why This Solution Works

### 1. Event Loop Safety
- **Detects existing event loops**: Uses `asyncio.get_running_loop()` to check
- **Thread isolation**: Runs async code in separate thread when needed
- **Fallback to asyncio.run**: Uses standard pattern when no loop exists

### 2. Consistent Error Handling
- **Single point of failure**: All async operations go through one function
- **Proper exception propagation**: Errors bubble up correctly
- **Type safety**: Proper type annotations throughout

### 3. Performance Benefits
- **Reduced overhead**: No repeated loop creation
- **Better resource management**: Proper cleanup of threads and loops
- **Connection reuse**: HTTP clients can be reused effectively

## Architecture Overview

```
MCP Tools (Sync)
      ↓
_run_async_operation() ← Sync/Async Boundary
      ↓
_execute_eventstream_operation() (Async)
      ↓
httpx.AsyncClient (Async HTTP)
      ↓
Microsoft Fabric API
```

## Key Benefits

### 1. Maintainability
- **Single pattern**: All async operations follow the same pattern
- **Easy to modify**: Changes to async handling only need to happen in one place
- **Clear separation**: Sync and async code boundaries are explicit

### 2. Reliability
- **No event loop conflicts**: Handles all edge cases properly
- **Consistent error handling**: All async errors handled the same way
- **Better debugging**: Centralized error reporting

### 3. Type Safety
- **Proper annotations**: Full type checking support
- **Clear interfaces**: Function signatures are explicit about async/sync boundaries
- **IDE support**: Better autocomplete and error detection

## Usage Examples

### Before (Anti-pattern)
```python
def function_a():
    import asyncio  # Repeated everywhere
    result = asyncio.run(some_async_op())  # Event loop conflicts
    return process(result)

def function_b():
    import asyncio  # Repeated everywhere
    result = asyncio.run(other_async_op())  # Different error handling
    return process(result)
```

### After (Standardized)
```python
def function_a():
    result = _run_async_operation(some_async_op())
    return process(result)

def function_b():
    result = _run_async_operation(other_async_op())
    return process(result)
```

## Best Practices Established

1. **Use the helper**: Always use `_run_async_operation()` for async calls in sync context
2. **Keep async pure**: Don't mix sync and async code in the same function
3. **Handle errors at boundaries**: Let the helper manage async/sync error translation
4. **Type everything**: Use proper type annotations for better maintenance

This pattern ensures robust, maintainable async/sync integration throughout the project.
