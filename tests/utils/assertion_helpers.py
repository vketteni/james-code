"""Assertion helper utilities for testing."""

import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import re

import pytest

from james_code.core.base import ToolResult, ExecutionContext


def assert_tool_result_valid(result: ToolResult, 
                           expected_success: bool = True,
                           required_metadata_keys: Optional[List[str]] = None):
    """Assert that a tool result is valid and meets expectations.
    
    Args:
        result: Tool result to validate
        expected_success: Whether the operation should have succeeded
        required_metadata_keys: Keys that must be present in metadata
        
    Raises:
        AssertionError: If result is invalid
    """
    # Check basic structure
    assert isinstance(result, ToolResult), f"Expected ToolResult, got {type(result)}"
    assert isinstance(result.success, bool), "ToolResult.success must be boolean"
    
    # Check success/failure expectation
    if expected_success:
        assert result.success, f"Expected success but got failure: {result.error}"
        assert result.data is not None, "Successful result should have data"
    else:
        assert not result.success, f"Expected failure but got success with data: {result.data}"
        assert result.error is not None, "Failed result should have error message"
        assert isinstance(result.error, str), "Error message must be string"
        assert len(result.error.strip()) > 0, "Error message cannot be empty"
    
    # Check metadata
    assert result.metadata is not None, "Metadata cannot be None"
    assert isinstance(result.metadata, dict), "Metadata must be dictionary"
    
    if required_metadata_keys:
        for key in required_metadata_keys:
            assert key in result.metadata, f"Required metadata key missing: {key}"


def assert_security_violation(result: ToolResult, 
                            expected_violation_type: Optional[str] = None):
    """Assert that a security violation was properly detected and handled.
    
    Args:
        result: Tool result to check
        expected_violation_type: Expected type of security violation
        
    Raises:
        AssertionError: If security violation not properly handled
    """
    # Operation should have failed
    assert not result.success, "Security violation should cause operation to fail"
    assert result.error is not None, "Security violation should have error message"
    
    # Check for security-related keywords in error
    error_lower = result.error.lower()
    security_keywords = [
        "security", "violation", "blocked", "unauthorized", "permission",
        "access denied", "outside working directory", "path traversal",
        "command injection", "dangerous", "not allowed"
    ]
    
    has_security_keyword = any(keyword in error_lower for keyword in security_keywords)
    assert has_security_keyword, f"Error message should indicate security issue: {result.error}"
    
    # Check for specific violation type if provided
    if expected_violation_type:
        violation_patterns = {
            "path_traversal": ["path traversal", "outside working directory", "invalid path"],
            "command_injection": ["command injection", "dangerous command", "not allowed"],
            "permission_denied": ["permission", "access denied", "unauthorized"],
            "resource_limit": ["resource limit", "too large", "exceeds limit"]
        }
        
        if expected_violation_type in violation_patterns:
            patterns = violation_patterns[expected_violation_type]
            has_specific_pattern = any(pattern in error_lower for pattern in patterns)
            assert has_specific_pattern, \
                f"Error should indicate {expected_violation_type}: {result.error}"


def assert_performance_within_limits(execution_time: float,
                                    memory_usage: Optional[float] = None,
                                    max_time: float = 1.0,
                                    max_memory_mb: float = 100.0):
    """Assert that performance metrics are within acceptable limits.
    
    Args:
        execution_time: Execution time in seconds
        memory_usage: Memory usage in MB (optional)
        max_time: Maximum allowed execution time
        max_memory_mb: Maximum allowed memory usage
        
    Raises:
        AssertionError: If performance limits exceeded
    """
    assert execution_time <= max_time, \
        f"Execution time exceeded limit: {execution_time:.3f}s > {max_time}s"
    
    if memory_usage is not None:
        assert memory_usage <= max_memory_mb, \
            f"Memory usage exceeded limit: {memory_usage:.2f}MB > {max_memory_mb}MB"


def assert_no_data_leakage(result: ToolResult, 
                         sensitive_patterns: Optional[List[str]] = None):
    """Assert that no sensitive data leaked in result.
    
    Args:
        result: Tool result to check
        sensitive_patterns: Patterns that should not appear in output
        
    Raises:
        AssertionError: If sensitive data detected
    """
    default_patterns = [
        r"password[:\s]*\w+",
        r"api[_-]?key[:\s]*\w+",
        r"secret[:\s]*\w+",
        r"token[:\s]*\w+",
        r"private[_-]?key",
        r"-----BEGIN .* PRIVATE KEY-----",
        r"[A-Za-z0-9+/]{40,}={0,2}",  # Base64 patterns
        r"\b[A-Fa-f0-9]{32}\b",       # MD5 hashes
        r"\b[A-Fa-f0-9]{40}\b",       # SHA1 hashes
        r"\b[A-Fa-f0-9]{64}\b",       # SHA256 hashes
    ]
    
    patterns = (sensitive_patterns or []) + default_patterns
    
    # Check result data
    if result.data and isinstance(result.data, str):
        for pattern in patterns:
            matches = re.findall(pattern, result.data, re.IGNORECASE)
            assert not matches, f"Sensitive data pattern found in result data: {pattern}"
    
    # Check error message
    if result.error:
        for pattern in patterns:
            matches = re.findall(pattern, result.error, re.IGNORECASE)
            assert not matches, f"Sensitive data pattern found in error message: {pattern}"
    
    # Check metadata
    metadata_str = str(result.metadata)
    for pattern in patterns:
        matches = re.findall(pattern, metadata_str, re.IGNORECASE)
        assert not matches, f"Sensitive data pattern found in metadata: {pattern}"


