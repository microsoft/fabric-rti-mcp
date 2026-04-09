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
// ❌ TRIGGERED ERROR — 24M rows, no pre-filter
Consumption
| summarize dcount(Consumed), count() by Timestamp, HouseholdId, MeterType
| where dcount_Consumed > 1

// ✅ FIX — filter first, reduce grouping columns
Consumption
| where Timestamp between (datetime(2023-04-15) .. datetime(2023-04-16))
| summarize dcount(Consumed) by HouseholdId, MeterType
| where dcount_Consumed > 1
```

### Pattern B: Join explosion

```kql
// ❌ TRIGGERED ERROR — 25K IPs × 195 polygons
ip_locations
| join kind=inner (Cities | where HackersCount >= 256) on $left.CityName == $right.CityName

// ✅ FIX — pre-filter both sides, check cardinality first
let filtered_ips = ip_locations | where CountryCode == "US" | summarize by CityName;
let target_cities = Cities | where HackersCount >= 256 | project CityName;
filtered_ips | join kind=inner target_cities on CityName
```

### Pattern C: High-cardinality dcount()

```kql
// ❌ TRIGGERED ERROR — Full distinct value enumeration
Logs | summarize dcount(SourceIP), dcount(DestIP), dcount(Port) by bin(Timestamp, 1h)

// ✅ FIX — use approximate counts or filter first
Logs
| where Timestamp > ago(1d)
| summarize dcount(SourceIP) by bin(Timestamp, 1h)
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
TableA | join kind=inner TableB on $left.Id

// ✅ FIX — specify both sides
TableA | join kind=inner TableB on $left.Id == $right.Id
```

```kql
// ❌ TRIGGERED ERROR — expression in join condition
TableA | join kind=inner TableB on $left.Id == $right.tolower(Name)

// ✅ FIX — pre-compute the expression, join on the computed column
TableA
| join kind=inner (TableB | extend NameLower = tolower(Name)) on $left.Id == $right.NameLower
```

### 2b. Equality only

**Error message**: `join: Only equality is allowed in this context.`

```kql
// ❌ TRIGGERED ERROR — geo-distance in join predicate
TableA | join TableB on geo_distance_2points(a.Lat, a.Lon, b.Lat, b.Lon) < 1000

// ✅ FIX — pre-bucket into spatial cells
TableA
| extend cell = geo_point_to_s2cell(Lon, Lat, 8)
| join kind=inner (TableB | extend cell = geo_point_to_s2cell(Lon, Lat, 8)) on cell
| where geo_distance_2points(Lat, Lon, Lat1, Lon1) < 1000  // post-filter for precision
```

```kql
// ❌ TRIGGERED ERROR — range join
Sales | join Thresholds on $left.Amount > $right.MinAmount

// ✅ FIX — bin values and join on bins
Sales
| extend amount_bin = bin(Amount, 100)
| join kind=inner (Thresholds | extend amount_bin = bin(MinAmount, 100)) on amount_bin
| where Amount > MinAmount  // post-filter
```

---

## 3. Network / Transient

**Error message**: `Failed to process network request for the endpoint: https://kvc4bf3...`

Cause: Corrupted cluster URIs or genuine network timeouts.

**Recovery strategy**: 
1. Verify the cluster URI is clean ASCII (no Unicode characters)
2. Retry with a fresh URI
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

```kql
// ❌ — .show is a management command, don't pipe query operators onto it
.show tables | project TableName

// ✅ — use kusto_command for management commands, kusto_query for queries
// Step 1: kusto_command(command=".show tables", ...)
// Step 2: kusto_query(query="TableName | take 5", ...)
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
Runs
| extend startCell = geo_point_to_s2cell(StartLon, StartLat, 16)
| join kind=inner (...) on startCell

// ✅ — explicit tostring()
Runs
| extend startCell = tostring(geo_point_to_s2cell(StartLon, StartLat, 16))
| join kind=inner (... | extend startCell = tostring(geo_point_to_s2cell(Lon, Lat, 16))) on startCell
```

This occurs most often with `geo_point_to_s2cell()`, `hash()`, and `strcat()` return values.

---

## 8. extract_all Regex Groups

**Error message**: `extractall(): argument 2 must be a valid regex with [1..16] matching groups`

```kql
// ❌ — Missing capturing group
| extend words = extract_all(@"[a-zA-Z]{3,}", tolower(Title))

// ✅ — Add parentheses
| extend words = extract_all(@"([a-zA-Z]{3,})", tolower(Title))
```

Unlike Python's `re.findall()`, KQL's `extract_all` requires at least one `()` group.

---

## 9. Serialization Required

**Error message**: `Function 'row_cumsum' cannot be invoked. The row set must be serialized.`

```kql
// ❌
ChatServerLogs
| summarize Online = sum(Direction) by bin(Timestamp, 5m)
| extend CumulativeOnline = row_cumsum(Online)

// ✅ — add order by (implicitly serializes)
ChatServerLogs
| summarize Online = sum(Direction) by bin(Timestamp, 5m)
| order by Timestamp asc
| extend CumulativeOnline = row_cumsum(Online)
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
| `python` | ❌ Not available | Use local Python instead |

---

## 11. graph-match Syntax

**Error message**: `graph-match operator: variable edge 'path' edges don't have property 'IsVulnerable'`

```kql
// ❌ — property access on variable-length edge
graph-match (src)-[path*1..3]->(dst)
  where path.IsVulnerable == true

// ✅ — filter edges at definition, not traversal
let edges = Edges | where IsVulnerable == true;
graph(Nodes, edges)
| graph-match (src)-[path*1..3]->(dst)
  project src.Name, dst.Name
```

The fix is to pre-filter edges before graph construction.

---

## 12. E_RUNAWAY_QUERY

**Error message**: `Runaway query (E_RUNAWAY_QUERY): Join output block exceeded memory budget`

```kql
// ❌ — 25K × 195 unconstrained cross-join
ip_locs | join kind=inner (Cities | where EstimatedHackersCount >= 256) on ...

// ✅ — check cardinality first, pre-filter aggressively
// Step 1: ip_locs | summarize dcount(JoinKey)  → if >10K, add filters
// Step 2: Cities | where EstimatedHackersCount >= 256 | count  → if >100, narrow criteria
// Step 3: Then join
```

**Prevention**: Always `dcount()` both join sides before executing. If left × right > 1M, add filters.
