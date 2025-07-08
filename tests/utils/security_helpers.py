"""Security testing helper utilities."""

import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass

import pytest

from james_code.core.base import ToolResult, ExecutionContext
from james_code.safety import SafetyManager


@dataclass
class SecurityTestResult:
    """Result of a security test."""
    attack_type: str
    payload: str
    blocked: bool
    error_message: Optional[str] = None
    execution_time: float = 0.0
    detected_by: Optional[str] = None
    metadata: Dict[str, Any] = None


class SecurityTestHelper:
    """Helper class for security testing operations."""
    
    def __init__(self, safety_manager: SafetyManager, logger: Optional[logging.Logger] = None):
        """Initialize security test helper.
        
        Args:
            safety_manager: SafetyManager instance to test
            logger: Optional logger for test operations
        """
        self.safety_manager = safety_manager
        self.logger = logger or logging.getLogger(__name__)
        self.attack_history: List[SecurityTestResult] = []
    
    def test_path_traversal(self, paths: List[str], context: ExecutionContext) -> List[SecurityTestResult]:
        """Test path traversal attack prevention.
        
        Args:
            paths: List of malicious paths to test
            context: Execution context for testing
            
        Returns:
            List of test results
        """
        results = []
        
        for path in paths:
            start_time = time.time()
            
            try:
                # Test path validation
                is_valid = self.safety_manager.validate_path(path)
                execution_time = time.time() - start_time
                
                result = SecurityTestResult(
                    attack_type="path_traversal",
                    payload=path,
                    blocked=not is_valid,
                    execution_time=execution_time,
                    detected_by="SafetyManager.validate_path" if not is_valid else None
                )
                
                if not is_valid:
                    result.error_message = f"Path validation failed for: {path}"
                    self.logger.info(f"✓ Blocked path traversal: {path}")
                else:
                    self.logger.warning(f"✗ Path traversal not blocked: {path}")
                    
            except Exception as e:
                execution_time = time.time() - start_time
                result = SecurityTestResult(
                    attack_type="path_traversal",
                    payload=path,
                    blocked=True,
                    error_message=str(e),
                    execution_time=execution_time,
                    detected_by="Exception handler"
                )
                self.logger.info(f"✓ Path traversal blocked by exception: {path}")
            
            results.append(result)
            self.attack_history.append(result)
        
        return results
    
    def test_command_injection(self, commands: List[str], context: ExecutionContext) -> List[SecurityTestResult]:
        """Test command injection attack prevention.
        
        Args:
            commands: List of malicious commands to test
            context: Execution context for testing
            
        Returns:
            List of test results
        """
        results = []
        
        for command in commands:
            start_time = time.time()
            
            try:
                # Test command validation
                is_valid = self.safety_manager.validate_command(command)
                execution_time = time.time() - start_time
                
                result = SecurityTestResult(
                    attack_type="command_injection",
                    payload=command,
                    blocked=not is_valid,
                    execution_time=execution_time,
                    detected_by="SafetyManager.validate_command" if not is_valid else None
                )
                
                if not is_valid:
                    result.error_message = f"Command validation failed for: {command}"
                    self.logger.info(f"✓ Blocked command injection: {command}")
                else:
                    self.logger.warning(f"✗ Command injection not blocked: {command}")
                    
            except Exception as e:
                execution_time = time.time() - start_time
                result = SecurityTestResult(
                    attack_type="command_injection",
                    payload=command,
                    blocked=True,
                    error_message=str(e),
                    execution_time=execution_time,
                    detected_by="Exception handler"
                )
                self.logger.info(f"✓ Command injection blocked by exception: {command}")
            
            results.append(result)
            self.attack_history.append(result)
        
        return results
    
    def test_resource_exhaustion(self, payloads: List[str], context: ExecutionContext) -> List[SecurityTestResult]:
        """Test resource exhaustion attack prevention.
        
        Args:
            payloads: List of resource exhaustion payloads
            context: Execution context for testing
            
        Returns:
            List of test results
        """
        results = []
        
        for payload in payloads:
            start_time = time.time()
            
            try:
                # Test resource limits
                if len(payload) > self.safety_manager.config.max_input_size:
                    blocked = True
                    error_message = f"Payload exceeds max input size: {len(payload)} bytes"
                    detected_by = "SafetyManager.max_input_size"
                else:
                    blocked = False
                    error_message = None
                    detected_by = None
                
                execution_time = time.time() - start_time
                
                result = SecurityTestResult(
                    attack_type="resource_exhaustion",
                    payload=payload[:100] + "..." if len(payload) > 100 else payload,
                    blocked=blocked,
                    error_message=error_message,
                    execution_time=execution_time,
                    detected_by=detected_by,
                    metadata={"payload_size": len(payload)}
                )
                
                if blocked:
                    self.logger.info(f"✓ Blocked resource exhaustion: {len(payload)} bytes")
                else:
                    self.logger.warning(f"✗ Resource exhaustion not blocked: {len(payload)} bytes")
                    
            except Exception as e:
                execution_time = time.time() - start_time
                result = SecurityTestResult(
                    attack_type="resource_exhaustion",
                    payload=payload[:100] + "..." if len(payload) > 100 else payload,
                    blocked=True,
                    error_message=str(e),
                    execution_time=execution_time,
                    detected_by="Exception handler",
                    metadata={"payload_size": len(payload)}
                )
                self.logger.info(f"✓ Resource exhaustion blocked by exception: {len(payload)} bytes")
            
            results.append(result)
            self.attack_history.append(result)
        
        return results
    
    def get_attack_summary(self) -> Dict[str, Any]:
        """Get summary of all attack tests performed.
        
        Returns:
            Summary statistics of attack tests
        """
        if not self.attack_history:
            return {"total_attacks": 0, "blocked": 0, "success_rate": 0.0}
        
        total_attacks = len(self.attack_history)
        blocked_attacks = sum(1 for result in self.attack_history if result.blocked)
        success_rate = (blocked_attacks / total_attacks) * 100
        
        attack_types = {}
        for result in self.attack_history:
            if result.attack_type not in attack_types:
                attack_types[result.attack_type] = {"total": 0, "blocked": 0}
            attack_types[result.attack_type]["total"] += 1
            if result.blocked:
                attack_types[result.attack_type]["blocked"] += 1
        
        avg_execution_time = sum(result.execution_time for result in self.attack_history) / total_attacks
        
        return {
            "total_attacks": total_attacks,
            "blocked_attacks": blocked_attacks,
            "unblocked_attacks": total_attacks - blocked_attacks,
            "success_rate": success_rate,
            "attack_types": attack_types,
            "average_execution_time": avg_execution_time,
            "max_execution_time": max(result.execution_time for result in self.attack_history),
            "min_execution_time": min(result.execution_time for result in self.attack_history)
        }


