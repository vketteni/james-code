# James Code Tools Reference

This directory contains auto-generated reference documentation for all James Code tools.

## Available Tools

| Tool | Purpose | Key Actions |
|------|---------|-------------|
| [ReadTool](reference/read-tool.md) | File system reading | read_file, list_directory, file_exists |
| [WriteTool](reference/write-tool.md) | File creation and modification | write_file, append_file, create_directory |
| [ExecuteTool](reference/execute-tool.md) | Safe command execution | execute commands with filtering and timeouts |
| [FindTool](reference/find-tool.md) | Advanced search capabilities | find_files, search_content, find_function |
| [UpdateTool](reference/update-tool.md) | Surgical file editing | update_lines, replace_pattern, apply_patch |
| [TodoTool](reference/todo-tool.md) | Task management | create_todo, list_todos, update_todo |
| [TaskTool](reference/task-tool.md) | Task decomposition | decompose_task, create_plan, execute_plan |

## Documentation Structure

- **Reference**: Detailed parameter documentation (auto-generated from tool schemas)
- **Concepts**: Stable conceptual guides for understanding tools and patterns
- **Examples**: Working code examples and demonstrations (living documentation)

## Quick Navigation

### By Category
- **File Operations**: [ReadTool](reference/read-tool.md), [WriteTool](reference/write-tool.md), [UpdateTool](reference/update-tool.md)
- **Search & Discovery**: [FindTool](reference/find-tool.md)
- **Execution**: [ExecuteTool](reference/execute-tool.md)
- **Task Management**: [TodoTool](reference/todo-tool.md), [TaskTool](reference/task-tool.md)

### By Use Case
- **Code Analysis**: Use FindTool → ReadTool → UpdateTool
- **File Processing**: Use FindTool → ReadTool → WriteTool
- **Development Tasks**: Use TaskTool → multiple tools → TodoTool

## Conceptual Guides

Deep-dive guides for understanding tool categories and patterns:

- **[File Operations](concepts/file-operations.md)** - READ, WRITE, UPDATE tools and patterns
- **[Search and Discovery](concepts/search-and-discovery.md)** - FIND tool and search strategies
- **[Task Management](concepts/task-management.md)** - TODO and TASK tools for planning
- **[Security Model](concepts/security-model.md)** - Security framework and best practices

## Examples and Workflows

Living documentation with executable examples:

- **[Examples Overview](examples/README.md)** - Structure and usage of examples
- **[File Operations Workflow](examples/workflows/file_operations_workflow.py)** - Complete workflow examples

## JSON Schemas

Machine-readable tool schemas are available in the [schemas/](schemas/) directory.

---
*This documentation is auto-generated from tool implementations.*