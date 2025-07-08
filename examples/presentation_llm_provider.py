"""
Presentation-specific Mock LLM Provider

This mock generates realistic LLM responses with structured tool calls
for demonstration purposes. The agent uses real parsing and tool execution.
"""

from typing import Optional, List, Dict, Any
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from james_code.core.base import LLMProvider


class PresentationLLMProvider(LLMProvider):
    """Mock LLM provider that generates realistic responses with tool calls for presentation."""
    
    def __init__(self):
        self.conversation_history = []
        
    def generate_response(self, prompt: str, tools: Optional[list] = None) -> str:
        """Generate realistic LLM response with structured tool calls."""
        
        # Analyze the prompt to determine appropriate response
        if "calculator" in prompt.lower() and "module" in prompt.lower():
            return self._generate_calculator_development_response(prompt)
        elif "analyze" in prompt.lower() or "explore" in prompt.lower():
            return self._generate_analysis_response(prompt)
        else:
            return self._generate_default_response(prompt)
    
    def _generate_calculator_development_response(self, prompt: str) -> str:
        """Generate response for calculator development request."""
        response = """I'll help you build a complete Python calculator module. Let me start by exploring the current workspace to understand the existing structure and then create a comprehensive implementation.

<tool_call>
<tool_name>find</tool_name>
<parameters>{"action": "find_files", "pattern": "*.py", "directory": "."}</parameters>
</tool_call>

Now let me check the overall directory structure to better understand the project layout:

<tool_call>
<tool_name>read</tool_name>
<parameters>{"action": "list_directory", "path": "."}</parameters>
</tool_call>

Based on the workspace analysis, I'll create a production-ready calculator module with the following approach:

📋 IMPLEMENTATION STRATEGY:
1. Create calculator.py with comprehensive arithmetic operations
2. Implement proper error handling and input validation
3. Add type hints and detailed docstrings
4. Create a comprehensive test suite
5. Include usage examples and documentation

🔧 TECHNICAL DECISIONS:
- Use Decimal class for precise floating-point arithmetic
- Implement custom exceptions for domain-specific errors
- Add comprehensive logging for debugging and monitoring
- Follow PEP 8 style guidelines throughout
- Include type hints for better IDE support and runtime checking

The implementation will be robust, well-tested, and production-ready."""

        return response
    
    def _generate_analysis_response(self, prompt: str) -> str:
        """Generate response for analysis requests."""
        response = """I'll analyze the current workspace and codebase structure to provide insights.

<tool_call>
<tool_name>find</tool_name>
<parameters>{"action": "find_files", "pattern": "*", "directory": "."}</parameters>
</tool_call>

Let me also search for any existing Python files to understand the codebase structure:

<tool_call>
<tool_name>find</tool_name>
<parameters>{"action": "find_files", "pattern": "*.py", "directory": "."}</parameters>
</tool_call>

Based on my analysis, I'll provide detailed insights about the project structure and recommendations for improvement."""

        return response
    
    def _generate_default_response(self, prompt: str) -> str:
        """Generate default response for other requests."""
        response = f"""I'll help you with: {prompt}

Let me start by exploring the current workspace:

<tool_call>
<tool_name>find</tool_name>
<parameters>{"action": "find_files", "pattern": "*", "directory": "."}</parameters>
</tool_call>

Based on my analysis, I'll provide a comprehensive solution."""

        return response
    
    def parse_tool_calls(self, response: str) -> List[Dict[str, Any]]:
        """Parse structured tool calls from LLM response using real XML parsing."""
        import re
        import json
        
        tool_calls = []
        
        # Find all <tool_call> blocks in the response
        tool_call_pattern = r'<tool_call>(.*?)</tool_call>'
        matches = re.findall(tool_call_pattern, response, re.DOTALL)
        
        for match in matches:
            # Extract tool name
            tool_name_match = re.search(r'<tool_name>(.*?)</tool_name>', match, re.DOTALL)
            if not tool_name_match:
                continue
            tool_name = tool_name_match.group(1).strip()
            
            # Extract parameters
            params_match = re.search(r'<parameters>(.*?)</parameters>', match, re.DOTALL)
            if params_match:
                try:
                    params_json = params_match.group(1).strip()
                    parameters = json.loads(params_json)
                except (json.JSONDecodeError, ValueError):
                    parameters = {}
            else:
                parameters = {}
            
            # Create structured tool call
            tool_call = {
                "tool": tool_name,
                "parameters": parameters,
                "status": "pending",  # Will be executed by the agent
                "raw_xml": f"<tool_call>{match}</tool_call>"
            }
            
            # Add action if specified in parameters
            if "action" in parameters:
                tool_call["action"] = parameters["action"]
            
            tool_calls.append(tool_call)
        
        return tool_calls