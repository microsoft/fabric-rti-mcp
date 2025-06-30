#!/usr/bin/env python3
"""
Test script for the Fabric RTI MCP Extension System.

This script demonstrates how to use the extension system and provides
a simple CLI for testing extension functionality, including extension test discovery.
"""

import sys
import json
import os
import subprocess
from typing import Dict, Any, List, Optional
from pathlib import Path

from fabric_rti_mcp.extensions import ExtensionRegistry


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
            os.path.dirname(__file__), 
            "fabric_rti_mcp", 
            "extensions"
        )
    
    def discover_extension_tests(self) -> Dict[str, List[str]]:
        """
        Discover all extension test files.
        
        Returns:
            Dict mapping extension names to their test file paths
        """
        extension_tests = {}
        
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
        extension_tests = self.discover_extension_tests()
        results = {}
        
        # Create mapping between extension names and directory names
        name_mapping = {
            "financial-analytics": "financial",
            "log-analytics": "loganalytics"
        }
        
        if extension_name:
            # Map extension name to directory name
            dir_name = name_mapping.get(extension_name, extension_name)
            
            if dir_name not in extension_tests:
                return {"error": f"No tests found for extension '{extension_name}' (looking for directory '{dir_name}')"}
            
            test_files = extension_tests[dir_name]
            results[extension_name] = self._run_pytest_on_files(test_files)
        else:
            # Run all extension tests, map back to extension names
            reverse_mapping = {v: k for k, v in name_mapping.items()}
            for dir_name, test_files in extension_tests.items():
                ext_name = reverse_mapping.get(dir_name, dir_name)
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
        
        # Create mapping between extension names and directory names
        name_mapping = {
            "financial-analytics": "financial",
            "log-analytics": "loganalytics"
        }
        
        for ext_name in extensions:
            # Map extension name to directory name
            dir_name = name_mapping.get(ext_name, ext_name)
            
            if dir_name in extension_tests:
                validation["extensions_with_tests"].append(ext_name)
                validation["test_coverage"][ext_name] = {
                    "has_tests": True,
                    "test_files": extension_tests[dir_name],
                    "test_count": len(extension_tests[dir_name])
                }
            else:
                validation["extensions_without_tests"].append(ext_name)
                validation["test_coverage"][ext_name] = {
                    "has_tests": False,
                    "test_files": [],
                    "test_count": 0
                }
        
        return validation


def list_extensions():
    """List all available extensions."""
    print("🔍 Discovering extensions...")
    registry = ExtensionRegistry()
    registry.discover_extensions()
    
    extensions = registry.list_extensions()
    
    if not extensions:
        print("❌ No extensions found.")
        return
    
    print(f"✅ Found {len(extensions)} extension(s):")
    
    info = registry.get_extension_info()
    for name in extensions:
        ext_info = info[name]
        print(f"  📦 {name} v{ext_info['version']}")
        print(f"     {ext_info['description']}")
        if ext_info['dependencies']:
            print(f"     Dependencies: {', '.join(ext_info['dependencies'])}")
        print()


def test_extension_loading():
    """Test extension loading and registration."""
    print("🧪 Testing extension loading...")
    
    try:
        registry = ExtensionRegistry()
        registry.discover_extensions()
        
        extensions = registry.list_extensions()
        print(f"✅ Successfully loaded {len(extensions)} extensions")
        
        for ext_name in extensions:
            extension = registry.get_extension(ext_name)
            print(f"  ✓ {ext_name}: {extension.__class__.__name__}")
            
    except Exception as e:
        print(f"❌ Error loading extensions: {e}")
        sys.exit(1)


def show_extension_config(extension_name: str):
    """Show configuration for a specific extension."""
    print(f"🔧 Configuration for extension: {extension_name}")
    
    from fabric_rti_mcp.extensions.config import ExtensionConfig
    config = ExtensionConfig()
    
    ext_config = config.get_extension_config(extension_name)
    
    if ext_config:
        print(json.dumps(ext_config, indent=2))
    else:
        print(f"❌ No configuration found for extension: {extension_name}")


def test_financial_templates():
    """Test financial analytics KQL templates."""
    print("💰 Testing Financial Analytics templates...")
    
    try:
        from fabric_rti_mcp.extensions.financial.templates import FinancialKQLTemplates
        
        templates = FinancialKQLTemplates()
        
        # Test moving average query
        query = templates.get_moving_average_query(
            "StockPrices", "close_price", "timestamp", 20
        )
        print("✅ Moving average query generated successfully")
        print(f"   Length: {len(query)} characters")
        
        # Test trend analysis query
        query = templates.get_trend_analysis_query(
            "StockPrices", "close_price", "timestamp", "symbol", 30
        )
        print("✅ Trend analysis query generated successfully")
        print(f"   Length: {len(query)} characters")
        
    except ImportError:
        print("❌ Financial Analytics extension not available")
    except Exception as e:
        print(f"❌ Error testing financial templates: {e}")


