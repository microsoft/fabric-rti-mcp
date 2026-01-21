"""Unit tests for context abilities in kusto_service module."""

import os
from unittest.mock import MagicMock, patch

import pytest

from fabric_rti_mcp.services.kusto import kusto_service


@pytest.fixture
def mock_env_vars():
    """Set up environment variables for testing."""
    with patch.dict(os.environ, {
        kusto_service.CONTEXT_ABILITIES_KUSTO_URL: "https://test.kusto.windows.net",
        kusto_service.CONTEXT_ABILITIES_TABLE_NAME: "TestContextAbilities"
    }):
        yield


@pytest.fixture
def mock_kusto_query():
    """Mock the kusto_query function."""
    with patch('fabric_rti_mcp.services.kusto.kusto_service.kusto_query') as mock:
        yield mock


def test_context_disabled_when_no_env_vars():
    """Test that context is disabled when environment variables are not set."""
    with patch.dict(os.environ, {}, clear=True):
        assert not kusto_service.is_context_enabled()


def test_context_enabled_with_env_vars(mock_env_vars: None):
    """Test that context is enabled when both environment variables are set."""
    assert kusto_service.is_context_enabled()


def test_list_context_abilities_returns_empty_when_disabled():
    """Test that list_context_abilities returns empty list when disabled."""
    with patch.dict(os.environ, {}, clear=True):
        result = kusto_service.list_context_abilities()
        assert result == []


def test_list_context_abilities_queries_kusto(mock_env_vars: None, mock_kusto_query: MagicMock):
    """Test that list_context_abilities queries Kusto with correct parameters."""
    mock_kusto_query.return_value = {
        "format": "columnar",
        "data": {
            "FileName": ["ability1.md", "ability2.md"],
            "Content": [
                "# Ability 1\n\nDescription 1\n\nContent 1",
                "# Ability 2\n\nDescription 2\n\nContent 2"
            ]
        }
    }
    
    result = kusto_service.list_context_abilities()
    
    # Verify kusto_query was called
    mock_kusto_query.assert_called_once()
    call_args = mock_kusto_query.call_args
    assert call_args.kwargs['cluster_uri'] == "https://test.kusto.windows.net"
    assert "TestContextAbilities" in call_args.kwargs['query']
    assert "FileName" in call_args.kwargs['query']
    assert "Content" in call_args.kwargs['query']
    
    # Verify result structure (name should have .md stripped)
    assert len(result) == 2
    assert result[0]['name'] == "ability1"
    assert result[0]['description'] == "Description 1"  # First non-header line
    assert "# Ability 1" in result[0]['content']
    assert "test.kusto.windows.net" in result[0]['source']


def test_list_context_abilities_truncates_long_descriptions(mock_env_vars: None, mock_kusto_query: MagicMock):
    """Test that long descriptions are truncated."""
    long_content = "# Title\n\n" + "A" * 300
    mock_kusto_query.return_value = {
        "format": "columnar",
        "data": {
            "FileName": ["ability1.md"],
            "Content": [long_content]
        }
    }
    
    result = kusto_service.list_context_abilities()
    
    assert len(result) == 1
    assert len(result[0]['description']) == 203  # 200 chars + "..."
    assert result[0]['description'].endswith("...")


def test_list_context_abilities_handles_errors(mock_env_vars: None, mock_kusto_query: MagicMock):
    """Test that list_context_abilities handles query errors gracefully."""
    mock_kusto_query.side_effect = Exception("Query failed")
    
    result = kusto_service.list_context_abilities()
    
    assert len(result) == 1
    assert result[0]['name'] == "error"
    assert "Query failed" in result[0]['description']


def test_inject_context_ability_returns_error_when_disabled():
    """Test that inject_context_ability returns error when disabled."""
    with patch.dict(os.environ, {}, clear=True):
        result = kusto_service.inject_context_ability("test_ability")
        
        assert result['name'] == "test_ability"
        assert "not configured" in result['description']
        assert result['source'] == "not_configured"


