from __future__ import annotations

import os
from dataclasses import dataclass


class KontextEnvVarNames:
    """Environment variable names for Kontext service configuration."""

    cluster_uri = "KONTEXT_CLUSTER"
    database = "KONTEXT_DATABASE"
    embedding_uri = "KONTEXT_EMBEDDING_URI"
    memory_table = "KONTEXT_TABLE"

    @staticmethod
    def all() -> list[str]:
        """Return a list of all environment variable names used by KontextConfig."""
        return [
            KontextEnvVarNames.cluster_uri,
            KontextEnvVarNames.database,
            KontextEnvVarNames.embedding_uri,
            KontextEnvVarNames.memory_table,
        ]


@dataclass(slots=True, frozen=True)
class KontextConfig:
    """Configuration for the Kontext memory service."""

    cluster_uri: str
    database: str
    embedding_uri: str
    memory_table: str = "Memory"

    @property
    def query_endpoint(self) -> str:
        """Get the query endpoint URL."""
        return self.cluster_uri

    @staticmethod
    def from_env() -> KontextConfig:
        """Create configuration from environment variables."""
        cluster_uri = os.getenv(KontextEnvVarNames.cluster_uri)
        database = os.getenv(KontextEnvVarNames.database)
        embedding_uri = os.getenv(KontextEnvVarNames.embedding_uri)

        # Check for required variables
        missing_vars: list[str] = []
        if not cluster_uri:
            missing_vars.append(KontextEnvVarNames.cluster_uri)
        if not database:
            missing_vars.append(KontextEnvVarNames.database)
        if not embedding_uri:
            missing_vars.append(KontextEnvVarNames.embedding_uri)

        if missing_vars:
            raise ValueError(f"{', '.join(missing_vars)} environment variable(s) are required")

        # At this point we know these are not None due to the checks above
        assert cluster_uri is not None
        assert database is not None
        assert embedding_uri is not None

        memory_table = os.getenv(KontextEnvVarNames.memory_table, "Memory")

        return KontextConfig(
            cluster_uri=cluster_uri,
            database=database,
            embedding_uri=embedding_uri,
            memory_table=memory_table,
        )

    @staticmethod
    def existing_env_vars() -> dict[str, str | None]:
        """Return a dictionary of currently set environment variables for Kontext configuration."""
        return {var_name: os.getenv(var_name) for var_name in KontextEnvVarNames.all()}