def validate_security_boundary(tool_result: ToolResult, expected_blocked: bool = True) -> bool:
    """Validate that a security boundary was properly enforced.
    
    Args:
        tool_result: Result from tool execution
        expected_blocked: Whether the operation should have been blocked
        
    Returns:
        True if security boundary behaved as expected
    """
    if expected_blocked:
        # Operation should have been blocked
        if tool_result.success:
            return False  # Security failure - operation succeeded when it should have been blocked
        
        # Check for security-related error messages
        security_keywords = [
            "outside working directory",
            "path traversal",
            "command injection",
            "permission denied",
            "security violation",
            "blocked",
            "unauthorized"
        ]
        
        if tool_result.error:
            error_lower = tool_result.error.lower()
            return any(keyword in error_lower for keyword in security_keywords)
        
        return True  # Operation failed, which is expected for blocked operations
    else:
        # Operation should have succeeded
        return tool_result.success


def assert_attack_blocked(tool_result: ToolResult, attack_type: str):
    """Assert that an attack was properly blocked.
    
    Args:
        tool_result: Result from tool execution
        attack_type: Type of attack being tested
        
    Raises:
        AssertionError: If attack was not properly blocked
    """
    assert not tool_result.success, f"{attack_type} attack was not blocked"
    assert tool_result.error is not None, f"{attack_type} attack blocked but no error message provided"
    
    # Check for appropriate error message
    security_keywords = [
        "security",
        "blocked",
        "unauthorized",
        "permission",
        "invalid",
        "outside working directory"
    ]
    
    error_lower = tool_result.error.lower()
    assert any(keyword in error_lower for keyword in security_keywords), \
        f"{attack_type} attack blocked but error message doesn't indicate security issue: {tool_result.error}"


