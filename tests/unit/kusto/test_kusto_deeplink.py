import base64
import gzip
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, unquote, urlparse

import pytest

from fabric_rti_mcp.services.kusto.kusto_service import (
    OFFERING_ADX,
    OFFERING_FABRIC,
    _build_adx_deeplink,
    _build_fabric_deeplink,
    _detect_offering_from_uri,
    _encode_query,
    kusto_deeplink_from_query,
)


def _decode_query(encoded: str) -> str:
    """Roundtrip decode: URL-decode → base64-decode → gzip-decompress → UTF-8."""
    b64 = unquote(encoded)
    compressed = base64.b64decode(b64)
    return gzip.decompress(compressed).decode("utf-8")


def _extract_query_param(url: str, param: str) -> str:
    """Extract a query parameter value from a URL."""
    parsed = urlparse(url)
    return parse_qs(parsed.query)[param][0]


class TestEncodeQuery:
    def test_roundtrip(self) -> None:
        query = "StormEvents | take 10"
        encoded = _encode_query(query)
        assert _decode_query(encoded) == query

    def test_unicode_roundtrip(self) -> None:
        query = "T | where Name == '日本語'"
        encoded = _encode_query(query)
        assert _decode_query(encoded) == query


class TestDetectOfferingFromUri:
    def test_fabric_domain(self) -> None:
        assert _detect_offering_from_uri("https://mycluster.kusto.fabric.microsoft.com") == OFFERING_FABRIC

    def test_adx_public(self) -> None:
        assert _detect_offering_from_uri("https://help.kusto.windows.net") == OFFERING_ADX

    def test_unknown_domain(self) -> None:
        assert _detect_offering_from_uri("https://example.com") is None

    def test_invalid_uri(self) -> None:
        assert _detect_offering_from_uri("not-a-uri") is None


class TestBuildAdxDeeplink:
    def test_simple_query(self) -> None:
        url = _build_adx_deeplink("https://help.kusto.windows.net", "Samples", "StormEvents | take 10")
        assert url is not None
        assert url.startswith("https://dataexplorer.azure.com/clusters/help.kusto.windows.net/databases/Samples?query=")
        decoded = _decode_query(_extract_query_param(url, "query"))
        assert decoded == "StormEvents | take 10"

    def test_regional_cluster(self) -> None:
        url = _build_adx_deeplink("https://mycluster.westus.kusto.windows.net", "MyDb", "T | count")
        assert url is not None
        parsed = urlparse(url)
        assert "/clusters/mycluster.westus.kusto.windows.net/" in parsed.path

    def test_exceeds_max_length(self) -> None:
        long_query = "".join(f"{i:04X}" for i in range(10000))
        assert _build_adx_deeplink("https://help.kusto.windows.net", "Samples", long_query) is None

    def test_invalid_uri(self) -> None:
        assert _build_adx_deeplink("not-a-uri", "db", "query") is None

    def test_unsupported_domain(self) -> None:
        assert _build_adx_deeplink("https://example.com", "db", "query") is None

    def test_trailing_slash(self) -> None:
        url = _build_adx_deeplink("https://help.kusto.windows.net/", "Samples", "T | take 1")
        assert url is not None
        parsed = urlparse(url)
        assert "/clusters/help.kusto.windows.net/" in parsed.path

    def test_database_with_special_chars(self) -> None:
        url = _build_adx_deeplink("https://help.kusto.windows.net", "my db/test", "T | take 1")
        assert url is not None
        parsed = urlparse(url)
        assert "/databases/my%20db%2Ftest" in parsed.path


