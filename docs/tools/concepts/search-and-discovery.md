# Search and Discovery - Concepts

Search and discovery capabilities enable the James Code system to intelligently navigate and understand complex codebases, making it possible to work autonomously with unfamiliar projects.

## What Search and Discovery Does

The **FindTool** provides sophisticated search capabilities that go far beyond simple file listing:

- **Pattern-based file discovery** - Find files using glob patterns and wildcards
- **Content search** - Search within file contents using strings or regex
- **Function discovery** - Language-aware search for functions, classes, and structures
- **Metadata filtering** - Find files by size, date, or other attributes

## Mental Model

Think of search and discovery as **intelligence gathering** for autonomous operation:

1. **Reconnaissance**: Understand the project landscape
2. **Targeting**: Find specific files or patterns of interest  
3. **Analysis**: Extract relevant information from search results
4. **Action**: Use findings to guide subsequent operations

### The Search Hierarchy

```
Search and Discovery
├── Structural Search (What exists?)
│   ├── File patterns (*.py, *.js)
│   ├── Directory structures
│   └── Project organization
├── Content Search (What's inside?)
│   ├── String patterns
│   ├── Regular expressions
│   └── Code constructs
└── Semantic Search (What does it do?)
    ├── Function definitions
    ├── Class structures
    └── Language-specific patterns
```

## When to Use Search

### Use FindTool When:
- **Exploring unknown codebases** - Getting oriented in new projects
- **Code analysis tasks** - Understanding how code is organized
- **Refactoring operations** - Finding all instances of patterns to change
- **Dependency mapping** - Understanding how components relate
- **Bug hunting** - Locating error patterns or problematic code
- **Documentation tasks** - Finding code to document or explain

### Don't Use FindTool When:
- **You know exact file paths** - Use ReadTool directly
- **Creating new files** - Use WriteTool or UpdateTool
- **Simple directory listing** - ReadTool's list_directory is sufficient

## Key Search Patterns

### Pattern 1: Progressive Discovery
```python
# Start broad, then narrow down
# 1. Get overall structure
find_tool.execute(context, action="find_files", pattern="*", max_depth=2)

# 2. Focus on specific file types
find_tool.execute(context, action="find_files", pattern="*.py")

# 3. Search for specific patterns
find_tool.execute(context, action="search_content", query="class.*API")
```

### Pattern 2: Language-Aware Analysis
```python
# Find all functions in a codebase
find_tool.execute(context, action="find_function", 
                 function_name="process_data", language="python")

# Search for specific patterns by language
find_tool.execute(context, action="search_content", 
                 query="def.*test_", file_types=["*.py"])
```

### Pattern 3: Multi-Criteria Search
```python
# Combine multiple search criteria
# 1. Find large Python files
find_tool.execute(context, action="find_by_size", 
                 min_size=10000, directory="src")

# 2. Search content in those files
find_tool.execute(context, action="search_content", 
                 query="performance", file_types=["*.py"])
```

### Pattern 4: Search → Analyze → Act
```python
# 1. Find relevant files
files_result = find_tool.execute(context, action="find_files", pattern="*config*")

# 2. Analyze content
for file_info in files_result.data:
    content_result = read_tool.execute(context, action="read_file", 
                                     path=file_info["path"])
    # Analyze content...

# 3. Take action based on findings
update_tool.execute(context, action="replace_pattern", ...)
```

## Search Strategies

### Exploratory Search (Unknown Codebases)
**Goal**: Understand project structure and organization

```python
# 1. Map the landscape
find_tool.execute(context, action="find_files", pattern="*", max_depth=3)

# 2. Identify key file types
find_tool.execute(context, action="find_files", pattern="*.{py,js,ts,java}")

# 3. Find configuration and documentation
find_tool.execute(context, action="find_files", pattern="*{config,readme,doc}*")

# 4. Look for main entry points
find_tool.execute(context, action="search_content", query="if __name__ == \"__main__\"")
```

### Targeted Search (Specific Goals)
**Goal**: Find specific functions, patterns, or structures

```python
# Find specific function implementations
find_tool.execute(context, action="find_function", 
                 function_name="authenticate", language="python")

# Find error handling patterns
find_tool.execute(context, action="search_content", 
                 query="try:|except:|catch", use_regex=True)

# Find configuration values
find_tool.execute(context, action="search_content", 
                 query="API_KEY|DATABASE_URL", use_regex=True)
```

