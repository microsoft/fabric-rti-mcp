---
name: kql
description: "KQL language expertise for writing correct, efficient Kusto queries using the Fabric RTI MCP tools. Covers syntax gotchas, join patterns, dynamic types, datetime pitfalls, regex patterns, serialization, memory management, result-size discipline, and advanced functions (geo, vector, graph). USE THIS SKILL whenever writing, debugging, or reviewing KQL queries — even simple ones — because the gotchas section prevents the most common errors that waste tool calls and cause expensive retry cascades. Trigger on: KQL, Kusto, ADX, Azure Data Explorer, Fabric Eventhouse, log analysis, data exploration, time series, anomaly detection, summarize, where clause, join, extend, project, let statement, parse operator, extract function, any mention of pipe-forward query syntax."
---

# KQL Mastery

## 1. Running KQL with Fabric RTI MCP

Fabric RTI MCP exposes Kusto functionality as MCP tools. Authentication is handled transparently using Azure Identity.

### Available tools

| Tool | Purpose |
|------|---------|
| `kusto_query` | Execute a KQL query on a database |
| `kusto_command` | Execute a management command (`.show`, `.create`, etc.) |
| `kusto_list_entities` | List databases, tables, external tables, materialized views, functions, graphs |
| `kusto_describe_database` | Get schema for all entities in a database |
| `kusto_describe_database_entity` | Get schema for a specific entity (table, function, etc.) |
| `kusto_sample_entity` | Get sample data from a table or other entity |
| `kusto_graph_query` | Execute a graph query using snapshots or transient graphs |
| `kusto_ingest_inline_into_table` | Ingest inline CSV data into a table |
| `kusto_known_services` | List configured Kusto services |
| `kusto_get_shots` | Retrieve semantically similar shots from a shots table |
| `kusto_deeplink_from_query` | Build a deeplink URL to open a query in the web explorer |

### Query vs management commands

KQL has two execution planes, each with its own MCP tool:

| Plane | Tool | Starts with | Examples |
|-------|------|-------------|----------|
| **Query** | `kusto_query` | Table name, `let`, `print`, `datatable` | `StormEvents \| where State == "TEXAS"` |
| **Management** | `kusto_command` | `.show`, `.create`, `.set`, `.drop`, `.alter` | `.show tables`, `.show table T schema` |

### Basic usage

```
# Query plane — use kusto_query
kusto_query(
    cluster_uri="https://help.kusto.windows.net",
    database="Samples",
    query="StormEvents | summarize count() by EventType | top 5 by count_ desc"
)

# Management plane — use kusto_command
kusto_command(
    cluster_uri="https://help.kusto.windows.net",
    database="Samples",
    command=".show tables"
)

# Schema exploration — use kusto_describe_database or kusto_describe_database_entity
kusto_describe_database(
    cluster_uri="https://help.kusto.windows.net",
    database="Samples"
)

# Sample data — use kusto_sample_entity
kusto_sample_entity(
    cluster_uri="https://help.kusto.windows.net",
    database="Samples",
    entity_name="StormEvents",
    entity_type="table",
    sample_size=5
)

# Graph queries — use kusto_graph_query
kusto_graph_query(
    cluster_uri="https://mycluster.kusto.windows.net",
    database="MyDB",
    graph_name="MyGraph",
    query="| graph-match (node) project labels=labels(node)"
)

# Deeplinks — use kusto_deeplink_from_query
kusto_deeplink_from_query(
    cluster_uri="https://help.kusto.windows.net",
    database="Samples",
    query="StormEvents | count"
)
```

### Exploration workflow

When encountering a new cluster or database:

1. **List entities**: `kusto_list_entities(cluster_uri, entity_type="tables", database="MyDB")`
2. **Get schema**: `kusto_describe_database_entity(entity_name="MyTable", entity_type="table", cluster_uri=..., database=...)`
3. **Sample data**: `kusto_sample_entity(entity_name="MyTable", entity_type="table", cluster_uri=..., sample_size=5)`
4. **Count rows**: `kusto_query(query="MyTable | count", cluster_uri=..., database=...)`
5. **Run analysis**: `kusto_query(query="MyTable | where ... | summarize ...", cluster_uri=..., database=...)`

