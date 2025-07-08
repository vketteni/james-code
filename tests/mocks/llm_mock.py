"""LLM mocking infrastructure for deterministic testing."""

import json
import re
import time
import hashlib
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import threading
import random

import pytest


class LLMErrorType(Enum):
    """Types of LLM errors to simulate."""
    NETWORK_ERROR = "network_error"
    API_KEY_INVALID = "api_key_invalid"
    RATE_LIMIT = "rate_limit"
    QUOTA_EXCEEDED = "quota_exceeded"
    CONTENT_FILTER = "content_filter"
    TIMEOUT = "timeout"
    SERVICE_UNAVAILABLE = "service_unavailable"
    INVALID_REQUEST = "invalid_request"
    CONTEXT_LENGTH_EXCEEDED = "context_length_exceeded"


@dataclass
class MockLLMResponse:
    """Mock LLM response for testing."""
    content: str
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    usage: Dict[str, int] = field(default_factory=dict)
    model: str = "mock-model"
    finish_reason: str = "stop"
    response_time: float = 0.1
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponseScenario:
    """Scenario for generating mock LLM responses."""
    name: str
    pattern: Union[str, re.Pattern]
    response: Union[MockLLMResponse, Callable[[str], MockLLMResponse]]
    priority: int = 100
    enabled: bool = True
    usage_count: int = 0