def test_loganalytics_templates():
    """Test log analytics KQL templates."""
    print("📊 Testing Log Analytics templates...")
    
    try:
        from fabric_rti_mcp.extensions.loganalytics.templates import LogAnalyticsKQLTemplates
        
        templates = LogAnalyticsKQLTemplates()
        
        # Test failed logins query
        query = templates.get_failed_logins_query(
            "SecurityLogs", "username", "source_ip", "timestamp", "status", 24
        )
        print("✅ Failed logins query generated successfully")
        print(f"   Length: {len(query)} characters")
        
        # Test suspicious IPs query
        query = templates.get_suspicious_ips_query(
            "SecurityLogs", "source_ip", "timestamp", "activity", 100, 12
        )
        print("✅ Suspicious IPs query generated successfully")
        print(f"   Length: {len(query)} characters")
        
    except ImportError:
        print("❌ Log Analytics extension not available")
    except Exception as e:
        print(f"❌ Error testing log analytics templates: {e}")


def discover_extension_tests():
    """Discover all extension test files."""
    print("🔍 Discovering extension test files...")
    
    discovery = ExtensionTestDiscovery()
    extension_tests = discovery.discover_extension_tests()
    
    if not extension_tests:
        print("❌ No extension test files found.")
        return
    
    print(f"✅ Found test files for {len(extension_tests)} extension(s):")
    
    for ext_name, test_files in extension_tests.items():
        print(f"  📋 {ext_name}:")
        for test_file in test_files:
            print(f"     • {os.path.basename(test_file)}")
        print()


def run_extension_tests(extension_name=None):
    """Run tests for extensions."""        
    print(f"🧪 Running tests for {'all extensions' if not extension_name else extension_name}...")
    
    discovery = ExtensionTestDiscovery()
    results = discovery.run_extension_tests(extension_name)
    
    if "error" in results:
        print(f"❌ Error: {results['error']}")
        return
    
    for ext_name, result in results.items():
        status_icon = "✅" if result["status"] == "passed" else "❌"
        print(f"{status_icon} {ext_name}: {result['status']}")
        
        if result["status"] != "passed":
            print(f"     Return code: {result.get('returncode', 'N/A')}")
            if result.get('stderr'):
                print(f"     Error output:")
                for line in result['stderr'].split('\n')[:5]:  # Show first 5 lines
                    if line.strip():
                        print(f"       {line}")
        print()


def validate_test_coverage():
    """Validate that all extensions have proper test coverage."""        
    print("🔍 Validating extension test coverage...")
    
    discovery = ExtensionTestDiscovery()
    validation = discovery.validate_extension_tests()
    
    print(f"✅ Extensions with tests ({len(validation['extensions_with_tests'])}):")
    for ext_name in validation['extensions_with_tests']:
        coverage = validation['test_coverage'][ext_name]
        print(f"  📋 {ext_name}: {coverage['test_count']} test file(s)")
    
    if validation['extensions_without_tests']:
        print(f"\n⚠️  Extensions without tests ({len(validation['extensions_without_tests'])}):")
        for ext_name in validation['extensions_without_tests']:
            print(f"  📋 {ext_name}")
    
    print(f"\n📊 Overall test coverage: {len(validation['extensions_with_tests'])}/{len(validation['test_coverage'])} extensions")


def main():
    """Main CLI function."""
    if len(sys.argv) < 2:
        print("Usage: python test_extensions.py <command> [args]")
        print("\nCommands:")
        print("  list                    - List all available extensions")
        print("  test                    - Test extension loading")
        print("  config <ext_name>       - Show extension configuration")
        print("  test-financial          - Test financial analytics templates")
        print("  test-logs              - Test log analytics templates")
        print("  discover-tests          - Discover all extension test files")
        print("  run-tests [ext_name]   - Run tests for extensions")
        print("  validate-coverage       - Validate test coverage for extensions")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "list":
        list_extensions()
    elif command == "test":
        test_extension_loading()
    elif command == "config":
        if len(sys.argv) < 3:
            print("Usage: python test_extensions.py config <extension_name>")
            sys.exit(1)
        show_extension_config(sys.argv[2])
    elif command == "test-financial":
        test_financial_templates()
    elif command == "test-logs":
        test_loganalytics_templates()
    elif command == "discover-tests":
        discover_extension_tests()
    elif command == "run-tests":
        ext_name = sys.argv[2] if len(sys.argv) > 2 else None
        run_extension_tests(ext_name)
    elif command == "validate-coverage":
        validate_test_coverage()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