## 2. Dynamic Type Discipline

KQL's `dynamic` type is flexible but strict in certain contexts. A common mistake is using a dynamic column in `summarize by`, `order by`, or `join on` without casting.

**The rule**: Any time you use a dynamic-typed column in `by`, `on`, or `order by`, wrap it in an explicit cast.

```kql
// ❌ ERROR: "Summarize group key 'Partners' is of a 'dynamic' type"
| summarize count() by Partners

// ✅ FIX
| summarize count() by tostring(Partners)
```

```kql
// ❌ ERROR: "order operator: key can't be of dynamic type"
| order by Area desc

// ✅ FIX
| order by tostring(Area) desc
```

```kql
// ❌ ERROR in join: dynamic join key
| join kind=inner other on $left.Area == $right.Area

// ✅ FIX — cast both sides
| extend Area_str = tostring(Area)
| join kind=inner (other | extend Area_str = tostring(Area)) on Area_str
```

**Self-correction**: When you see "is of a 'dynamic' type" in an error, add `tostring()`, `tolong()`, or `todouble()`.

## 3. Join Patterns & Pitfalls

KQL joins have constraints that differ from SQL.

### Equality only
KQL join conditions support **only `==`**. No `<`, `>`, `!=`, or function calls in join predicates.

```kql
// ❌ ERROR: "Only equality is allowed in this context"
| join on geo_distance_2points(a.Lat, a.Lon, b.Lat, b.Lon) < 1000

// ✅ WORKAROUND — pre-bucket into spatial cells, then join on cell ID
| extend cell = geo_point_to_s2cell(Lon, Lat, 8)
| join kind=inner (other | extend cell = geo_point_to_s2cell(Lon, Lat, 8)) on cell
```

For range joins, pre-bin values: `| extend bin_val = bin(Value, 100)`, then join on `bin_val`.

### Left/right attribute matching
Both sides of a join `on` clause must reference **column entities only** — not expressions, not aggregates.

```kql
// ❌ ERROR: "for each left attribute, right attribute should be selected"
| join kind=inner other on $left.col1

// ✅ FIX — specify both sides explicitly
| join kind=inner other on $left.col1 == $right.col1
```

### Cardinality check before large joins
**Always** check cardinality before joining tables with >10K rows. A cross-join explosion was the source of the single `E_RUNAWAY_QUERY` error (25K × 195 = potential 4.8M rows).

```kql
// Before joining, check how many rows each side contributes
TableA | summarize dcount(JoinKey)  // → 25,000? Too many for an unconstrained join
TableB | summarize dcount(JoinKey)  // → 195? OK if filtered first
```

## 4. Regex in KQL

KQL handles regex natively — no need for Python.

### The `extract_all` gotcha
Unlike Python's `re.findall()`, KQL's `extract_all` **requires capturing groups** in the regex:

```kql
// ❌ ERROR: "extractall(): argument 2 must be a valid regex with [1..16] matching groups"
| extend words = extract_all(@"[a-zA-Z]{3,}", Text)

// ✅ FIX — add parentheses around the pattern
| extend words = extract_all(@"([a-zA-Z]{3,})", Text)
```

### Regex toolkit — don't fall back to Python
| Function | Use case | Example |
|----------|----------|---------|
| `extract(regex, group, source)` | Single match | `extract(@"User '([^']+)'", 1, Msg)` |
| `extract_all(regex, source)` | All matches (needs `()`) | `extract_all(@"(\w+)", Text)` |
| `parse` | Structured extraction | `parse Msg with * "User '" Sender "' sent" *` |
| `matches regex` | Boolean filter | `where Url matches regex @"^https?://"` |
| `replace_regex` | Find and replace | `replace_regex(@"\s+", " ", Text)` |

