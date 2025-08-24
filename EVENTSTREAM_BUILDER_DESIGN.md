# 🎯 **Eventstream Builder Design Plan**
*Based on Microsoft Fabric Eventstream API Specification*

## 🏗️ **Core Architecture Concept**

### **Builder Pattern with Real Fabric Components**
Building eventstreams using actual Microsoft Fabric source types, destination types, and operators as documented in the official API.

```
Real Sources + Real Destinations + Real Operators + Real Streams = Fabric-Compatible Definition → Create Eventstream
```

## 📦 **Tool Categories Based on Fabric API**

### **1. Source Management Tools**
**Purpose:** Add and configure real Fabric data sources

#### **Cloud Sources:**
- `eventstream_add_azure_eventhub_source()` - Azure Event Hub
- `eventstream_add_azure_iothub_source()` - Azure IoT Hub  
- `eventstream_add_amazon_kinesis_source()` - Amazon Kinesis
- `eventstream_add_amazon_msk_kafka_source()` - Amazon MSK Kafka
- `eventstream_add_apache_kafka_source()` - Apache Kafka
- `eventstream_add_confluent_cloud_source()` - Confluent Cloud
- `eventstream_add_google_pubsub_source()` - Google Pub/Sub

#### **Database CDC Sources:**
- `eventstream_add_azure_cosmosdb_cdc_source()` - Azure Cosmos DB CDC
- `eventstream_add_azure_sqldb_cdc_source()` - Azure SQL DB CDC
- `eventstream_add_azure_sqlmi_cdc_source()` - Azure SQL Managed Instance CDC
- `eventstream_add_sqlserver_vm_cdc_source()` - SQL Server on VM CDC
- `eventstream_add_mysql_cdc_source()` - MySQL CDC
- `eventstream_add_postgresql_cdc_source()` - PostgreSQL CDC

#### **Fabric-Native Sources:**
- `eventstream_add_sample_data_source()` - Sample Data (Bicycles, etc.)
- `eventstream_add_fabric_workspace_events_source()` - Fabric Workspace Events
- `eventstream_add_fabric_job_events_source()` - Fabric Job Events
- `eventstream_add_fabric_onelake_events_source()` - Fabric OneLake Events
- `eventstream_add_custom_endpoint_source()` - Custom REST Endpoint

### **2. Destination Management Tools**
**Purpose:** Add and configure real Fabric destinations

#### **Fabric Destinations:**
- `eventstream_add_eventhouse_destination()` - Eventhouse (KQL Database)
- `eventstream_add_lakehouse_destination()` - Lakehouse (Delta Tables)
- `eventstream_add_custom_endpoint_destination()` - Custom REST Endpoint

### **3. Operator Management Tools**
**Purpose:** Add real Fabric stream processing operators

#### **Data Processing Operators:**
- `eventstream_add_filter_operator()` - Filter with conditions
- `eventstream_add_manage_fields_operator()` - Rename/Cast/Function operations
- `eventstream_add_aggregate_operator()` - Aggregation with partitioning
- `eventstream_add_groupby_operator()` - Group By with windowing
- `eventstream_add_join_operator()` - Join streams with time windows
- `eventstream_add_union_operator()` - Union multiple streams
- `eventstream_add_expand_operator()` - Expand JSON/nested data

### **4. Stream Management Tools**
**Purpose:** Define actual Fabric stream types

#### **Stream Types:**
- `eventstream_add_default_stream()` - Default stream from sources
- `eventstream_add_derived_stream()` - Derived stream from operators

### **5. Definition Management Tools**
**Purpose:** Manage the complete eventstream lifecycle

- `eventstream_start_definition()` - Initialize new definition
- `eventstream_get_current_definition()` - View current state
- `eventstream_validate_definition()` - Fabric-compliant validation
- `eventstream_create_from_definition()` - Deploy to Fabric
- `eventstream_clear_definition()` - Reset builder

## 🔍 **Detailed Tool Specifications**

