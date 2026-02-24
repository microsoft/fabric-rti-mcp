import base64
import gzip

import pytest

from fabric_rti_mcp.services.kusto.kusto_deeplink import build_web_explorer_url


def _decode_query_from_url(url: str) -> str:
    """Roundtrip decode: extract query param → URL-decode → base64-decode → gzip-decompress → UTF-8."""
    from urllib.parse import unquote, urlparse, parse_qs

    parsed = urlparse(url)
    encoded = parse_qs(parsed.query)["query"][0]
    compressed = base64.b64decode(encoded)
    return gzip.decompress(compressed).decode("utf-8")


def test_simple_query_produces_valid_url() -> None:
    url = build_web_explorer_url("https://help.kusto.windows.net", "Samples", "StormEvents | take 10")

    assert url is not None
    assert url.startswith("https://dataexplorer.azure.com/clusters/help.kusto.windows.net/databases/Samples?query=")
    assert _decode_query_from_url(url) == "StormEvents | take 10"


def test_regional_cluster_produces_valid_url() -> None:
    url = build_web_explorer_url("https://mycluster.westus.kusto.windows.net", "MyDb", "MyTable | count")

    assert url is not None
    assert url.startswith(
        "https://dataexplorer.azure.com/clusters/mycluster.westus.kusto.windows.net/databases/MyDb?query="
    )


def test_us_gov_cloud_uses_correct_explorer_base() -> None:
    url = build_web_explorer_url("https://mycluster.kusto.usgovcloudapi.net", "db1", "T | take 1")

    assert url is not None
    assert url.startswith(
        "https://dataexplorer.azure.us/clusters/mycluster.kusto.usgovcloudapi.net/databases/db1?query="
    )


def test_china_cloud_uses_correct_explorer_base() -> None:
    url = build_web_explorer_url("https://mycluster.kusto.chinacloudapi.cn", "db1", "T | take 1")

    assert url is not None
    assert url.startswith(
        "https://dataexplorer.azure.cn/clusters/mycluster.kusto.chinacloudapi.cn/databases/db1?query="
    )


def test_query_exceeding_max_length_returns_none() -> None:
    # Incrementing hex values resist gzip compression well
    long_query = "".join(f"{i:04X}" for i in range(10000))

    url = build_web_explorer_url("https://help.kusto.windows.net", "Samples", long_query)

    assert url is None


def test_invalid_uri_returns_none() -> None:
    url = build_web_explorer_url("not-a-uri", "db", "query")

    assert url is None


def test_unsupported_domain_returns_none() -> None:
    url = build_web_explorer_url("https://example.com", "db", "query")

    assert url is None


def test_trailing_slash_produces_valid_url() -> None:
    url = build_web_explorer_url("https://help.kusto.windows.net/", "Samples", "StormEvents | take 10")

    assert url is not None
    assert url.startswith("https://dataexplorer.azure.com/clusters/help.kusto.windows.net/databases/Samples?query=")
