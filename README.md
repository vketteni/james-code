# James Code

Hi, James Code is an agentic system, essentially a reconstruction of claude code. 

## 🚀 Disclaimer

James is still in development, designs aren't fully implemented, logical inconsitencies can still be present.   

## Getting Started

```bash
poetry install
poetry run python -m src.james_code.cli --interactive
```

```bash
poetry install --extras llm
export OPENAI_API_KEY="your-key"
poetry run james-code --llm-provider openai --llm-model gpt-4.1 --interactive
```

## Examples

```bash
👤 You: create a new file that contains the message "hi, it's chatgpt"
🤖 Agent: I have created a new file containing the message "hi, it's chatgpt" at the path /home/vketteni/projects/james-code/workspace/new_message.txt. Would you like to do anything else?

👤 You: can you run ls?
🤖 Agent: The directory contains the following files:
- agent_task_plans.json
- new_message.txt

Would you like to do anything else?
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
- **FindTool**: File and content search capabilities  
- **UpdateTool**: Surgical file modifications and patch application
- **TodoTool**: Task management with tool execution (multi-turn)
- **TaskTool**: Task decomposition and execution planning 


## 📍 Program Starting Points

  ```toml
  # pyproject.toml
  [tool.poetry.scripts]
  james-code = "james_code.cli:main"  # Entry point
  ```

##  🔄 Execution Flow

James Code follows an **LLM-driven architecture** where the LLM controls the entire conversation flow:

  1. **CLI Entry**:
  ```python
  # cli.py:main()
  def main():
      agent = setup_agent(args)  # Creates Agent with LLM provider
      agent.process_request(user_input)  # Starts conversation loop
  ```

  2. **Agent Initialization**:
  ```python
  # agent.py:__init__()
  def _register_default_tools(self):
      tools = [
          ReadTool(), WriteTool(), ExecuteTool(), FindTool(),
          UpdateTool(), TodoTool(tool_registry=self.tool_registry, 
                                 llm_provider=self.llm_provider), 
          TaskTool() 
      ]
  ```

  3. **LLM-Driven Conversation Loop**:
  ```python
  # agent.py:_handle_request_directly()
  while iteration < max_iterations:
      # LLM analyzes conversation context
      conversation_context = self._build_conversation_context()
      llm_response = self.llm_provider.generate_response(
          conversation_context, tools=self._get_available_tools_schema()
      )
      
      # Parse and execute any tool calls
      tool_calls = self.llm_provider.parse_tool_calls(llm_response)
      if not tool_calls:
          break  # LLM finished
      
      # Execute tools and add results to conversation
      for tool_call in tool_calls:
          result = self._execute_tool_call(tool_call)
          self._add_tool_results_to_conversation([tool_call], [result])
      
      # Continue until LLM decides to finish
  ```

  4. **TodoTool Integration**:
  ```python
  # TodoTool can execute other tools and auto-expand
  todo_tool.execute(context, action="execute_todo", todo_id="123")
  # → Executes configured tool and captures results
  
  todo_tool.execute(context, action="auto_expand_todo", todo_id="123") 
  # → Uses LLM to create intelligent follow-up todos
  ```


## 🏗️ Architecture Decision Records

This project uses Architecture Decision Records (ADRs) to document important architectural decisions. All ADRs are stored in `docs/adr/`.

### Current ADRs

- [ADR-0001: Use Architecture Decision Records](docs/adr/0001-use-architecture-decision-records.md)
- [ADR-0002: Agent Architecture Design](docs/adr/0002-agent-architecture-design.md)
- [ADR-0003: Tool System Design](docs/adr/0003-tool-system-design.md)
- [ADR-0004: Safety and Sandboxing Approach](docs/adr/0004-safety-and-sandboxing-approach.md)
- [ADR-0005: MCP Protocol Compatibility](docs/adr/0005-mcp-protocol-compatibility.md)
- [ADR-0006: Additional Fundamental Tools](docs/adr/0006-additional-fundamental-tools.md)
- [ADR-0009: Testing Implementation Strategy](docs/adr/0009-testing-implementation-strategy.md)
- [ADR-0010: LLM-Driven Architecture](docs/adr/0010-llm-driven-architecture.md)
