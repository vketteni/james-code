# File Operations - Concepts

File operations form the foundation of the James Code system, enabling autonomous navigation and manipulation of the local file system with robust security constraints.

## What File Operations Do

The James Code system provides three complementary tools for file operations:

- **ReadTool**: Safe file system reading and exploration
- **WriteTool**: File creation and basic modification  
- **UpdateTool**: Surgical editing and sophisticated file modifications

## Mental Model

Think of file operations as a **read → analyze → modify** workflow:

1. **Discovery Phase**: Use ReadTool to explore and understand the file system
2. **Analysis Phase**: Read file contents to understand structure and context
3. **Modification Phase**: Use WriteTool for new files, UpdateTool for precise edits

### The File Operations Hierarchy

```
File System Navigation
├── ReadTool (Safe exploration)
│   ├── Directory listing
│   ├── File reading
│   └── Metadata access
├── WriteTool (Basic modification)
│   ├── File creation
│   ├── Content writing
│   └── Directory management
└── UpdateTool (Surgical editing)
    ├── Line-based updates
    ├── Pattern replacement
    └── Patch application
```

## When to Use Each Tool

### Use ReadTool When:
- **Exploring unknown codebases** - Understanding project structure
- **Gathering context** - Reading configuration files, documentation
- **Verifying state** - Checking if files exist, getting metadata
- **Content analysis** - Reading files before making modifications

### Use WriteTool When:
- **Creating new files** - Scripts, configuration, documentation
- **Simple content updates** - Overwriting entire files
- **Directory structure** - Creating folder hierarchies
- **Initial file creation** - When starting from scratch

### Use UpdateTool When:
- **Code modifications** - Changing specific functions or classes
- **Configuration updates** - Modifying specific settings
- **Bug fixes** - Targeted line-by-line corrections
- **Refactoring** - Systematic pattern-based changes

## Key Patterns

### Pattern 1: Explore → Read → Modify
```python
# 1. Explore the structure
read_tool.execute(context, action="list_directory", path="src")

# 2. Read specific files
read_tool.execute(context, action="read_file", path="src/main.py")

# 3. Make targeted updates
update_tool.execute(context, action="replace_pattern", 
                   path="src/main.py", pattern="old_function", replacement="new_function")
```

### Pattern 2: Search → Update → Verify
```python
# 1. Find files to modify
find_tool.execute(context, action="find_files", pattern="*.py")

# 2. Update each file
update_tool.execute(context, action="update_lines", 
                   path="file.py", start_line=10, end_line=15, new_content="new code")

# 3. Verify changes
read_tool.execute(context, action="read_file", path="file.py")
```

### Pattern 3: Backup → Modify → Restore (if needed)
```python
# UpdateTool automatically creates backups in metadata
result = update_tool.execute(context, action="update_lines", ...)

# Backup is available in result.metadata["backup_content"] for rollback
if not result.success:
    # Can restore from backup if needed
    write_tool.execute(context, action="write_file", 
                      path="file.py", content=result.metadata["backup_content"])
```

## Integration Points

### With Search Tools
File operations work seamlessly with FindTool:
- **Find** → **Read** → **Update** workflow
- Search for patterns, read matching files, make surgical edits

### With Task Management
File operations integrate with TodoTool and TaskTool:
- Break complex file modifications into subtasks
- Track progress of multi-file refactoring operations

### With Execution Tools
File operations enable execution workflows:
- Create scripts with WriteTool
- Execute with ExecuteTool
- Update based on results with UpdateTool

## Security Model

All file operations operate within a **security sandbox**:

### Path Validation
- All operations confined to working directory
- Path traversal attacks prevented
- Symbolic link protections

### Resource Limits
- File size limits (10MB default)
- Operation timeouts
- Memory usage constraints

### Audit Trail
- All file modifications logged
- Security violations tracked
- Backup creation for rollback

## Best Practices

### 1. Always Verify Before Modifying
```python
# Check if file exists before updating
exists_result = read_tool.execute(context, action="file_exists", path="target.py")
if exists_result.data:
    # Safe to proceed with update
    update_tool.execute(...)
```

### 2. Use Surgical Updates When Possible
```python
# Prefer UpdateTool over WriteTool for existing files
# This preserves file history and enables rollback
update_tool.execute(context, action="replace_pattern", ...)
# vs
write_tool.execute(context, action="write_file", ...)  # Overwrites entire file
```

### 3. Leverage Backup Capabilities
```python
# UpdateTool provides automatic backups
result = update_tool.execute(...)
backup_content = result.metadata.get("backup_content")
# Store backup reference for later rollback if needed
```

### 4. Batch Related Operations
```python
# Group related file operations together
# This improves performance and maintains consistency
for file_path in python_files:
    update_tool.execute(context, action="replace_pattern", 
                       path=file_path, pattern="old_import", replacement="new_import")
```

## Common Use Cases

### Code Refactoring
1. **Find** all files containing old patterns
2. **Read** each file to understand context
3. **Update** with surgical precision
4. **Verify** changes are correct

### Configuration Management
1. **Read** existing configuration files
2. **Update** specific settings without affecting others
3. **Verify** configuration is valid

### Documentation Generation
1. **Find** source files with documentation
2. **Read** code structure and comments  
3. **Write** new documentation files
4. **Update** existing docs with changes

### Project Setup
1. **Create** directory structure with WriteTool
2. **Write** template files and configurations
3. **Update** templates with project-specific values

## Troubleshooting

### File Not Found Errors
- Always check file existence with ReadTool first
- Verify working directory context
- Check path syntax and separators

### Permission Denied
- Ensure files are within working directory
- Check file permissions and ownership
- Verify safety manager configuration

### Large File Handling
- Files over 10MB are rejected by default
- Use streaming operations for large files
- Consider breaking large files into smaller parts

### Encoding Issues
- Tools assume UTF-8 encoding
- Binary files are automatically detected and rejected
- Use appropriate encoding for non-UTF-8 files

---

*This conceptual documentation focuses on stable usage patterns and mental models that rarely change, complementing the auto-generated technical reference.*