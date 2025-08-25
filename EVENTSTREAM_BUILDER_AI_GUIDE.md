# Eventstream Builder AI Guidance

## Overview for AI Assistants

This document provides guidance for AI assistants when helping users create Microsoft Fabric Eventstreams using the builder pattern. The builder enables step-by-step construction of complex eventstream configurations through a user-friendly workflow.

## When to Use the Builder

### Recommended Scenarios
- User asks to "create an eventstream" without detailed specifications
- User wants to build an eventstream step-by-step
- User is learning Fabric Eventstreams and needs guidance
- User wants to create a demo or proof-of-concept
- User prefers guided workflow over complex configuration

### Not Recommended
- User provides complete eventstream definition upfront
- User specifically requests direct API usage
- Simple eventstream with minimal configuration (use `eventstream_create_simple` instead)

## Workflow Guidance

### 1. Always Start with Session
```python
session = eventstream_start_definition(
    name="UserDescriptiveName",  # Use user's preferred name
    description="Clear description based on user requirements"
)
session_id = session["session_id"]
```

### 2. Guide Users Through Component Selection

#### Sources Selection
Ask users about their data source:
- **"Do you want to use sample data for testing?"** → `eventstream_add_sample_data_source`
- **"Do you have a custom API or endpoint?"** → `eventstream_add_custom_endpoint_source`

For sample data, explain options:
- **Bicycles**: Small, structured data good for learning
- **Stock**: Time-series data good for analytics
- **YellowTaxi**: Larger dataset good for performance testing
- **Clickstream**: High-volume data good for scale testing

#### Streams Design
Explain stream types:
- **Default Stream**: Direct passthrough from sources (recommended for beginners)
- **Derived Stream**: For processed/transformed data (advanced scenarios)

#### Destinations Selection  
Ask about data usage:
- **"Do you want to store data for analytics?"** → Eventhouse destination
- **"Do you need real-time integration?"** → Custom endpoint destination
- **"Do you want both?"** → Add multiple destinations

### 3. Always Validate Before Creating
```python
validation = eventstream_validate_definition(session_id)
if not validation["is_valid"]:
    # Show errors to user and guide fixes
    # Don't proceed to creation
```

### 4. Create Only After Successful Validation
```python
if validation["is_valid"]:
    result = eventstream_create_from_definition(session_id, workspace_id)
    # Show success message with eventstream details
```

## User Interaction Patterns

### Beginner Users
1. Start with simple explanation of eventstreams
2. Suggest sample data source for learning
3. Use default stream for simplicity
4. Add Eventhouse destination for data exploration
5. Explain each step as you go

Example conversation:
```
User: "I want to create an eventstream"
AI: "I'll help you create an eventstream step-by-step. Let's start with sample data to learn how it works, then you can customize later. What should we call your eventstream?"
User: "TestStream"
AI: "Great! Let me start a session for 'TestStream'..."
```

### Advanced Users
1. Ask about specific requirements upfront
2. Suggest appropriate patterns based on use case
3. Explain why certain configurations are recommended
4. Offer optimization suggestions

### Learning Users
1. Explain each component type when adding
2. Show the current definition periodically
3. Explain validation results clearly
4. Suggest improvements based on best practices

## Common Use Cases and Patterns

### Demo/PoC Creation
```python
# Quick demo setup
session = eventstream_start_definition("Demo", "Quick demo eventstream")
eventstream_add_sample_data_source(session_id, "SampleData", "Bicycles")
eventstream_add_default_stream(session_id, "MainStream", ["SampleData"])
eventstream_add_eventhouse_destination(session_id, "Analytics", workspace_id, eh_id, "demo", "events", ["MainStream"])
```

### IoT Data Pipeline
```python
# IoT scenario
session = eventstream_start_definition("IoTPipeline", "Industrial sensor data pipeline")
eventstream_add_custom_endpoint_source(session_id, "SensorAPI", "https://sensors.company.com/data")
eventstream_add_default_stream(session_id, "SensorStream", ["SensorAPI"])
eventstream_add_eventhouse_destination(session_id, "HistoricalData", workspace_id, eh_id, "iot", "sensors", ["SensorStream"])
eventstream_add_custom_endpoint_destination(session_id, "AlertSystem", "https://alerts.company.com/webhook", ["SensorStream"])
```

### Real-time Integration
```python
# API integration
session = eventstream_start_definition("APIIntegration", "Real-time API data forwarding")
eventstream_add_custom_endpoint_source(session_id, "ExternalAPI", "https://external.api.com/events")
eventstream_add_default_stream(session_id, "APIStream", ["ExternalAPI"])
eventstream_add_custom_endpoint_destination(session_id, "InternalSystem", "https://internal.company.com/webhook", ["APIStream"])
```

## Error Handling Guidance

