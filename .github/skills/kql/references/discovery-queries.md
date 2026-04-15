# KQL Schema Discovery Queries

Reference for schema exploration commands. Use these to understand a database's structure before writing queries.

---

## Table and Column Discovery

### Table Discovery

```kql
// List all tables with row counts and sizes
.show tables details
| project TableName, TotalRowCount, TotalOriginalSize, TotalExtentSize, HotOriginalSize

// List tables (names only)
.show tables
| project TableName

// Table schema (column names, types, folder)
.show table StormEvents schema as json

// Table schema as CSL (for scripting)
.show table StormEvents cslschema

// Compact column listing (CSL format)
.show table StormEvents cslschema
| project TableName, Schema
```

### Column Statistics

```kql
// Column cardinality and statistics (sample-based)
.show table StormEvents column statistics

// Quick column profiling via query
StormEvents
| take 10000
| summarize
    Rows = count(),
    Nulls = countif(isnull(BeginLat)),
    Distinct = dcount(State),
    MinVal = min(StartTime),
    MaxVal = max(StartTime)
```

---

## Function and View Discovery

### Function Discovery

```kql
// List all stored functions
.show functions
| project Name, Parameters, Body = substring(Body, 0, 100), DocString, Folder

// Full function definition
.show function MyFunction2

// Functions in a folder
.show functions
| where Folder == "Demo"
```

### Materialized View Discovery

```kql
// List all materialized views
.show materialized-views
| project Name, SourceTable, Query = substring(Query, 0, 100), IsEnabled, IsHealthy

// View statistics (lag, processed records)
.show materialized-view DailyCovid19 statistics

// View extents
.show materialized-view DailyCovid19 extents
| summarize ExtentCount = count(), TotalRows = sum(RowCount)
```

---

## Policy Discovery

```kql
// Retention policies
.show table StormEvents policy retention

// Caching policies
.show table StormEvents policy caching

// Streaming ingestion policy
.show table StormEvents policy streamingingestion

// Update policies
.show table StormEvents policy update

// All major policies for a table (run individually):
// retention, caching, streamingingestion, update, merge, sharding
```

---

## External Tables and Ingestion Mappings

### External Table Discovery

```kql
// List external tables
.show external tables
| project TableName, TableType, Folder, ConnectionStrings

// External table schema
.show external table TaxiRides schema as json
```

### Ingestion Mapping Discovery

```kql
// CSV mappings for a table
.show table StormEvents ingestion csv mappings

// JSON mappings for a table
.show table StormEvents ingestion json mappings

// All mappings for a table
.show table StormEvents ingestion mappings
```

---

## Graph Model Discovery

```kql
// List all graph models
.show graph_models

// Show a specific graph model definition
.show graph_model Simple

// List graph snapshots
.show graph_snapshots
```

---

## Security Discovery

```kql
// Database-level principals
.show database Samples principals

// Table-level principals
.show table StormEvents principals

// Current identity
print CurrentUser = current_principal(), Cluster = current_cluster_endpoint()
```

---

## Database Overview Script

Run this sequence to get a complete picture of a KQL Database:

```kql
// 1. Database stats (uses current database context)
.show database datastats

// 2. All tables with details
.show tables details
| project TableName, TotalRowCount, TotalOriginalSize, CachingPolicy
| order by TotalRowCount desc

// 3. All functions
.show functions
| project Name, Folder, DocString, Parameters

// 4. All materialized views
.show materialized-views
| project Name, SourceTable, IsEnabled, IsHealthy

// 5. All external tables
.show external tables

// 6. All graph models
.show graph_models
```

---

## Advanced Troubleshooting

Commands for diagnosing ingestion failures, throttling, capacity issues, and cluster health.

### Ingestion Failures

When data isn't showing up after ingestion, check for failures (retained for 14 days):

```kql
// Show all recent ingestion failures
.show ingestion failures

// Filter to a specific table
.show ingestion failures
| where Table == "StormEvents"
| where FailedOn > ago(1d)
| project FailedOn, Table, FailureKind, ErrorCode, Details
| order by FailedOn desc

// Check a specific operation
.show ingestion failures with (OperationId = 'GUID-HERE')
```

Key columns: `FailureKind` (Permanent vs Transient), `ErrorCode`, `Details`, `OriginatesFromUpdatePolicy`.

### Cluster Capacity

Check whether the cluster is running out of capacity for ingestion, merges, exports, or other operations:

```kql
// Show capacity for all resource types
.show capacity

// Show capacity for a specific operation
.show capacity ingestions
.show capacity extents-merge
.show capacity data-export
.show capacity materialized-view
.show capacity extents-partition
```

Returns `Total`, `Consumed`, and `Remaining` for each resource. If `Remaining` is 0, operations are being throttled.

### Cluster Diagnostics

```kql
// Cluster health and node state
.show diagnostics

// Currently running queries (useful for identifying long-running or stuck queries)
.show queries

// Completed commands and their resource usage
.show commands
| where StartedOn > ago(1h)
| project CommandType, StartedOn, Duration, State, ResourceUtilization

// Combined view of commands and queries
.show commands-and-queries
| where StartedOn > ago(1h)
| order by StartedOn desc

// Administrative operations log
.show operations
| where StartedOn > ago(1d)
| where State == "Failed"
```

### Workload Groups

Workload groups control resource governance — per-request limits, rate limits, and concurrency. If queries are being throttled or rejected, check workload group configuration:

```kql
// Show all workload groups and their policies
.show workload_group default

// Monitor requests by workload group
.show commands-and-queries
| where StartedOn > ago(1h)
| summarize count(), avg(Duration), sum(TotalCPU) by WorkloadGroup
```

Built-in workload groups:
- **`default`** — catches all requests not classified elsewhere
- **`internal`** — internal system requests (cannot be modified)
- **`$materialized-views`** — materialized view materialization process

### Troubleshooting Decision Tree

| Symptom | First command | What to look for |
|---------|--------------|------------------|
| Data not appearing after ingestion | `.show ingestion failures` | `FailureKind`, `ErrorCode`, `Details` |
| Queries running slowly or timing out | `.show capacity` | `Remaining` = 0 on any resource |
| Queries being rejected/throttled | `.show workload_group default` | Rate limits, concurrent request caps |
| Cluster unresponsive | `.show diagnostics` | Node health, memory pressure |
| Merges falling behind | `.show capacity extents-merge` | `Remaining` = 0 |
| Materialized views stale | `.show materialized-view DailyCovid19 statistics` | Materialization lag |
