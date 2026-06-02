from azure.core.credentials import TokenCredential
from azure.kusto.data import KustoClient, KustoConnectionStringBuilder
from azure.kusto.ingest import KustoStreamingIngestClient

from fabric_rti_mcp.authentication.auth_context import get_credential


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
        return get_credential(authority=login_endpoint)


def sanitize_uri(cluster_uri: str) -> str:
    cluster_uri = cluster_uri.strip()
    if cluster_uri.endswith("/"):
        cluster_uri = cluster_uri[:-1]
    return cluster_uri
