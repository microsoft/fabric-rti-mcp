# Eventstream Builder MCP Server - User Guide

## Quick Start for AI Agents

When helping users create eventstreams, follow this recommended pattern:

### 1. Start with the Foundation
```
Source → Default Stream → Derived Stream → Destination
```

### 2. Recommended Flow
1. **Start Definition:** `eventstream_start_definition()`
2. **Add Source:** `eventstream_add_sample_data_source()` or `eventstream_add_custom_endpoint_source()`
3. **Add Default Stream:** `eventstream_add_default_stream()` (use eventstream name as stream name)
4. **Add Derived Stream:** `eventstream_add_derived_stream()` ⭐ **RECOMMENDED**
5. **Add Destination:** `eventstream_add_eventhouse_destination()` or `eventstream_add_custom_endpoint_destination()`
6. **Validate:** `eventstream_validate_definition()`
7. **Create:** `eventstream_create_from_definition()`

### 3. Why Derived Streams?
- **Better Architecture:** Separates raw data ingestion from processed data
- **Flexibility:** Easy to add transformation logic later
- **Monitoring:** Better observability and debugging
- **Best Practice:** Follows Microsoft Fabric recommendations

### 4. Example Conversation Flow

**User:** "Create an eventstream with bicycle data"

**AI Response:** 
"I'll create an eventstream with bicycle sample data. I recommend using a derived stream for data processing - this follows best practices and provides better flexibility for future enhancements."

**Then build:**
1. Source: BicycleDataSource
2. Default Stream: [EventstreamName]-stream
3. Derived Stream: ProcessedBikeData (or similar descriptive name)
4. Destination: (ask user for preference)

### 5. Common Scenarios

#### Scenario: User wants "simple" eventstream
- Still recommend derived stream
- Explain: "Even for simple cases, a derived stream provides better architecture"

#### Scenario: User specifies destination type
- Build the full pipeline with derived stream
- Connect derived stream to their specified destination

#### Scenario: User wants multiple destinations
- Use derived stream as the common processing point
- Connect derived stream to multiple destinations

### 6. Error Handling

#### Eventhouse Destination Fails
- Common issue: Eventhouse item/database doesn't exist
- Fallback: Create with custom endpoint, suggest manual configuration
- Explain: "I'll create the eventstream foundation. You can then add the Eventhouse destination through the Fabric UI."

#### Name Already Exists
- Suggest slight variation (e.g., append "v2" or timestamp)
- Explain: "The name might be temporarily reserved. Let me try a variation."

### 7. Architectural Guidance Prompts

Use these prompts to guide users toward better architectures:

- "I recommend adding a derived stream for data processing - this follows best practices"
- "Would you like me to add a derived stream for data transformation?"
- "For better flexibility, I suggest using the pattern: Source → Default Stream → Derived Stream → Destination"

### 8. Documentation References

- See `EVENTSTREAM_BUILDER_BEST_PRACTICES.md` for detailed architectural guidance
- Check tool descriptions for built-in recommendations
- Review successful eventstream patterns in the codebase

### 9. Testing and Validation

Always:
- Validate definition before creation
- Show the complete architecture to users
- Verify the eventstream appears in the workspace after creation

### 10. Future Enhancements

The MCP server now includes:
- ✅ Architectural guidance in tool responses
- ✅ Best practice recommendations
- ✅ Clear next steps with hints
- ✅ Comprehensive documentation

This guidance helps ensure consistent, well-architected eventstreams across all users and AI agents.