class MockLLMProvider:
    """Base mock LLM provider for testing."""
    
    def __init__(self, model_name: str = "mock-gpt-4"):
        """Initialize mock LLM provider.
        
        Args:
            model_name: Name of the mock model
        """
        self.model_name = model_name
        self.scenarios: List[LLMResponseScenario] = []
        self.call_history: List[Dict[str, Any]] = []
        self.token_usage: Dict[str, int] = {"input": 0, "output": 0, "total": 0}
        self.error_simulation: Optional[LLMErrorType] = None
        self.response_delay: float = 0.0
        self._lock = threading.Lock()
    
    def add_scenario(self, scenario: LLMResponseScenario):
        """Add a response scenario.
        
        Args:
            scenario: Scenario to add
        """
        with self._lock:
            self.scenarios.append(scenario)
            # Sort by priority (lower number = higher priority)
            self.scenarios.sort(key=lambda s: s.priority)
    
    def add_simple_scenario(self, 
                          pattern: str, 
                          response_content: str,
                          tool_calls: List[Dict[str, Any]] = None,
                          priority: int = 100):
        """Add a simple response scenario.
        
        Args:
            pattern: Pattern to match in prompts
            response_content: Response content to return
            tool_calls: Optional tool calls to include
            priority: Priority (lower = higher priority)
        """
        response = MockLLMResponse(
            content=response_content,
            tool_calls=tool_calls or [],
            usage={"input_tokens": 50, "output_tokens": len(response_content.split())},
            response_time=0.1,
            model=self.model_name
        )
        
        scenario = LLMResponseScenario(
            name=f"simple_{pattern}",
            pattern=pattern,
            response=response,
            priority=priority
        )
        
        self.add_scenario(scenario)
    
    def generate_response(self, 
                         prompt: str, 
                         context: Optional[Dict[str, Any]] = None) -> MockLLMResponse:
        """Generate a mock response for the given prompt.
        
        Args:
            prompt: User prompt
            context: Optional context for generation
            
        Returns:
            Mock LLM response
            
        Raises:
            Exception: If error simulation is enabled
        """
        with self._lock:
            # Record the call
            call_record = {
                "timestamp": time.time(),
                "prompt": prompt,
                "context": context,
                "model": self.model_name
            }
            self.call_history.append(call_record)
            
            # Simulate errors if configured
            if self.error_simulation:
                self._simulate_error()
            
            # Add response delay if configured
            if self.response_delay > 0:
                time.sleep(self.response_delay)
            
            # Find matching scenario
            response = self._find_matching_response(prompt, context)
            
            # Update token usage
            self.token_usage["input"] += response.usage.get("input_tokens", 0)
            self.token_usage["output"] += response.usage.get("output_tokens", 0)
            self.token_usage["total"] += response.usage.get("total_tokens", 
                                                          response.usage.get("input_tokens", 0) + 
                                                          response.usage.get("output_tokens", 0))
            
            return response
    
    def _find_matching_response(self, 
                              prompt: str, 
                              context: Optional[Dict[str, Any]]) -> MockLLMResponse:
        """Find matching response scenario for prompt.
        
        Args:
            prompt: User prompt
            context: Optional context
            
        Returns:
            Mock LLM response
        """
        for scenario in self.scenarios:
            if not scenario.enabled:
                continue
                
            # Check if pattern matches
            if isinstance(scenario.pattern, str):
                if scenario.pattern.lower() in prompt.lower():
                    match_found = True
                else:
                    match_found = False
            else:  # regex pattern
                match_found = bool(scenario.pattern.search(prompt))
            
            if match_found:
                scenario.usage_count += 1
                
                # Generate response
                if callable(scenario.response):
                    return scenario.response(prompt)
                else:
                    return scenario.response
        
        # No matching scenario found, return default
        return self._generate_default_response(prompt)
    
    def _generate_default_response(self, prompt: str) -> MockLLMResponse:
        """Generate a default response when no scenario matches.
        
        Args:
            prompt: User prompt
            
        Returns:
            Default mock response
        """
        # Simple pattern matching for common operations
        prompt_lower = prompt.lower()
        
        if "read" in prompt_lower and "file" in prompt_lower:
            content = 'I need to read a file. Let me use the read tool.'
            tool_calls = [{
                "name": "read",
                "parameters": {"action": "read_file", "path": "example.txt"}
            }]
        elif "write" in prompt_lower and "file" in prompt_lower:
            content = 'I need to write to a file. Let me use the write tool.'
            tool_calls = [{
                "name": "write", 
                "parameters": {"action": "write_file", "path": "output.txt", "content": "Hello"}
            }]
        elif "execute" in prompt_lower or "run" in prompt_lower:
            content = 'I need to execute a command. Let me use the execute tool.'
            tool_calls = [{
                "name": "execute",
                "parameters": {"command": "echo Hello"}
            }]
        else:
            content = f'I understand you want me to help with: {prompt[:100]}...'
            tool_calls = []
        
        return MockLLMResponse(
            content=content,
            tool_calls=tool_calls,
            usage={
                "input_tokens": len(prompt.split()),
                "output_tokens": len(content.split()),
                "total_tokens": len(prompt.split()) + len(content.split())
            },
            response_time=0.1,
            model=self.model_name,
            metadata={"generated": "default_response"}
        )
    
    def _simulate_error(self):
        """Simulate an LLM error based on configured error type.
        
        Raises:
            Various exceptions based on error_simulation setting
        """
        error_messages = {
            LLMErrorType.NETWORK_ERROR: "Network connection failed",
            LLMErrorType.API_KEY_INVALID: "Invalid API key provided",
            LLMErrorType.RATE_LIMIT: "Rate limit exceeded, please try again later",
            LLMErrorType.QUOTA_EXCEEDED: "API quota exceeded",
            LLMErrorType.CONTENT_FILTER: "Content filtered due to policy violation",
            LLMErrorType.TIMEOUT: "Request timed out",
            LLMErrorType.SERVICE_UNAVAILABLE: "Service temporarily unavailable",
            LLMErrorType.INVALID_REQUEST: "Invalid request format",
            LLMErrorType.CONTEXT_LENGTH_EXCEEDED: "Context length exceeds model limit"
        }
        
        message = error_messages.get(self.error_simulation, "Unknown LLM error")
        
        if self.error_simulation == LLMErrorType.NETWORK_ERROR:
            raise ConnectionError(message)
        elif self.error_simulation == LLMErrorType.TIMEOUT:
            raise TimeoutError(message)
        elif self.error_simulation == LLMErrorType.RATE_LIMIT:
            raise Exception(f"RateLimitError: {message}")
        else:
            raise Exception(f"LLMError: {message}")
    
    def get_call_history(self) -> List[Dict[str, Any]]:
        """Get history of all LLM calls.
        
        Returns:
            List of call records
        """
        with self._lock:
            return self.call_history.copy()
    
    def get_token_usage(self) -> Dict[str, int]:
        """Get total token usage statistics.
        
        Returns:
            Token usage dictionary
        """
        with self._lock:
            return self.token_usage.copy()
    
    def get_scenario_usage(self) -> Dict[str, int]:
        """Get usage statistics for each scenario.
        
        Returns:
            Dictionary mapping scenario names to usage counts
        """
        with self._lock:
            return {scenario.name: scenario.usage_count for scenario in self.scenarios}
    
    def reset(self):
        """Reset all state (call history, token usage, scenario usage)."""
        with self._lock:
            self.call_history.clear()
            self.token_usage = {"input": 0, "output": 0, "total": 0}
            for scenario in self.scenarios:
                scenario.usage_count = 0
    
    def enable_error_simulation(self, error_type: LLMErrorType):
        """Enable error simulation.
        
        Args:
            error_type: Type of error to simulate
        """
        self.error_simulation = error_type
    
    def disable_error_simulation(self):
        """Disable error simulation."""
        self.error_simulation = None
    
    def set_response_delay(self, delay: float):
        """Set artificial response delay.
        
        Args:
            delay: Delay in seconds
        """
        self.response_delay = delay


