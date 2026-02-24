import base64
import gzip
from urllib.parse import quote, urlparse

_MAX_URL_LENGTH = 8000

_PUBLIC_EXPLORER_BASE = "https://dataexplorer.azure.com"
_US_GOV_EXPLORER_BASE = "https://dataexplorer.azure.us"
_CHINA_EXPLORER_BASE = "https://dataexplorer.azure.cn"

# Cloud domain suffix → Web Explorer base URL mapping.
# Order doesn't matter; we check all suffixes.
_CLOUD_MAPPINGS: list[tuple[str, str]] = [
    # Public cloud
    (".kusto.windows.net", _PUBLIC_EXPLORER_BASE),
    (".kustodev.windows.net", _PUBLIC_EXPLORER_BASE),
    (".kustomfa.windows.net", _PUBLIC_EXPLORER_BASE),
    (".kusto.data.microsoft.com", _PUBLIC_EXPLORER_BASE),
    (".kusto.fabric.microsoft.com", _PUBLIC_EXPLORER_BASE),
    (".kusto.azuresynapse.net", _PUBLIC_EXPLORER_BASE),
    # US Government
    (".kusto.usgovcloudapi.net", _US_GOV_EXPLORER_BASE),
    (".kustomfa.usgovcloudapi.net", _US_GOV_EXPLORER_BASE),
    # China
    (".kusto.chinacloudapi.cn", _CHINA_EXPLORER_BASE),
    (".kustomfa.chinacloudapi.cn", _CHINA_EXPLORER_BASE),
    (".kusto.azuresynapse.azure.cn", _CHINA_EXPLORER_BASE),
]


def _get_explorer_base_url(host: str) -> str | None:
    host_lower = host.lower()
    for suffix, explorer_base in _CLOUD_MAPPINGS:
        if host_lower.endswith(suffix):
            return explorer_base
    return None


def build_web_explorer_url(cluster_uri: str, database: str, query: str) -> str | None:
    """
    Build a Kusto Web Explorer deeplink URL that opens the given query in the
    Azure Data Explorer Web UI.

    Returns None if the cluster URI is invalid, the domain is unrecognized, or
    the resulting URL exceeds 8000 characters.
    """
    try:
        parsed = urlparse(cluster_uri)
        if not parsed.scheme or not parsed.hostname:
            return None
    except Exception:
        return None

    host = parsed.hostname
    explorer_base = _get_explorer_base_url(host)
    if explorer_base is None:
        return None

    query_bytes = query.encode("utf-8")
    compressed = gzip.compress(query_bytes)
    b64 = base64.b64encode(compressed).decode("ascii")
    url_encoded = quote(b64, safe="")

    url = f"{explorer_base}/clusters/{host}/databases/{database}?query={url_encoded}"

    if len(url) > _MAX_URL_LENGTH:
        return None

    return url