## 5. Serialization Requirements

Window functions need serialized (ordered) input.

```kql
// ❌ ERROR: "Function 'row_cumsum' cannot be invoked. The row set must be serialized."
| summarize Online = sum(Direction) by bin(Timestamp, 5m)
| extend CumulativeOnline = row_cumsum(Online)

// ✅ FIX — add | serialize (or | order by, which implicitly serializes)
| summarize Online = sum(Direction) by bin(Timestamp, 5m)
| order by Timestamp asc
| extend CumulativeOnline = row_cumsum(Online)
```

Functions requiring serialization: `row_number()`, `row_cumsum()`, `prev()`, `next()`, `row_window_session()`.

## 6. Memory-Safe Query Patterns

The most common memory error. Caused by scanning too much data without pre-filtering.

### The progression of safety
```
Safest ──────────────────────────────────────────────── Most dangerous
| count    | take 10    | where + summarize    | summarize (no filter)    | full scan
```

### Rules for large tables (>1M rows)

1. **Always start with `| count`** to understand table size
2. **Always `| where` before `| summarize`** — filter time range, partition key, or category first
3. **Never `dcount()` on high-cardinality columns** without pre-filtering
4. **Check join cardinality** before executing (see Section 3)
5. **Use `materialize()`** for subqueries referenced multiple times

```kql
// ❌ OUT OF MEMORY — 24M rows, no filter, dcount on every column
Consumption
| summarize dcount(Consumed), count() by Timestamp, HouseholdId, MeterType
| where dcount_Consumed > 1

// ✅ SAFE — filter first, then aggregate
Consumption
| where Timestamp between (datetime(2023-04-15) .. datetime(2023-04-16))
| summarize dcount(Consumed) by HouseholdId, MeterType
| where dcount_Consumed > 1
```

### When you see `E_LOW_MEMORY_CONDITION`
The query touched too much data. Your options:
- Add `| where` filters (time range, partition key)
- Reduce the number of `by` columns in `summarize`
- Break into smaller time windows and union results
- Use `| sample 10000` for exploratory work instead of full scans

### When you see `E_RUNAWAY_QUERY`
A join or aggregation produced too many output rows. Check join cardinality — one or both sides is too large.

## 7. Result Size Discipline

Large results slow down analysis. Prevention:

| Query type | Safeguard |
|-----------|-----------|
| Exploratory | Always end with `\| take 10` or `\| take 20` |
| Aggregation | Use `\| top 20 by ...` not unbounded `summarize` |
| Wide rows (vectors, JSON) | `\| project` only needed columns |
| `make_list()` / `make_set()` | Avoid on high-cardinality groups (produces huge cells) |
| Unknown size | Run `\| count` first |

**The vector trap**: Tables with embedding columns (1536-dim float arrays) produce ~30KB per row. Even `| take 20` yields 600KB. Always `| project` away vector columns unless you specifically need them.

**With MCP tools**: Use `kusto_sample_entity` for quick data previews. For deeper exploration, use `kusto_query` with `| take N` or `| top N` to bound results.

## 8. String Comparison Strictness

KQL sometimes requires explicit casts when comparing computed string values — even when both sides are already strings.

```kql
// ❌ ERROR: "Cannot compare values of types string and string. Try adding explicit casts"
| where geo_point_to_s2cell(Lon, Lat, 16) == other_cell

// ✅ FIX — wrap both sides in tostring()
| where tostring(geo_point_to_s2cell(Lon, Lat, 16)) == tostring(other_cell)
```

This is most common with computed values from `geo_point_to_s2cell()`, `hash()`, and `strcat()` comparisons. When in doubt, cast with `tostring()`.

## 9. Advanced Functions

KQL handles these natively — no need for Python:

### Vector similarity
```kql
// Don't export vectors and compute cosine similarity in Python
let target = toscalar(Vectors | where Word == "test" | project Vec);
Data | extend sim = series_cosine_similarity(parse_json(VecColumn), target)
| top 10 by sim desc
```

