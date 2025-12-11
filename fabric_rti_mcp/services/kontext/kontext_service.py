import time
from typing import Any, Literal, Protocol

from azure.kusto.data import KustoClient
from azure.kusto.data.exceptions import KustoServiceError
from azure.kusto.ingest import KustoStreamingIngestClient

from fabric_rti_mcp.config import logger
from fabric_rti_mcp.services.kontext.kontext_config import KontextConfig
from fabric_rti_mcp.services.kusto.kusto_connection import KustoConnection


class KontextProtocol(Protocol):
    """Protocol defining the interface for Kontext memory clients."""

    @property
    def config(self) -> KontextConfig:
        """Return the configuration for the Kontext client."""
        ...

    def is_ready(self) -> bool:
        """Check if the Kusto database is ready for queries."""
        ...

    def setup(self) -> None:
        """Set up the working tables."""
        ...

    def remember(self, item: str, type: str, scope: Literal["user", "global"] = "user") -> str:
        """Ingest a memory item into the Kusto database. Returns the ID of the ingested fact."""
        ...

    def recall(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
        top_k: int | None = None,
        scope: Literal["user", "global"] = "user",
    ) -> list[dict[str, Any]]:
        """Recall facts from the Kusto database based on a query and metadata filters."""
        ...


MEMORY_TABLE_SCHEMA = "id:string,item:string,type:string,scope:string,creation_time:datetime,embedding:dynamic"


