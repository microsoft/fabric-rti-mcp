"""
Tests for the extension system base components and extension test discovery.
"""

import pytest
import os
import importlib.util
import sys
from unittest.mock import Mock, MagicMock
from typing import Any, Dict, List, Optional
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from fabric_rti_mcp.extensions.base import ExtensionBase
from fabric_rti_mcp.extensions.registry import ExtensionRegistry
from fabric_rti_mcp.extensions.config import ExtensionConfig


class ExtensionTestDiscovery:
    """
    Discovers and runs tests for all extensions.
    """
    
    def __init__(self, extensions_root: Optional[str] = None):
        """
        Initialize the test discovery system.
        
        Args:
            extensions_root: Root directory containing extensions
        """
        self.extensions_root = extensions_root or os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "fabric_rti_mcp", 
            "extensions"
        )
    
    def discover_extension_tests(self) -> Dict[str, List[str]]:
        """
        Discover all extension test files.
        
        Returns:
            Dict mapping extension names to their test file paths
        """
        extension_tests: Dict[str, List[str]] = {}
        
        if not os.path.exists(self.extensions_root):
            return extension_tests
        
        for item in os.listdir(self.extensions_root):
            extension_path = os.path.join(self.extensions_root, item)
            
            if os.path.isdir(extension_path) and not item.startswith('__'):
                # Look for test files in the extension directory
                test_files = []
                for file in os.listdir(extension_path):
                    if file.startswith('test_') and file.endswith('.py'):
                        test_files.append(os.path.join(extension_path, file))
                
                if test_files:
                    extension_tests[item] = test_files
        
        return extension_tests
    
    def run_extension_tests(self, extension_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Run tests for a specific extension or all extensions.
        
        Args:
            extension_name: Name of extension to test, or None for all
            
        Returns:
            Dict containing test results
        """
        import subprocess
        
        extension_tests = self.discover_extension_tests()
        results = {}
        
        if extension_name:
            if extension_name not in extension_tests:
                return {"error": f"No tests found for extension '{extension_name}'"}
            
            test_files = extension_tests[extension_name]
            results[extension_name] = self._run_pytest_on_files(test_files)
        else:
            for ext_name, test_files in extension_tests.items():
                results[ext_name] = self._run_pytest_on_files(test_files)
        
        return results
    
    def _run_pytest_on_files(self, test_files: List[str]) -> Dict[str, Any]:
        """
        Run pytest on the given test files.
        
        Args:
            test_files: List of test file paths
            
        Returns:
            Dict containing test results
        """
        import subprocess
        
        try:
            # Run pytest on the test files
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "-v"] + test_files,
                capture_output=True,
                text=True,
                cwd=os.path.dirname(self.extensions_root)
            )
            
            return {
                "status": "passed" if result.returncode == 0 else "failed",
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "files": test_files
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "files": test_files
            }
    
    def validate_extension_tests(self) -> Dict[str, Any]:
        """
        Validate that all extensions have proper test coverage.
        
        Returns:
            Dict containing validation results
        """
        validation = {
            "extensions_with_tests": [],
            "extensions_without_tests": [],
            "test_coverage": {}
        }
        
        # Get all extensions
        registry = ExtensionRegistry()
        registry.discover_extensions()
        extensions = registry.list_extensions()
        
        # Get test files
        extension_tests = self.discover_extension_tests()
        
        for ext_name in extensions:
            if ext_name in extension_tests:
                validation["extensions_with_tests"].append(ext_name)
                validation["test_coverage"][ext_name] = {
                    "has_tests": True,
                    "test_files": extension_tests[ext_name],
                    "test_count": len(extension_tests[ext_name])
                }
            else:
                validation["extensions_without_tests"].append(ext_name)
                validation["test_coverage"][ext_name] = {
                    "has_tests": False,
                    "test_files": [],
                    "test_count": 0
                }
        
        return validation


# Test implementation of ExtensionBase for testing
class TestExtension(ExtensionBase):
    def __init__(self, name: str = "test-extension", version: str = "1.0.0"):
        self._name = name
        self._version = version
        self.tools_registered = False
        
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def version(self) -> str:
        return self._version
    
    @property
    def description(self) -> str:
        return "Test extension for unit testing"
    
    def register_tools(self, mcp: FastMCP) -> None:
        self.tools_registered = True
        
        @mcp.tool()
        def test_tool() -> str:
            """A test tool."""
            return "test result"
    
    def get_dependencies(self) -> List[str]:
        return ["test-dependency"]


class TestExtensionBase:
    """Test cases for ExtensionBase abstract class."""
    
    def test_extension_properties(self):
        """Test that extension properties are accessible."""
        extension = TestExtension()
        
        assert extension.name == "test-extension"
        assert extension.version == "1.0.0"
        assert extension.description == "Test extension for unit testing"
        assert extension.get_dependencies() == ["test-dependency"]
    
    def test_extension_default_methods(self):
        """Test default implementations of optional methods."""
        extension = TestExtension()
        
        # Test default implementations
        assert extension.get_configuration_schema() is None
        
        # These should not raise exceptions
        extension.initialize()
        extension.cleanup()
    
    def test_extension_initialization_with_config(self):
        """Test extension initialization with configuration."""
        extension = TestExtension()
        config = {"test_setting": "test_value"}
        
        # Should not raise exception
        extension.initialize(config)


class TestExtensionRegistry:
    """Test cases for ExtensionRegistry."""
    
    def test_registry_initialization(self):
        """Test registry initializes correctly."""
        registry = ExtensionRegistry()
        
        assert len(registry.list_extensions()) == 0
        assert isinstance(registry.get_extension_info(), dict)
    
    def test_register_extension(self):
        """Test registering an extension."""
        registry = ExtensionRegistry()
        extension = TestExtension()
        
        registry.register(extension)
        
        assert "test-extension" in registry.list_extensions()
        assert registry.get_extension("test-extension") is extension
    
    def test_register_duplicate_extension_raises_error(self):
        """Test that registering duplicate extension raises ValueError."""
        registry = ExtensionRegistry()
        extension1 = TestExtension()
        extension2 = TestExtension()  # Same name
        
        registry.register(extension1)
        
        with pytest.raises(ValueError, match="already registered"):
            registry.register(extension2)
    
    def test_register_tools_with_mcp(self):
        """Test registering extension tools with MCP server."""
        registry = ExtensionRegistry()
        extension = TestExtension()
        registry.register(extension)
        
        mock_mcp = Mock(spec=FastMCP)
        registry.register_all_tools(mock_mcp)
        
        assert extension.tools_registered is True
    
    def test_get_extension_info(self):
        """Test getting extension information."""
        registry = ExtensionRegistry()
        extension = TestExtension()
        registry.register(extension)
        
        info = registry.get_extension_info()
        
        assert "test-extension" in info
        assert info["test-extension"]["version"] == "1.0.0"
        assert info["test-extension"]["description"] == "Test extension for unit testing"
        assert info["test-extension"]["dependencies"] == ["test-dependency"]
    
    def test_cleanup_all_extensions(self):
        """Test cleanup of all registered extensions."""
        registry = ExtensionRegistry()
        extension = TestExtension()
        
        # Mock the cleanup method to verify it's called
        extension.cleanup = Mock()
        registry.register(extension)
        
        registry.cleanup_all()
        
        extension.cleanup.assert_called_once()


class TestExtensionConfig:
    """Test cases for ExtensionConfig."""
    
    def test_config_initialization(self, tmp_path):
        """Test config initialization with custom directory."""
        config_dir = str(tmp_path / "test_configs")
        config = ExtensionConfig(config_dir)
        
        assert config.config_dir == config_dir
        # Directory should be created
        assert (tmp_path / "test_configs").exists()
    
    def test_get_extension_config_none_when_not_found(self):
        """Test that None is returned when no config is found."""
        config = ExtensionConfig()
        
        result = config.get_extension_config("nonexistent-extension")
        
        assert result is None
    
    def test_save_and_load_config(self, tmp_path):
        """Test saving and loading extension configuration."""
        config_dir = str(tmp_path / "test_configs")
        config = ExtensionConfig(config_dir)
        
        test_config = {
            "setting1": "value1",
            "setting2": 42,
            "setting3": ["item1", "item2"]
        }
        
        # Save config
        config.save_extension_config("test-extension", test_config)
        
        # Load config
        loaded_config = config.get_extension_config("test-extension")
        
        assert loaded_config == test_config
    
    def test_list_configured_extensions(self, tmp_path):
        """Test listing configured extensions."""
        config_dir = str(tmp_path / "test_configs")
        config = ExtensionConfig(config_dir)
        
        # Save configs for multiple extensions
        config.save_extension_config("ext1", {"setting": "value1"})
        config.save_extension_config("ext2", {"setting": "value2"})
        
        configured = config.list_configured_extensions()
        
        assert "ext1" in configured
        assert "ext2" in configured
        assert len(configured) == 2
    
    @pytest.mark.parametrize("env_vars,expected", [
        ({"FABRIC_RTI_TEST_SETTING1": "value1"}, {"setting1": "value1"}),
        ({"FABRIC_RTI_TEST_SETTING2": '{"key": "value"}'}, {"setting2": {"key": "value"}}),
        ({"FABRIC_RTI_OTHER_SETTING": "value"}, {}),  # Wrong prefix
    ])
    def test_environment_variable_parsing(self, env_vars, expected, monkeypatch):
        """Test parsing configuration from environment variables."""
        config = ExtensionConfig()
        
        # Set environment variables
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)
        
        result = config.get_extension_config("test")
        
        if expected:
            assert result == expected
        else:
            assert result is None or result == {}


@pytest.fixture
def sample_cluster_uri() -> str:
    """Sample cluster URI for testing."""
    return "https://test.kusto.windows.net"


@pytest.fixture  
def mock_mcp() -> Mock:
    """Mock FastMCP server for testing."""
    return Mock(spec=FastMCP)
