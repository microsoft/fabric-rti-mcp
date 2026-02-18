from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

from fabric_rti_mcp.config import logger
from fabric_rti_mcp.services.kusto.kusto_config import DEFAULT_SCHEMA_CACHE_TTL_SECONDS, KustoConfig


def _default_cache_dir() -> Path:
    """Return the platform-appropriate default cache directory."""
    base = os.environ.get("XDG_CACHE_HOME") or os.path.join(Path.home(), ".cache")
    return Path(base) / "fabric-rti-mcp" / "kusto-schema"


def _cache_key(cluster_uri: str, database: str, query: str) -> str:
    raw = f"{cluster_uri.lower()}|{database.lower()}|{query}"
    return hashlib.sha256(raw.encode()).hexdigest()


class KustoSchemaCache:
    def __init__(self, cache_dir: Path, ttl_seconds: int = DEFAULT_SCHEMA_CACHE_TTL_SECONDS) -> None:
        self._cache_dir = cache_dir
        self._ttl_seconds = ttl_seconds

    def get(self, cluster_uri: str, database: str, query: str) -> dict[str, Any] | None:
        """Return cached result if it exists and is fresh, otherwise None."""
        key = _cache_key(cluster_uri, database, query)
        path = self._cache_dir / f"{key}.json"
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            cached_at = data.get("cached_at", 0)
            if time.time() - cached_at > self._ttl_seconds:
                logger.info("Schema cache entry expired for %s/%s", cluster_uri, database)
                return None
            return data.get("result")
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to read schema cache entry: %s", e)
            return None

    def put(self, cluster_uri: str, database: str, query: str, result: dict[str, Any]) -> None:
        """Store a result in the cache."""
        try:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            key = _cache_key(cluster_uri, database, query)
            path = self._cache_dir / f"{key}.json"
            payload = {"cached_at": time.time(), "cluster_uri": cluster_uri, "database": database, "result": result}
            path.write_text(json.dumps(payload), encoding="utf-8")
        except OSError as e:
            logger.warning("Failed to write schema cache entry: %s", e)


_SCHEMA_CACHE: KustoSchemaCache | None = None


def get_schema_cache() -> KustoSchemaCache | None:
    """Return the singleton schema cache instance, or None if caching is disabled."""
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is not None:
        return _SCHEMA_CACHE

    config = KustoConfig.from_env()
    if not config.schema_cache_enabled:
        return None

    cache_dir = Path(config.schema_cache_path) if config.schema_cache_path else _default_cache_dir()
    _SCHEMA_CACHE = KustoSchemaCache(cache_dir, config.schema_cache_ttl_seconds)
    return _SCHEMA_CACHE


def reset_schema_cache() -> None:
    """Reset the singleton so the next call to get_schema_cache() re-reads config."""
    global _SCHEMA_CACHE
    _SCHEMA_CACHE = None
