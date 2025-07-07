#!/usr/bin/env python3
"""Documentation generator for Agent LLM tools.

This script automatically generates reference documentation from tool schemas,
ensuring the documentation stays in sync with the actual tool implementations.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from james_code.tools import (
    ReadTool, WriteTool, ExecuteTool, FindTool, 
    UpdateTool, TodoTool, TaskTool
)


class DocumentationGenerator:
    """Generates documentation from tool schemas."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.tools = {
            'read': ReadTool(),
            'write': WriteTool(), 
            'execute': ExecuteTool(),
            'find': FindTool(),
            'update': UpdateTool(),
            'todo': TodoTool(),
            'task': TaskTool()
        }
    
    def generate_all(self):
        """Generate documentation for all tools."""
        print("🔧 Generating tool documentation...")
        
        # Create directories
        (self.output_dir / "reference").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "schemas").mkdir(parents=True, exist_ok=True)
        
        # Generate reference docs for each tool
        for tool_name, tool in self.tools.items():
            print(f"  📝 Generating {tool_name} documentation...")
            self._generate_tool_reference(tool_name, tool)
            self._generate_tool_schema(tool_name, tool)
        
        # Generate overview
        self._generate_tools_overview()
        
        print("✅ Documentation generation complete!")
    
    def _generate_tool_reference(self, tool_name: str, tool):
        """Generate reference documentation for a tool."""
        schema = tool.get_schema()
        
        # Extract information from schema
        parameters = schema.get('parameters', {})
        properties = parameters.get('properties', {})
        required = parameters.get('required', [])
        
        # Generate markdown
        md_content = self._build_reference_markdown(tool_name, tool, schema, properties, required)
        
        # Write to file
        output_file = self.output_dir / "reference" / f"{tool_name}-tool.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
    
    def _generate_tool_schema(self, tool_name: str, tool):
        """Generate JSON schema file for a tool."""
        schema = tool.get_schema()
        
        # Pretty-print JSON schema
        schema_file = self.output_dir / "schemas" / f"{tool_name}-schema.json"
        with open(schema_file, 'w', encoding='utf-8') as f:
            json.dump(schema, f, indent=2, ensure_ascii=False)
    
    def _build_reference_markdown(self, tool_name: str, tool, schema: Dict, properties: Dict, required: List) -> str:
        """Build markdown reference documentation."""
        
        md_lines = [
            f"# {tool_name.title()}Tool Reference",
            "",
            f"**Description:** {schema.get('description', tool.description)}",
            "",
            "## Quick Reference",
            "",
            f"```python",
            f"from james_code.tools import {tool_name.title()}Tool",
            f"",
            f"tool = {tool_name.title()}Tool()",
            f"result = tool.execute(context, **parameters)",
            f"```",
            "",
            "## Parameters",
            ""
        ]
        
        # Parameters table
        if properties:
            md_lines.extend([
                "| Parameter | Type | Required | Description |",
                "|-----------|------|----------|-------------|"
            ])
            
            for param_name, param_info in properties.items():
                is_required = "✅" if param_name in required else "❌"
                param_type = param_info.get('type', 'unknown')
                description = param_info.get('description', 'No description')
                
                # Handle enum types
                if 'enum' in param_info:
                    enum_values = ', '.join(f"`{v}`" for v in param_info['enum'])
                    param_type = f"enum: {enum_values}"
                
                md_lines.append(f"| `{param_name}` | {param_type} | {is_required} | {description} |")
            
            md_lines.append("")
        
        # Parameter details
        if properties:
            md_lines.extend([
                "## Parameter Details",
                ""
            ])
            
            for param_name, param_info in properties.items():
                md_lines.extend([
                    f"### `{param_name}`",
                    ""
                ])
                
                # Type and description
                param_type = param_info.get('type', 'unknown')
                description = param_info.get('description', 'No description')
                md_lines.append(f"**Type:** `{param_type}`")
                md_lines.append(f"**Required:** {'Yes' if param_name in required else 'No'}")
                md_lines.append(f"**Description:** {description}")
                
                # Enum values
                if 'enum' in param_info:
                    md_lines.append(f"**Allowed values:** {', '.join(f'`{v}`' for v in param_info['enum'])}")
                
                # Default value
                if 'default' in param_info:
                    md_lines.append(f"**Default:** `{param_info['default']}`")
                
                # Constraints
                if 'minimum' in param_info:
                    md_lines.append(f"**Minimum:** {param_info['minimum']}")
                if 'maximum' in param_info:
                    md_lines.append(f"**Maximum:** {param_info['maximum']}")
                
                md_lines.append("")
        
        # Usage examples
        md_lines.extend([
            "## Usage Examples",
            "",
            self._generate_usage_examples(tool_name, properties),
            "",
            "## Return Value",
            "",
            "Returns a `ToolResult` object with:",
            "",
            "```python",
            "@dataclass",
            "class ToolResult:",
            "    success: bool",
            "    data: Any",
            "    error: Optional[str] = None",
            "    metadata: Dict[str, Any] = field(default_factory=dict)",
            "```",
            "",
            "## Security Considerations",
            "",
            self._generate_security_notes(tool_name),
            "",
            "## See Also",
            "",
            self._generate_see_also(tool_name),
            "",
            "---",
            "*This documentation is auto-generated from tool schemas.*"
        ])
        
        return "\n".join(md_lines)
    
    def _generate_usage_examples(self, tool_name: str, properties: Dict) -> str:
        """Generate usage examples based on tool type."""
        
        examples = {
            'read': '''```python
# List directory contents
result = read_tool.execute(context, action="list_directory", path=".")

# Read a file
result = read_tool.execute(context, action="read_file", path="example.txt")

# Check if file exists
result = read_tool.execute(context, action="file_exists", path="config.json")
```''',
            
            'write': '''```python
# Create a new file
result = write_tool.execute(
    context, 
    action="write_file", 
    path="output.txt", 
    content="Hello, World!"
)

# Append to existing file
result = write_tool.execute(
    context,
    action="append_file",
    path="log.txt",
    content="New log entry\\n"
)
```''',
            
            'execute': '''```python
# Execute a simple command
result = execute_tool.execute(context, command="ls -la")

# Execute with timeout
result = execute_tool.execute(
    context,
    command="python script.py",
    timeout=60
)
```''',
            
            'find': '''```python
# Find files by pattern
result = find_tool.execute(
    context,
    action="find_files",
    pattern="*.py"
)

# Search content in files
result = find_tool.execute(
    context,
    action="search_content",
    query="def main",
    file_types=["*.py"]
)
```''',
            
            'update': '''```python
# Update specific lines
result = update_tool.execute(
    context,
    action="update_lines",
    path="script.py",
    start_line=10,
    end_line=12,
    new_content="# Updated code\\nprint('Hello')"
)

# Replace pattern
result = update_tool.execute(
    context,
    action="replace_pattern",
    path="config.py",
    pattern="old_value",
    replacement="new_value"
)
```''',
            
            'todo': '''```python
# Create a todo
result = todo_tool.execute(
    context,
    action="create_todo",
    title="Implement feature X",
    priority="high"
)

# List todos
result = todo_tool.execute(context, action="list_todos")
```''',
            
            'task': '''```python
# Decompose a task
result = task_tool.execute(
    context,
    action="decompose_task",
    description="Build a REST API",
    task_type="development"
)

# Get next steps
result = task_tool.execute(
    context,
    action="get_next_steps",
    plan_id="plan-123"
)
```'''
        }
        
        return examples.get(tool_name, "```python\n# Usage examples to be added\n```")
    
    def _generate_security_notes(self, tool_name: str) -> str:
        """Generate security considerations for each tool."""
        
        security_notes = {
            'read': "- All file paths are validated to be within the working directory\n- File size limits apply (10MB default)\n- Binary files are detected and rejected",
            'write': "- Path validation prevents writing outside working directory\n- File size limits enforced\n- Directory creation is restricted to allowed paths",
            'execute': "- Command filtering with configurable allow/block lists\n- Timeout limits prevent infinite execution\n- Process isolation and cleanup\n- Output size limits",
            'find': "- Search operations confined to working directory\n- Resource limits on search depth and results\n- File size limits for content search",
            'update': "- All security constraints from read/write tools apply\n- Backup content stored for rollback\n- Pattern validation for safety",
            'todo': "- Data stored in working directory only\n- Input validation on all parameters",
            'task': "- Task plans stored locally\n- Parameter validation for all actions"
        }
        
        return security_notes.get(tool_name, "Standard security constraints apply.")
    
    def _generate_see_also(self, tool_name: str) -> str:
        """Generate cross-references to related tools."""
        
        related_tools = {
            'read': "- [WriteTool](write-tool.md) - File creation and modification\n- [FindTool](find-tool.md) - Advanced search capabilities",
            'write': "- [ReadTool](read-tool.md) - File reading operations\n- [UpdateTool](update-tool.md) - Surgical file editing",
            'execute': "- [TaskTool](task-tool.md) - Task execution planning\n- [Safety Manager](../concepts/security-model.md) - Security framework",
            'find': "- [ReadTool](read-tool.md) - File content access\n- [UpdateTool](update-tool.md) - Modify found files",
            'update': "- [ReadTool](read-tool.md) - Read files before updating\n- [FindTool](find-tool.md) - Find files to update",
            'todo': "- [TaskTool](task-tool.md) - Complex task decomposition\n- [Task Management Guide](../concepts/task-management.md)",
            'task': "- [TodoTool](todo-tool.md) - Simple task tracking\n- [Task Management Guide](../concepts/task-management.md)"
        }
        
        return related_tools.get(tool_name, "- [Tool Overview](../README.md)")
    
    def _generate_tools_overview(self):
        """Generate the main tools overview page."""
        
        md_content = [
            "# Agent LLM Tools Reference",
            "",
            "This directory contains auto-generated reference documentation for all Agent LLM tools.",
            "",
            "## Available Tools",
            "",
            "| Tool | Purpose | Key Actions |",
            "|------|---------|-------------|"
        ]
        
        tool_summaries = {
            'read': ("File system reading", "read_file, list_directory, file_exists"),
            'write': ("File creation and modification", "write_file, append_file, create_directory"),
            'execute': ("Safe command execution", "execute commands with filtering and timeouts"),
            'find': ("Advanced search capabilities", "find_files, search_content, find_function"),
            'update': ("Surgical file editing", "update_lines, replace_pattern, apply_patch"),
            'todo': ("Task management", "create_todo, list_todos, update_todo"),
            'task': ("Task decomposition", "decompose_task, create_plan, execute_plan")
        }
        
        for tool_name in self.tools.keys():
            purpose, actions = tool_summaries[tool_name]
            md_content.append(f"| [{tool_name.title()}Tool](reference/{tool_name}-tool.md) | {purpose} | {actions} |")
        
        md_content.extend([
            "",
            "## Documentation Structure",
            "",
            "- **Reference**: Detailed parameter documentation (auto-generated)",
            "- **Concepts**: Stable conceptual guides for understanding tools",
            "- **Examples**: Working code examples and demonstrations",
            "",
            "## Quick Navigation",
            "",
            "### By Category",
            "- **File Operations**: [ReadTool](reference/read-tool.md), [WriteTool](reference/write-tool.md), [UpdateTool](reference/update-tool.md)",
            "- **Search & Discovery**: [FindTool](reference/find-tool.md)",
            "- **Execution**: [ExecuteTool](reference/execute-tool.md)", 
            "- **Task Management**: [TodoTool](reference/todo-tool.md), [TaskTool](reference/task-tool.md)",
            "",
            "### By Use Case",
            "- **Code Analysis**: Use FindTool → ReadTool → UpdateTool",
            "- **File Processing**: Use FindTool → ReadTool → WriteTool",
            "- **Development Tasks**: Use TaskTool → multiple tools → TodoTool",
            "",
            "## JSON Schemas",
            "",
            "Machine-readable tool schemas are available in the [schemas/](schemas/) directory.",
            "",
            "---",
            "*This documentation is auto-generated from tool implementations.*"
        ])
        
        output_file = self.output_dir / "README.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(md_content))


def main():
    """Generate all tool documentation."""
    
    # Set up paths
    project_root = Path(__file__).parent.parent
    docs_dir = project_root / "docs" / "tools"
    
    # Create generator and run
    generator = DocumentationGenerator(docs_dir)
    generator.generate_all()
    
    print(f"📁 Documentation generated in: {docs_dir}")
    print("🔍 Review the generated files:")
    print(f"  - Overview: {docs_dir / 'README.md'}")
    print(f"  - References: {docs_dir / 'reference'}/")
    print(f"  - Schemas: {docs_dir / 'schemas'}/")


if __name__ == "__main__":
    main()