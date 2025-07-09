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
        
        # Initialize LLM provider (mock for now)
        self.llm_provider = self._create_llm_provider(config.llm_provider)
        
        # Initialize tool registry
        self.tool_registry = ToolRegistry()
        self._register_default_tools()
        
        # Conversation state
        self.conversation_history: List[ConversationMessage] = []
        self.execution_context = ExecutionContext(
            working_directory=self.working_directory,
            session_id=config.session_id or f"session_{int(time.time())}"
        )
        
        # Configure LLM provider with agent context for authentic behavior
        if hasattr(self.llm_provider, 'set_agent_context'):
            self.llm_provider.set_agent_context(self.tool_registry, self.execution_context)
        
        # Current conversation state
        self.iteration_count = 0
        
        self.logger.info(f"Agent initialized in {self.working_directory}")
    
    def _add_message(self, role: str, msg: str):
            msg = ConversationMessage(role, msg, "timestamp")
            self.conversation_history.append(msg)

    def _register_default_tools(self):
        """Register default tools."""
        tools = [
            ReadTool(),
            WriteTool(),
            ExecuteTool(),
            FindTool(),
            UpdateTool(),
            TodoTool(tool_registry=self.tool_registry, llm_provider=self.llm_provider),
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
    
    def _handle_request_directly(self) -> str:
        """Handle request with iterative LLM-driven conversation loop."""
        try:
            # Get the latest user message
            user_messages = [msg for msg in self.conversation_history if msg.role == "user"]
            if not user_messages:
                return "No user input to process"
            
            # Start iterative conversation loop
            max_iterations = self.config.max_iterations
            iteration = 0
            final_response = ""
            
            while iteration < max_iterations:
                iteration += 1
                self.logger.debug(f"LLM conversation iteration {iteration}")
                
                # Update conversation history for context awareness
                if hasattr(self.llm_provider, 'authentic_mock'):
                    self.llm_provider.authentic_mock.conversation_history = self.conversation_history
                
                # Get full conversation context for LLM
                conversation_context = self._build_conversation_context()
                
                # Generate LLM response with tools available
                llm_response = self.llm_provider.generate_response(
                    conversation_context, 
                    tools=self._get_available_tools_schema()
                )
                
                # Parse tool calls from response
                tool_calls = self.llm_provider.parse_tool_calls(llm_response)
                
                # If no tool calls, LLM has finished - return the response
                if not tool_calls:
                    final_response = llm_response
                    break
                
                # Execute tool calls and gather results
                tool_results = []
                for tool_call in tool_calls:
                    result = self._execute_tool_call(tool_call)
                    tool_results.append(result)
                
                # Add tool results to conversation history for next iteration
                self._add_tool_results_to_conversation(tool_calls, tool_results)
                
                # If this is the last iteration, return what we have
                if iteration >= max_iterations:
                    final_response = f"Completed {iteration} iterations. Last response: {llm_response}"
                    break
            
            return final_response
            
        except Exception as e:
            return f"Error in LLM conversation loop: {str(e)}"
    
    def _build_conversation_context(self) -> str:
        """Build complete conversation context for LLM."""
        context_parts = []
        
        # Add system context
        context_parts.append("You are an AI assistant with access to tools for file operations, code execution, and task management.")
        context_parts.append("Use tools when appropriate to help the user accomplish their goals.")
        context_parts.append("You can use the 'todo' tool to create and manage complex planning tasks.")
        context_parts.append("")
        
        # Add conversation history
        for msg in self.conversation_history:
            if msg.role == "user":
                context_parts.append(f"User: {msg.content}")
            elif msg.role == "assistant":
                context_parts.append(f"Assistant: {msg.content}")
            elif msg.role == "tool":
                context_parts.append(f"Tool Result: {msg.content}")
        
        return "\n".join(context_parts)
    
    def _get_available_tools_schema(self) -> list:
        """Get schema of available tools for LLM."""
        tools_schema = []
        
        for tool_name in self.tool_registry.get_all_tools():
            tool = self.tool_registry.get_tool(tool_name)
            if tool and hasattr(tool, 'get_schema'):
                schema = tool.get_schema()
                tools_schema.append({
                    "name": tool_name,
                    "description": tool.description,
                    "schema": schema
                })
        
        return tools_schema
    
    def _execute_tool_call(self, tool_call: dict) -> dict:
        """Execute a single tool call and return result."""
        try:
            tool_name = tool_call.get("tool")
            params = tool_call.get("parameters", {})
            
            tool = self.tool_registry.get_tool(tool_name)
            if not tool:
                return {
                    "success": False,
                    "error": f"Tool '{tool_name}' not found"
                }
            
            result = tool.execute(self.execution_context, **params)
            
            return {
                "success": result.success,
                "data": result.data,
                "error": result.error,
                "metadata": result.metadata
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error executing tool: {str(e)}"
            }
    
    def _add_tool_results_to_conversation(self, tool_calls: list, tool_results: list):
        """Add tool execution results to conversation history."""
        for tool_call, result in zip(tool_calls, tool_results):
            tool_name = tool_call.get("tool", "unknown")
            
            if result["success"]:
                result_content = f"Tool '{tool_name}' executed successfully. Result: {result['data']}"
            else:
                result_content = f"Tool '{tool_name}' failed. Error: {result['error']}"
            
            self._add_message("tool", result_content)
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get conversation history as list of dictionaries."""
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp,
                "metadata": msg.metadata
            }
            for msg in self.conversation_history
        ]
    
    def save_session(self, session_file: str) -> bool:
        """Save current session to file."""
        try:
            session_data = {
                "config": {
                    "working_directory": str(self.working_directory),
                    "max_iterations": self.config.max_iterations,
                    "verbose_logging": self.config.verbose_logging
                },
                "conversation_history": self.get_conversation_history(),
                "iteration_count": self.iteration_count,
                "session_metadata": {
                    "saved_at": time.time(),
                    "agent_version": "1.0.0"
                }
            }
            
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Session saved to: {session_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving session: {str(e)}")
            return False
    
    def load_session(self, session_file: str) -> bool:
        """Load session from file."""
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # Restore conversation history
            self.conversation_history = []
            for msg_data in session_data.get("conversation_history", []):
                self._add_message(
                    role=msg_data["role"],
                    content=msg_data["content"],
                    metadata=msg_data.get("metadata", {})
                )
            
            # Restore state
            self.iteration_count = session_data.get("iteration_count", 0)
            
            self.logger.info(f"Session loaded from: {session_file}")
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