# Kontext Memory Service

**Semantic memory for AI agents integrated into Fabric RTI MCP.**

Kontext transforms Azure Data Explorer (Kusto) into a sophisticated context engine that goes beyond simple vector storage. While traditional vector DBs only store embeddings, Kontext provides layered memory with rich temporal and usage signals—combining recency, frequency, semantic similarity, and temporal awareness.

This service has been integrated into the fabric-rti-mcp server, providing memory capabilities alongside other Fabric services.

## Overview

Kontext provides two powerful MCP tools for intelligent memory management:

### `remember`
```python
remember(fact: str, type: str, scope: Optional[str] = "global") -> str
```
Stores a memory item in the Kusto-backed memory store with automatic embedding generation.

**Parameters:**
- `fact`: Text to remember
- `type`: Memory type (`"fact"`, `"context"`, or `"thought"`)
- `scope`: Memory scope (defaults to `"global"`)

**Returns:** Unique ID of the stored memory

### `recall`
```python
recall(query: str, filters: Optional[Dict[str, Any]] = None, top_k: int = 10) -> List[Dict[str, Any]]
```
Retrieves relevant memories using semantic similarity and KQL-powered ranking.

**Parameters:**
- `query`: Search query for semantic matching
- `filters`: Optional filters (e.g., `{"type": "fact", "scope": "global"}`)
- `top_k`: Maximum number of results to return

**Returns:** List of memory objects with metadata (`id`, `fact`, `type`, `scope`, `creation_time`, `sim`)

## Why Kontext?

**The Gap**: Agents need intelligent memory that considers not just semantic similarity, but also temporal patterns, usage frequency, and contextual relevance. Most vector databases fall short by ignoring these rich signals and locking you into a single cloud provider.

**The Solution**: Kontext leverages Kusto's powerful query language (KQL) to score and rank memories using multiple dimensions:

```kql
// Conceptual query for scoring memories
Memory 
| extend score = w_t * exp(-ago(ingest)/7d) * 
                 w_f * log(1+hits) * 
                 w_s * cosine_sim * 
                 w_p * pin 
| top 20 by score
```

## Key Benefits

- **Temporal Reasoning**: Native timestamp handling, retention policies, and time-decay scoring
- **Semantic Retrieval**: Built-in vector columns with cosine similarity search  
- **Expressive Ranking**: KQL enables complex scoring that weighs time, frequency, pins, and semantics
- **Cost Effective**: Free tier with instant provisioning and predictable scaling
- **True Portability**: Simple MCP API keeps your models and cloud providers interchangeable

## Architecture

```
Agent ⇆ Kontext MCP
         ├── remember(fact, meta)
         └── recall(query, meta)
                  ↓
           Azure Kusto
```

**Ingest**: Text splitting → embedding generation → vector + metadata storage  
**Retrieve**: KQL-powered scoring combines temporal, frequency, semantic, and pin signals

## Configuration

### Prerequisites

Before using Kontext, you need to run these commands on your Kusto cluster to enable managed identity and Azure OpenAI callouts:

**1. Enable Managed Identity for Azure AI:**
```kql
.alter database KustoMemoryTest policy managed_identity ```
[
  {
    "ObjectId": "system",
    "AllowedUsages": "AzureAI"
  }
]```
```

**2. Enable Azure OpenAI Callout Policy:**
```kql
.alter-merge cluster policy callout
```
[
  {
    "CalloutType": "azure_openai",
    "CalloutUriRegex": "https://[A-Za-z0-9-]{3,63}\\.(?:openai\\.azure\\.com|cognitiveservices\\.azure\\.com|cognitive\\.microsoft\\.com|services\\.ai\\.azure\\.com)(?:/.*)?",
    "CanCall": true
  }
]
```
```

### Environment Variables

Kontext is integrated into the fabric-rti-mcp server and requires the following environment variables:

**Environment Variables:**
- `KONTEXT_CLUSTER`: Your Azure Data Explorer cluster URL (e.g., `https://your-cluster.kusto.windows.net/`)
- `KONTEXT_DATABASE`: Database name for storing memories
- `KONTEXT_TABLE`: Table name for memory storage (default: "Memory")
- `KONTEXT_EMBEDDING_URI`: Azure OpenAI endpoint for embedding generation

Example:
```bash
export KONTEXT_CLUSTER="https://your-cluster.kusto.windows.net/"
export KONTEXT_DATABASE="your-database"
export KONTEXT_TABLE="Memory"
export KONTEXT_EMBEDDING_URI="https://your-openai.azure.com/openai/deployments/text-embedding-3-large/embeddings?api-version=2023-05-15;managed_identity=system"
```

The kontext tools will be available as part of the fabric-rti-mcp server once these variables are configured.

## Current Features

- **remember**: Store facts with automatic embedding generation using Kusto's `ai_embeddings()` plugin
- **recall**: Retrieve semantically similar facts using cosine similarity search
- **FastMCP Integration**: Built on the FastMCP framework for easy tool registration and schema generation
- **Kusto Backend**: Leverages Azure Data Explorer for scalable storage and querying

## Roadmap

- **Advanced Scoring**: Multi-dimensional ranking with temporal decay, frequency weighting, and pin support
- **Memory Tiers**: Short-term context, working memory, and long-term fact storage
- **Hosted Embeddings**: Optional E5 model hosting to reduce setup friction
- **Enhanced Caching**: Multi-tier memory management and query optimization



## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