### **Example: Azure Event Hub Source**
```python
def eventstream_add_azure_eventhub_source(
    source_name: str,
    data_connection_id: str,
    consumer_group_name: str = "$Default",
    encoding: str = "UTF8",
    definition_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add Azure Event Hub source to eventstream definition.
    
    :param source_name: Unique name for this source
    :param data_connection_id: Azure Event Hub connection ID (UUID)
    :param consumer_group_name: Consumer group name
    :param encoding: Input encoding (UTF8, etc.)
    :param definition_id: Session ID for the definition being built
    :return: Updated definition summary with source added
    """
```

### **Example: Eventhouse Destination**
```python
def eventstream_add_eventhouse_destination(
    destination_name: str,
    workspace_id: str,
    item_id: str,
    database_name: str,
    table_name: str,
    data_ingestion_mode: str = "ProcessedIngestion",
    encoding: str = "UTF8",
    input_nodes: List[str] = None,
    definition_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add Eventhouse destination to eventstream definition.
    
    :param destination_name: Unique name for this destination
    :param workspace_id: Fabric workspace ID
    :param item_id: Eventhouse item ID
    :param database_name: Target KQL database name
    :param table_name: Target table name
    :param data_ingestion_mode: ProcessedIngestion or DirectIngestion
    :param encoding: Input encoding
    :param input_nodes: Source nodes feeding this destination
    :param definition_id: Session ID for the definition being built
    :return: Updated definition with destination added
    """
```

### **Example: Filter Operator**
```python
def eventstream_add_filter_operator(
    operator_name: str,
    input_nodes: List[str],
    conditions: List[Dict[str, Any]],
    definition_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add filter operator to eventstream definition.
    
    :param operator_name: Unique name for this operator
    :param input_nodes: Input stream/operator names
    :param conditions: Filter conditions in Fabric format
    :param definition_id: Session ID for the definition being built
    :return: Updated definition with operator added
    
    Example conditions:
    [
        {
            "column": {
                "columnName": "BikepointID",
                "expressionType": "ColumnReference"
            },
            "operatorType": "NotEquals",
            "value": {
                "dataType": "Nvarchar(max)",
                "value": "0",
                "expressionType": "Literal"
            }
        }
    ]
    """
```

### **Example: Sample Data Source**
```python
def eventstream_add_sample_data_source(
    source_name: str,
    sample_type: str = "Bicycles",
    definition_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add sample data source to eventstream definition.
    
    :param source_name: Unique name for this source
    :param sample_type: Type of sample data (Bicycles, Stock, IoT, etc.)
    :param definition_id: Session ID for the definition being built
    :return: Updated definition with sample source added
    """
```

## 🎯 **Enhanced Workflow Examples**

### **Simple Bicycles to Eventhouse:**
```python
# 1. Start building
eventstream_start_definition(name="BicyclesAnalytics")

# 2. Add sample source
eventstream_add_sample_data_source(
    source_name="BicyclesSource",
    sample_type="Bicycles"
)

# 3. Add default stream
eventstream_add_default_stream(
    stream_name="BicyclesStream",
    input_nodes=["BicyclesSource"]
)

# 4. Add eventhouse destination
eventstream_add_eventhouse_destination(
    destination_name="AnalyticsDB",
    workspace_id="1fe73fdf-9574-47fe-9b23-cb0b6d8d74b1",
    item_id="ad39bea2-f4ba-4cb6-adfa-598dd1ccb594",
    database_name="RoomSensorsEventhouse",
    table_name="BicycleData",
    input_nodes=["BicyclesStream"]
)

# 5. Create the eventstream
eventstream_create_from_definition(
    workspace_id="1fe73fdf-9574-47fe-9b23-cb0b6d8d74b1"
)
```

