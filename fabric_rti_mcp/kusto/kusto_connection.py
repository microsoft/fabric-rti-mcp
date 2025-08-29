import time
from contextvars import ContextVar
from typing import Any, Optional

from azure.core.credentials import AccessToken, TokenCredential
from azure.identity import DefaultAzureCredential
from azure.kusto.data import KustoClient, KustoConnectionStringBuilder
from azure.kusto.ingest import KustoStreamingIngestClient

# Thread-safe context variable to store the current request's auth token
_request_token: ContextVar[Optional[str]] = ContextVar("_request_token", default=None)


def set_auth_token(token: Optional[str]) -> None:
    """Set the auth token for the current request context"""
    _request_token.set(token)


def get_auth_token() -> Optional[str]:
    """Get the auth token from the current request context"""
    return _request_token.get()


class BearerTokenCredential(TokenCredential):
    """A credential that uses a bearer token directly."""

    def __init__(self, token: str):
        self.token = token

    def get_token(self, *scopes: str, **kwargs: Any) -> AccessToken:
        """Get the token for the specified scopes."""
        # Create an AccessToken with a far future expiration
        actoken = AccessToken(token=self.token, expires_on=int(time.time()) + 3600)
        return actoken


class KustoConnection:
    query_client: KustoClient
    ingestion_client: KustoStreamingIngestClient
    default_database: str

    def __init__(self, cluster_uri: str, default_database: Optional[str] = None):
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
            # Use the bearer token directly if available (HTTP mode)
            return BearerTokenCredential(token)

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
