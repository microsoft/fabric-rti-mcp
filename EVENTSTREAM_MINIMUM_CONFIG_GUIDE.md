# Minimum Configuration for Valid Microsoft Fabric Eventstream

Based on analysis of working eventstreams and successful API calls, here's the optimal minimum configuration for a valid Eventstream:

## 🏗️ Core Architecture Requirements

### **1. ABSOLUTE MINIMUM (Source + Default Stream)**
```json
{
  "sources": [
    {
      "name": "DataSource", 
      "type": "SampleData",
      "properties": {
        "type": "Bicycles"  // or "Stock", "YellowTaxi", "Clickstream"
      }
    }
  ],
  "streams": [
    {
      "name": "MyEventstream-stream",
      "type": "DefaultStream", 
      "properties": {},
      "inputNodes": [
        {
          "name": "DataSource"
        }
      ]
    }
  ],
  "destinations": [],
  "operators": [],
  "compatibilityLevel": "1.0"
}
```

### **2. PRACTICAL MINIMUM (Source + Default + Derived Stream)**
```json
{
  "sources": [
    {
      "name": "BicycleDataSource",
      "type": "SampleData",
      "properties": {
        "type": "Bicycles"
      }
    }
  ],
  "streams": [
    {
      "name": "MyEventstream-stream",
      "type": "DefaultStream",
      "properties": {},
      "inputNodes": [
        {
          "name": "BicycleDataSource"
        }
      ]
    },
    {
      "name": "ProcessedData", 
      "type": "DerivedStream",
      "properties": {
        "inputSerialization": {
          "type": "Json",
          "properties": {
            "encoding": "UTF8"
          }
        }
      },
      "inputNodes": [
        {
          "name": "MyEventstream-stream"
        }
      ]
    }
  ],
  "destinations": [],
  "operators": [],
  "compatibilityLevel": "1.0"
}
```

## 🔧 Builder Tool Recommendations

### **Current Issues with Builder Tools:**
1. **ID Fields Added Unnecessarily**: Builder functions add optional `id` fields that aren't required
2. **Limited Source Types**: Only supports SampleData and CustomEndpoint
3. **Fixed Stream Naming**: Default stream always uses `{eventstream-name}-stream`
4. **No Validation**: Missing pre-creation validation

### **Optimal Builder Tool Configuration:**

#### **1. Enhanced Source Configuration**
```python
def create_sample_data_source(name: str, sample_type: str = "Bicycles") -> dict:
    """Create a properly configured sample data source."""
    return {
        "name": name,
        "type": "SampleData", 
        "properties": {
            "type": sample_type  # "Bicycles", "Stock", "YellowTaxi", "Clickstream"
        }
    }
```

#### **2. Enhanced Stream Configuration**
```python
def create_default_stream(name: str, input_sources: list[str]) -> dict:
    """Create a default stream with proper configuration."""
    return {
        "name": name,
        "type": "DefaultStream",
        "properties": {},
        "inputNodes": [{"name": source} for source in input_sources]
    }

def create_derived_stream(name: str, input_streams: list[str]) -> dict:
    """Create a derived stream with JSON serialization."""
    return {
        "name": name,
        "type": "DerivedStream", 
        "properties": {
            "inputSerialization": {
                "type": "Json",
                "properties": {
                    "encoding": "UTF8"
                }
            }
        },
        "inputNodes": [{"name": stream} for stream in input_streams]
    }
```

## 📋 Critical Requirements Checklist

### **✅ MUST HAVE:**
- [ ] At least one **source** (no `id` field required)
- [ ] At least one **stream** that references the source
- [ ] **compatibilityLevel**: "1.0" (position doesn't matter, but conventionally at bottom)
- [ ] **inputNodes** array with proper `name` references
- [ ] **Empty arrays** for unused sections (destinations, operators)

### **✅ RECOMMENDED:**
- [ ] **Descriptive names** for all components
- [ ] **Default stream** as entry point from sources
- [ ] **Derived stream** for data processing/transformation
- [ ] **JSON serialization** properties for derived streams
- [ ] **Unique naming** to avoid "ItemDisplayNameNotAvailableYet" errors

### **❌ COMMON PITFALLS:**
- Creating streams without sources (causes "Default stream is not allowed when there are no sources")
- Missing `inputNodes` references
- Invalid source property types
- Reusing recent eventstream names

## 🚀 Recommended Builder Workflow

```python
# 1. Generate unique name with timestamp
eventstream_name = f"BikeStream{datetime.now().strftime('%Y%m%d%H%M')}"

# 2. Create source
source = create_sample_data_source("BicycleDataSource", "Bicycles")

# 3. Create default stream 
default_stream = create_default_stream(f"{eventstream_name}-stream", ["BicycleDataSource"])

# 4. Create derived stream
derived_stream = create_derived_stream("ProcessedBikeData", [f"{eventstream_name}-stream"])

# 5. Assemble definition
definition = {
    "sources": [source],
    "streams": [default_stream, derived_stream], 
    "destinations": [],
    "operators": [],
    "compatibilityLevel": "1.0"
}
```

This approach ensures minimal but complete eventstream configurations that will pass Fabric API validation.