### **Complex Processing Pipeline:**
```python
# 1. Start building
eventstream_start_definition(name="ComplexBicyclesProcessing")

# 2. Add sample source
eventstream_add_sample_data_source("BicyclesSource", "Bicycles")

# 3. Add default stream
eventstream_add_default_stream("RawBicycles", ["BicyclesSource"])

# 4. Add filter for active bikes
eventstream_add_filter_operator(
    operator_name="ActiveBikesFilter",
    input_nodes=["RawBicycles"],
    conditions=[{
        "column": {"columnName": "BikepointID", "expressionType": "ColumnReference"},
        "operatorType": "NotEquals",
        "value": {"dataType": "Nvarchar(max)", "value": "0", "expressionType": "Literal"}
    }]
)

# 5. Add aggregation
eventstream_add_groupby_operator(
    operator_name="BikeStats",
    input_nodes=["ActiveBikesFilter"],
    group_by_columns=["Location"],
    aggregations=[{
        "aggregateFunction": "Average",
        "column": {"columnName": "AvailableBikes"},
        "alias": "AVG_Available"
    }],
    window_type="Tumbling",
    window_duration={"value": 5, "unit": "Minute"}
)

# 6. Add derived stream
eventstream_add_derived_stream("ProcessedBicycles", ["BikeStats"])

# 7. Add eventhouse destination
eventstream_add_eventhouse_destination(
    destination_name="ProcessedAnalytics",
    workspace_id="1fe73fdf-9574-47fe-9b23-cb0b6d8d74b1",
    item_id="ad39bea2-f4ba-4cb6-adfa-598dd1ccb594",
    database_name="RoomSensorsEventhouse",
    table_name="BikeAggregates",
    input_nodes=["ProcessedBicycles"]
)

# 8. Create the eventstream
eventstream_create_from_definition(
    workspace_id="1fe73fdf-9574-47fe-9b23-cb0b6d8d74b1"
)
```

## 💾 **State Management with Fabric Schema**

### **EventstreamDefinitionBuilder Class:**
```python
class EventstreamDefinitionBuilder:
    def __init__(self):
        self.definition = {
            "sources": [],
            "destinations": [],
            "operators": [],
            "streams": [],
            "compatibilityLevel": "1.0"
        }
        self.metadata = {
            "name": None,
            "description": None,
            "created_at": None,
            "session_id": str(uuid.uuid4())
        }
    
    def add_source(self, source_config: Dict[str, Any]) -> None:
        """Add a source using Fabric API format"""
        self.definition["sources"].append(source_config)
    
    def add_destination(self, dest_config: Dict[str, Any]) -> None:
        """Add a destination using Fabric API format"""
        self.definition["destinations"].append(dest_config)
    
    def validate_fabric_compliance(self) -> List[str]:
        """Validate against Fabric API schema"""
        # Implement Fabric-specific validation rules
        pass
```

## 🔍 **Discovery and Helper Tools**

### **Discovery Tools:**
```python
def eventstream_list_sample_data_types() -> List[str]:
    """Return available sample data types"""
    return ["Bicycles", "Stock", "IoT", "WebLogs", "SalesData"]

def eventstream_list_operator_types() -> List[str]:
    """Return available operator types"""
    return ["Filter", "ManageFields", "Aggregate", "GroupBy", "Join", "Union", "Expand"]

def eventstream_get_operator_schema(operator_type: str) -> Dict[str, Any]:
    """Get the expected schema for an operator type"""
    # Return Fabric API schema for the operator
    pass
```

## 🎯 **Benefits of Fabric-Native Design**

### **Compliance & Compatibility:**
- **API Compliant** - Generated definitions match Fabric API exactly
- **Future Proof** - Based on official Microsoft specification
- **Validation** - Schema validation against real Fabric requirements

### **Rich Functionality:**
- **17 Source Types** - All major cloud and database sources
- **3 Destination Types** - Fabric-native destinations
- **7 Operator Types** - Complete processing capabilities
- **2 Stream Types** - Default and derived streams

### **Real-World Ready:**
- **Production Ready** - Based on actual Fabric capabilities
- **Enterprise Sources** - CDC, Kafka, Event Hubs, IoT Hub
- **Advanced Processing** - Joins, aggregations, windowing
- **Fabric Integration** - Native Eventhouse, Lakehouse support

## 🚀 **Implementation Phases**

### **Phase 1: Foundation (Week 1)**
- EventstreamDefinitionBuilder class
- Basic source tools (SampleData, CustomEndpoint)
- Basic destination tools (Eventhouse)
- Simple stream creation
- Core validation framework

