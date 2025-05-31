from azure.identity import ChainedTokenCredential, DefaultAzureCredential
from azure.kusto.data import KustoClient, KustoConnectionStringBuilder
from azure.kusto.ingest import KustoStreamingIngestClient


class KustoConnection:
    query_client: KustoClient
    ingestion_client: KustoStreamingIngestClient

    def __init__(self, cluster_uri: str):
        credential = self._get_credential()
        kcsb = KustoConnectionStringBuilder.with_azure_token_credential(
            connection_string=cluster_uri, credential=credential
        )
        self.query_client = KustoClient(kcsb)
        self.ingestion_client = KustoStreamingIngestClient(kcsb)

    def _get_credential(self) -> ChainedTokenCredential:
        return DefaultAzureCredential(
            exclude_shared_token_cache_credential=True,
            exclude_interactive_browser_credential=False,
        )