### Geo operations
```kql
// Point-in-polygon check
| where geo_point_in_polygon(Longitude, Latitude, dynamic({"type":"Polygon","coordinates":[...]}))

// Distance between two points (meters)
| extend dist = geo_distance_2points(Lon1, Lat1, Lon2, Lat2)

// Spatial bucketing for joins
| extend cell = geo_point_to_s2cell(Lon, Lat, 8)
```

### Graph queries

Use the `kusto_graph_query` MCP tool for graph traversal. It automatically handles graph snapshots when available:

```kql
// Build and traverse a graph
graph(Nodes, Edges)
| graph-match (src)-[e*1..5]->(dst)
  where src.Name == "start" and dst.IsTarget == true
  project src.Name, dst.Name, path_length = array_length(e)
```

### Time series
```kql
// Create a time series and detect anomalies
| make-series count() default=0 on Timestamp step 1h
| extend anomalies = series_decompose_anomalies(count_)
```

For detailed examples and patterns, consult `references/advanced-patterns.md`.

## 10. Self-Correction Lookup Table

When you encounter an error, look it up here before retrying:

| Error message contains | Likely cause | Fix |
|---|---|---|
| `is of a 'dynamic' type` | Dynamic column in `by`/`on`/`order by` | Wrap in `tostring()`/`tolong()` |
| `Only equality is allowed` | Range predicate in join condition | Pre-bucket with S2/H3 cells or `bin()` |
| `extractall(): matching groups` | Missing `()` in regex | Add `()`: `@"(\w+)"` not `@"\w+"` |
| `row set must be serialized` | Window function on unsorted data | Add `\| serialize` or `\| order by` before it |
| `Cannot compare values of types string and string` | Computed string comparison | Add `tostring()` on both sides |
| `Failed to resolve column named 'X'` | Wrong column name or wrong table | Use `kusto_describe_database_entity` to check column names |
| `E_LOW_MEMORY_CONDITION` | Query touched too much data | Add `\| where` filters, reduce time range, break into steps |
| `E_RUNAWAY_QUERY` | Join/aggregation produced too many rows | Check cardinality before joining; add pre-filters |
| `for each left attribute, right attribute` | Join `on` clause incomplete | Use explicit form: `on $left.X == $right.Y` |
| `needs to be bracketed` | Reserved word used as identifier | Use `['keyword']` syntax |
| `plugin doesn't exist` | Unavailable plugin on this cluster | Fall back to equivalent function or Python |
| `Expected string literal in datetime()` | Bare integer in datetime literal | Use `datetime(2024-01-01)` not `datetime(2024)` |
| `Unexpected token` after `by` | Complex expression in summarize by-clause | `extend` the expression first, then `summarize by` the column |
| `not recognized` / `unknown operator` | Operator not available on this engine | Check operator support; try equivalent (`order by` = `sort by`) |

## 11. Datetime Pitfalls

Datetime literals are a common source of errors. A wrong literal format can cascade into completely different approaches instead of fixing the small issue.

### Literal format
```kql
// ❌ WRONG — bare year is not a valid datetime
| where StartTime > datetime(2007)

// ✅ RIGHT — always use full date format
| where StartTime > datetime(2007-01-01)
```

### Filtering by year, month, or hour
```kql
// ❌ WRONG — comparing datetime column to integer
| where StartTime == 2007

// ✅ RIGHT — use datetime_part() to extract components
| where datetime_part("year", StartTime) == 2007

// ✅ ALSO RIGHT — use between with datetime range
| where StartTime between (datetime(2007-01-01) .. datetime(2007-12-31))
```

### Time bucketing in summarize
```kql
// ❌ WRONG — complex expression directly in by-clause can fail in some engines
| summarize count() by startofmonth(StartTime)

// ✅ SAFER — extend first, then summarize by the computed column
| extend Month = startofmonth(StartTime)
| summarize count() by Month
| order by Month asc
```

