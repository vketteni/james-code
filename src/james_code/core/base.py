"""Base classes and interfaces for the agent LLM system."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from pathlib import Path


@dataclass
class ToolResult:
    """Result from tool execution."""
    success: bool
    data: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionContext:
    """Context for tool execution."""
    working_directory: Path
    environment: Dict[str, str] = field(default_factory=dict)
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class Tool(ABC):
    """Abstract base class for all tools."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    def execute(self, context: ExecutionContext, **kwargs) -> ToolResult:
        """Execute the tool with given parameters."""
        pass
    
    @abstractmethod
    def validate_input(self, **kwargs) -> bool:
        """Validate input parameters before execution."""
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's parameter schema."""
        schema = {
            "name": self.name,
            "description": self.description,
            "parameters": self._get_parameter_schema()
        }
        
        # Add examples if the tool provides them
        examples = self._get_examples()
        if examples:
            schema["examples"] = examples
            
        return schema
    
    @abstractmethod
    def _get_parameter_schema(self) -> Dict[str, Any]:
        """Get the parameter schema for this tool."""
        pass
    
    def _get_examples(self) -> Optional[List[Dict[str, Any]]]:
        """Get usage examples for this tool. Override in subclasses to provide examples."""
        return None


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def generate_response(self, prompt: str, tools: Optional[list] = None) -> str:
        """Generate a response using the LLM."""
        pass
    
    @abstractmethod
    def parse_tool_calls(self, response: str) -> list:
        """Parse tool calls from LLM response."""
        pass


class ToolRegistry:
    """Registry for managing available tools."""
    
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
    
    def register(self, tool: Tool):
        """Register a tool."""
        self._tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def get_all_tools(self) -> Dict[str, Tool]:
        """Get all registered tools."""
        return self._tools.copy()
    
    def get_tool_schemas(self) -> list:
        """Get schemas for all registered tools."""
        return [tool.get_schema() for tool in self._tools.values()]