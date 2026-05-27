import time
from typing import Any

from azure.core.credentials import AccessToken, TokenCredential
from azure.identity import DefaultAzureCredential
from azure.kusto.data import KustoClient, KustoConnectionStringBuilder
from azure.kusto.ingest import KustoStreamingIngestClient

from fabric_rti_mcp.authentication.auth_context import get_auth_token
from fabric_rti_mcp.authentication.auth_context import set_auth_token as set_auth_token


class BearerTokenCredential(TokenCredential):
    """A credential that reads the bearer token from the current request's ContextVar on each call."""

    def get_token(self, *scopes: str, **kwargs: Any) -> AccessToken:
        token = get_auth_token()
        if not token:
            raise ValueError("No auth token available in request context")
        return AccessToken(token=token, expires_on=int(time.time()) + 3600)


class KustoConnection:
    query_client: KustoClient
    ingestion_client: KustoStreamingIngestClient
    default_database: str

    def __init__(self, cluster_uri: str, default_database: str | None = None):
        cluster_uri = sanitize_uri(cluster_uri)
        kcsb = KustoConnectionStringBuilder.with_azure_token_credential(
            connection_string=cluster_uri,
            credential_from_login_endpoint=lambda login_endpoint: self._get_credential(login_endpoint),
        )
        self.query_client = KustoClient(kcsb)
        self.ingestion_client = KustoStreamingIngestClient(kcsb)

        default_database = default_database or KustoConnectionStringBuilder.DEFAULT_DATABASE_NAME
        default_database = default_database.strip()
        self.default_database = default_database

    def _get_credential(self, login_endpoint: str) -> TokenCredential:
        # Check if we have a bearer token from HTTP auth
        token = get_auth_token()
        if token:
            return BearerTokenCredential()

        return DefaultAzureCredential(
            exclude_shared_token_cache_credential=True,
            exclude_interactive_browser_credential=False,
            authority=login_endpoint,
        )


def sanitize_uri(cluster_uri: str) -> str:
    cluster_uri = cluster_uri.strip()
    if cluster_uri.endswith("/"):
        cluster_uri = cluster_uri[:-1]
    return cluster_uri