def assert_file_operation_safe(file_path: Path, 
                             base_directory: Path,
                             operation_type: str = "unknown"):
    """Assert that a file operation is safe (within allowed boundaries).
    
    Args:
        file_path: Path of file operation
        base_directory: Base directory that operations should be confined to
        operation_type: Type of operation for error messages
        
    Raises:
        AssertionError: If file operation is unsafe
    """
    try:
        # Resolve paths to handle symlinks and relative paths
        resolved_file = file_path.resolve()
        resolved_base = base_directory.resolve()
        
        # Check if file path is within base directory
        resolved_file.relative_to(resolved_base)
        
    except ValueError:
        raise AssertionError(
            f"Unsafe {operation_type} operation: {file_path} is outside base directory {base_directory}"
        )


def assert_command_safe(command: str, 
                       allowed_commands: Optional[List[str]] = None):
    """Assert that a command is safe to execute.
    
    Args:
        command: Command to validate
        allowed_commands: List of allowed command prefixes
        
    Raises:
        AssertionError: If command is unsafe
    """
    # Check for empty command
    assert command and command.strip(), "Command cannot be empty"
    
    # Check against allowed commands if provided
    if allowed_commands:
        command_parts = command.split()
        base_command = command_parts[0] if command_parts else ""
        
        is_allowed = any(base_command.startswith(allowed) for allowed in allowed_commands)
        assert is_allowed, f"Command not in allowed list: {base_command}"
    
    # Check for dangerous patterns
    dangerous_patterns = [
        'rm -rf', 'format', 'mkfs', 'dd if=', '>/dev/',
        'chmod 777', 'sudo', 'su -', 'nc -l'
    ]
    
    command_lower = command.lower()
    for pattern in dangerous_patterns:
        assert pattern not in command_lower, f"Dangerous command pattern detected: {pattern}"
    
    # Check for command injection patterns
    injection_patterns = ['$()', '`', '&&', '||', ';', '|']
    for pattern in injection_patterns:
        assert pattern not in command, f"Command injection pattern detected: {pattern}"


def assert_no_resource_leaks(initial_state: Dict[str, Any], 
                           final_state: Dict[str, Any],
                           tolerance: Dict[str, Any] = None):
    """Assert that no significant resource leaks occurred.
    
    Args:
        initial_state: Resource state before operation
        final_state: Resource state after operation
        tolerance: Acceptable differences in resource usage
        
    Raises:
        AssertionError: If resource leaks detected
    """
    default_tolerance = {
        'memory_mb': 10.0,      # 10MB tolerance
        'open_files': 5,        # 5 file descriptors tolerance
        'processes': 2          # 2 process tolerance
    }
    
    tolerance = tolerance or default_tolerance
    
    # Check memory usage
    if 'memory_mb' in initial_state and 'memory_mb' in final_state:
        memory_diff = final_state['memory_mb'] - initial_state['memory_mb']
        assert memory_diff <= tolerance['memory_mb'], \
            f"Memory leak detected: {memory_diff:.2f}MB increase"
    
    # Check open files
    if 'open_files' in initial_state and 'open_files' in final_state:
        files_diff = final_state['open_files'] - initial_state['open_files']
        assert files_diff <= tolerance['open_files'], \
            f"File descriptor leak detected: {files_diff} files not closed"
    
    # Check processes
    if 'processes' in initial_state and 'processes' in final_state:
        proc_diff = final_state['processes'] - initial_state['processes']
        assert proc_diff <= tolerance['processes'], \
            f"Process leak detected: {proc_diff} processes not terminated"


def assert_operation_atomic(operation_result: ToolResult, 
                          side_effects_check: callable):
    """Assert that an operation was atomic (all-or-nothing).
    
    Args:
        operation_result: Result of the operation
        side_effects_check: Function to check for side effects
        
    Raises:
        AssertionError: If operation was not atomic
    """
    if operation_result.success:
        # Operation succeeded - side effects should be present
        side_effects = side_effects_check()
        assert side_effects, "Successful operation should have side effects"
    else:
        # Operation failed - no side effects should be present
        side_effects = side_effects_check()
        assert not side_effects, "Failed operation should not have side effects"


