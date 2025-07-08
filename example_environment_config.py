#!/usr/bin/env python3
"""
Example script demonstrating the environment variable configuration feature
for the Fabric RTI MCP server.

This script shows how to configure multiple Kusto clusters using environment
variables as requested in GitHub issue #22.
"""

import os


# Example configuration matching the GitHub issue specification
def setup_environment_variables():
    """Set up environment variables for multiple Kusto clusters."""

    # Primary cluster (no suffix)
    os.environ["KUSTO_SERVICE_URI"] = "https://cluster.westus.kusto.windows.net/"
    os.environ["KUSTO_DATABASE"] = "Datasets"
    os.environ["KUSTO_DESCRIPTION"] = "Represents the default cluster"

    # Secondary cluster (suffix __1)
    os.environ["KUSTO_SERVICE_URI__1"] = "https://test.kusto.windows.net/"
    os.environ["KUSTO_DATABASE__1"] = "test_default_db"
    os.environ["KUSTO_DESCRIPTION__1"] = "Represents the test cluster"

    # Third cluster (suffix __2)
    os.environ["KUSTO_SERVICE_URI__2"] = "https://third.kusto.windows.net/"
    os.environ["KUSTO_DATABASE__2"] = "third_default_db"
    os.environ["KUSTO_DESCRIPTION__2"] = "Represents the third cluster"


def demonstrate_functionality():
    """Demonstrate the environment variable loading functionality."""

    # Set up environment variables
    setup_environment_variables()

    # Import and use the kusto service
    from fabric_rti_mcp.kusto.kusto_service import (
        kusto_get_clusters,
        KUSTO_CONNECTION_CACHE,
    )

    print("🔧 Environment Variables Configuration Demo")
    print("=" * 50)

    # Show loaded clusters
    clusters = kusto_get_clusters()
    print(f"\nLoaded {len(clusters)} clusters from environment variables:")

    for i, (uri, description) in enumerate(clusters, 1):
        cluster_info = KUSTO_CONNECTION_CACHE[uri]
        print(f"\n{i}. Cluster: {uri}")
        print(f"   Description: {description}")
        print(f"   Default Database: {cluster_info.default_database}")

    print("\n✅ All clusters loaded successfully!")
    print("\nThis configuration matches the format requested in GitHub issue #22:")
    print("https://github.com/microsoft/fabric-rti-mcp/issues/22")


if __name__ == "__main__":
    demonstrate_functionality()
