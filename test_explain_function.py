#!/usr/bin/env python3

import os
os.environ['AZ_OPENAI_COMPLETION_ENDPOINT'] = 'https://test-endpoint.com'

from fabric_rti_mcp.kusto.kusto_service import kusto_explain_kql_results

def test_function():
    # Test 1: Simple query
    print("Test 1: Simple query")
    query1 = "StormEvents | take 5"
    result1 = kusto_explain_kql_results(query1)
    print("Input:")
    print(query1)
    print("\nOutput:")
    print(result1)
    print("\n" + "="*60 + "\n")
    
    # Test 2: Complex query
    print("Test 2: Complex query")
    query2 = """StormEvents 
| where State == "TEXAS"
| summarize count() by EventType
| order by count_ desc
| take 10"""
    result2 = kusto_explain_kql_results(query2)
    print("Input:")
    print(query2)
    print("\nOutput:")
    print(result2)
    print("\n" + "="*60 + "\n")
    
    # Test 3: Query with custom endpoint
    print("Test 3: Query with custom endpoint")
    query3 = "MyTable | where Column1 > 100"
    result3 = kusto_explain_kql_results(query3, completion_endpoint="https://custom-endpoint.com")
    print("Input:")
    print(query3)
    print("\nOutput:")
    print(result3)

if __name__ == "__main__":
    test_function()
