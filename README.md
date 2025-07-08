# James Code

Hi, James Code is an agentic system, essentially a reconstruction of claude code. 

## 🚀 Disclaimer

James is still in development, designs aren't fully implemented, logical inconsitencies can still be present.   

The goal is to establish a multi-turn response pattern akin to OpenAI/Anthropic.
```python
  OpenAI/Anthropic Pattern:
  messages = [{"role": "user", "content": "Analyze this codebase"}]

  while True:
      response = client.chat.completions.create(
          model="gpt-4",
          messages=messages,
          tools=tool_schemas
      )

      if response.choices[0].finish_reason == "tool_calls":
          # Execute tools and add results
          for tool_call in response.choices[0].message.tool_calls:
              result = execute_tool(tool_call)
              messages.append({
                  "role": "tool",
                  "tool_call_id": tool_call.id,
                  "content": str(result)
              })
      else:
          break  # LLM finished without more tools
```


## 🚀 Feature Plan

### Core Capabilities
- **🔍 Search**: Pattern-based file discovery, content search, function finding
- **✏️ Editing**: Line-based updates, pattern replacement, patch application  
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

## 📄 License

This project is currently in development. License to be determined.