class TestBuildFabricDeeplink:
    def test_simple_query(self) -> None:
        url = _build_fabric_deeplink(
            "https://fabric.microsoft.com",
            "https://mycluster.kusto.fabric.microsoft.com",
            "MyDb",
            "T | take 10",
        )
        assert url is not None
        assert url.startswith("https://fabric.microsoft.com/groups/me/queryworkbenches/querydeeplink")
        params = parse_qs(urlparse(url).query)
        assert params["experience"] == ["fabric-developer"]
        assert params["databaseItemId"] == ["MyDb"]
        decoded = _decode_query(params["query"][0])
        assert decoded == "T | take 10"

    def test_custom_base_url(self) -> None:
        url = _build_fabric_deeplink(
            "https://custom.fabric.com",
            "https://mycluster.kusto.fabric.microsoft.com",
            "db",
            "T",
        )
        assert url is not None
        assert url.startswith("https://custom.fabric.com/")

    def test_exceeds_max_length(self) -> None:
        long_query = "".join(f"{i:04X}" for i in range(10000))
        assert (
            _build_fabric_deeplink("https://fabric.microsoft.com", "https://x.kusto.fabric.microsoft.com", "db", long_query)
            is None
        )


class TestKustoGetWebExplorerUrl:
    @patch("fabric_rti_mcp.services.kusto.kusto_service.get_kusto_connection")
    def test_adx_cluster(self, mock_get_conn: MagicMock) -> None:
        result = kusto_deeplink_from_query("https://help.kusto.windows.net", "Samples", "T | take 10")
        assert result["offering"] == OFFERING_ADX
        assert result["web_explorer_url"] is not None
        assert result["web_explorer_url"].startswith("https://dataexplorer.azure.com/")
        mock_get_conn.assert_not_called()

    @patch("fabric_rti_mcp.services.kusto.kusto_service.get_kusto_connection")
    def test_fabric_cluster(self, mock_get_conn: MagicMock) -> None:
        result = kusto_deeplink_from_query(
            "https://mycluster.kusto.fabric.microsoft.com", "MyDb", "T | take 10"
        )
        assert result["offering"] == OFFERING_FABRIC
        assert result["web_explorer_url"] is not None
        assert result["web_explorer_url"].startswith("https://fabric.microsoft.com/groups/me/queryworkbenches/querydeeplink")
        mock_get_conn.assert_not_called()

    @patch("fabric_rti_mcp.services.kusto.kusto_service._execute")
    def test_unknown_domain_falls_back_to_show_version_adx(self, mock_execute: MagicMock) -> None:
        mock_execute.return_value = {
            "format": "columnar",
            "data": {"ServiceType": ["Azure Data Explorer"]},
        }
        result = kusto_deeplink_from_query("https://unknown.example.com", "db", "T | take 10")
        mock_execute.assert_called_once()
        assert result["offering"] == OFFERING_ADX
        # URL is None because the domain is not in ADX cloud mappings
        assert result["web_explorer_url"] is None

    @patch("fabric_rti_mcp.services.kusto.kusto_service._execute")
    def test_unknown_domain_falls_back_to_show_version_fabric(self, mock_execute: MagicMock) -> None:
        mock_execute.return_value = {
            "format": "columnar",
            "data": {"ServiceType": ["Microsoft Fabric Eventhouse"]},
        }
        result = kusto_deeplink_from_query("https://unknown.example.com", "db", "T | take 10")
        assert result["offering"] == OFFERING_FABRIC
        assert result["web_explorer_url"] is not None
        assert result["web_explorer_url"].startswith("https://fabric.microsoft.com/groups/me/queryworkbenches/querydeeplink")

    @patch("fabric_rti_mcp.services.kusto.kusto_service._execute")
    def test_unknown_domain_show_version_fails(self, mock_execute: MagicMock) -> None:
        mock_execute.side_effect = RuntimeError("Connection failed")
        result = kusto_deeplink_from_query("https://unknown.example.com", "db", "T | take 10")
        assert result["offering"] is None
        assert result["web_explorer_url"] is None

    @patch("fabric_rti_mcp.services.kusto.kusto_service.get_kusto_connection")
    def test_strips_query_whitespace(self, mock_get_conn: MagicMock) -> None:
        result = kusto_deeplink_from_query("https://help.kusto.windows.net", "Samples", "  T | take 10  ")
        assert result["web_explorer_url"] is not None
        decoded = _decode_query(_extract_query_param(result["web_explorer_url"], "query"))
        assert decoded == "T | take 10"

    @patch.dict("os.environ", {"FABRIC_RTI_KUSTO_DEEPLINK_STYLE": "fabric"})
    @patch("fabric_rti_mcp.services.kusto.kusto_service.get_kusto_connection")
    def test_env_override_forces_fabric_for_adx_cluster(self, mock_get_conn: MagicMock) -> None:
        result = kusto_deeplink_from_query("https://help.kusto.windows.net", "Samples", "T | take 10")
        assert result["offering"] == OFFERING_FABRIC
        assert result["web_explorer_url"] is not None
        assert result["web_explorer_url"].startswith("https://fabric.microsoft.com/groups/me/queryworkbenches/querydeeplink")
        mock_get_conn.assert_not_called()

    @patch.dict("os.environ", {"FABRIC_RTI_KUSTO_DEEPLINK_STYLE": "adx"})
    @patch("fabric_rti_mcp.services.kusto.kusto_service.get_kusto_connection")
    def test_env_override_forces_adx_for_fabric_cluster(self, mock_get_conn: MagicMock) -> None:
        result = kusto_deeplink_from_query("https://mycluster.kusto.fabric.microsoft.com", "MyDb", "T | take 10")
        assert result["offering"] == OFFERING_ADX
        # URL is None because fabric domain is not in ADX cloud mappings
        assert result["web_explorer_url"] is None
        mock_get_conn.assert_not_called()

    @patch.dict("os.environ", {"FABRIC_RTI_KUSTO_DEEPLINK_STYLE": "invalid"})
    @patch("fabric_rti_mcp.services.kusto.kusto_service.get_kusto_connection")
    def test_env_override_invalid_value_returns_none(self, mock_get_conn: MagicMock) -> None:
        result = kusto_deeplink_from_query("https://help.kusto.windows.net", "Samples", "T | take 10")
        assert result["offering"] is None
        assert result["web_explorer_url"] is None


