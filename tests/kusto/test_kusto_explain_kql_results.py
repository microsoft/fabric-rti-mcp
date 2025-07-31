from unittest.mock import patch
import pytest
from fabric_rti_mcp.kusto.kusto_service import kusto_explain_kql_results


@patch("fabric_rti_mcp.kusto.kusto_service.DEFAULT_COMPLETION_ENDPOINT", "https://test-endpoint.com")
def test_kusto_explain_kql_results_success() -> None:
    """Test that kusto_explain_kql_results successfully modifies KQL query to add explanations."""
    # Arrange
    input_query = "StormEvents | take 5"
    
    # Act
    result = kusto_explain_kql_results(input_query)
    
    # Assert
    assert isinstance(result, str)
    assert "let model_endpoint = 'https://test-endpoint.com'" in result
    assert "StormEvents | take 5" in result
    assert "| extend RowData = tostring(pack_all())" in result
    assert "| extend NaturalLanguageDescription = toscalar(evaluate ai_completion" in result
    assert "| project-away RowData" in result


@patch("fabric_rti_mcp.kusto.kusto_service.DEFAULT_COMPLETION_ENDPOINT", "https://test-endpoint.com")
def test_kusto_explain_kql_results_complex_query() -> None:
    """Test with a more complex KQL query."""
    # Arrange
    input_query = """StormEvents 
| where State == "TEXAS"
| summarize count() by EventType
| order by count_ desc"""
    
    # Act
    result = kusto_explain_kql_results(input_query)
    
    # Assert
    assert isinstance(result, str)
    assert "let model_endpoint = 'https://test-endpoint.com'" in result
    # Should preserve the original query structure
    assert 'where State == "TEXAS"' in result
    assert "summarize count() by EventType" in result
    assert "order by count_ desc" in result
    assert "| extend RowData = tostring(pack_all())" in result
    assert "| extend NaturalLanguageDescription = toscalar(evaluate ai_completion" in result


def test_kusto_explain_kql_results_empty_query() -> None:
    """Test that empty query raises ValueError."""
    with pytest.raises(ValueError, match="KQL query cannot be empty"):
        kusto_explain_kql_results("")
    
    with pytest.raises(ValueError, match="KQL query cannot be empty"):
        kusto_explain_kql_results("   ")


@patch("fabric_rti_mcp.kusto.kusto_service.DEFAULT_COMPLETION_ENDPOINT", None)
def test_kusto_explain_kql_results_no_endpoint() -> None:
    """Test that missing endpoint raises ValueError."""
    with pytest.raises(ValueError, match="No completion endpoint provided"):
        kusto_explain_kql_results("StormEvents | take 5")


@patch("fabric_rti_mcp.kusto.kusto_service.DEFAULT_COMPLETION_ENDPOINT", "https://test-endpoint.com")
def test_kusto_explain_kql_results_custom_endpoint() -> None:
    """Test using custom completion endpoint."""
    # Arrange
    input_query = "StormEvents | take 3"
    custom_endpoint = "https://custom-endpoint.com"
    
    # Act
    result = kusto_explain_kql_results(input_query, completion_endpoint=custom_endpoint)
    
    # Assert
    assert f"let model_endpoint = '{custom_endpoint}'" in result
    assert "StormEvents | take 3" in result


@patch("fabric_rti_mcp.kusto.kusto_service.DEFAULT_COMPLETION_ENDPOINT", "https://test-endpoint.com")
def test_kusto_explain_kql_results_whitespace_handling() -> None:
    """Test that query whitespace is properly handled."""
    # Arrange
    input_query = """
    
    StormEvents | take 10
    
    """
    
    # Act
    result = kusto_explain_kql_results(input_query)
    
    # Assert
    # Should clean up whitespace but preserve the query
    assert "StormEvents | take 10" in result
    assert "let model_endpoint = 'https://test-endpoint.com'" in result
    lines = result.split('\n')
    # First line should be the let statement
    assert lines[0] == "let model_endpoint = 'https://test-endpoint.com';"


@patch("fabric_rti_mcp.kusto.kusto_service.DEFAULT_COMPLETION_ENDPOINT", "https://test-endpoint.com")
def test_kusto_explain_kql_results_query_structure() -> None:
    """Test that the returned query has the correct structure."""
    # Arrange
    input_query = "MyTable | where Column1 > 100"
    
    # Act
    result = kusto_explain_kql_results(input_query)
    
    # Assert
    lines = [line.strip() for line in result.split('\n') if line.strip()]
    
    # Should have the expected structure
    assert lines[0] == "let model_endpoint = 'https://test-endpoint.com';"
    assert lines[1] == "MyTable | where Column1 > 100"
    assert lines[2] == "| extend RowData = tostring(pack_all())"
    assert lines[3].startswith("| extend NaturalLanguageDescription = toscalar(evaluate ai_completion(")
    assert lines[4] == "| project-away RowData"


@patch("fabric_rti_mcp.kusto.kusto_service.DEFAULT_COMPLETION_ENDPOINT", "https://test-endpoint.com")
def test_kusto_explain_kql_results_prompt_content() -> None:
    """Test that the AI completion prompt is correctly structured."""
    # Arrange
    input_query = "TestTable | take 1"
    
    # Act
    result = kusto_explain_kql_results(input_query)
    
    # Assert
    # Should contain the correct prompt structure
    assert "strcat('Explain this data row in natural language: ', RowData)" in result
    assert "evaluate ai_completion" in result