### Impact Analysis (Change Assessment)
**Goal**: Understand the impact of potential changes

```python
# Find all usages of a function before modifying it
find_tool.execute(context, action="search_content", 
                 query="old_function_name", file_types=["*.py"])

# Find all imports of a module
find_tool.execute(context, action="search_content", 
                 query="from.*old_module import|import.*old_module", use_regex=True)
```

## Integration Patterns

### With File Operations
Search provides intelligence for file operations:

```python
# Search → Read → Update workflow
# 1. Find files to modify
files = find_tool.execute(context, action="find_files", pattern="*.py")

# 2. Read and analyze each file
for file_info in files.data:
    content = read_tool.execute(context, action="read_file", path=file_info["path"])
    if "old_pattern" in content.data:
        # 3. Update files that match criteria
        update_tool.execute(context, action="replace_pattern", 
                           path=file_info["path"], pattern="old_pattern", 
                           replacement="new_pattern")
```

### With Task Management
Search supports task planning and decomposition:

```python
# Use search results to create todos
search_result = find_tool.execute(context, action="search_content", 
                                query="TODO|FIXME", use_regex=True)

for match in search_result.data:
    todo_tool.execute(context, action="create_todo",
                     title=f"Address TODO in {match['file']}",
                     description=match['content'])
```

### With Code Analysis
Search enables sophisticated code analysis:

```python
# Analyze code complexity
functions = find_tool.execute(context, action="find_function", 
                            function_name=".*", language="python")

# Analyze each function
for func in functions.data:
    # Read function content and analyze complexity
    # Generate analysis reports
```

## Performance Considerations

### Search Scope Management
- **Use max_depth** to limit recursive searches
- **Filter by file types** to reduce search space
- **Use specific directories** rather than searching from root

### Result Limiting
- **Set max_results** to prevent overwhelming output
- **Use progressive refinement** rather than broad searches
- **Cache common search results** when appropriate

### Resource Usage
- **Large codebases** may require multiple targeted searches
- **Content search** is more expensive than file pattern matching
- **Regex searches** are more expensive than string searches

## Advanced Search Techniques

### Fuzzy Matching
```python
# Find files with similar names
find_tool.execute(context, action="find_files", pattern="*test*")
find_tool.execute(context, action="find_files", pattern="*spec*")
```

### Multi-Language Projects
```python
# Search across different languages
languages = ["python", "javascript", "java"]
for lang in languages:
    find_tool.execute(context, action="find_function", 
                     function_name="main", language=lang)
```

### Historical Analysis
```python
# Find recently modified files
find_tool.execute(context, action="find_by_date", 
                 min_date=last_week_timestamp)
```

## Best Practices

### 1. Start Broad, Then Narrow
Begin with general searches, then refine based on results.

### 2. Use Appropriate Search Types
- **File patterns** for structure discovery
- **Content search** for specific code or text
- **Function search** for code analysis

### 3. Combine Search with Analysis
Don't just find files—analyze what you find to guide next steps.

### 4. Respect Resource Limits
Use filters and limits to keep searches manageable.

### 5. Cache Important Results
Store search results that will be used multiple times.

## Common Use Cases

### Codebase Onboarding
1. **Map project structure** with file pattern searches
2. **Find entry points** with function searches
3. **Understand dependencies** with import searches
4. **Locate tests** with pattern matching

### Refactoring Tasks
1. **Find all usages** of code to be changed
2. **Identify dependencies** and relationships
3. **Plan modification strategy** based on findings
4. **Execute changes** systematically

### Security Audits
1. **Find potential vulnerabilities** with pattern searches
2. **Locate authentication code** with function searches
3. **Check for hardcoded secrets** with content searches
4. **Analyze access patterns** across codebase

### Documentation Generation
1. **Find undocumented functions** with function searches
2. **Locate existing documentation** with file searches
3. **Identify public APIs** with pattern analysis
4. **Generate documentation** based on findings

---

*Search and discovery provide the intelligence that makes autonomous operation possible, enabling the agent to understand and navigate complex codebases effectively.*