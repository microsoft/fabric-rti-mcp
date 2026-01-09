---
abstract: Recipe to estimate storm probability and severity using StormEvents data
name: weather-forecast-task
---

# Weather forecast task

This is a "recipe" document: it contains domain workflow instructions that an agent can load and apply together with the MCP Kusto tools.

## Schema

StormEvents - US storm events.

Source: https://www.ncdc.noaa.gov/stormevents

Columns (Samples database):
- `StartTime: datetime`, `EndTime: datetime`
- `EpisodeId: int`, `EventId: int`
- `State: string`, `EventType: string`
- `InjuriesDirect: int`, `InjuriesIndirect: int`
- `DeathsDirect: int`, `DeathsIndirect: int`
- `DamageProperty: int`, `DamageCrops: int`
- `Source: string`
- `BeginLocation: string`, `EndLocation: string`
- `BeginLat: real`, `BeginLon: real`, `EndLat: real`, `EndLon: real`
- `EpisodeNarrative: string`, `EventNarrative: string`
- `StormSummary: dynamic`

## Logic

This dataset is historical (the `Samples` database on the help cluster contains year-2007 data). When you see "last 7 days" below, treat it as "the last 7 days relative to the latest timestamp in the table", not relative to the current date.

To estimate the probability of a storm for a certain day and location:

1) Calculate a baseline probability from recent history
- Use the last 7 days of events (relative to the dataset's latest date) for the target region (e.g., `State`) to estimate a short-term base rate.

2) Adjust using seasonality
- Compare the same date window across previous years for the same region (if your dataset spans multiple years). In this help-cluster sample you can skip this step.

3) Guesstimate strength/severity
- Use the distribution of `DamageProperty`, `DamageCrops`, injuries, and deaths for similar `EventType` and region.

4) Produce an output summary
- Probability estimate (qualitative or numeric), expected event types, and a short rationale.

## Queries (KQL examples)

Check schema (columns/types):

```kusto
StormEvents
| getschema
```

Get the dataset time range (useful for interpreting "last 7 days"):

```kusto
StormEvents
| summarize minStart=min(StartTime), maxStart=max(StartTime), rows=count()
```

Baseline probability of "any storm day" by State in the last 7 days (relative to latest timestamp):

```kusto
let max_t = toscalar(StormEvents | summarize max(StartTime));
let start_t = max_t - 7d;
StormEvents
| where StartTime between (start_t .. max_t)
| summarize storm_days=dcount(bin(StartTime, 1d)), total_events=count() by State
| extend p_any_storm_day = todouble(storm_days) / 7.0
| order by total_events desc
```

Expected event types for a specific State in the last 7 days:

```kusto
let target_state = "ILLINOIS";
let max_t = toscalar(StormEvents | summarize max(StartTime));
let start_t = max_t - 7d;
StormEvents
| where State == target_state
| where StartTime between (start_t .. max_t)
| summarize events=count() by EventType
| top 10 by events desc
```

Simple severity proxy for a State (last 7 days):

```kusto
let target_state = "ILLINOIS";
let max_t = toscalar(StormEvents | summarize max(StartTime));
let start_t = max_t - 7d;
StormEvents
| where State == target_state
| where StartTime between (start_t .. max_t)
| extend severity_score = DamageProperty + DamageCrops + 1000*(DeathsDirect+DeathsIndirect) + 100*(InjuriesDirect+InjuriesIndirect)
| summarize avg_severity=avg(severity_score), p95_severity=percentile(severity_score, 95), events=count() by EventType
| order by p95_severity desc
```

## Tool usage hints (MCP)

- Discover schema: use `kusto_describe_database_entity` on `StormEvents`.
- Get examples: use `kusto_sample_entity` on `StormEvents`.
- Execute KQL: use `kusto_query`.
