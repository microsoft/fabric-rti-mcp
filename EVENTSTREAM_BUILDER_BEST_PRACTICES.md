# Eventstream Builder Best Practices and Architectural Guidance

## Overview
This document provides architectural guidance and best practices for using the Eventstream Builder MCP tools.

## Recommended Architecture Patterns

### 1. Basic Eventstream Pattern
```
Source → Default Stream → Destination
```
- Use when you need simple data ingestion without transformation
- Example: Raw sensor data directly to storage

### 2. Processing Pattern (Recommended)
```
Source → Default Stream → Derived Stream → Destination
```
- **Recommended for most use cases**
- Derived streams allow for data transformation, filtering, and processing
- Better separation of concerns
- More flexible for future enhancements

### 3. Multi-Processing Pattern
```
Source → Default Stream → Multiple Derived Streams → Multiple Destinations
```
- Use when you need to process the same data in different ways
- Example: One stream for real-time analytics, another for long-term storage

## Best Practices

### When to Use Derived Streams
- **Always recommended** when you have a single source and need any processing
- Provides a clean separation between raw data ingestion and processed data
- Allows for future transformation logic without changing the source
- Better for debugging and monitoring

### Naming Conventions
- **Sources:** Descriptive of the data source (e.g., "BicycleDataSource", "SensorDataSource")
- **Default Streams:** Use the eventstream name (follows established pattern)
- **Derived Streams:** Descriptive of the processing (e.g., "ProcessedBikeData", "FilteredSensorData")
- **Destinations:** Descriptive of the target (e.g., "BikeDataDestination", "EventhouseDestination")

### Common Anti-Patterns to Avoid
- ❌ Going directly from source to destination without any streams
- ❌ Using generic names like "Stream1", "Destination1"
- ❌ Adding destinations without considering the data processing pipeline

## Tool Usage Recommendations

### For AI Agents and Automated Systems
When building eventstreams programmatically:

1. **Always start with the processing pattern** unless specifically told otherwise
2. **Ask users about their intended data flow** before adding destinations
3. **Recommend derived streams** for data transformation and processing
4. **Validate the complete pipeline** before creation

### Response Templates
When users request basic eventstreams, respond with:
> "I recommend using a derived stream for data processing. This pattern is more flexible and follows best practices. Would you like me to add a derived stream for processing the data?"

## Integration Points

### With Eventhouse
- Always verify Eventhouse item IDs and database names exist
- Use meaningful table names that reflect the processed data
- Consider data schema requirements

### With Custom Endpoints
- Use descriptive endpoint URLs
- Consider authentication requirements
- Plan for error handling

## Future Enhancements
- Consider adding validation for common architectural patterns
- Implement templates for common use cases
- Add schema validation for destinations

## Testing and Validation
- Use `python tests/validate_final.py` for PR readiness validation
- Test eventstream creation with both sample data and real data sources
- Validate derived stream processing with different transformation scenarios
