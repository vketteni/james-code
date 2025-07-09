"""OpenAI LLM provider implementation."""

import json
import os
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from ..core.base import LLMProvider

try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None


@dataclass
class OpenAIConfig:
    """Configuration for OpenAI provider."""
    api_key: Optional[str] = None
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    timeout: int = 30
    max_retries: int = 3


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider with function calling support."""
    
    def __init__(self, config: Optional[OpenAIConfig] = None):
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "OpenAI package not installed. Install with: pip install openai"
            )
        
        self.config = config or OpenAIConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize OpenAI client
        api_key = self.config.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenAI API key not provided. Set OPENAI_API_KEY environment variable "
                "or pass api_key in OpenAIConfig"
            )
        
        self.client = OpenAI(
            api_key=api_key,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries
        )
        
        # Verify the model is available
        self._verify_model()
    
    def _verify_model(self):
        """Verify the specified model is available."""
        try:
            # Test with a simple request
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            self.logger.info(f"OpenAI model {self.config.model} verified successfully")
        except Exception as e:
            self.logger.error(f"Failed to verify OpenAI model {self.config.model}: {e}")
            raise
    
    def generate_response(self, prompt: str, tools: Optional[List[Dict[str, Any]]] = None) -> str:
        """Generate a response using OpenAI's chat completion API."""
        try:
            messages = [{"role": "user", "content": prompt}]
            
            # Prepare request parameters
            request_params = {
                "model": self.config.model,
                "messages": messages,
                "temperature": self.config.temperature,
            }
            
            # Add max_tokens if specified
            if self.config.max_tokens:
                request_params["max_tokens"] = self.config.max_tokens
            
            # Add tools if provided
            if tools:
                request_params["tools"] = tools
                request_params["tool_choice"] = "auto"
            
            self.logger.debug(f"OpenAI request: {json.dumps(request_params, indent=2)}")
            
            # Make the API call
            response = self.client.chat.completions.create(**request_params)
            
            # Extract the response
            if response.choices and response.choices[0].message:
                message = response.choices[0].message
                
                # Store the full response for tool call parsing
                self._last_response = response
                
                # Return the content (might be empty if only tool calls)
                return message.content or ""
            else:
                self.logger.error("No response from OpenAI API")
                return "Error: No response from OpenAI"
                
        except Exception as e:
            self.logger.error(f"OpenAI API error: {str(e)}")
            return f"Error: {str(e)}"
    
    def parse_tool_calls(self, response: str) -> List[Dict[str, Any]]:
        """Parse tool calls from the last OpenAI response."""
        if not hasattr(self, '_last_response') or not self._last_response:
            return []
        
        try:
            message = self._last_response.choices[0].message
            
            if not message.tool_calls:
                return []
            
            tool_calls = []
            for tool_call in message.tool_calls:
                if tool_call.type == "function":
                    function_call = tool_call.function
                    
                    # Parse the function arguments
                    try:
                        arguments = json.loads(function_call.arguments)
                    except json.JSONDecodeError as e:
                        self.logger.error(f"Failed to parse tool call arguments: {e}")
                        arguments = {}
                    
                    tool_calls.append({
                        "tool": function_call.name,
                        "parameters": arguments,
                        "id": tool_call.id
                    })
            
            return tool_calls
            
        except Exception as e:
            self.logger.error(f"Error parsing tool calls: {str(e)}")
            return []
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        return {
            "provider": "openai",
            "model": self.config.model,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "available": OPENAI_AVAILABLE
        }
    
    def estimate_tokens(self, text: str) -> int:
        """Rough estimate of token count (4 characters ≈ 1 token)."""
        return len(text) // 4
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics if available."""
        if hasattr(self, '_last_response') and self._last_response:
            usage = self._last_response.usage
            if usage:
                return {
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens
                }
        return {}