def simulate_attack(attack_type: str, payload: str, target_tool, context: ExecutionContext) -> SecurityTestResult:
    """Simulate a specific type of attack.
    
    Args:
        attack_type: Type of attack to simulate
        payload: Attack payload
        target_tool: Tool to test attack against
        context: Execution context
        
    Returns:
        Security test result
    """
    start_time = time.time()
    
    try:
        if attack_type == "path_traversal":
            result = target_tool.execute(context, action="read_file", path=payload)
        elif attack_type == "command_injection":
            result = target_tool.execute(context, command=payload)
        elif attack_type == "resource_exhaustion":
            result = target_tool.execute(context, content=payload)
        else:
            raise ValueError(f"Unknown attack type: {attack_type}")
        
        execution_time = time.time() - start_time
        
        return SecurityTestResult(
            attack_type=attack_type,
            payload=payload,
            blocked=not result.success,
            error_message=result.error,
            execution_time=execution_time,
            detected_by=target_tool.__class__.__name__ if not result.success else None
        )
        
    except Exception as e:
        execution_time = time.time() - start_time
        
        return SecurityTestResult(
            attack_type=attack_type,
            payload=payload,
            blocked=True,
            error_message=str(e),
            execution_time=execution_time,
            detected_by="Exception handler"
        )


def create_security_test_matrix(attack_vectors: Dict[str, List[str]], 
                              tools: List[Any]) -> List[Dict[str, Any]]:
    """Create a test matrix for security testing.
    
    Args:
        attack_vectors: Dictionary of attack types and their vectors
        tools: List of tools to test
        
    Returns:
        List of test cases to execute
    """
    test_matrix = []
    
    for attack_type, vectors in attack_vectors.items():
        for vector in vectors:
            for tool in tools:
                test_case = {
                    "attack_type": attack_type,
                    "payload": vector,
                    "tool": tool,
                    "expected_blocked": True,
                    "test_id": f"{attack_type}_{tool.__class__.__name__}_{hash(vector) % 10000}"
                }
                test_matrix.append(test_case)
    
    return test_matrix


class SecurityMonitor:
    """Monitor security events during testing."""
    
    def __init__(self):
        """Initialize security monitor."""
        self.events: List[Dict[str, Any]] = []
        self.violations: List[Dict[str, Any]] = []
    
    def log_event(self, event_type: str, details: Dict[str, Any]):
        """Log a security event.
        
        Args:
            event_type: Type of security event
            details: Event details
        """
        event = {
            "timestamp": time.time(),
            "type": event_type,
            "details": details
        }
        self.events.append(event)
        
        if event_type == "security_violation":
            self.violations.append(event)
    
    def get_violation_count(self) -> int:
        """Get total number of security violations.
        
        Returns:
            Number of violations detected
        """
        return len(self.violations)
    
    def get_events_by_type(self, event_type: str) -> List[Dict[str, Any]]:
        """Get events of a specific type.
        
        Args:
            event_type: Type of events to retrieve
            
        Returns:
            List of matching events
        """
        return [event for event in self.events if event["type"] == event_type]
    
    def clear(self):
        """Clear all logged events."""
        self.events.clear()
        self.violations.clear()


@pytest.fixture
def security_monitor():
    """Provide a security monitor for testing."""
    monitor = SecurityMonitor()
    yield monitor
    # Cleanup if needed
    monitor.clear()