def assert_error_handling_consistent(results: List[ToolResult]):
    """Assert that error handling is consistent across multiple results.
    
    Args:
        results: List of tool results to check
        
    Raises:
        AssertionError: If error handling is inconsistent
    """
    assert len(results) > 0, "Cannot check consistency with empty results"
    
    # Check that all failed results have error messages
    for i, result in enumerate(results):
        if not result.success:
            assert result.error is not None, f"Result {i}: Failed operation missing error message"
            assert isinstance(result.error, str), f"Result {i}: Error message not string"
            assert len(result.error.strip()) > 0, f"Result {i}: Empty error message"
    
    # Check that successful results don't have error messages
    for i, result in enumerate(results):
        if result.success:
            if result.error is not None:
                assert result.error == "", f"Result {i}: Successful operation has error message"


def assert_metadata_complete(result: ToolResult, 
                           expected_keys: List[str],
                           operation_type: str = "operation"):
    """Assert that result metadata contains all expected information.
    
    Args:
        result: Tool result to check
        expected_keys: Keys that should be present in metadata
        operation_type: Type of operation for error messages
        
    Raises:
        AssertionError: If metadata is incomplete
    """
    assert result.metadata is not None, f"{operation_type} result missing metadata"
    assert isinstance(result.metadata, dict), f"{operation_type} metadata not dictionary"
    
    for key in expected_keys:
        assert key in result.metadata, f"{operation_type} metadata missing key: {key}"
        assert result.metadata[key] is not None, f"{operation_type} metadata key {key} is None"


def assert_audit_trail_complete(audit_events: List[Dict[str, Any]], 
                               expected_operations: List[str]):
    """Assert that audit trail contains all expected operations.
    
    Args:
        audit_events: List of audit events
        expected_operations: Operations that should be audited
        
    Raises:
        AssertionError: If audit trail is incomplete
    """
    assert len(audit_events) >= len(expected_operations), \
        f"Insufficient audit events: {len(audit_events)} < {len(expected_operations)}"
    
    audited_operations = [event.get('operation', '') for event in audit_events]
    
    for operation in expected_operations:
        assert operation in audited_operations, f"Operation not audited: {operation}"


def assert_timing_reasonable(start_time: float, 
                           end_time: float,
                           min_time: float = 0.0,
                           max_time: float = 30.0):
    """Assert that operation timing is reasonable.
    
    Args:
        start_time: Operation start timestamp
        end_time: Operation end timestamp
        min_time: Minimum expected duration
        max_time: Maximum expected duration
        
    Raises:
        AssertionError: If timing is unreasonable
    """
    duration = end_time - start_time
    
    assert duration >= min_time, f"Operation too fast: {duration:.3f}s < {min_time}s"
    assert duration <= max_time, f"Operation too slow: {duration:.3f}s > {max_time}s"
    assert start_time <= end_time, f"Invalid timing: start {start_time} > end {end_time}"


class TestResultValidator:
    """Comprehensive validator for test results."""
    
    def __init__(self, strict_mode: bool = True):
        """Initialize validator.
        
        Args:
            strict_mode: Whether to apply strict validation rules
        """
        self.strict_mode = strict_mode
        self.validation_errors: List[str] = []
    
    def validate_result(self, result: ToolResult, context: Dict[str, Any]) -> bool:
        """Validate a tool result comprehensively.
        
        Args:
            result: Tool result to validate
            context: Validation context
            
        Returns:
            True if validation passed
        """
        self.validation_errors.clear()
        
        try:
            # Basic structure validation
            assert_tool_result_valid(result)
            
            # Security validation if expected
            if context.get('expect_security_violation'):
                assert_security_violation(result, context.get('violation_type'))
            
            # Performance validation if limits provided
            if 'execution_time' in context:
                assert_performance_within_limits(
                    context['execution_time'],
                    context.get('memory_usage'),
                    context.get('max_time', 1.0),
                    context.get('max_memory_mb', 100.0)
                )
            
            # Data leakage check
            assert_no_data_leakage(result, context.get('sensitive_patterns'))
            
            # Metadata completeness
            if 'required_metadata' in context:
                assert_metadata_complete(result, context['required_metadata'])
            
            return True
            
        except AssertionError as e:
            self.validation_errors.append(str(e))
            if self.strict_mode:
                raise
            return False
    
    def get_validation_errors(self) -> List[str]:
        """Get list of validation errors.
        
        Returns:
            List of validation error messages
        """
        return self.validation_errors.copy()


@pytest.fixture
def result_validator():
    """Provide a test result validator."""
    return TestResultValidator()