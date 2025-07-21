# 🧪 Manual Testing Guide - Phase 1 Eventstream Builder

## Quick Start Testing

### 1. Run the MCP Server
```bash
# Start the MCP server
python -m fabric_rti_mcp.server
```

### 2. Test the 12 New Tools

The Phase 1 implementation adds these 12 tools to the MCP server:

#### Definition Management (3 tools)
1. `eventstream_start_definition` - Start building
2. `eventstream_validate_definition` - Check if valid
3. `eventstream_create_from_definition` - Deploy to Fabric

#### Sources (2 tools)  
4. `eventstream_add_sample_data_source` - Add sample data
5. `eventstream_add_custom_endpoint_source` - Add REST endpoint

#### Streams (2 tools)
6. `eventstream_add_default_stream` - Basic stream
7. `eventstream_add_derived_stream` - Processed stream

#### Destinations (2 tools)
8. `eventstream_add_eventhouse_destination` - Send to Eventhouse
9. `eventstream_add_custom_endpoint_destination` - Send to REST endpoint

#### Helpers (3 tools)
10. `eventstream_get_current_definition` - Show current state
11. `eventstream_clear_definition` - Reset/clear
12. `eventstream_list_available_components` - Show what's available

### 3. Test the Target Workflow

**Target User Prompt:** 
> "I want to create a simple eventstream that takes bicycle sample data and stores it in my Eventhouse database. Can you help me build this step by step?"

**Expected 5-Step Flow:**

1. **Start Definition**
   ```
   Call: eventstream_start_definition("BicycleAnalytics", "Bicycle data analysis")
   Result: Returns session_id for next steps
   ```

2. **Add Bicycle Source**
   ```
   Call: eventstream_add_sample_data_source(session_id, "BicycleSource", "Bicycles")
   Result: Sample bicycle data source added
   ```

3. **Add Default Stream**
   ```
   Call: eventstream_add_default_stream(session_id, "BicycleStream", ["BicycleSource"])
   Result: Stream connecting source to destinations
   ```

4. **Add Eventhouse Destination**
   ```
   Call: eventstream_add_eventhouse_destination(
       session_id=session_id,
       destination_name="AnalyticsDB",
       workspace_id="your-workspace-id",
       item_id="your-eventhouse-id", 
       database_name="your-database",
       table_name="BicycleData",
       input_streams=["BicycleStream"]
   )
   Result: Eventhouse destination configured
   ```

5. **Validate & Create**
   ```
   Call: eventstream_validate_definition(session_id)
   Result: Should show "valid": true
   
   Call: eventstream_create_from_definition(session_id, workspace_id)
   Result: Creates actual eventstream in Fabric
   ```

### 4. Test Helper Tools

- **Check Progress:** `eventstream_get_current_definition(session_id)`
- **See Options:** `eventstream_list_available_components()`  
- **Start Over:** `eventstream_clear_definition(session_id)`

### 5. Success Criteria

✅ **Phase 1 is successful if:**
- All 12 tools are available in MCP server
- User can complete the 5-step bicycle → Eventhouse workflow
- Tools provide helpful guidance and error messages
- Definition validates correctly before creation
- Session management works (can track progress)

### 6. Testing Tips

- **Use VS Code with MCP extension** for easy tool testing
- **Start with `eventstream_list_available_components()`** to see what's available
- **Save session IDs** - you'll need them for multi-step workflows
- **Test validation early** - catch issues before trying to create
- **Try error cases** - invalid session IDs, missing parameters, etc.

### 7. Known Limitations (Out of Scope for Phase 1)

❌ **Not yet implemented:**
- Multiple sample data types (only Bicycles)
- Azure Event Hub, IoT Hub sources  
- Lakehouse destinations
- Operators (filter, aggregate, etc.)
- Advanced validation
- Multi-user sessions

✅ **Will be added in future phases**

---

**Happy Testing!** 🚀

If you encounter issues, check:
1. Import errors → verify file paths
2. Session not found → check session_id parameter
3. Validation fails → review required fields
4. Tool not available → restart MCP server
