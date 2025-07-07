"""EXECUTE tool for command execution."""

import subprocess
import signal
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from threading import Timer

from ..core.base import Tool, ToolResult, ExecutionContext


class ExecuteTool(Tool):
    """Tool for executing shell commands."""
    
    def __init__(self, allowed_commands: Optional[List[str]] = None, blocked_commands: Optional[List[str]] = None):
        super().__init__(
            name="execute",
            description="Execute shell commands"
        )
        self.allowed_commands = allowed_commands or []
        self.blocked_commands = blocked_commands or [
            "rm", "rmdir", "del", "format", "fdisk", "mkfs",
            "sudo", "su", "passwd", "chmod", "chown",
            "wget", "curl", "ssh", "scp", "rsync",
            "python", "pip", "npm", "node", "go", "cargo",
            "docker", "podman", "systemctl", "service"
        ]
    
    def validate_input(self, **kwargs) -> bool:
        """Validate input parameters."""
        command = kwargs.get("command")
        timeout = kwargs.get("timeout", 30)
        
        if not command or not isinstance(command, str):
            return False
        
        if not isinstance(timeout, (int, float)) or timeout <= 0 or timeout > 300:
            return False
        
        return True
    
    def execute(self, context: ExecutionContext, **kwargs) -> ToolResult:
        """Execute the command."""
        if not self.validate_input(**kwargs):
            return ToolResult(
                success=False,
                data=None,
                error="Invalid input parameters"
            )
        
        command = kwargs["command"]
        timeout = kwargs.get("timeout", 30)
        working_dir = kwargs.get("working_dir")
        
        try:
            # Security validation
            security_check = self._validate_command_security(command)
            if not security_check.success:
                return security_check
            
            # Determine working directory
            if working_dir:
                work_path = Path(context.working_directory) / working_dir
                work_path = work_path.resolve()
                
                # Security check: ensure working dir is within allowed directory
                if not str(work_path).startswith(str(context.working_directory.resolve())):
                    return ToolResult(
                        success=False,
                        data=None,
                        error="Working directory outside allowed path"
                    )
                
                if not work_path.exists() or not work_path.is_dir():
                    return ToolResult(
                        success=False,
                        data=None,
                        error=f"Working directory does not exist: {work_path}"
                    )
            else:
                work_path = context.working_directory
            
            # Execute command with timeout
            return self._execute_command(command, work_path, timeout, context.environment)
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error executing command: {str(e)}"
            )
    
    def _validate_command_security(self, command: str) -> ToolResult:
        """Validate command against security policies."""
        command_lower = command.lower().strip()
        
        # Check for blocked commands
        for blocked in self.blocked_commands:
            if command_lower.startswith(blocked.lower()):
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Command blocked for security: {blocked}"
                )
        
        # If allow list is defined, check against it
        if self.allowed_commands:
            command_base = command_lower.split()[0] if command_lower.split() else ""
            if command_base not in [cmd.lower() for cmd in self.allowed_commands]:
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
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Command contains dangerous pattern: {pattern}"
                )
        
        return ToolResult(success=True, data=None)
    
    def _execute_command(self, command: str, working_dir: Path, timeout: float, env: Dict[str, str]) -> ToolResult:
        """Execute the command with proper timeout and resource limits."""
        try:
            # Prepare environment
            exec_env = os.environ.copy()
            exec_env.update(env)
            
            # Start process
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(working_dir),
                env=exec_env,
                text=True,
                preexec_fn=os.setsid if os.name != 'nt' else None
            )
            
            # Set up timeout
            timer = Timer(timeout, self._kill_process, [process])
            timer.start()
            
            try:
                stdout, stderr = process.communicate()
                timer.cancel()
                
                # Check output size limits (1MB each)
                if len(stdout) > 1024 * 1024:
                    stdout = stdout[:1024 * 1024] + "\n[Output truncated - exceeded 1MB limit]"
                
                if len(stderr) > 1024 * 1024:
                    stderr = stderr[:1024 * 1024] + "\n[Error output truncated - exceeded 1MB limit]"
                
                return ToolResult(
                    success=process.returncode == 0,
                    data={
                        "stdout": stdout,
                        "stderr": stderr,
                        "return_code": process.returncode,
                        "command": command
                    },
                    error=None if process.returncode == 0 else f"Command failed with return code {process.returncode}",
                    metadata={
                        "working_directory": str(working_dir),
                        "timeout": timeout,
                        "timed_out": False
                    }
                )
                
            except subprocess.TimeoutExpired:
                timer.cancel()
                self._kill_process(process)
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Command timed out after {timeout} seconds",
                    metadata={"timed_out": True}
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error executing command: {str(e)}"
            )
    
    def _kill_process(self, process: subprocess.Popen):
        """Kill a process and its children."""
        try:
            if os.name == 'nt':
                # Windows
                process.terminate()
            else:
                # Unix-like systems
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                # Give it a moment to terminate gracefully
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except (ProcessLookupError, OSError):
            # Process already terminated
            pass
    
    def _get_parameter_schema(self) -> Dict[str, Any]:
        """Get parameter schema for this tool."""
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Shell command to execute"
                },
                "timeout": {
                    "type": "number",
                    "description": "Timeout in seconds (default: 30, max: 300)",
                    "default": 30,
                    "minimum": 1,
                    "maximum": 300
                },
                "working_dir": {
                    "type": "string",
                    "description": "Working directory relative to context (optional)"
                }
            },
            "required": ["command"]
        }