### Useful datetime functions
| Function | Purpose | Example |
|----------|---------|---------|
| `bin(ts, 1h)` | Round to nearest bucket | `bin(Timestamp, 1d)` |
| `startofmonth(ts)` | First day of month | `startofmonth(Timestamp)` |
| `datetime_part("hour", ts)` | Extract component | `datetime_part("year", Timestamp)` |
| `format_datetime(ts, fmt)` | Format as string | `format_datetime(Timestamp, "yyyy-MM")` |
| `ago(1d)` | Relative time | `where Timestamp > ago(7d)` |
| `between(a .. b)` | Range filter | `where Timestamp between (datetime(2024-01-01) .. datetime(2024-01-31))` |
| `todatetime(str)` | Parse string → datetime | `todatetime("2024-01-15T10:30:00Z")` |
| `totimespan(str)` | Parse string → timespan | `totimespan("01:30:00")` |

## 12. Operator Naming & Equality

KQL has subtle differences from SQL syntax.

### Equality operators
```kql
// In where clauses, == is case-sensitive, =~ is case-insensitive
| where State == "TEXAS"      // exact match
| where State =~ "texas"      // case-insensitive
| where State != "TEXAS"      // not equal
| where State !~ "texas"      // case-insensitive not equal

// In joins, use == only
| join kind=inner other on $left.Key == $right.Key
```

### sort vs order
Both `sort by` and `order by` work identically in KQL — they are aliases. Use whichever you prefer, but be consistent.

### contains vs has
```kql
// contains: substring match (slower)
| where Message contains "error"        // finds "MyErrorHandler" too

// has: term/word match (faster, uses index)
| where Message has "error"             // matches word boundaries only

// For exact prefix/suffix
| where Message startswith "Error:"
| where Message endswith ".log"
```

## 13. Error Recovery Strategy

When a first KQL query fails, the temptation is to abandon the entire approach and try something completely different. The correct response is almost always to **fix the specific error**, not change strategy.

### The pattern to avoid
```
Query 1: extract(@"pattern", 1, col)  → Parse error
Query 2: todynamic(col)               → Different error  
Query 3: parse_json(col)              → Another error
Query 4: Python script                → Works but 10x tokens
```

### The correct pattern
```
Query 1: extract(@"pattern", 1, col)  → Parse error (bad escaping)
Query 2: extract(@"pattern", 1, col)  → Fix the specific escaping issue → Success
```

**Rules for error recovery:**
1. Read the error message carefully — it almost always tells you exactly what's wrong
2. Fix the **specific** syntax/escaping issue, don't switch approaches
3. Use the self-correction table (Section 10) to map errors to fixes
4. Only switch approaches after 2 failed fixes of the same query
5. The `parse` operator is often simpler than `extract()` for structured text:

```kql
// Instead of complex regex:
// extract(@"User '([^']+)' sent (\d+) bytes", 1, Message)

// Use parse for structured extraction:
| parse Message with * "User '" Username "' sent " ByteCount " bytes" *
```

## 14. Query Writing Checklist

Before running any KQL query, mentally check:

1. **Pre-filtered?** Large tables have a `| where` before any `| summarize`
2. **Result bounded?** Exploratory queries end with `| take N` or `| top N`
3. **Dynamic columns cast?** Any dynamic column in `by`/`on`/`order by` is wrapped
4. **Regex has groups?** `extract_all` patterns have `()` around what you want to capture
5. **Join cardinality safe?** Both sides checked with `dcount()` before joining
6. **Needed columns only?** Wide tables get `| project` to drop unneeded columns
7. **Datetime literals valid?** Using `datetime(2024-01-01)` not `datetime(2024)` or bare integers
8. **Complex by-expressions?** Use `| extend` first, then `| summarize by` the computed column
9. **Error recovery plan?** If a query fails, fix the specific error — don't change strategy
10. **Right tool?** Use `kusto_query` for queries, `kusto_command` for management commands, `kusto_sample_entity` for quick previews
