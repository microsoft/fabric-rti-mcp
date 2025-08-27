# ------------------------------------------------------------------------------
# ⚠️  DEVELOPMENT IMAGE – NOT FOR PRODUCTION USE ⚠️
# ------------------------------------------------------------------------------
# This Dockerfile starts an MCP server with **NO built-in authentication,
# transport security, or token verification**.
#
# If you attach an Azure Managed Identity (or any cloud credential) the server
# inherits it; anyone who can reach the container can then act as that
# identity.  Because the server does not verify audience / issuer / expiry,
# a malicious caller could forward arbitrary tokens to downstream services.
#
# Therefore **NEVER**:
#   • Run this image in production.
#   • Expose it to the Internet or untrusted networks.
#
# If you need a hardened build, you MUST add:
#   1. TLS termination (or run behind a trusted proxy with TLS).  
#   2. Strong authentication (e.g., OAuth 2.0 / mTLS).  
#   3. Token verification: validate issuer, audience, signature, expiry,     
#      and revocation before forwarding calls.  
#   4. Least-privilege scoping of any attached identities.
# ------------------------------------------------------------------------------
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files and source code structure
COPY pyproject.toml uv.lock* ./
COPY fabric_rti_mcp/ ./fabric_rti_mcp/

# Install Python dependencies
# Set a fallback version for setuptools-scm when Git is not available
ENV SETUPTOOLS_SCM_PRETEND_VERSION=0.1.0
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Set environment variables with defaults
# Kusto configuration
ENV KUSTO_SERVICE_URI=""
ENV KUSTO_SERVICE_DEFAULT_DB=""
ENV AZ_OPENAI_EMBEDDING_ENDPOINT=""
ENV KUSTO_KNOWN_SERVICES=""
ENV KUSTO_EAGER_CONNECT="false"
ENV KUSTO_ALLOW_UNKNOWN_SERVICES="true"
ENV FABRIC_RTI_KUSTO_TIMEOUT=""

# Transport configuration
ENV FABRIC_RTI_TRANSPORT="http"
ENV FABRIC_RTI_HTTP_HOST="0.0.0.0"
ENV FABRIC_RTI_HTTP_PORT="8000"
ENV FABRIC_RTI_DEBUG_MODE="false"

# Azure Managed Identity configuration
ENV AZURE_CLIENT_ID=""
ENV AZURE_TENANT_ID=""
ENV AZURE_FEDERATED_TOKEN_FILE=""

# Fabric API configuration
ENV FABRIC_API_BASE="https://api.fabric.microsoft.com/v1"

# Expose the HTTP port
EXPOSE 8000

# Run the server
ENTRYPOINT ["python", "-m", "fabric_rti_mcp.server"]
