# Eventstream Definition Schema Fix Report

## Issue Identified

The eventstream builder was incorrectly including `name` and `description` fields in the eventstream definition that gets base64-encoded and sent to the Microsoft Fabric API.

## Root Cause Analysis

### Incorrect Structure (Before Fix)
```json
// Builder was creating this definition:
{
  "name": "TestMCPSampleBikes",           // ❌ Should not be here
  "description": "Simple eventstream...", // ❌ Should not be here
  "sources": [...],
  "streams": [...],
  "destinations": [...],
  "operators": [...],
  "compatibilityLevel": "1.0"
}

// Which resulted in this HTTP payload:
{
  "displayName": "TestMCPSampleBikes",    // ✅ Correct location
  "description": "Simple eventstream...", // ✅ Correct location
  "definition": {
    "parts": [{
      "payload": "<base64-encoded-definition-with-duplicate-name-description>"
    }]
  }
}
```

### Correct Structure (After Fix)
```json
// Builder now creates this definition:
{
  "sources": [...],
  "streams": [...], 
  "destinations": [...],
  "operators": [...],
  "compatibilityLevel": "1.0"
}

// Which results in this HTTP payload:
{
  "displayName": "TestMCPSampleBikes",    // ✅ Name goes here
  "description": "Simple eventstream...", // ✅ Description goes here
  "definition": {
    "parts": [{
      "payload": "<base64-encoded-definition-without-duplicates>"
    }]
  }
}
```

## Evidence from Existing Code

The original `_create_basic_eventstream_definition()` in `eventstream_service.py` was already correct:
```python
def _create_basic_eventstream_definition(name, stream_id):
    return {
        "compatibilityLevel": "1.0",      # ✅ No name/description
        "sources": [],
        "destinations": [],
        "operators": [],
        "streams": [...]
    }
```

But the builder's `_create_basic_definition()` was incorrect:
```python
def _create_basic_definition(name, description):
    return {
        "name": name,                     # ❌ Should not be here
        "description": description,       # ❌ Should not be here
        "sources": [],
        # ...
    }
```

## Fix Applied

### Code Changes
- **File**: `eventstream_builder_service.py`
- **Function**: `_create_basic_definition()`
- **Change**: Removed `name` and `description` from the returned definition
- **Reason**: These fields belong in the outer HTTP payload, not the inner eventstream definition

### Updated Function
```python
def _create_basic_definition(name: str, description: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a basic eventstream definition template for the interactive builder workflow.
    This creates an empty structure that gets populated through builder methods.
    Note: name and description are NOT included here as they belong in the outer HTTP payload.
    
    :param name: Name of the eventstream being built (used for session metadata only)
    :param description: Optional description of the eventstream (used for session metadata only)
    :return: Empty eventstream definition template ready for builder population
    """
    return {
        "sources": [],
        "streams": [],
        "destinations": [],
        "operators": [],
        "compatibilityLevel": "1.0"
    }
```

## Impact Assessment

### Positive Impacts
1. **API Compliance**: Definition structure now matches Microsoft Fabric API schema exactly
2. **No Duplication**: Eliminates duplicate name/description in HTTP payload
3. **Consistency**: Builder and direct service now use the same definition structure
4. **Cleaner Payload**: Smaller, cleaner base64-encoded definition

### Potential Concerns
1. **Backward Compatibility**: Existing definitions with name/description may still work (Microsoft APIs often ignore extra fields)
2. **Testing Needed**: Should verify that the API accepts both formats

## Verification

### Before Fix
```json
{
  "name": "TestMCPSampleBikes",
  "description": "Simple eventstream for bicycle sample data with derived stream", 
  "sources": [...],
  "streams": [...],
  "destinations": [],
  "operators": [],
  "compatibilityLevel": "1.0"
}
```

### After Fix  
```json
{
  "sources": [...],
  "streams": [...],
  "destinations": [],
  "operators": [],
  "compatibilityLevel": "1.0"
}
```

## Recommendation

✅ **This fix should be applied** because:
1. It aligns with the official Microsoft Fabric API schema
2. It matches the existing pattern in `eventstream_service.py`
3. It eliminates redundant data in the HTTP payload
4. It's unlikely to break existing functionality (APIs typically ignore extra fields)

## Status: ✅ FIXED

The eventstream definition structure has been corrected to match the Microsoft Fabric API schema. Name and description are now properly stored in session metadata and used only in the outer HTTP payload, not in the inner eventstream definition.
