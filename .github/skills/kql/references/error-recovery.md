# Error Recovery Reference

Complete mapping of common KQL error patterns. For each error: the exact message, a real query that triggered it, and the fix.

## Table of Contents

1. [E_LOW_MEMORY_CONDITION](#1-e_low_memory_condition)
2. [Join Errors](#2-join-errors)
3. [Network / Transient](#3-network--transient)
4. [Dynamic Type Errors](#4-dynamic-type-errors)
5. [Unresolved Names](#5-unresolved-names)
6. [Syntax Errors](#6-syntax-errors)
7. [String Comparison](#7-string-comparison)
8. [extract_all Regex Groups](#8-extract_all-regex-groups)
9. [Serialization Required](#9-serialization-required)
10. [Missing Plugins](#10-missing-plugins)
11. [graph-match Syntax](#11-graph-match-syntax)
12. [E_RUNAWAY_QUERY](#12-e_runaway_query)

---

## 1. E_LOW_MEMORY_CONDITION

**Error message**: `Query execution lacks memory resources to complete (80DA0007): Partial query failure: Low memory condition (E_LOW_MEMORY_CONDITION)`

### Pattern A: Unfiltered aggregation on large table

```kql
// ❌ TRIGGERED ERROR — large table, no pre-filter, too many group-by columns
StormEvents
| summarize dcount(EventType), count() by StartTime, State, Source
| where dcount_EventType > 1

// ✅ FIX — filter first, reduce grouping columns
StormEvents
| where StartTime between (datetime(2007-04-15) .. datetime(2007-04-16))
| summarize dcount(EventType) by State, Source
| where dcount_EventType > 1
```

### Pattern B: Join explosion

```kql
// ❌ TRIGGERED ERROR — unconstrained join between two large tables
StormEvents
| join kind=inner (PopulationData) on State

// ✅ FIX — pre-filter both sides, check cardinality first
let filtered_storms = StormEvents | where State == "TEXAS" | summarize by State;
let target_states = PopulationData | project State;
filtered_storms | join kind=inner (target_states) on State
```

### Pattern C: High-cardinality dcount()

```kql
// ❌ TRIGGERED ERROR — Full distinct value enumeration on many columns
StormEvents | summarize dcount(EventType), dcount(Source), dcount(BeginLocation) by bin(StartTime, 1h)

// ✅ FIX — filter first, reduce to one dcount
StormEvents
| where StartTime between (datetime(2007-06-01) .. datetime(2007-06-30T23:59:59))
| summarize dcount(EventType) by bin(StartTime, 1h)
```

**Recovery strategy**: When you see this error, your query is touching too much data. Options:
1. Add `| where` time-range or partition filter
2. Reduce `by` columns in `summarize`
3. Break the query into smaller time windows
4. Use `| sample 10000` for exploration

---

## 2. Join Errors

### 2a. Left/right attribute mismatch

**Error message**: `join: for each left attribute, right attribute should be selected.`

```kql
// ❌ TRIGGERED ERROR — incomplete on clause
StormEvents | join kind=inner PopulationData on $left.State

// ✅ FIX — specify both sides
StormEvents | join kind=inner (PopulationData) on $left.State == $right.State
```

```kql
// ❌ TRIGGERED ERROR — expression in join condition
StormEvents | join kind=inner (PopulationData) on $left.State == $right.tolower(State)

// ✅ FIX — pre-compute the expression, join on the computed column
StormEvents
| join kind=inner (PopulationData | extend StateLower = tolower(State)) on $left.State == $right.StateLower
```

### 2b. Equality only

**Error message**: `join: Only equality is allowed in this context.`

```kql
// ❌ TRIGGERED ERROR — geo-distance in join predicate
StormEvents | join (nyc_taxi) on geo_distance_2points(BeginLon, BeginLat, pickup_longitude, pickup_latitude) < 1000

// ✅ FIX — pre-bucket into spatial cells
StormEvents
| extend cell = geo_point_to_s2cell(BeginLon, BeginLat, 8)
| join kind=inner (nyc_taxi | extend cell = geo_point_to_s2cell(pickup_longitude, pickup_latitude, 8)) on cell
| where geo_distance_2points(BeginLat, BeginLon, pickup_latitude, pickup_longitude) < 1000
```

```kql
// ❌ TRIGGERED ERROR — range join
StormEvents | join (PopulationData) on $left.DamageProperty > $right.Population

// ✅ FIX — bin values and join on bins
StormEvents
| extend damage_bin = bin(DamageProperty, 1000000)
| join kind=inner (PopulationData | extend damage_bin = bin(Population, 1000000)) on damage_bin
| where DamageProperty > Population
```

---

## 3. Network / Transient

**Error message**: `Failed to process network request for the endpoint: https://kvc4bf3...`

Cause: Corrupted cluster URIs or genuine network timeouts.

**Recovery strategy**: 
1. Verify the cluster URI is clean ASCII (no Unicode characters)
2. Retry with a fresh URI from the environment variable
3. If persistent, wait 30 seconds and retry (cluster may be overloaded)

---

## 4. Dynamic Type Errors

### 4a. Summarize by dynamic

**Error message**: `Summarize group key 'Area' is of a 'dynamic' type. Please use an explicit cast`

```kql
// ❌
| summarize count() by Area
// ✅
| summarize count() by tostring(Area)
```

### 4b. Order by dynamic

**Error message**: `order operator: key can't be of dynamic type`

```kql
// ❌
| order by Properties.Score desc
// ✅
| order by todouble(Properties.Score) desc
```

### 4c. Join on dynamic

**Error message**: `join key 'Area' is of a 'dynamic' type. Please use an explicit cast`

```kql
// ❌
| join kind=inner other on Area
// ✅
| extend Area_str = tostring(Area)
| join kind=inner (other | extend Area_str = tostring(Area)) on Area_str
```

---

## 5. Unresolved Names

**Error message**: `Failed to resolve column or scalar expression named 'X'` or `Failed to resolve entity 'X'`

### Common causes

| Cause | Example |
|-------|---------|
| Invented column name | `NewVIN` (doesn't exist; actual is `VIN`) |
| Wrong table | Queried `Traffic` instead of `CarsTraffic` |
| Table not yet ingested or in different database | Table not found |
| Typo | `EstimatedHackersCount` vs actual column name |
| Let-variable scope | Variable defined in different query |

**Recovery strategy**:
1. Use `kusto_describe_database_entity` to check exact column names
2. Check exact table and column names — KQL is case-sensitive for column names
3. If querying a table that should exist but doesn't, check which database you're connected to
4. Most unresolved names are matchable against the cached schema — look for similar names

---

## 6. Syntax Errors

### 6a. Management command in query pipe

**Error message**: `Unexpected control command`

This error occurs when a query pipes INTO a management command (not the other way around — management commands CAN have query operators piped after them). With Fabric RTI MCP, use `kusto_command` for management commands and `kusto_query` for queries.

```kql
// ✅ WORKS — management output is tabular, can be filtered
.show tables | project TableName | where TableName has "Events"

// ❌ ERROR — query piped into management command
StormEvents | take 5 | .show tables
```

### 6b. Reserved words as identifiers

**Error message**: `The name 'shards' needs to be bracketed as ['shards']`

```kql
// ❌
let shards = ...

// ✅
let ['shards'] = ...
// Or better: rename the variable
let shard_info = ...
```

### 6c. Syntax: Expected comma

Various syntax issues, usually from mixing SQL syntax into KQL:

```kql
// ❌ SQL-style
SELECT * FROM Table WHERE x = 1

// ✅ KQL-style
Table | where x == 1
```

---

## 7. String Comparison

**Error message**: `Cannot compare values of types string and string. Try adding explicit casts`

Despite both sides being strings, KQL sometimes requires explicit casts for computed values.

```kql
// ❌ — S2 cell comparison
StormEvents
| extend startCell = geo_point_to_s2cell(BeginLon, BeginLat, 16)
| join kind=inner (nyc_taxi | extend startCell = geo_point_to_s2cell(pickup_longitude, pickup_latitude, 16)) on startCell

// ✅ — explicit tostring()
StormEvents
| extend startCell = tostring(geo_point_to_s2cell(BeginLon, BeginLat, 16))
| join kind=inner (nyc_taxi | extend startCell = tostring(geo_point_to_s2cell(pickup_longitude, pickup_latitude, 16))) on startCell
```

This occurs most often with `geo_point_to_s2cell()`, `hash()`, and `strcat()` return values.

---

## 8. extract_all Regex Groups

**Error message**: `extractall(): argument 2 must be a valid regex with [1..16] matching groups`

```kql
// ❌ — Missing capturing group
StormEvents | extend words = extract_all(@"[a-zA-Z]{3,}", tolower(EventNarrative))

// ✅ — Add parentheses
StormEvents | extend words = extract_all(@"([a-zA-Z]{3,})", tolower(EventNarrative))
```

Unlike Python's `re.findall()`, KQL's `extract_all` requires at least one `()` group.

---

## 9. Serialization Required

**Error message**: `Function 'row_cumsum' cannot be invoked. The row set must be serialized.`

```kql
// ❌
StormEvents
| where State == "TEXAS"
| summarize DailyCount = count() by bin(StartTime, 1d)
| extend CumulativeCount = row_cumsum(DailyCount)

// ✅ — add order by (implicitly serializes)
StormEvents
| where State == "TEXAS"
| summarize DailyCount = count() by bin(StartTime, 1d)
| order by StartTime asc
| extend CumulativeCount = row_cumsum(DailyCount)
```

Affected functions: `row_number()`, `row_cumsum()`, `prev()`, `next()`, `row_window_session()`.

---

## 10. Missing Plugins

**Error message**: `plugin 'geo_point_in_polygon': plugin doesn't exist.`

Some KQL functions are plugins that may not be enabled on free-tier clusters.

**Recovery strategy**: Use the equivalent non-plugin function or fall back to Python for that specific operation.

| Plugin | Status on free cluster | Alternative |
|--------|----------------------|-------------|
| `geo_point_in_polygon` (as plugin) | ❌ Not available | Use as scalar function: `geo_point_in_polygon(lon, lat, polygon)` |
| `python` | ❌ Not available | Use powershell tool to run Python locally |

---

## 11. graph-match Syntax

**Error message**: `graph-match operator: variable edge 'path' edges don't have property 'IsVulnerable'`

```kql
// ❌ — property access on variable-length edge
graph-match (src)-[path*1..3]->(dst)
  where path.IsVulnerable == true

// ✅ — filter edges before building the graph
let edges = Edges | where IsVulnerable == true;
edges
| make-graph SourceId --> TargetId with Nodes on NodeId
| graph-match (src)-[path*1..3]->(dst)
  project src.Name, dst.Name

// ✅ — or use label-based filtering on persistent graphs
graph("MyGraph")
| graph-match (src)-[path*1..3]->(dst)
  where all(path, labels() has "Vulnerable")
  project src.Name, dst.Name
```

The fix is to pre-filter edges before graph construction.

---

## 12. E_RUNAWAY_QUERY

**Error message**: `Runaway query (E_RUNAWAY_QUERY): Join output block exceeded memory budget`

```kql
// ❌ — unconstrained cross-join on large tables
StormEvents | join kind=inner (nyc_taxi) on $left.EventId == $right.passenger_count

// ✅ — check cardinality first, pre-filter aggressively
// Step 1: StormEvents | summarize dcount(State)  → 67 — OK
// Step 2: PopulationData | count  → check if manageable
// Step 3: Pre-filter, then join
StormEvents
| where State in ("NEW YORK", "TEXAS")
| join kind=inner (PopulationData) on State
| take 5 | project State, EventType, Population
```

**Prevention**: Always `dcount()` both join sides before executing. If left × right > 1M, add filters.