class DeterministicLLMProvider(MockLLMProvider):
    """Deterministic LLM provider that always returns the same response for the same input."""
    
    def __init__(self, model_name: str = "deterministic-mock"):
        """Initialize deterministic provider."""
        super().__init__(model_name)
        self.response_cache: Dict[str, MockLLMResponse] = {}
    
    def generate_response(self, 
                         prompt: str, 
                         context: Optional[Dict[str, Any]] = None) -> MockLLMResponse:
        """Generate deterministic response based on prompt hash.
        
        Args:
            prompt: User prompt
            context: Optional context
            
        Returns:
            Deterministic mock response
        """
        # Create deterministic key from prompt and context
        key = self._create_cache_key(prompt, context)
        
        if key in self.response_cache:
            # Return cached response
            cached_response = self.response_cache[key]
            # Update call history
            with self._lock:
                self.call_history.append({
                    "timestamp": time.time(),
                    "prompt": prompt,
                    "context": context,
                    "model": self.model_name,
                    "cached": True
                })
            return cached_response
        
        # Generate new response and cache it
        response = super().generate_response(prompt, context)
        self.response_cache[key] = response
        return response
    
    def _create_cache_key(self, prompt: str, context: Optional[Dict[str, Any]]) -> str:
        """Create deterministic cache key.
        
        Args:
            prompt: User prompt
            context: Optional context
            
        Returns:
            Cache key string
        """
        # Create hash of prompt and context
        content = prompt
        if context:
            content += json.dumps(context, sort_keys=True)
        
        return hashlib.sha256(content.encode()).hexdigest()


class ErrorSimulatingLLMProvider(MockLLMProvider):
    """LLM provider that simulates various error conditions."""
    
    def __init__(self, model_name: str = "error-mock"):
        """Initialize error simulating provider."""
        super().__init__(model_name)
        self.error_probability: float = 0.0
        self.error_sequence: List[LLMErrorType] = []
        self.current_error_index: int = 0
    
    def set_error_probability(self, probability: float):
        """Set probability of errors occurring.
        
        Args:
            probability: Error probability (0.0 to 1.0)
        """
        self.error_probability = max(0.0, min(1.0, probability))
    
    def set_error_sequence(self, errors: List[LLMErrorType]):
        """Set sequence of errors to cycle through.
        
        Args:
            errors: List of error types to cycle through
        """
        self.error_sequence = errors
        self.current_error_index = 0
    
    def generate_response(self, 
                         prompt: str, 
                         context: Optional[Dict[str, Any]] = None) -> MockLLMResponse:
        """Generate response with potential errors.
        
        Args:
            prompt: User prompt
            context: Optional context
            
        Returns:
            Mock response or raises error
        """
        # Check if we should simulate an error
        should_error = False
        
        if self.error_simulation is not None:
            # Error simulation is explicitly enabled
            should_error = True
        elif self.error_sequence:
            # Use error sequence
            self.error_simulation = self.error_sequence[self.current_error_index]
            self.current_error_index = (self.current_error_index + 1) % len(self.error_sequence)
            should_error = True
        elif self.error_probability > 0:
            # Use random probability
            should_error = random.random() < self.error_probability
            if should_error:
                # Pick random error type
                self.error_simulation = random.choice(list(LLMErrorType))
        
        if should_error:
            return super().generate_response(prompt, context)  # Will raise error
        else:
            # Temporarily disable error simulation for this call
            old_error = self.error_simulation
            self.error_simulation = None
            response = super().generate_response(prompt, context)
            self.error_simulation = old_error
            return response