class KontextClient(KontextProtocol):
    """Client for interacting with Kontext memory service backed by Kusto."""

    def __init__(self, config: KontextConfig):
        """
        Initialize the Kusto client with the cluster URI.
        """
        self._config = config
        self._connection: KustoConnection | None = None
        # Cache the value of is_ready to avoid repeated checks.
        self._ready: bool = False
        # Cache the scope retrieved from principal roles.
        self._scope_cache: str | None = None

    def _connect(self) -> None:
        if not self._connection:
            self._connection = KustoConnection(
                cluster_uri=self.config.cluster_uri, default_database=self.config.database
            )

    def _execute(self, kql: str, database: str | None = None) -> list[dict[str, Any]]:
        try:
            # Build connection string using device authentication
            client = self.get_query_provider()
            # Execute query
            db_name = database or self.config.database
            response = client.execute(db_name, kql)

            # Convert response to list of dictionaries
            results: list[dict[str, Any]] = []
            if response.primary_results:
                primary_result = response.primary_results[0]
                for row in primary_result:
                    results.append(dict(zip([col.column_name for col in primary_result.columns], row)))

            return results

        except KustoServiceError as e:
            logger.error(f"Kusto service error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise

    def get_query_provider(self) -> KustoClient:
        self._connect()
        assert self._connection is not None
        return self._connection.query_client

    def get_ingest_provider(self) -> KustoStreamingIngestClient:
        self._connect()
        assert self._connection is not None
        return self._connection.ingestion_client

    @property
    def config(self) -> KontextConfig:
        """Return the configuration for the Kontext client."""
        return self._config

    def setup(self) -> None:
        """Set up the working tables. If already set up, this is a no-op."""
        try:
            if self.is_ready():
                return
            self._connect()
            # Create the memory table (kusto creation command just skips if it exists)
            create_table_kql = f"""
            .create table {self.config.memory_table} ({MEMORY_TABLE_SCHEMA})
            """
            self._execute(create_table_kql, self.config.database)
            logger.info(f"Memory table '{self.config.memory_table}' is ready.")
        except KustoServiceError as e:
            logger.error(f"Kusto service error during setup: {e}")
            raise

    def is_ready(self) -> bool:
        """Check if the Kusto database is ready for queries."""
        # no need to check again if already ready (unless we called a destructive command, which we don't have yet)
        if self._ready:
            return True

        try:
            self._connect()
            # Perform a simple query to check readiness
            resp: list[dict[str, Any]] = self._execute(".show database cslschema", self.config.database)
            if resp and len(resp) > 0:
                memory_table = next(
                    (table for table in resp if table.get("TableName") == self.config.memory_table),
                    None,
                )
                if memory_table:
                    self._ready = memory_table.get("Schema") == MEMORY_TABLE_SCHEMA
        except KustoServiceError as e:
            logger.error(f"Kusto service error: {e}")

        except Exception as e:
            logger.error(f"Error checking database readiness: {e}")

        return self._ready

    def _retrieve_scope(self) -> str:
        """
        Retrieve scope from Kusto principal roles.
        Executes once and caches the result. Falls back to 'global' if query fails or returns null.

        :return: The scope string (display name prefix or 'global')
        """
        if self._scope_cache is not None:
            return self._scope_cache

        try:
            self._connect()
            query = ".show principal roles | take 1 | project split(DisplayName, '(')[0]"
            results = self._execute(query, self.config.database)

            if results and len(results) > 0:
                # Get the first column value from the first row
                first_row = results[0]
                # The result will have a single column, get its value
                scope_value = next(iter(first_row.values()), None)

                if scope_value and isinstance(scope_value, str) and scope_value.strip():
                    self._scope_cache = scope_value.strip()
                    logger.info(f"Retrieved scope from principal roles: '{self._scope_cache}'")
                else:
                    self._scope_cache = "global"
                    logger.info("Scope query returned null or empty, using default: 'global'")
            else:
                self._scope_cache = "global"
                logger.info("Scope query returned no results, using default: 'global'")

        except Exception as e:
            logger.warning(f"Failed to retrieve scope from principal roles: {e}. Using default: 'global'")
            self._scope_cache = "global"

        return self._scope_cache

    def _determine_scope(self, scope: Literal["user", "global"]) -> str:
        """
        Resolve the effective scope based on preference and available identifiers.

        If scope is "global", returns "global".
        If scope is "user", retrieves the user-specific identifier from principal roles.
        Falls back to "global" if the user identifier is unavailable or equals "global".
        """
        if scope == "global":
            return "global"

        user_scope = self._retrieve_scope()
        if user_scope and user_scope.strip().lower() != "global":
            return user_scope.strip()

        logger.info("User identifier unavailable or invalid, falling back to 'global' scope")
        return "global"

    def remember(self, item: str, type: str, scope: Literal["user", "global"] = "user") -> str:
        id = f"fact_{int(time.time())}"
        try:
            self.setup()
            resolved_scope = self._determine_scope(scope)
            command = f""".set-or-append {self.config.memory_table} <|
            print
                id="{id}",
                item="{item}",
                type="{type}",
                scope="{resolved_scope}",
                creation_time=now(),
                embedding=toscalar(evaluate ai_embeddings("{item}", "{self.config.embedding_uri}"))
            """

            self._execute(command, self.config.database)
            return id
        except Exception as e:
            logger.error(f"Error ingesting memory {id}: {e}")
            raise

    def recall(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
        top_k: int | None = 10,
        scope: Literal["user", "global"] = "user",
    ) -> list[dict[str, Any]]:
        try:
            self.setup()
            resolved_scope = self._determine_scope(scope)

            # Build the query with inline embedding generation
            kql_query = f"""
            let q_vec = toscalar(evaluate ai_embeddings("{query}", "{self.config.embedding_uri}"));
            {self.config.memory_table}
            | extend sim = series_cosine_similarity(embedding, q_vec)
            | project-away embedding
            | where sim > 0
            | where scope == '{resolved_scope}'
            """

            if filters:
                if "type" in filters:
                    kql_query += f" | where type == '{filters['type']}'"

            kql_query += " | order by sim desc"

            if top_k is not None:
                kql_query += f" | take {top_k}"

            results = self._execute(kql_query, self.config.database)

            return results

        except Exception as e:
            logger.error(f"Error recalling facts for query '{query}': {e}")
            raise


class KontextClientCache:
    """Singleton cache for Kontext client to avoid repeated authentication."""

    _client: KontextClient | None = None
    _config_hash: str | None = None

    @classmethod
    def get_client(cls, config: KontextConfig | None = None) -> KontextClient:
        """
        Get or create a cached Kontext client.

        :param config: Optional configuration. If None, loads from environment.
        :return: Cached or new KontextClient instance
        """
        if config is None:
            config = KontextConfig.from_env()

        # Create a simple hash of the config to detect changes
        config_hash = f"{config.cluster_uri}:{config.database}:{config.embedding_uri}:{config.memory_table}"

        # Return cached client if config hasn't changed
        if cls._client is not None and cls._config_hash == config_hash:
            return cls._client

        # Create new client if config changed or no client exists
        cls._client = KontextClient(config)
        cls._config_hash = config_hash
        logger.info(f"Created Kontext client for cluster: {config.cluster_uri}")

        return cls._client