def test_inject_context_ability_queries_kusto(mock_env_vars: None, mock_kusto_query: MagicMock):
    """Test that inject_context_ability queries Kusto correctly."""
    mock_kusto_query.return_value = {
        "format": "columnar",
        "data": {
            "FileName": ["ability1.md"],
            "Content": ["# Ability 1\n\nDescription 1\n\nFull content here"]
        }
    }
    
    result = kusto_service.inject_context_ability("ability1")
    
    # Verify kusto_query was called
    mock_kusto_query.assert_called_once()
    call_args = mock_kusto_query.call_args
    assert call_args.kwargs['cluster_uri'] == "https://test.kusto.windows.net"
    assert "TestContextAbilities" in call_args.kwargs['query']
    assert "FileName" in call_args.kwargs['query']
    assert "ability1.md" in call_args.kwargs['query']  # Should add .md extension
    
    # Verify result
    assert result['name'] == "ability1"
    assert result['description'] == "Description 1"
    assert "# Ability 1" in result['content']


def test_inject_context_ability_returns_not_found(mock_env_vars: None, mock_kusto_query: MagicMock):
    """Test that inject_context_ability returns not found for missing ability."""
    mock_kusto_query.return_value = {
        "format": "columnar",
        "data": {
            "FileName": [],
            "Content": []
        }
    }
    
    result = kusto_service.inject_context_ability("missing_ability")
    
    assert result['name'] == "missing_ability"
    assert "not found" in result['description']
    assert result['content'] == ""


def test_inject_context_ability_handles_errors(mock_env_vars: None, mock_kusto_query: MagicMock):
    """Test that inject_context_ability handles errors gracefully."""
    mock_kusto_query.side_effect = Exception("Query failed")
    
    result = kusto_service.inject_context_ability("test_ability")
    
    assert result['name'] == "test_ability"
    assert "Query failed" in result['description']


def test_list_context_abilities_with_custom_columns(mock_kusto_query: MagicMock):
    """Test that context abilities work with custom column names."""
    with patch.dict(os.environ, {
        kusto_service.CONTEXT_ABILITIES_KUSTO_URL: "https://test.kusto.windows.net",
        kusto_service.CONTEXT_ABILITIES_TABLE_NAME: "CustomTable",
        kusto_service.CONTEXT_ABILITIES_NAME_COLUMN: "Title",
        kusto_service.CONTEXT_ABILITIES_CONTENT_COLUMN: "Body"
    }):
        mock_kusto_query.return_value = {
            "format": "columnar",
            "data": {
                "Title": ["custom-ability.md"],
                "Body": ["# Custom\n\nCustom description\n\nCustom content"]
            }
        }
        
        result = kusto_service.list_context_abilities()
        
        # Verify query uses custom column names
        call_args = mock_kusto_query.call_args
        assert "Title" in call_args.kwargs['query']
        assert "Body" in call_args.kwargs['query']
        
        # Verify result
        assert len(result) == 1
        assert result[0]['name'] == "custom-ability"
        assert result[0]['description'] == "Custom description"


def test_inject_context_ability_with_custom_columns(mock_kusto_query: MagicMock):
    """Test that inject_context_ability works with custom column names."""
    with patch.dict(os.environ, {
        kusto_service.CONTEXT_ABILITIES_KUSTO_URL: "https://test.kusto.windows.net",
        kusto_service.CONTEXT_ABILITIES_TABLE_NAME: "CustomTable",
        kusto_service.CONTEXT_ABILITIES_NAME_COLUMN: "Title",
        kusto_service.CONTEXT_ABILITIES_CONTENT_COLUMN: "Body"
    }):
        mock_kusto_query.return_value = {
            "format": "columnar",
            "data": {
                "Title": ["custom-ability.md"],
                "Body": ["# Custom\n\nCustom description"]
            }
        }
        
        result = kusto_service.inject_context_ability("custom-ability")
        
        # Verify query uses custom column names
        call_args = mock_kusto_query.call_args
        assert "Title" in call_args.kwargs['query']
        assert "Body" in call_args.kwargs['query']
        assert "custom-ability.md" in call_args.kwargs['query']
        
        # Verify result
        assert result['name'] == "custom-ability"
        assert result['description'] == "Custom description"
        assert "# Custom" in result['content']
