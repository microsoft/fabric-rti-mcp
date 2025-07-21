#!/usr/bin/env python3
"""
MCP Server Merger Script

This script helps merge another MCP server codebase into the current one.
Usage: python merge_mcp_server.py --source-path "C:/path/to/other/mcp/server" --module-name "new_module"
"""

import argparse
import os
import shutil
import sys
from pathlib import Path
from typing import List, Dict, Any
import ast
import re


class MCPServerMerger:
    def __init__(self, source_path: str, target_path: str, module_name: str):
        self.source_path = Path(source_path)
        self.target_path = Path(target_path)
        self.module_name = module_name
        self.target_module_path = self.target_path / "fabric_rti_mcp" / module_name
        
    def analyze_source_structure(self) -> Dict[str, Any]:
        """Analyze the source codebase structure and dependencies."""
        analysis = {
            "python_files": [],
            "dependencies": [],
            "mcp_tools": [],
            "main_files": [],
            "config_files": []
        }
        
        if not self.source_path.exists():
            print(f"Error: Source path {self.source_path} does not exist")
            return analysis
            
        # Find Python files
        for py_file in self.source_path.rglob("*.py"):
            analysis["python_files"].append(str(py_file.relative_to(self.source_path)))
            
        # Find config files
        for config_file in ["pyproject.toml", "requirements.txt", "setup.py", "setup.cfg"]:
            config_path = self.source_path / config_file
            if config_path.exists():
                analysis["config_files"].append(config_file)
                
        # Look for main entry points
        for py_file in self.source_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'if __name__ == "__main__"' in content or 'FastMCP' in content:
                        analysis["main_files"].append(str(py_file.relative_to(self.source_path)))
            except Exception as e:
                print(f"Warning: Could not read {py_file}: {e}")
                
        return analysis
    
    def extract_dependencies(self) -> List[str]:
        """Extract dependencies from source codebase."""
        dependencies = []
        
        # Check pyproject.toml
        pyproject_path = self.source_path / "pyproject.toml"
        if pyproject_path.exists():
            try:
                with open(pyproject_path, 'r') as f:
                    content = f.read()
                    # Simple regex to find dependencies
                    deps_match = re.search(r'dependencies\s*=\s*\[(.*?)\]', content, re.DOTALL)
                    if deps_match:
                        deps_content = deps_match.group(1)
                        deps = re.findall(r'"([^"]+)"', deps_content)
                        dependencies.extend(deps)
            except Exception as e:
                print(f"Warning: Could not parse pyproject.toml: {e}")
                
        # Check requirements.txt
        requirements_path = self.source_path / "requirements.txt"
        if requirements_path.exists():
            try:
                with open(requirements_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            dependencies.append(line)
            except Exception as e:
                print(f"Warning: Could not parse requirements.txt: {e}")
                
        return dependencies
    
    def create_module_structure(self):
        """Create the new module directory structure."""
        self.target_module_path.mkdir(parents=True, exist_ok=True)
        
        # Create __init__.py
        init_file = self.target_module_path / "__init__.py"
        init_file.write_text('"""New module integrated from external MCP server."""\n')
        
        print(f"Created module structure at: {self.target_module_path}")
    
    def copy_and_adapt_files(self, analysis: Dict[str, Any]):
        """Copy and adapt files from source to target module."""
        for py_file in analysis["python_files"]:
            source_file = self.source_path / py_file
            
            # Skip __pycache__ and other unwanted files
            if "__pycache__" in str(source_file) or source_file.name.startswith('.'):
                continue
                
            # Determine target filename and adapt imports
            target_filename = self._adapt_filename(py_file)
            target_file = self.target_module_path / target_filename
            
            try:
                with open(source_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Adapt the content
                adapted_content = self._adapt_file_content(content, py_file)
                
                # Write to target
                target_file.parent.mkdir(parents=True, exist_ok=True)
                with open(target_file, 'w', encoding='utf-8') as f:
                    f.write(adapted_content)
                    
                print(f"Copied and adapted: {py_file} -> {target_filename}")
                
            except Exception as e:
                print(f"Error processing {py_file}: {e}")
    
    def _adapt_filename(self, original_filename: str) -> str:
        """Adapt filename to follow current project conventions."""
        path = Path(original_filename)
        
        # If it's a main server file, rename it
        if path.name in ['server.py', 'main.py', '__main__.py']:
            return f"{self.module_name}_server.py"
        elif path.name == 'tools.py':
            return f"{self.module_name}_tools.py"
        elif 'service' in path.name.lower():
            return f"{self.module_name}_service.py"
        else:
            return path.name
    
    def _adapt_file_content(self, content: str, filename: str) -> str:
        """Adapt file content to work with the target codebase."""
        # Add header comment
        adapted_content = f'"""\nIntegrated from external MCP server: {filename}\nAdapted for fabric-rti-mcp\n"""\n\n'
        
        # TODO: Add more sophisticated import adaptation
        # For now, just add the original content
        adapted_content += content
        
        return adapted_content
    
    def generate_integration_guide(self, analysis: Dict[str, Any], dependencies: List[str]):
        """Generate a guide for completing the integration."""
        guide_path = self.target_path / f"{self.module_name}_integration_guide.md"
        
        guide_content = f"""# {self.module_name.title()} Integration Guide

## Files Copied
{chr(10).join(f"- {f}" for f in analysis["python_files"])}

## Dependencies to Add
Add these to pyproject.toml dependencies:
```toml
{chr(10).join(f'"{dep}",' for dep in dependencies)}
```

## Next Steps

### 1. Review and Adapt Code
- Check all copied files in `fabric_rti_mcp/{self.module_name}/`
- Update imports to use the new module structure
- Adapt connection handling to follow the KustoConnection pattern

### 2. Create Service Layer
- Rename main service file to `{self.module_name}_service.py`
- Follow the pattern from `kusto_service.py`:
  - Connection caching
  - Error handling
  - Result formatting

### 3. Create Tools Layer
- Create `{self.module_name}_tools.py`
- Register tools with appropriate annotations:
  - `readOnlyHint=True` for queries/read operations
  - `destructiveHint=True` for modify/delete operations

### 4. Update Main Server
- Add import: `from fabric_rti_mcp.{self.module_name} import {self.module_name}_tools`
- Update `register_tools()` function to include: `{self.module_name}_tools.register_tools(mcp)`

### 5. Test Integration
- Run existing tests to ensure no regression
- Create tests for new functionality
- Test MCP tool registration and execution

## Configuration Files Found
{chr(10).join(f"- {f}" for f in analysis["config_files"])}

## Main Files Identified
{chr(10).join(f"- {f}" for f in analysis["main_files"])}
"""
        
        with open(guide_path, 'w') as f:
            f.write(guide_content)
            
        print(f"Integration guide created: {guide_path}")
    
    def merge(self):
        """Execute the full merge process."""
        print(f"Starting merge of {self.source_path} into {self.target_path}")
        print(f"Module name: {self.module_name}")
        
        # Step 1: Analyze source
        print("\n1. Analyzing source structure...")
        analysis = self.analyze_source_structure()
        
        # Step 2: Extract dependencies
        print("2. Extracting dependencies...")
        dependencies = self.extract_dependencies()
        
        # Step 3: Create module structure
        print("3. Creating module structure...")
        self.create_module_structure()
        
        # Step 4: Copy and adapt files
        print("4. Copying and adapting files...")
        self.copy_and_adapt_files(analysis)
        
        # Step 5: Generate integration guide
        print("5. Generating integration guide...")
        self.generate_integration_guide(analysis, dependencies)
        
        print(f"\n✅ Merge completed!")
        print(f"📁 New module created at: {self.target_module_path}")
        print(f"📖 See integration guide: {self.target_path / f'{self.module_name}_integration_guide.md'}")


def main():
    parser = argparse.ArgumentParser(description="Merge MCP server codebases")
    parser.add_argument("--source-path", required=True, help="Path to the source MCP server")
    parser.add_argument("--module-name", required=True, help="Name for the new module")
    parser.add_argument("--target-path", default=".", help="Path to target codebase (default: current directory)")
    
    args = parser.parse_args()
    
    merger = MCPServerMerger(
        source_path=args.source_path,
        target_path=args.target_path,
        module_name=args.module_name
    )
    
    merger.merge()


if __name__ == "__main__":
    main()