### Session Errors
- If session not found, start a new one
- If session timeout, restart workflow
- Always check session exists before operations

### Validation Errors
Show users exactly what needs to be fixed:
```python
validation = eventstream_validate_definition(session_id)
if not validation["is_valid"]:
    print("❌ Please fix these issues:")
    for error in validation["errors"]:
        print(f"  • {error}")
    
    if validation["warnings"]:
        print("⚠️ Consider these improvements:")
        for warning in validation["warnings"]:
            print(f"  • {warning}")
```

### Resource Errors
- Verify workspace exists and is accessible
- Check Eventhouse permissions
- Validate custom endpoint accessibility

## Conversation Flow Examples

### Complete Beginner Flow
```
User: "How do I create an eventstream?"
AI: "I'll guide you through creating an eventstream step-by-step! An eventstream processes real-time data from sources to destinations. Let's start:

1. First, what would you like to name your eventstream?"

User: "MyFirstStream"
AI: "Perfect! I'll create a session for 'MyFirstStream'. For learning, I recommend starting with sample data. Would you like to use sample bicycle data, stock market data, or taxi trip data?"

User: "Bicycle data sounds good"
AI: "Great choice! Bicycle data is perfect for learning - it's small and easy to understand. Let me add that as a source..."

[Continue building step by step]
```

### Advanced User Flow
```
User: "I need an eventstream that takes data from our API and sends it to both our data warehouse and a webhook"
AI: "That's a perfect use case for multiple destinations! Let me help you build:

1. Source: Your API endpoint
2. Stream: Process the API data  
3. Destinations: Both Eventhouse (data warehouse) and custom endpoint (webhook)

What's your API endpoint URL?"

User: "https://api.ourcompany.com/events"
AI: "Excellent! Let me start building this eventstream with your API source..."
```

## Best Practices for AI Assistants

### Do
- Always validate before creating
- Explain each step clearly
- Ask clarifying questions when requirements are unclear
- Suggest best practices based on use case
- Show current definition state when helpful
- Provide next steps after creation

### Don't
- Skip validation step
- Create without user confirmation
- Use complex configurations for beginners
- Assume user requirements without asking
- Proceed if validation fails
- Forget to explain what each component does

## Tool Usage Patterns

### Standard Workflow
1. `eventstream_start_definition()` - Always first
2. `eventstream_add_*_source()` - At least one source
3. `eventstream_add_*_stream()` - Connect sources to processing
4. `eventstream_add_*_destination()` - Define where data goes
5. `eventstream_validate_definition()` - Always before creation
6. `eventstream_create_from_definition()` - Final step

### Inspection and Debugging
- Use `eventstream_get_current_definition()` to show progress
- Use `eventstream_list_available_components()` to show options
- Use `eventstream_validate_definition()` for troubleshooting

### Recovery and Restart
- Use `eventstream_clear_definition()` to start over
- Always check if session exists before operations
- Restart workflow if session is lost

## Integration with Other Tools

### Workspace Discovery
Before creating, help user find workspace:
```python
# If workspace_id not known, help user discover
workspaces = fabric_list_workspaces()  # If available
```

### Eventhouse Integration  
Help user find Eventhouse resources:
```python
# Guide user to correct Eventhouse details
# Explain database and table requirements
```

### Custom Endpoint Testing
Suggest testing endpoints before adding:
```python
# Recommend user verify endpoint accessibility
# Explain authentication requirements
```

## Troubleshooting Common Issues

### "Session not found"
1. Check if MCP server restarted (sessions are in-memory)
2. Start new session
3. Guide user through workflow again

### "Source/Stream not found"
1. Show current definition to user
2. Check component names match exactly
3. Ensure proper order (sources before streams, streams before destinations)

### "Invalid workspace"
1. Verify workspace ID format (UUID)
2. Check user permissions
3. Try listing available workspaces

### "Permission denied"
1. Check Fabric authentication
2. Verify workspace access
3. Confirm Eventhouse permissions

## Success Metrics

### Successful Session
- Session created successfully
- All components added without errors
- Validation passes
- Eventstream created in Fabric
- User understands the workflow

### Learning Outcomes
- User understands eventstream components
- User can repeat process independently
- User knows how to troubleshoot common issues
- User understands best practices

## Advanced Scenarios

### Multi-Stream Processing
When user needs complex processing:
1. Start with simple default stream
2. Add derived streams for processing
3. Explain stream relationships
4. Validate data flow logic

### High-Volume Data
When user mentions performance:
1. Recommend appropriate sample data types for testing
2. Suggest ingestion mode options
3. Explain scaling considerations
4. Plan for monitoring and optimization

### Enterprise Integration
When user mentions enterprise requirements:
1. Focus on security best practices
2. Explain compliance considerations
3. Suggest proper authentication methods
4. Plan for monitoring and governance
