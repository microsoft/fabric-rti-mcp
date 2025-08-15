# 🎯 Phase 1 Implementation Plan - Eventstream Builder
*Internal Planning Document - Not for Commit*

## Exit Criteria: Target User Prompt
```
"I want to create a simple eventstream that takes bicycle sample data and stores it in my Eventhouse database. Can you help me build this step by step?"
```

## Expected User Experience Flow
1. **User asks** for help creating a bicycle → Eventhouse eventstream
2. **System responds** with step-by-step guidance using builder tools
3. **User follows** the guided workflow (5 steps)
4. **System creates** a working eventstream in their Fabric workspace
5. **User validates** the eventstream is running and data is flowing

## Phase 1 Minimum Viable Tools (12 tools)

### Definition Management (3 tools)
- `eventstream_start_definition()` - Initialize builder session
- `eventstream_validate_definition()` - Validate current definition
- `eventstream_create_from_definition()` - Deploy to Fabric

### Source Management (2 tools)
- `eventstream_add_sample_data_source()` - Add bicycle sample data
- `eventstream_add_custom_endpoint_source()` - Add custom REST endpoint source

### Stream Management (2 tools)
- `eventstream_add_default_stream()` - Create default stream from sources
- `eventstream_add_derived_stream()` - Create derived stream from operators

### Destination Management (2 tools)
- `eventstream_add_eventhouse_destination()` - Add Eventhouse destination
- `eventstream_add_custom_endpoint_destination()` - Add custom REST endpoint destination

### Helper Tools (3 tools)
- `eventstream_get_current_definition()` - Show current state
- `eventstream_clear_definition()` - Reset builder (for mistakes)
- `eventstream_list_available_components()` - Show available sources/destinations

## Success Checklist

### Functional Requirements
- [ ] User can start a new eventstream definition
- [ ] User can add bicycle sample data source
- [ ] User can add custom endpoint source
- [ ] User can add default stream from sources
- [ ] User can add derived stream from operators
- [ ] User can add Eventhouse destination
- [ ] User can add custom endpoint destination
- [ ] User can validate the complete definition
- [ ] User can create the eventstream in Fabric
- [ ] User can view current definition state
- [ ] User can clear/reset if needed
- [ ] User can list available components

### Technical Requirements
- [ ] Session management works (UUID-based)
- [ ] State persistence during build process
- [ ] Fabric API compliance for generated definitions
- [ ] Error handling with helpful messages
- [ ] Integration with existing eventstream service
- [ ] Proper async/sync bridging

### User Experience Requirements
- [ ] Clear, step-by-step guidance
- [ ] Helpful error messages with suggested fixes
- [ ] Progress indication during build process
- [ ] Validation feedback before creation
- [ ] Success confirmation after creation

## Acceptance Test
```
Given: User has a Fabric workspace with an Eventhouse
When: User asks to create bicycle sample → Eventhouse eventstream
Then: System guides them through 5-step process
And: System creates working eventstream in Fabric
And: User can see bicycle data flowing into Eventhouse
```

## Key Metrics
- **Tool Count**: 12 tools (expanded scope)
- **User Steps**: 5-7 steps (flexible workflow)
- **Success Rate**: User can complete scenario without errors
- **Time to Value**: Under 5 minutes from request to working eventstream

## Scope Boundaries

### In Scope
- Single sample data type (Bicycles)
- Custom endpoint sources and destinations
- Single Eventhouse destination type
- Default and derived stream types
- Basic validation and error handling
- Simple linear workflow (no operators yet)
- Session management basics
- Component discovery

### Out of Scope (Future Phases)
- Multiple sample data types
- Azure Event Hub, IoT Hub sources
- Lakehouse destinations
- Operators and complex processing
- Advanced validation
- Multi-user session handling
- Complex error recovery

## Implementation Files to Create
1. `fabric_rti_mcp/eventstream/eventstream_builder_service.py` - Core builder logic
2. `fabric_rti_mcp/eventstream/eventstream_builder_tools.py` - MCP tool definitions
3. Update `fabric_rti_mcp/eventstream/__init__.py` - Export builder classes
4. Update `fabric_rti_mcp/server.py` - Register builder tools
5. `tests/eventstream/test_eventstream_builder.py` - Unit tests

---
**Created:** July 4, 2025  
**Status:** Planning Phase  
**Branch:** feature/eventstream-builder