class RateLimitedLLMProvider(MockLLMProvider):
    """LLM provider that simulates rate limiting."""
    
    def __init__(self, model_name: str = "rate-limited-mock", requests_per_minute: int = 60):
        """Initialize rate limited provider.
        
        Args:
            model_name: Model name
            requests_per_minute: Rate limit
        """
        super().__init__(model_name)
        self.requests_per_minute = requests_per_minute
        self.request_times: List[float] = []
    
    def generate_response(self, 
                         prompt: str, 
                         context: Optional[Dict[str, Any]] = None) -> MockLLMResponse:
        """Generate response with rate limiting.
        
        Args:
            prompt: User prompt
            context: Optional context
            
        Returns:
            Mock response
            
        Raises:
            Exception: If rate limit exceeded
        """
        current_time = time.time()
        
        # Clean old requests (older than 1 minute)
        cutoff_time = current_time - 60.0
        self.request_times = [t for t in self.request_times if t > cutoff_time]
        
        # Check rate limit
        if len(self.request_times) >= self.requests_per_minute:
            raise Exception("RateLimitError: Rate limit exceeded")
        
        # Record request time
        self.request_times.append(current_time)
        
        return super().generate_response(prompt, context)


class TokenTrackingLLMProvider(MockLLMProvider):
    """LLM provider that tracks detailed token usage."""
    
    def __init__(self, model_name: str = "token-tracking-mock"):
        """Initialize token tracking provider."""
        super().__init__(model_name)
        self.detailed_usage: List[Dict[str, Any]] = []
        self.cost_per_token = {"input": 0.0001, "output": 0.0002}  # Mock pricing
    
    def generate_response(self, 
                         prompt: str, 
                         context: Optional[Dict[str, Any]] = None) -> MockLLMResponse:
        """Generate response with detailed token tracking.
        
        Args:
            prompt: User prompt
            context: Optional context
            
        Returns:
            Mock response with detailed usage
        """
        response = super().generate_response(prompt, context)
        
        # Record detailed usage
        usage_record = {
            "timestamp": time.time(),
            "prompt_length": len(prompt),
            "response_length": len(response.content),
            "input_tokens": response.usage.get("input_tokens", 0),
            "output_tokens": response.usage.get("output_tokens", 0),
            "total_tokens": response.usage.get("total_tokens", 0),
            "estimated_cost": self._calculate_cost(response.usage),
            "model": self.model_name
        }
        
        self.detailed_usage.append(usage_record)
        
        return response
    
    def _calculate_cost(self, usage: Dict[str, int]) -> float:
        """Calculate estimated cost for token usage.
        
        Args:
            usage: Token usage dictionary
            
        Returns:
            Estimated cost in dollars
        """
        input_cost = usage.get("input_tokens", 0) * self.cost_per_token["input"]
        output_cost = usage.get("output_tokens", 0) * self.cost_per_token["output"]
        return input_cost + output_cost
    
    def get_cost_summary(self) -> Dict[str, float]:
        """Get cost summary.
        
        Returns:
            Cost summary dictionary
        """
        total_cost = sum(record["estimated_cost"] for record in self.detailed_usage)
        total_tokens = sum(record["total_tokens"] for record in self.detailed_usage)
        
        return {
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "average_cost_per_token": total_cost / total_tokens if total_tokens > 0 else 0,
            "num_requests": len(self.detailed_usage)
        }