### **Phase 2: Core Sources (Week 2)**
- Azure Event Hub, IoT Hub sources
- Amazon Kinesis, MSK sources
- Kafka sources (Apache, Confluent)
- Basic operator support (Filter, ManageFields)

### **Phase 3: Advanced Operators (Week 3)**
- Aggregate, GroupBy operators
- Join, Union, Expand operators
- Complex condition building
- Window function support

### **Phase 4: Advanced Sources (Week 4)**
- All CDC sources (Cosmos, SQL, MySQL, PostgreSQL)
- Fabric event sources (Workspace, Job, OneLake)
- Google Pub/Sub source
- Lakehouse destinations

### **Phase 5: Polish & Documentation (Week 5)**
- Discovery tools
- Advanced validation
- Comprehensive examples
- Performance optimization
- Documentation and tutorials

## 📋 **Fabric API Reference**

### **Complete Source Types:**
1. **AzureEventHub** - Azure Event Hub
2. **AzureIoTHub** - Azure IoT Hub
3. **CustomEndpoint** - Custom REST Endpoint
4. **SampleData** - Sample Data (Bicycles, Stock, etc.)
5. **AmazonKinesis** - Amazon Kinesis
6. **AmazonMSKKafka** - Amazon MSK Kafka
7. **ApacheKafka** - Apache Kafka
8. **ConfluentCloud** - Confluent Cloud
9. **AzureCosmosDBCDC** - Azure Cosmos DB CDC
10. **AzureSQLDBCDC** - Azure SQL Database CDC
11. **AzureSQLMIDBCDC** - Azure SQL Managed Instance CDC
12. **SQLServerOnVMDBCDC** - SQL Server on VM CDC
13. **MySQLCDC** - MySQL CDC
14. **PostgreSQLCDC** - PostgreSQL CDC
15. **GooglePubSub** - Google Pub/Sub
16. **FabricWorkspaceItemEvents** - Fabric Workspace Events
17. **FabricJobEvents** - Fabric Job Events
18. **FabricOneLakeEvents** - Fabric OneLake Events

### **Complete Destination Types:**
1. **CustomEndpoint** - Custom REST Endpoint
2. **Lakehouse** - Lakehouse (Delta Tables)
3. **Eventhouse** - Eventhouse (KQL Database)

### **Complete Operator Types:**
1. **Filter** - Conditional filtering
2. **Join** - Stream joining with time windows
3. **ManageFields** - Rename, Cast, Function operations
4. **Aggregate** - Aggregation with partitioning
5. **GroupBy** - Group By with windowing
6. **Union** - Union multiple streams
7. **Expand** - Expand JSON/nested data

### **Stream Types:**
1. **DefaultStream** - Default stream from sources
2. **DerivedStream** - Derived stream from operators

## 🔧 **Technical Implementation Notes**

### **Session Management:**
- Each builder session gets a unique UUID
- Session state persists for reasonable timeout period
- Multiple concurrent sessions supported
- Session cleanup on completion or timeout

### **Validation Strategy:**
- **Input Validation** - Parameter checking for each tool
- **Semantic Validation** - Logical consistency (e.g., compatible data types)
- **Topology Validation** - Ensure connected flow exists
- **API Validation** - Final check against Fabric API schema

### **Error Handling:**
- Clear error messages with specific guidance
- Validation errors include suggested fixes
- Progressive validation after each addition
- Rollback capability for invalid operations

### **Performance Considerations:**
- Lazy validation (validate on request, not on every addition)
- Efficient session storage and retrieval
- Minimal API calls during building phase
- Batch validation for complex definitions

---

## 📚 **Reference Links**

- [Microsoft Fabric Eventstream API](https://github.com/microsoft/fabric-event-streams/blob/main/API%20Templates/eventstream-definition.json)
- [Fabric Real-Time Intelligence Documentation](https://learn.microsoft.com/en-us/fabric/real-time-intelligence/)
- [Eventstream Documentation](https://learn.microsoft.com/en-us/fabric/real-time-intelligence/event-streams/)

---

**Created:** July 2, 2025  
**Version:** 1.0  
**Status:** Design Phase