class TestDeeplinkInputValidation:
    def test_empty_cluster_uri(self) -> None:
        with pytest.raises(ValueError, match="cluster_uri is required"):
            kusto_deeplink_from_query("", "db", "T | take 10")

    def test_whitespace_cluster_uri(self) -> None:
        with pytest.raises(ValueError, match="cluster_uri is required"):
            kusto_deeplink_from_query("   ", "db", "T | take 10")

    def test_empty_database(self) -> None:
        with pytest.raises(ValueError, match="database is required"):
            kusto_deeplink_from_query("https://help.kusto.windows.net", "", "T | take 10")

    def test_whitespace_database(self) -> None:
        with pytest.raises(ValueError, match="database is required"):
            kusto_deeplink_from_query("https://help.kusto.windows.net", "  ", "T | take 10")

    def test_empty_query(self) -> None:
        with pytest.raises(ValueError, match="query is required"):
            kusto_deeplink_from_query("https://help.kusto.windows.net", "Samples", "")

    def test_whitespace_query(self) -> None:
        with pytest.raises(ValueError, match="query is required"):
            kusto_deeplink_from_query("https://help.kusto.windows.net", "Samples", "   ")

    def test_invalid_scheme(self) -> None:
        with pytest.raises(ValueError, match="must use http or https"):
            kusto_deeplink_from_query("ftp://help.kusto.windows.net", "Samples", "T | take 10")

    def test_no_scheme(self) -> None:
        with pytest.raises(ValueError, match="must use http or https"):
            kusto_deeplink_from_query("help.kusto.windows.net", "Samples", "T | take 10")

    def test_no_hostname(self) -> None:
        with pytest.raises(ValueError, match="missing a hostname"):
            kusto_deeplink_from_query("https://", "Samples", "T | take 10")
