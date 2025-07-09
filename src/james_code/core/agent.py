"""Main agent orchestration system."""

import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import time

from .base import Tool, ToolResult, ExecutionContext, LLMProvider, ToolRegistry
from ..safety.safety_manager import SafetyManager, SafetyConfig
from ..tools import (
    ReadTool, WriteTool, ExecuteTool, FindTool, 
    UpdateTool, TodoTool, TaskTool
)
# Removed authentic_agentic_mock import - using clean architecture


@dataclass
class AgentConfig:
    """Configuration for the agent."""
    working_directory: str
    llm_provider: str = "mock"  # Will be expanded later
    safety_config: Optional[SafetyConfig] = None
    max_iterations: int = 50
    verbose_logging: bool = True
    session_id: Optional[str] = None


@dataclass
class ConversationMessage:
    """A message in the conversation."""
    role: str  # 'user', 'assistant', 'system', 'tool'
    content: str
    timestamp: float
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class Agent:
    """Main agent orchestration system."""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.working_directory = Path(config.working_directory).resolve()
        
        # Ensure working directory exists
        self.working_directory.mkdir(parents=True, exist_ok=True)
        
        # Set up safety manager
        if config.safety_config:
            self.safety_manager = SafetyManager(config.safety_config)
        else:
            # Default safety configuration
            default_safety_config = SafetyConfig(
                base_directory=str(self.working_directory),
                enable_audit_logging=config.verbose_logging
            )
            self.safety_manager = SafetyManager(default_safety_config)
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        if config.verbose_logging:
            logging.basicConfig(level=logging.INFO)
        
        # Initialize tool registry
        self.tool_registry = ToolRegistry()
        self._register_default_tools()
        
        # Initialize LLM provider (mock for now)
        self.llm_provider = self._create_llm_provider(config.llm_provider)
        
        # Conversation state
        self.conversation_history: List[ConversationMessage] = []
        self.execution_context = ExecutionContext(
            working_directory=self.working_directory,
            session_id=config.session_id or f"session_{int(time.time())}"
        )
        
        # Configure LLM provider with agent context for authentic behavior
        if hasattr(self.llm_provider, 'set_agent_context'):
            self.llm_provider.set_agent_context(self.tool_registry, self.execution_context)
        
        # Current task state
        self.current_plan_id: Optional[str] = None
        self.iteration_count = 0
        
        self.logger.info(f"Agent initialized in {self.working_directory}")
    
    def _register_default_tools(self):
        """Register default tools."""
        tools = [
            ReadTool(),
            WriteTool(),
            ExecuteTool(),
            FindTool(),
            UpdateTool(),
            TodoTool(),
            TaskTool()
        ]
        
        for tool in tools:
            self.tool_registry.register(tool)
        
        self.logger.info(f"Registered {len(tools)} tools")
    
    def _create_llm_provider(self, provider_name: str) -> LLMProvider:
        """Create LLM provider instance."""
        if provider_name == "mock":
            return MockLLMProvider()
        else:
            # TODO: Implement real LLM providers (OpenAI, Anthropic, etc.)
            raise ValueError(f"LLM provider not supported: {provider_name}")
    
    def process_request(self, user_input: str) -> str:
        """Process a user request and return response."""
        try:
            # Add user message to conversation
            self._add_message("user", user_input)
            
            # Reset iteration counter
            self.iteration_count = 0
            
            # Process the request
            response = self._process_conversation()
            
            # Add assistant response to conversation
            self._add_message("assistant", response)
            
            return response
            
        except Exception as e:
            error_msg = f"Error processing request: {str(e)}"
            self.logger.error(error_msg)
            self._add_message("assistant", error_msg)
            return error_msg
    
    def _process_conversation(self) -> str:
        """Process the current conversation state."""
        # Always use direct LLM-driven approach
        return self._handle_request_directly()
    
    
    def _get_conversation_context(self) -> str:
        """Get conversation context for task planning."""
        recent_messages = self.conversation_history[-5:]  # Last 5 messages
        context_parts = []
        
        for msg in recent_messages:
            if msg.role in ["user", "assistant"]:
                context_parts.append(f"{msg.role}: {msg.content[:200]}...")
        
        return "\n".join(context_parts)
    
    def _execute_current_plan(self) -> str:
        """Execute the current task plan."""
        try:
            task_tool = self.tool_registry.get_tool("task")
            if not task_tool:
                return "Task tool not available"
            
            # Get next executable steps
            next_steps_result = task_tool.execute(
                self.execution_context,
                action="get_next_steps",
                plan_id=self.current_plan_id
            )
            
            if not next_steps_result.success:
                return f"Error getting next steps: {next_steps_result.error}"
            
            next_steps = next_steps_result.data
            
            if not next_steps:
                # Plan is complete
                self.current_plan_id = None
                return "Task plan completed successfully!"
            
            # Execute the first available step
            step = next_steps[0]
            step_result = self._execute_step(step)
            
            # Update step status
            self._update_step_status(step["id"], step_result)
            
            if step_result.success:
                return f"Completed step: {step['title']}\nResult: {step_result.data}"
            else:
                return f"Step failed: {step['title']}\nError: {step_result.error}"
            
        except Exception as e:
            self.logger.error(f"Error executing plan: {str(e)}")
            return f"Error executing plan: {str(e)}"
    
    def _execute_step(self, step: Dict[str, Any]) -> ToolResult:
        """Execute a single step from a task plan."""
        try:
            tool_name = step["tool_name"]
            tool_params = step.get("tool_params", {})
            
            # Get the tool
            tool = self.tool_registry.get_tool(tool_name)
            if not tool:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Tool not found: {tool_name}"
                )
            
            # Validate with safety manager if needed
            if tool_name == "execute" and "command" in tool_params:
                safety_result = self.safety_manager.validate_command(tool_params["command"])
                if not safety_result.success:
                    return ToolResult(
                        success=False,
                        data=None,
                        error=f"Security violation: {safety_result.error}"
                    )
            
            # Execute the tool
            start_time = time.time()
            result = tool.execute(self.execution_context, **tool_params)
            execution_time = time.time() - start_time
            
            # Log execution
            self.logger.info(f"Executed {tool_name} in {execution_time:.2f}s: {result.success}")
            
            return result
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error executing step: {str(e)}"
            )
    
    def _update_step_status(self, step_id: str, result: ToolResult):
        """Update step status based on execution result."""
        try:
            task_tool = self.tool_registry.get_tool("task")
            if not task_tool:
                return
            
            status = "completed" if result.success else "failed"
            error_message = None if result.success else result.error
            
            task_tool.execute(
                self.execution_context,
                action="update_step",
                plan_id=self.current_plan_id,
                step_id=step_id,
                status=status,
                error_message=error_message,
                result=result.data if result.success else None
            )
            
        except Exception as e:
            self.logger.error(f"Error updating step status: {str(e)}")
    
    def _handle_request_directly(self) -> str:
        """Handle request directly without task planning."""
        try:
            # Get the latest user message
            user_messages = [msg for msg in self.conversation_history if msg.role == "user"]
            if not user_messages:
                return "No user input to process"
            
            latest_message = user_messages[-1].content
            
            # Update conversation history in authentic mock for context awareness
            if hasattr(self.llm_provider, 'authentic_mock'):
                self.llm_provider.authentic_mock.conversation_history = self.conversation_history
            
            # Use LLM provider to generate response
            llm_response = self.llm_provider.generate_response(latest_message)
            
            # Parse and execute any tool calls from the response
            tool_calls = self.llm_provider.parse_tool_calls(llm_response)
            
            # Execute tool calls if any
            if tool_calls:
                for tool_call in tool_calls:
                    tool_name = tool_call.get("tool")
                    params = tool_call.get("parameters", {})
                    
                    tool = self.tool_registry.get_tool(tool_name)
                    if tool and tool_call.get("status") != "executed":
                        result = tool.execute(self.execution_context, **params)
                        # Tool execution results are reflected in the response
            
            return llm_response
            
        except Exception as e:
            return f"Error handling request: {str(e)}"
    
    def _parse_and_execute_command(self, command: str) -> str:
        """Parse and execute a simple command."""
        command_lower = command.lower().strip()
        
        # List files
        if "list" in command_lower and ("file" in command_lower or "directory" in command_lower):
            read_tool = self.tool_registry.get_tool("read")
            result = read_tool.execute(
                self.execution_context,
                action="list_directory",
                path="."
            )
            if result.success:
                files = result.data
                file_list = "\n".join([f"- {f['name']} ({f['type']})" for f in files])
                return f"Files in current directory:\n{file_list}"
            else:
                return f"Error listing files: {result.error}"
        
        # Find files
        elif "find" in command_lower and "file" in command_lower:
            # Extract pattern (simple heuristic)
            words = command.split()
            pattern = "*"
            for i, word in enumerate(words):
                if word.lower() == "find" and i + 1 < len(words):
                    pattern = words[i + 1]
                    break
            
            find_tool = self.tool_registry.get_tool("find")
            result = find_tool.execute(
                self.execution_context,
                action="find_files",
                pattern=pattern
            )
            if result.success:
                files = result.data
                if files:
                    file_list = "\n".join([f"- {f['path']}" for f in files])
                    return f"Found files:\n{file_list}"
                else:
                    return f"No files found matching pattern: {pattern}"
            else:
                return f"Error finding files: {result.error}"
        
        # Read file
        elif "read" in command_lower and "file" in command_lower:
            # Extract filename (simple heuristic)
            words = command.split()
            filename = None
            for word in words:
                if "." in word and not word.startswith("."):
                    filename = word
                    break
            
            if not filename:
                return "Please specify a filename to read"
            
            read_tool = self.tool_registry.get_tool("read")
            result = read_tool.execute(
                self.execution_context,
                action="read_file",
                path=filename
            )
            if result.success:
                content = result.data
                return f"Content of {filename}:\n{content[:1000]}..." if len(content) > 1000 else f"Content of {filename}:\n{content}"
            else:
                return f"Error reading file: {result.error}"
        
        # Show status
        elif "status" in command_lower or "info" in command_lower:
            return self._get_agent_status()
        
        else:
            return f"I understand you want to: {command}\nHowever, I need more specific instructions. Try commands like:\n- 'list files'\n- 'find files matching *.py'\n- 'read file example.txt'\n- 'show status'"
    
    def _get_agent_status(self) -> str:
        """Get current agent status."""
        status_parts = [
            f"Agent Status:",
            f"- Working Directory: {self.working_directory}",
            f"- Available Tools: {len(self.tool_registry.get_all_tools())}",
            f"- Conversation Messages: {len(self.conversation_history)}",
            f"- Current Plan: {self.current_plan_id or 'None'}",
            f"- Session ID: {self.execution_context.session_id}"
        ]
        
        # Get security summary
        security_summary = self.safety_manager.get_security_summary()
        status_parts.append(f"- Security Violations: {security_summary['total_violations']}")
        
        return "\n".join(status_parts)
    
    def _add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Add a message to conversation history."""
        message = ConversationMessage(
            role=role,
            content=content,
            timestamp=time.time(),
            metadata=metadata or {}
        )
        self.conversation_history.append(message)
        
        # Keep conversation history manageable
        if len(self.conversation_history) > 100:
            self.conversation_history = self.conversation_history[-50:]
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get conversation history as list of dicts."""
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp,
                "metadata": msg.metadata
            }
            for msg in self.conversation_history
        ]
    
    def save_session(self, filepath: Optional[str] = None) -> bool:
        """Save current session to file."""
        try:
            if not filepath:
                filepath = self.working_directory / f"session_{self.execution_context.session_id}.json"
            
            session_data = {
                "config": {
                    "working_directory": str(self.config.working_directory),
                    "session_id": self.execution_context.session_id
                },
                "conversation_history": self.get_conversation_history(),
                "current_plan_id": self.current_plan_id
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Session saved to {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving session: {str(e)}")
            return False
    
    def load_session(self, filepath: str) -> bool:
        """Load session from file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # Restore conversation history
            self.conversation_history = []
            for msg_data in session_data.get("conversation_history", []):
                self.conversation_history.append(ConversationMessage(**msg_data))
            
            # Restore current plan
            self.current_plan_id = session_data.get("current_plan_id")
            
            self.logger.info(f"Session loaded from {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading session: {str(e)}")
            return False


class MockLLMProvider(LLMProvider):
    """Basic mock LLM provider for testing. Use presentation provider for demos."""
    
    def __init__(self):
        pass
    
    def generate_response(self, prompt: str, tools: Optional[list] = None) -> str:
        """Generate basic mock response."""
        return f"Mock response for: {prompt}"
    
    def parse_tool_calls(self, response: str) -> list:
        """Parse tool calls from response."""
        return []  # No tool calls in basic mock