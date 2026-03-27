import json
import time
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from fabric_rti_mcp.services.kusto.kusto_schema_cache import (
    KustoSchemaCache,
    _cache_key,
    get_schema_cache,
    reset_schema_cache,
)


@pytest.fixture(autouse=True)
def _reset_singleton() -> None:
    """Reset the module-level singleton before each test."""
    reset_schema_cache()


@pytest.fixture
def cache_dir(tmp_path: Path) -> Path:
    return tmp_path / "schema_cache"


@pytest.fixture
def schema_cache(cache_dir: Path) -> KustoSchemaCache:
    return KustoSchemaCache(cache_dir, ttl_seconds=3600)


SAMPLE_CLUSTER = "https://test.kusto.windows.net"
SAMPLE_DB = "testdb"
SAMPLE_QUERY = ".show databases entities"
SAMPLE_RESULT: dict = {"format": "columnar", "data": {"EntityName": ["Table1"]}}


class TestCacheKey:
    def test_deterministic(self) -> None:
        k1 = _cache_key("https://A.kusto.windows.net", "db", "q")
        k2 = _cache_key("https://A.kusto.windows.net", "db", "q")
        assert k1 == k2

    def test_case_insensitive(self) -> None:
        k1 = _cache_key("https://A.kusto.windows.net", "DB", "q")
        k2 = _cache_key("https://a.kusto.windows.net", "db", "q")
        assert k1 == k2

    def test_different_inputs_give_different_keys(self) -> None:
        k1 = _cache_key("https://a.kusto.windows.net", "db1", "q")
        k2 = _cache_key("https://a.kusto.windows.net", "db2", "q")
        assert k1 != k2


class TestKustoSchemaCache:
    def test_get_returns_none_for_empty_cache(self, schema_cache: KustoSchemaCache) -> None:
        assert schema_cache.get(SAMPLE_CLUSTER, SAMPLE_DB, SAMPLE_QUERY) is None

    def test_put_then_get_returns_result(self, schema_cache: KustoSchemaCache) -> None:
        schema_cache.put(SAMPLE_CLUSTER, SAMPLE_DB, SAMPLE_QUERY, SAMPLE_RESULT)
        cached = schema_cache.get(SAMPLE_CLUSTER, SAMPLE_DB, SAMPLE_QUERY)
        assert cached == SAMPLE_RESULT

    def test_expired_entry_returns_none(self, cache_dir: Path) -> None:
        cache = KustoSchemaCache(cache_dir, ttl_seconds=1)
        cache.put(SAMPLE_CLUSTER, SAMPLE_DB, SAMPLE_QUERY, SAMPLE_RESULT)

        # Manually backdate the cached_at timestamp
        key = _cache_key(SAMPLE_CLUSTER, SAMPLE_DB, SAMPLE_QUERY)
        path = cache_dir / f"{key}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["cached_at"] = time.time() - 10
        path.write_text(json.dumps(data), encoding="utf-8")

        assert cache.get(SAMPLE_CLUSTER, SAMPLE_DB, SAMPLE_QUERY) is None

    def test_corrupted_file_returns_none(self, schema_cache: KustoSchemaCache, cache_dir: Path) -> None:
        schema_cache.put(SAMPLE_CLUSTER, SAMPLE_DB, SAMPLE_QUERY, SAMPLE_RESULT)

        key = _cache_key(SAMPLE_CLUSTER, SAMPLE_DB, SAMPLE_QUERY)
        path = cache_dir / f"{key}.json"
        path.write_text("not valid json", encoding="utf-8")

        assert schema_cache.get(SAMPLE_CLUSTER, SAMPLE_DB, SAMPLE_QUERY) is None

    def test_different_queries_cached_separately(self, schema_cache: KustoSchemaCache) -> None:
        result_a: dict = {"format": "columnar", "data": {"EntityName": ["A"]}}
        result_b: dict = {"format": "columnar", "data": {"EntityName": ["B"]}}
        schema_cache.put(SAMPLE_CLUSTER, SAMPLE_DB, "query_a", result_a)
        schema_cache.put(SAMPLE_CLUSTER, SAMPLE_DB, "query_b", result_b)
        assert schema_cache.get(SAMPLE_CLUSTER, SAMPLE_DB, "query_a") == result_a
        assert schema_cache.get(SAMPLE_CLUSTER, SAMPLE_DB, "query_b") == result_b

    def test_put_creates_directory(self, tmp_path: Path) -> None:
        nested = tmp_path / "a" / "b" / "c"
        cache = KustoSchemaCache(nested)
        cache.put(SAMPLE_CLUSTER, SAMPLE_DB, SAMPLE_QUERY, SAMPLE_RESULT)
        assert nested.exists()
        assert cache.get(SAMPLE_CLUSTER, SAMPLE_DB, SAMPLE_QUERY) == SAMPLE_RESULT


