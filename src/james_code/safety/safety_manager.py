"""Safety manager for enforcing security constraints."""

import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field

from ..core.base import ExecutionContext, ToolResult


@dataclass
class SafetyConfig:
    """Configuration for safety constraints."""
    base_directory: str
    allowed_directories: List[str] = field(default_factory=list)
    blocked_commands: List[str] = field(default_factory=lambda: [
        "rm", "rmdir", "del", "format", "fdisk", "mkfs",
        "sudo", "su", "passwd", "chmod", "chown",
        "wget", "curl", "ssh", "scp", "rsync",
        "docker", "podman", "systemctl", "service"
    ])
    allowed_commands: List[str] = field(default_factory=list)
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    max_output_size: int = 1024 * 1024  # 1MB
    default_timeout: int = 30
    max_timeout: int = 300
    enable_audit_logging: bool = True
    strict_mode: bool = False


@dataclass
class SecurityViolation:
    """Record of a security violation."""
    timestamp: float
    violation_type: str
    description: str
    context: Dict[str, Any]
    severity: str  # 'low', 'medium', 'high', 'critical'


class SafetyManager:
    """Manages security constraints and auditing."""
    
    def __init__(self, config: SafetyConfig):
        self.config = config
        self.base_dir = Path(config.base_directory).resolve()
        self.violations: List[SecurityViolation] = []
        self.logger = logging.getLogger(__name__)
        
        # Set up audit logging
        if config.enable_audit_logging:
            self._setup_audit_logging()
    
    def _setup_audit_logging(self):
        """Set up audit logging."""
        audit_handler = logging.FileHandler(self.base_dir / "security_audit.log")
        audit_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        audit_handler.setFormatter(formatter)
        self.logger.addHandler(audit_handler)
        self.logger.setLevel(logging.INFO)
    
    def validate_path(self, path: str, context: ExecutionContext) -> ToolResult:
        """Validate that a path is within allowed directories."""
        try:
            target_path = Path(context.working_directory) / path
            target_path = target_path.resolve()
            
            # Check against base directory
            if not str(target_path).startswith(str(self.base_dir)):
                violation = SecurityViolation(
                    timestamp=time.time(),
                    violation_type="path_traversal",
                    description=f"Path outside base directory: {target_path}",
                    context={"path": str(target_path), "base_dir": str(self.base_dir)},
                    severity="high"
                )
                self._record_violation(violation)
                
                return ToolResult(
                    success=False,
                    data=None,
                    error="Path outside allowed directory"
                )
            
            # Check against additional allowed directories if configured
            if self.config.allowed_directories:
                allowed = False
                for allowed_dir in self.config.allowed_directories:
                    allowed_path = Path(allowed_dir).resolve()
                    if str(target_path).startswith(str(allowed_path)):
                        allowed = True
                        break
                
                if not allowed:
                    violation = SecurityViolation(
                        timestamp=time.time(),
                        violation_type="path_not_allowed",
                        description=f"Path not in allowed directories: {target_path}",
                        context={"path": str(target_path), "allowed_dirs": self.config.allowed_directories},
                        severity="medium"
                    )
                    self._record_violation(violation)
                    
                    return ToolResult(
                        success=False,
                        data=None,
                        error="Path not in allowed directories"
                    )
            
            self.logger.info(f"Path validated: {target_path}")
            return ToolResult(success=True, data=str(target_path))
            
        except Exception as e:
            violation = SecurityViolation(
                timestamp=time.time(),
                violation_type="path_validation_error",
                description=f"Error validating path: {str(e)}",
                context={"path": path, "error": str(e)},
                severity="medium"
            )
            self._record_violation(violation)
            
            return ToolResult(
                success=False,
                data=None,
                error=f"Error validating path: {str(e)}"
            )
    
    def validate_command(self, command: str) -> ToolResult:
        """Validate that a command is safe to execute."""
        try:
            command_lower = command.lower().strip()
            
            # Check for blocked commands
            for blocked in self.config.blocked_commands:
                if command_lower.startswith(blocked.lower()):
                    violation = SecurityViolation(
                        timestamp=time.time(),
                        violation_type="blocked_command",
                        description=f"Blocked command attempted: {blocked}",
                        context={"command": command, "blocked_command": blocked},
                        severity="high"
                    )
                    self._record_violation(violation)
                    
                    return ToolResult(
                        success=False,
                        data=None,
                        error=f"Command blocked for security: {blocked}"
                    )
            
            # If allow list is defined, check against it
            if self.config.allowed_commands:
                command_base = command_lower.split()[0] if command_lower.split() else ""
                if command_base not in [cmd.lower() for cmd in self.config.allowed_commands]:
                    violation = SecurityViolation(
                        timestamp=time.time(),
                        violation_type="command_not_allowed",
                        description=f"Command not in allowed list: {command_base}",
                        context={"command": command, "command_base": command_base},
                        severity="medium"
                    )
                    self._record_violation(violation)
                    
                    return ToolResult(
                        success=False,
                        data=None,
                        error=f"Command not in allowed list: {command_base}"
                    )
            
            # Check for dangerous patterns
            dangerous_patterns = [
                "&&", "||", ";", "|", ">", ">>", "<",
                "$(", "`", "eval", "exec", "source", ".",
                "rm -rf", ":(){ :|:& };:"  # Fork bomb pattern
            ]
            
            for pattern in dangerous_patterns:
                if pattern in command_lower:
                    violation = SecurityViolation(
                        timestamp=time.time(),
                        violation_type="dangerous_pattern",
                        description=f"Dangerous pattern in command: {pattern}",
                        context={"command": command, "pattern": pattern},
                        severity="high"
                    )
                    self._record_violation(violation)
                    
                    return ToolResult(
                        success=False,
                        data=None,
                        error=f"Command contains dangerous pattern: {pattern}"
                    )
            
            self.logger.info(f"Command validated: {command}")
            return ToolResult(success=True, data=command)
            
        except Exception as e:
            violation = SecurityViolation(
                timestamp=time.time(),
                violation_type="command_validation_error",
                description=f"Error validating command: {str(e)}",
                context={"command": command, "error": str(e)},
                severity="medium"
            )
            self._record_violation(violation)
            
            return ToolResult(
                success=False,
                data=None,
                error=f"Error validating command: {str(e)}"
            )
    
    def validate_file_size(self, size: int, operation: str) -> ToolResult:
        """Validate file size against limits."""
        if size > self.config.max_file_size:
            violation = SecurityViolation(
                timestamp=time.time(),
                violation_type="file_size_exceeded",
                description=f"File size exceeded limit: {size} > {self.config.max_file_size}",
                context={"size": size, "limit": self.config.max_file_size, "operation": operation},
                severity="medium"
            )
            self._record_violation(violation)
            
            return ToolResult(
                success=False,
                data=None,
                error=f"File size exceeds limit ({self.config.max_file_size} bytes)"
            )
        
        return ToolResult(success=True, data=size)
    
    def validate_timeout(self, timeout: int) -> ToolResult:
        """Validate timeout value."""
        if timeout > self.config.max_timeout:
            violation = SecurityViolation(
                timestamp=time.time(),
                violation_type="timeout_exceeded",
                description=f"Timeout exceeded limit: {timeout} > {self.config.max_timeout}",
                context={"timeout": timeout, "limit": self.config.max_timeout},
                severity="low"
            )
            self._record_violation(violation)
            
            return ToolResult(
                success=False,
                data=None,
                error=f"Timeout exceeds limit ({self.config.max_timeout} seconds)"
            )
        
        return ToolResult(success=True, data=timeout)
    
    def execute_with_limits(self, func: Callable, *args, **kwargs) -> ToolResult:
        """Execute a function with resource limits."""
        try:
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            self.logger.info(f"Function executed: {func.__name__} in {execution_time:.2f}s")
            return result
            
        except Exception as e:
            violation = SecurityViolation(
                timestamp=time.time(),
                violation_type="execution_error",
                description=f"Error executing function: {str(e)}",
                context={"function": func.__name__, "error": str(e)},
                severity="medium"
            )
            self._record_violation(violation)
            
            return ToolResult(
                success=False,
                data=None,
                error=f"Error executing function: {str(e)}"
            )
    
    def _record_violation(self, violation: SecurityViolation):
        """Record a security violation."""
        self.violations.append(violation)
        self.logger.warning(f"Security violation: {violation.violation_type} - {violation.description}")
        
        # In strict mode, raise an exception for high/critical violations
        if self.config.strict_mode and violation.severity in ["high", "critical"]:
            raise SecurityError(f"Security violation: {violation.description}")
    
    def get_violations(self, severity: Optional[str] = None) -> List[SecurityViolation]:
        """Get recorded violations, optionally filtered by severity."""
        if severity:
            return [v for v in self.violations if v.severity == severity]
        return self.violations.copy()
    
    def clear_violations(self):
        """Clear recorded violations."""
        self.violations.clear()
    
    def get_security_summary(self) -> Dict[str, Any]:
        """Get a summary of security status."""
        return {
            "total_violations": len(self.violations),
            "violations_by_severity": {
                severity: len([v for v in self.violations if v.severity == severity])
                for severity in ["low", "medium", "high", "critical"]
            },
            "violations_by_type": {
                violation_type: len([v for v in self.violations if v.violation_type == violation_type])
                for violation_type in set(v.violation_type for v in self.violations)
            },
            "config": {
                "base_directory": str(self.base_dir),
                "strict_mode": self.config.strict_mode,
                "audit_logging": self.config.enable_audit_logging
            }
        }


class SecurityError(Exception):
    """Exception raised for security violations in strict mode."""
    pass