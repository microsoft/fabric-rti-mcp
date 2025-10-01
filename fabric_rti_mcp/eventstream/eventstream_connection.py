# Import and re-export for backward compatibility
from fabric_rti_mcp.utils.fabric_api_http_client import (
    FabricAPIHttpClient,
    FabricHttpClientCache,
    DEFAULT_FABRIC_HTTP_CLIENT_CACHE,
)

# Backward compatibility alias
EventstreamConnection = FabricAPIHttpClient
