# Template for new module integration
# Replace <MODULE_NAME> with the actual module name from the other codebase

from typing import Any, Dict, List, Optional
from collections import defaultdict

from fabric_rti_mcp.common import logger

# TODO: Add specific imports for the new module's dependencies
# Example: from some_client import SomeClient, SomeConnectionStringBuilder


class ModuleConnectionCache(defaultdict[str, Any]):
    """Connection cache similar to KustoConnectionCache pattern."""
    def __missing__(self, key: str) -> Any:
        # TODO: Implement connection creation logic
        client = self._create_connection(key)
        self[key] = client
        return client
    
    def _create_connection(self, connection_string: str) -> Any:
        # TODO: Implement actual connection logic
        logger.info(f"Creating new connection for: {connection_string}")
        # return SomeClient(connection_string)
        pass


MODULE_CONNECTION_CACHE: Dict[str, Any] = ModuleConnectionCache()


def get_connection(connection_string: str) -> Any:
    """Get or create a connection from the cache."""
    # Clean up the connection string since agents can send messy inputs
    connection_string = connection_string.strip()
    if connection_string.endswith("/"):
        connection_string = connection_string[:-1]
    return MODULE_CONNECTION_CACHE[connection_string]


def _execute_operation(
    operation: str,
    connection_string: str,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Base execution method following the pattern from kusto_service.py
    """
    # Clean inputs
    operation = operation.strip()
    
    # Get connection
    client = get_connection(connection_string)
    
    try:
        # TODO: Implement the actual operation execution
        # result = client.execute(operation, **kwargs)
        # return format_results(result)
        return [{"status": "not_implemented", "operation": operation}]
    except Exception as e:
        logger.error(f"Error executing operation: {e}")
        raise


# TODO: Implement specific service functions following the pattern:
def module_query(
    query: str,
    connection_string: str,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Execute a query operation.
    
    :param query: The query to execute
    :param connection_string: Connection string for the service
    :return: Query results as list of dictionaries
    """
    return _execute_operation(query, connection_string, **kwargs)


def module_list_resources(
    connection_string: str
) -> List[Dict[str, Any]]:
    """
    List available resources.
    
    :param connection_string: Connection string for the service
    :return: List of available resources
    """
    return _execute_operation("LIST_RESOURCES", connection_string)


# TODO: Add more service functions as needed
# Follow the naming pattern: module_<operation_name>

# List of destructive operations (similar to DESTRUCTIVE_TOOLS in kusto_service.py)
DESTRUCTIVE_OPERATIONS = {
    # TODO: Add names of functions that perform destructive operations
    # "module_delete_resource",
    # "module_update_resource",
}
