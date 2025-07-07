# Agentic LLM System

A sophisticated agentic LLM system with comprehensive READ, WRITE, EXECUTE, FIND, UPDATE, TODO, and TASK tools for autonomous local environment navigation and task execution.

## 🚀 Features

### Core Capabilities
- **🔍 Advanced Search**: Pattern-based file discovery, content search, function finding
- **✏️ Surgical Editing**: Line-based updates, pattern replacement, patch application  
- **📋 Task Management**: TODO tracking, subtasks, progress monitoring
- **🧩 Task Decomposition**: Automatic breakdown of complex requests into executable steps
- **🛡️ Security Framework**: Multi-layered validation, audit logging, sandboxing
- **🔧 Tool Orchestration**: Seamless integration of all tools through unified interface

### Tool Suite
- **ReadTool**: File reading, directory listing, metadata access
- **WriteTool**: File creation, modification, deletion
- **ExecuteTool**: Safe command execution with timeout and filtering
- **FindTool**: Advanced file and content search capabilities  
- **UpdateTool**: Surgical file modifications and patch application
- **TodoTool**: Comprehensive task management with hierarchical organization
- **TaskTool**: Intelligent task decomposition and execution planning

## 🏗️ Architecture Decision Records

This project uses Architecture Decision Records (ADRs) to document important architectural decisions. All ADRs are stored in `docs/adr/`.

### Current ADRs

- [ADR-0001: Use Architecture Decision Records](docs/adr/0001-use-architecture-decision-records.md)
- [ADR-0002: Agent Architecture Design](docs/adr/0002-agent-architecture-design.md)
- [ADR-0003: Tool System Design](docs/adr/0003-tool-system-design.md)
- [ADR-0004: Safety and Sandboxing Approach](docs/adr/0004-safety-and-sandboxing-approach.md)
- [ADR-0005: MCP Protocol Compatibility](docs/adr/0005-mcp-protocol-compatibility.md)
- [ADR-0006: Additional Fundamental Tools](docs/adr/0006-additional-fundamental-tools.md)

## 📁 Project Structure

```
.
├── docs/
│   └── adr/                    # Architecture Decision Records
├── src/
│   └── james_code/
│       ├── core/               # Core agent and base classes
│       │   ├── base.py         # Abstract interfaces
│       │   └── agent.py        # Main agent orchestration
│       ├── tools/              # Tool implementations
│       │   ├── read_tool.py    # File system reading
│       │   ├── write_tool.py   # File system writing
│       │   ├── execute_tool.py # Command execution
│       │   ├── find_tool.py    # Search capabilities
│       │   ├── update_tool.py  # Surgical file editing
│       │   ├── todo_tool.py    # Task management
│       │   └── task_tool.py    # Task decomposition
│       ├── safety/             # Security framework
│       │   └── safety_manager.py
│       └── __init__.py
├── examples/                   # Usage examples
│   ├── basic_usage.py         # Simple examples
│   └── advanced_example.py    # Complex demonstrations
└── README.md
```

## 🚀 Quick Start

### Installation

```bash
# Install from PyPI (when available)
pip install james-code

# Or install from source
git clone https://github.com/your-org/james-code
cd james-code
poetry install
```

### Basic Usage

```python
from james_code import Agent, AgentConfig

# Configure the agent
config = AgentConfig(
    working_directory="./workspace",
    auto_planning=True,
    verbose_logging=True
)

# Initialize agent
agent = Agent(config)

# Process requests
response = agent.process_request("find all Python files and analyze their structure")
print(response)
```

### Command Line Interface

```bash
# Interactive mode
james-code --interactive --workspace ./my-project

# Single command
james-code --workspace ./my-project "analyze this codebase"

# With custom security settings
james-code --strict --allowed-commands python3,pytest "run tests"
```

### Advanced Usage with Custom Safety

```python
from james_code import Agent, AgentConfig, SafetyConfig

# Configure security
safety_config = SafetyConfig(
    base_directory="./secure_workspace",
    allowed_commands=["python3", "pytest", "git"],
    blocked_commands=["rm", "sudo"],
    enable_audit_logging=True,
    strict_mode=False
)

config = AgentConfig(
    working_directory="./workspace",
    safety_config=safety_config,
    auto_planning=True
)

agent = Agent(config)

# Complex development task
response = agent.process_request("""
Create a Python web API with:
1. FastAPI framework setup
2. Database models
3. REST endpoints
4. Unit tests
5. Documentation
""")
```

## 🔧 Direct Tool Usage

```python
# Access tools directly
find_tool = agent.tool_registry.get_tool("find")

# Search for functions
result = find_tool.execute(
    agent.execution_context,
    action="find_function",
    function_name="calculate",
    language="python"
)

# Update files surgically  
update_tool = agent.tool_registry.get_tool("update")
result = update_tool.execute(
    agent.execution_context,
    action="replace_pattern",
    path="calculator.py", 
    pattern="def old_function",
    replacement="def new_function"
)
```

## 🛡️ Security Features

- **Path Validation**: All operations confined to working directory
- **Command Filtering**: Configurable allow/block lists for commands
- **Resource Limits**: File size, timeout, and memory constraints
- **Audit Logging**: Comprehensive security event tracking
- **Violation Monitoring**: Real-time security violation detection

## 📋 Task Management

The system includes sophisticated task management capabilities:

```python
# Create todos
todo_tool = agent.tool_registry.get_tool("todo")
result = todo_tool.execute(
    agent.execution_context,
    action="create_todo",
    title="Implement authentication",
    priority="high",
    tags=["security", "backend"]
)

# Automatic task decomposition
task_tool = agent.tool_registry.get_tool("task")
result = task_tool.execute(
    agent.execution_context,
    action="decompose_task",
    description="Build a REST API with authentication",
    task_type="development"
)
```

## 🔍 Examples

Run the included examples to see the system in action:

```bash
# Basic usage
python examples/basic_usage.py

# Advanced capabilities  
python examples/advanced_example.py
```

## 🎯 Use Cases

- **Code Analysis**: Analyze large codebases, find patterns, generate reports
- **Development Automation**: Automate repetitive development tasks
- **File Processing**: Batch file operations with safety guarantees  
- **Project Management**: Break down complex projects into manageable tasks
- **Code Refactoring**: Safely refactor code with surgical precision
- **Documentation**: Generate and maintain project documentation

## 🔮 Future Enhancements

- **LLM Integration**: Support for OpenAI, Anthropic, and other providers
- **MCP Compatibility**: Model Context Protocol integration
- **Extended Tools**: Git operations, database tools, API clients
- **Web Interface**: Browser-based agent interaction
- **Plugin System**: Custom tool development framework

## 🤝 Contributing

This project follows a documentation-first approach using ADRs. Before implementing features:

1. Review existing ADRs in `docs/adr/`
2. Create new ADRs for significant decisions
3. Follow the established patterns and security practices
4. Ensure comprehensive testing

## 📄 License

This project is currently in development. License to be determined.test change
