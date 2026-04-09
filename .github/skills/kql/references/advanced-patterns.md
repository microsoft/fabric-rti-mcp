# Advanced KQL Patterns

Reference for specialized KQL features: graph queries, vector similarity, geospatial operations, time series, and external data. Consult this when a task requires these capabilities.

## Table of Contents

1. [Graph Queries](#1-graph-queries)
2. [Vector Similarity](#2-vector-similarity)
3. [Geospatial Operations](#3-geospatial-operations)
4. [Time Series Analysis](#4-time-series-analysis)
5. [External Data](#5-external-data)
6. [Stored Functions](#6-stored-functions)
7. [Materialized Views & Caching](#7-materialized-views--caching)

---

## 1. Graph Queries

KQL's graph model requires building a graph from node/edge tables, then traversing with `graph-match`.

### Building a graph

```kql
// Define nodes and edges
let nodes = YaccApplications | project NodeId = AppId, AppName, HostingIp;
let edges = YaccConnections | project SourceId = SourceAppId, TargetId = TargetAppId, Protocol, Port;

// Build and query
graph(nodes, edges)
| graph-match (src)-[e]->(dst)
  where src.AppName == "Gateway"
  project src.AppName, dst.AppName, e.Protocol
```

### Variable-length traversal

```kql
// Find all paths up to 5 hops from a start node
graph(nodes, edges)
| graph-match (start)-[path*1..5]->(target)
  where start.AppName == "Frontend"
  project start.AppName, target.AppName, hops = array_length(path)
```

### Pre-filtering edges (the key pattern)

Important: **filter edges BEFORE building the graph**, not during traversal. Edge properties are not accessible on variable-length paths during `graph-match`.

```kql
// ❌ WRONG — can't access properties on variable-length edge
graph-match (src)-[path*1..3]->(dst)
  where path.IsVulnerable == true

// ✅ RIGHT — pre-filter edges
let vulnerable_edges = Edges | where IsVulnerable == true;
graph(Nodes, vulnerable_edges)
| graph-match (src)-[path*1..3]->(dst)
  project src.Name, dst.Name
```

### Persistent graph snapshots

For repeated traversals, create a snapshot:

```kql
// Create once (management command)
.create graph-snapshot MyGraph
  <| graph(nodes, edges)

// Query repeatedly
graph("MyGraph")
| graph-match (src)-[e]->(dst)
  where src.Type == "Server"
  project src.Name, dst.Name
```

### graph-to-table for post-processing

```kql
graph(nodes, edges)
| graph-match (src)-[e]->(dst)
  project src.Name, dst.Name, e.Weight
| graph-to-table
| summarize TotalWeight = sum(Weight) by src_Name
| top 10 by TotalWeight desc
```

---

## 2. Vector Similarity

KQL has native vector operations — **don't export to Python** for cosine similarity.

### series_cosine_similarity

The most common vector operation.

```kql
// Find the most similar items to a target vector
let target_vec = toscalar(
    Embeddings | where Word == "test" | project Vec
);
Embeddings
| extend similarity = series_cosine_similarity(parse_json(Vec), target_vec)
| top 10 by similarity desc
```

### Combining vectors

```kql
// Weighted vector combination (e.g., word1 * 0.5 + word2 * 0.3 + word3 * 0.2)
let v1 = toscalar(Vecs | where Word == "hello" | project Vec);
let v2 = toscalar(Vecs | where Word == "world" | project Vec);
let v3 = toscalar(Vecs | where Word == "test" | project Vec);
let combined = series_add(
    series_add(
        series_multiply(v1, repeat(0.5, array_length(v1))),
        series_multiply(v2, repeat(0.3, array_length(v2)))
    ),
    series_multiply(v3, repeat(0.2, array_length(v3)))
);
```

### Performance consideration

Pairwise cosine similarity on 1536-dim vectors is expensive (~20s for large tables). Strategies:

1. **Pre-filter** — narrow candidates before computing similarity
2. **Round-and-join** — bucket vector dimensions to integers, join on buckets for approximate matching
3. **Project away vectors** — never include vector columns in results unless needed

```kql
// Round-and-join for approximate nearest neighbor
let target_rounded = toscalar(
    Vecs | where Word == "test"
    | project r = array_sort_asc(series_multiply(Vec, repeat(100, array_length(Vec))))
);
Vecs
| extend rounded = array_sort_asc(series_multiply(Vec, repeat(100, array_length(Vec))))
| where rounded[0] between (target_rounded[0]-10 .. target_rounded[0]+10)
| extend sim = series_cosine_similarity(Vec, toscalar(Vecs | where Word == "test" | project Vec))
| top 10 by sim desc
```

### Other series functions

| Function | Purpose |
|----------|---------|
| `series_cosine_similarity(a, b)` | Cosine similarity between two vectors |
| `series_pearson_correlation(a, b)` | Pearson correlation |
| `series_dot_product(a, b)` | Dot product |
| `series_add(a, b)` | Element-wise addition |
| `series_multiply(a, b)` | Element-wise multiplication |
| `series_subtract(a, b)` | Element-wise subtraction |
| `series_magnitude(a)` | L2 norm |

---

## 3. Geospatial Operations

### Point-in-polygon

```kql
// Check if a point is inside a polygon
| where geo_point_in_polygon(Longitude, Latitude,
    dynamic({"type":"Polygon","coordinates":[[[lon1,lat1],[lon2,lat2],...,[lon1,lat1]]]}))
```

Note: `geo_point_in_polygon` is a **scalar function**, not a plugin. It works on free clusters. Don't try to `evaluate` it as a plugin — use it directly in `| where` or `| extend`.

### Distance calculations

```kql
// Distance between two points (returns meters)
| extend distance_m = geo_distance_2points(Lon1, Lat1, Lon2, Lat2)

// Filter by distance
| where geo_distance_2points(Lon, Lat, -122.33, 47.61) < 5000  // within 5km of Seattle
```

### Spatial bucketing for joins

KQL joins are equality-only, so spatial proximity joins need pre-bucketing:

```kql
// S2 cells (Google's spatial index)
| extend cell = geo_point_to_s2cell(Longitude, Latitude, 8)  // level 8 ≈ 30km²

// H3 cells (Uber's spatial index)
| extend cell = geo_point_to_h3cell(Longitude, Latitude, 5)  // resolution 5 ≈ 253km²

// Then join on cell IDs
TableA
| extend cell = geo_point_to_s2cell(Lon, Lat, 10)
| join kind=inner (TableB | extend cell = geo_point_to_s2cell(Lon, Lat, 10)) on cell
```

### IP geolocation

```kql
// Lookup IP addresses against a geo table
| evaluate ipv4_lookup(IpGeoTable, ClientIP, IpRange)

// Check if IP is in a range
| where ipv4_is_in_range(ClientIP, "10.0.0.0/8")

// Compare two IPs for subnet membership
| where ipv4_is_in_any_range(ClientIP, dynamic(["10.0.0.0/8", "172.16.0.0/12"]))
```

---

## 4. Time Series Analysis

### Creating time series

```kql
// Basic time series
Events
| make-series count() default=0 on Timestamp step 1h
| render timechart

// Multi-series (one per category)
Events
| make-series count() default=0 on Timestamp step 1h by Category
```

### Anomaly detection

```kql
// Decompose and find anomalies
Events
| make-series count() default=0 on Timestamp step 1h
| extend (anomalies, score, baseline) = series_decompose_anomalies(count_)
| mv-expand Timestamp, count_, anomalies, score, baseline
| where anomalies != 0
```

### Period detection

```kql
// Find periodic patterns
Events
| make-series count() default=0 on Timestamp step 1m
| extend (periods, scores) = series_periods_detect(count_, 4.0, 1440.0, 2)
```

### Sessionization

```kql
// Group events into sessions with 30-minute gap
Events
| order by UserId, Timestamp asc
| extend SessionId = row_window_session(Timestamp, 30m, 24h, UserId != prev(UserId))
```

### Sliding window statistics

```kql
// Rolling average over 7 days
| make-series val=avg(Value) on Timestamp step 1d
| extend rolling_avg = series_fir(val, repeat(1.0/7, 7), false)
```

---

## 5. External Data

Load external files directly into KQL without ingestion:

```kql
// CSV from blob storage
let external_csv = external_data(col1:string, col2:long)
  [h@'https://storage.blob.core.windows.net/container/file.csv']
  with (ignoreFirstRecord=true);
external_csv | where col2 > 100
```

```kql
// Gzipped CSV
let primes = external_data(prime:long)
  [h@'https://yourstorage.blob.core.windows.net/prime-numbers/prime-numbers.csv.gz']
  with (ignoreFirstRecord=true);
primes | where prime < 100000000 | summarize max(prime)
```

**Limitations**: `external_data` handles tabular formats (CSV, TSV, JSON lines). For non-tabular content (images, PDFs, JavaScript), use the browser or Python.

---

## 6. Stored Functions

Some databases include pre-built stored functions (e.g., `Decrypt`, `Dekrypt`, `Verify`).

### Discovering stored functions

```kql
// Management command — use kusto_command or kusto_list_entities(entity_type="functions")
.show functions
```

### Invoking stored functions

```kql
// Call a stored function
Decrypt(ciphertext, key)

// Use in a query pipeline
Logs
| extend plaintext = Decrypt(EncryptedField, "MYKEY")
| where plaintext contains "suspicious"
```

### Common pitfalls with stored functions

1. **String escaping**: KQL uses single quotes for string literals. If the key contains special characters, use `@""` syntax:
   ```kql
   Decrypt(field, @"KEY'WITH'QUOTES")
   ```
2. **Argument types**: Ensure you pass the right type. If the function expects `string` and you have `dynamic`, cast with `tostring()`.
3. **Function not found**: Check the database — functions are database-scoped. Use `.show functions` to list available ones.

---

## 7. Materialized Views & Caching

### materialize() for subquery reuse

When a subquery is referenced multiple times, `materialize()` computes it once:

```kql
let expensive_result = materialize(
    HugeLogs
    | where Timestamp > ago(1d)
    | summarize count() by SourceIP
    | where count_ > 1000
);
// Use it twice without recomputing
expensive_result | summarize total = sum(count_)
| union (expensive_result | top 10 by count_ desc)
```

### toscalar() for single-value subqueries

```kql
// Extract a single value to use as a constant
let threshold = toscalar(Stats | summarize percentile(Value, 95));
Events | where Value > threshold
```

### datatable for inline test data

```kql
// Create test data without touching the database
let test_data = datatable(Name:string, Score:long) [
    "Alice", 95,
    "Bob", 87,
    "Charlie", 92
];
test_data | where Score > 90
```

Use `datatable` + `print` to test transformations on small samples before running on full tables.