class TestGetSchemaCache:
    @patch.dict("os.environ", {"FABRIC_RTI_KUSTO_SCHEMA_CACHE_ENABLED": "false"}, clear=False)
    def test_returns_none_when_disabled(self) -> None:
        assert get_schema_cache() is None

    @patch.dict("os.environ", {"FABRIC_RTI_KUSTO_SCHEMA_CACHE_ENABLED": "true"}, clear=False)
    def test_returns_cache_when_enabled(self) -> None:
        cache = get_schema_cache()
        assert cache is not None
        assert isinstance(cache, KustoSchemaCache)

    @patch.dict(
        "os.environ",
        {
            "FABRIC_RTI_KUSTO_SCHEMA_CACHE_ENABLED": "true",
            "FABRIC_RTI_KUSTO_SCHEMA_CACHE_PATH": "/tmp/test_schema_cache",
        },
        clear=False,
    )
    def test_uses_custom_path(self) -> None:
        cache = get_schema_cache()
        assert cache is not None
        assert cache._cache_dir == Path("/tmp/test_schema_cache")

    @patch.dict(
        "os.environ",
        {"FABRIC_RTI_KUSTO_SCHEMA_CACHE_ENABLED": "true", "FABRIC_RTI_KUSTO_SCHEMA_CACHE_TTL": "7200"},
        clear=False,
    )
    def test_uses_custom_ttl(self) -> None:
        cache = get_schema_cache()
        assert cache is not None
        assert cache._ttl_seconds == 7200

    @patch.dict("os.environ", {"FABRIC_RTI_KUSTO_SCHEMA_CACHE_ENABLED": "true"}, clear=False)
    def test_singleton_behaviour(self) -> None:
        c1 = get_schema_cache()
        c2 = get_schema_cache()
        assert c1 is c2


class TestServiceIntegration:
    @patch("fabric_rti_mcp.services.kusto.kusto_service.get_kusto_connection")
    @patch("fabric_rti_mcp.services.kusto.kusto_service.get_schema_cache")
    def test_describe_database_uses_cache_hit(
        self,
        mock_get_cache: Mock,
        mock_get_conn: Mock,
    ) -> None:
        """When cache returns a hit, _execute should NOT be called."""
        from fabric_rti_mcp.services.kusto.kusto_service import kusto_describe_database

        mock_cache = MagicMock()
        mock_cache.get.return_value = SAMPLE_RESULT
        mock_get_cache.return_value = mock_cache

        result = kusto_describe_database("https://test.kusto.windows.net", "mydb")
        assert result == SAMPLE_RESULT
        mock_get_conn.assert_not_called()

    @patch("fabric_rti_mcp.services.kusto.kusto_service.get_kusto_connection")
    @patch("fabric_rti_mcp.services.kusto.kusto_service.get_schema_cache")
    def test_describe_database_populates_cache_on_miss(
        self,
        mock_get_cache: Mock,
        mock_get_conn: Mock,
        mock_kusto_response: MagicMock,
    ) -> None:
        """When cache misses, the result should be stored back in cache."""
        from fabric_rti_mcp.services.kusto.kusto_service import kusto_describe_database

        mock_cache = MagicMock()
        mock_cache.get.return_value = None
        mock_get_cache.return_value = mock_cache

        mock_client = MagicMock()
        mock_client.execute.return_value = mock_kusto_response
        mock_connection = MagicMock()
        mock_connection.query_client = mock_client
        mock_connection.default_database = "default_db"
        mock_get_conn.return_value = mock_connection

        result = kusto_describe_database("https://test.kusto.windows.net", "mydb")
        assert result is not None
        mock_cache.put.assert_called_once()

    @patch("fabric_rti_mcp.services.kusto.kusto_service.get_kusto_connection")
    @patch("fabric_rti_mcp.services.kusto.kusto_service.get_schema_cache")
    def test_describe_database_works_without_cache(
        self,
        mock_get_cache: Mock,
        mock_get_conn: Mock,
        mock_kusto_response: MagicMock,
    ) -> None:
        """When caching is disabled (None), describe_database still works normally."""
        from fabric_rti_mcp.services.kusto.kusto_service import kusto_describe_database

        mock_get_cache.return_value = None

        mock_client = MagicMock()
        mock_client.execute.return_value = mock_kusto_response
        mock_connection = MagicMock()
        mock_connection.query_client = mock_client
        mock_connection.default_database = "default_db"
        mock_get_conn.return_value = mock_connection

        result = kusto_describe_database("https://test.kusto.windows.net", "mydb")
        assert result is not None

    @patch("fabric_rti_mcp.services.kusto.kusto_service.get_kusto_connection")
    @patch("fabric_rti_mcp.services.kusto.kusto_service.get_schema_cache")
    def test_describe_entity_uses_cache_hit(
        self,
        mock_get_cache: Mock,
        mock_get_conn: Mock,
    ) -> None:
        from fabric_rti_mcp.services.kusto.kusto_service import kusto_describe_database_entity

        mock_cache = MagicMock()
        mock_cache.get.return_value = SAMPLE_RESULT
        mock_get_cache.return_value = mock_cache

        result = kusto_describe_database_entity("MyTable", "table", "https://test.kusto.windows.net", "mydb")
        assert result == SAMPLE_RESULT
        mock_get_conn.assert_not_called()

    @patch("fabric_rti_mcp.services.kusto.kusto_service.get_kusto_connection")
    @patch("fabric_rti_mcp.services.kusto.kusto_service.get_schema_cache")
    def test_describe_entity_populates_cache_on_miss(
        self,
        mock_get_cache: Mock,
        mock_get_conn: Mock,
        mock_kusto_response: MagicMock,
    ) -> None:
        from fabric_rti_mcp.services.kusto.kusto_service import kusto_describe_database_entity

        mock_cache = MagicMock()
        mock_cache.get.return_value = None
        mock_get_cache.return_value = mock_cache

        mock_client = MagicMock()
        mock_client.execute.return_value = mock_kusto_response
        mock_connection = MagicMock()
        mock_connection.query_client = mock_client
        mock_connection.default_database = "default_db"
        mock_get_conn.return_value = mock_connection

        result = kusto_describe_database_entity("MyTable", "table", "https://test.kusto.windows.net", "mydb")
        assert result is not None
        mock_cache.put.assert_called_once()