def create_mock_llm_provider(provider_type: str = "standard", **kwargs) -> MockLLMProvider:
    """Factory function to create mock LLM providers.
    
    Args:
        provider_type: Type of provider to create
        **kwargs: Additional arguments for provider
        
    Returns:
        Mock LLM provider instance
    """
    providers = {
        "standard": MockLLMProvider,
        "deterministic": DeterministicLLMProvider,
        "error_simulating": ErrorSimulatingLLMProvider,
        "rate_limited": RateLimitedLLMProvider,
        "token_tracking": TokenTrackingLLMProvider
    }
    
    if provider_type not in providers:
        raise ValueError(f"Unknown provider type: {provider_type}")
    
    return providers[provider_type](**kwargs)


# Pre-configured scenarios for common testing patterns
def get_code_analysis_scenarios() -> List[LLMResponseScenario]:
    """Get scenarios for code analysis testing."""
    scenarios = []
    
    # File reading scenario
    scenarios.append(LLMResponseScenario(
        name="file_reading",
        pattern=re.compile(r"read.*file", re.IGNORECASE),
        response=MockLLMResponse(
            content="I'll read the file for you.",
            tool_calls=[{
                "name": "read",
                "parameters": {"action": "read_file", "path": "example.py"}
            }],
            usage={"input_tokens": 20, "output_tokens": 10}
        ),
        priority=10
    ))
    
    # Code modification scenario
    scenarios.append(LLMResponseScenario(
        name="code_modification",
        pattern=re.compile(r"(modify|change|update).*code", re.IGNORECASE),
        response=MockLLMResponse(
            content="I'll modify the code as requested.",
            tool_calls=[{
                "name": "update",
                "parameters": {
                    "action": "update_lines",
                    "path": "example.py",
                    "start_line": 5,
                    "end_line": 10,
                    "new_content": "# Updated code here"
                }
            }],
            usage={"input_tokens": 30, "output_tokens": 15}
        ),
        priority=20
    ))
    
    return scenarios


def get_security_testing_scenarios() -> List[LLMResponseScenario]:
    """Get scenarios for security testing."""
    scenarios = []
    
    # Security violation detection
    scenarios.append(LLMResponseScenario(
        name="security_violation",
        pattern=re.compile(r"(\.\.\/|\/etc\/|rm -rf|sudo)", re.IGNORECASE),
        response=MockLLMResponse(
            content="I cannot help with that request as it appears to involve potentially unsafe operations.",
            tool_calls=[],
            usage={"input_tokens": 25, "output_tokens": 20},
            finish_reason="content_filter"
        ),
        priority=1  # Highest priority
    ))
    
    return scenarios


@pytest.fixture
def mock_llm_provider():
    """Provide a standard mock LLM provider for testing."""
    provider = MockLLMProvider("test-mock-gpt-4")
    yield provider
    provider.reset()


@pytest.fixture
def deterministic_llm_provider():
    """Provide a deterministic mock LLM provider for testing."""
    provider = DeterministicLLMProvider("test-deterministic-mock")
    yield provider
    provider.reset()


@pytest.fixture
def code_analysis_llm_provider():
    """Provide an LLM provider configured for code analysis testing."""
    provider = MockLLMProvider("code-analysis-mock")
    
    # Add code analysis scenarios
    for scenario in get_code_analysis_scenarios():
        provider.add_scenario(scenario)
    
    yield provider
    provider.reset()


@pytest.fixture
def security_aware_llm_provider():
    """Provide an LLM provider configured for security testing."""
    provider = MockLLMProvider("security-aware-mock")
    
    # Add security scenarios
    for scenario in get_security_testing_scenarios():
        provider.add_scenario(scenario)
    
    yield provider
    provider.reset()