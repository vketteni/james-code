"""Process testing helper utilities."""

import subprocess
import psutil
import time
import signal
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
import queue
import os

import pytest


@dataclass
class ProcessResult:
    """Result of a process execution."""
    pid: Optional[int]
    returncode: Optional[int]
    stdout: str
    stderr: str
    execution_time: float
    memory_usage: Dict[str, float] = field(default_factory=dict)
    cpu_usage: float = 0.0
    terminated_by_timeout: bool = False
    security_violation: bool = False


@dataclass
class ProcessLimits:
    """Process execution limits."""
    max_execution_time: float = 30.0  # seconds
    max_memory_mb: float = 512.0       # MB
    max_cpu_percent: float = 80.0      # %
    max_open_files: int = 100
    max_processes: int = 10


class ProcessMonitor:
    """Monitor process execution and resource usage."""
    
    def __init__(self, pid: int, limits: ProcessLimits):
        """Initialize process monitor.
        
        Args:
            pid: Process ID to monitor
            limits: Resource limits to enforce
        """
        self.pid = pid
        self.limits = limits
        self.start_time = time.time()
        self.samples: List[Dict[str, Any]] = []
        self.violations: List[str] = []
        self._stop_monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
    
    def start_monitoring(self):
        """Start monitoring the process."""
        self._monitor_thread = threading.Thread(target=self._monitor_loop)
        self._monitor_thread.start()
    
    def stop_monitoring(self) -> Dict[str, Any]:
        """Stop monitoring and return results.
        
        Returns:
            Monitoring results summary
        """
        self._stop_monitoring = True
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)
        
        return self._get_summary()
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        try:
            process = psutil.Process(self.pid)
        except psutil.NoSuchProcess:
            return
        
        while not self._stop_monitoring:
            try:
                # Check if process still exists
                if not process.is_running():
                    break
                
                # Sample resource usage
                sample = {
                    'timestamp': time.time(),
                    'memory_mb': process.memory_info().rss / 1024 / 1024,
                    'cpu_percent': process.cpu_percent(),
                    'num_threads': process.num_threads(),
                    'open_files': len(process.open_files()),
                    'num_children': len(process.children())
                }
                
                self.samples.append(sample)
                
                # Check limits
                self._check_limits(sample, process)
                
                time.sleep(0.1)  # Sample every 100ms
                
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break
            except Exception as e:
                self.violations.append(f"Monitoring error: {e}")
                break
    
    def _check_limits(self, sample: Dict[str, Any], process: psutil.Process):
        """Check if process violates limits.
        
        Args:
            sample: Current resource sample
            process: Process object
        """
        # Check execution time
        execution_time = time.time() - self.start_time
        if execution_time > self.limits.max_execution_time:
            self.violations.append(f"Execution time limit exceeded: {execution_time:.2f}s")
            self._terminate_process(process)
        
        # Check memory usage
        if sample['memory_mb'] > self.limits.max_memory_mb:
            self.violations.append(f"Memory limit exceeded: {sample['memory_mb']:.2f}MB")
            self._terminate_process(process)
        
        # Check CPU usage (use average of recent samples)
        if len(self.samples) >= 5:
            recent_cpu = sum(s['cpu_percent'] for s in self.samples[-5:]) / 5
            if recent_cpu > self.limits.max_cpu_percent:
                self.violations.append(f"CPU limit exceeded: {recent_cpu:.2f}%")
                self._terminate_process(process)
        
        # Check open files
        if sample['open_files'] > self.limits.max_open_files:
            self.violations.append(f"Open files limit exceeded: {sample['open_files']}")
            self._terminate_process(process)
        
        # Check number of child processes
        if sample['num_children'] > self.limits.max_processes:
            self.violations.append(f"Process limit exceeded: {sample['num_children']}")
            self._terminate_process(process)
    
    def _terminate_process(self, process: psutil.Process):
        """Terminate the process due to limit violation.
        
        Args:
            process: Process to terminate
        """
        try:
            # Try graceful termination first
            process.terminate()
            
            # Give it a moment to terminate gracefully
            try:
                process.wait(timeout=2.0)
            except psutil.TimeoutExpired:
                # Force kill if still running
                process.kill()
                
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    def _get_summary(self) -> Dict[str, Any]:
        """Get monitoring summary.
        
        Returns:
            Summary of monitoring results
        """
        if not self.samples:
            return {
                'total_samples': 0,
                'violations': self.violations,
                'limits_exceeded': len(self.violations) > 0
            }
        
        memory_values = [s['memory_mb'] for s in self.samples]
        cpu_values = [s['cpu_percent'] for s in self.samples if s['cpu_percent'] > 0]
        
        return {
            'total_samples': len(self.samples),
            'execution_time': time.time() - self.start_time,
            'memory_usage': {
                'max_mb': max(memory_values),
                'avg_mb': sum(memory_values) / len(memory_values),
                'peak_sample': max(self.samples, key=lambda x: x['memory_mb'])
            },
            'cpu_usage': {
                'max_percent': max(cpu_values) if cpu_values else 0,
                'avg_percent': sum(cpu_values) / len(cpu_values) if cpu_values else 0
            },
            'violations': self.violations,
            'limits_exceeded': len(self.violations) > 0,
            'samples': self.samples
        }


class ProcessTestHelper:
    """Helper class for process testing operations."""
    
    def __init__(self, limits: Optional[ProcessLimits] = None):
        """Initialize process test helper.
        
        Args:
            limits: Process limits to enforce
        """
        self.limits = limits or ProcessLimits()
        self.active_monitors: Dict[int, ProcessMonitor] = {}
        self.process_history: List[ProcessResult] = []
    
    def execute_with_monitoring(self, 
                              command: Union[str, List[str]], 
                              cwd: Optional[Path] = None,
                              env: Optional[Dict[str, str]] = None,
                              input_data: Optional[str] = None) -> ProcessResult:
        """Execute a command with resource monitoring.
        
        Args:
            command: Command to execute
            cwd: Working directory
            env: Environment variables
            input_data: Input data to send to process
            
        Returns:
            Process execution result
        """
        start_time = time.time()
        
        try:
            # Prepare command
            if isinstance(command, str):
                cmd_args = command
                shell = True
            else:
                cmd_args = command
                shell = False
            
            # Start process
            process = subprocess.Popen(
                cmd_args,
                shell=shell,
                cwd=cwd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE if input_data else None,
                text=True
            )
            
            # Start monitoring
            monitor = ProcessMonitor(process.pid, self.limits)
            self.active_monitors[process.pid] = monitor
            monitor.start_monitoring()
            
            # Execute process
            try:
                stdout, stderr = process.communicate(
                    input=input_data, 
                    timeout=self.limits.max_execution_time
                )
                terminated_by_timeout = False
            except subprocess.TimeoutExpired:
                # Process exceeded time limit
                process.kill()
                stdout, stderr = process.communicate()
                terminated_by_timeout = True
            
            # Stop monitoring
            monitor_results = monitor.stop_monitoring()
            
            execution_time = time.time() - start_time
            
            result = ProcessResult(
                pid=process.pid,
                returncode=process.returncode,
                stdout=stdout or "",
                stderr=stderr or "",
                execution_time=execution_time,
                memory_usage=monitor_results.get('memory_usage', {}),
                cpu_usage=monitor_results.get('cpu_usage', {}).get('max_percent', 0),
                terminated_by_timeout=terminated_by_timeout,
                security_violation=monitor_results.get('limits_exceeded', False)
            )
            
            # Clean up monitor
            if process.pid in self.active_monitors:
                del self.active_monitors[process.pid]
            
            self.process_history.append(result)
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            result = ProcessResult(
                pid=None,
                returncode=-1,
                stdout="",
                stderr=str(e),
                execution_time=execution_time,
                security_violation=True
            )
            
            self.process_history.append(result)
            return result
    
    def execute_command_safely(self, 
                             command: str, 
                             allowed_commands: Optional[List[str]] = None,
                             cwd: Optional[Path] = None) -> ProcessResult:
        """Execute a command with safety checks.
        
        Args:
            command: Command to execute
            allowed_commands: List of allowed command prefixes
            cwd: Working directory
            
        Returns:
            Process execution result
        """
        # Basic command validation
        if allowed_commands:
            command_parts = command.split()
            if not command_parts:
                return ProcessResult(
                    pid=None,
                    returncode=-1,
                    stdout="",
                    stderr="Empty command",
                    execution_time=0.0,
                    security_violation=True
                )
            
            base_command = command_parts[0]
            if not any(base_command.startswith(allowed) for allowed in allowed_commands):
                return ProcessResult(
                    pid=None,
                    returncode=-1,
                    stdout="",
                    stderr=f"Command not allowed: {base_command}",
                    execution_time=0.0,
                    security_violation=True
                )
        
        # Check for dangerous patterns
        dangerous_patterns = [
            'rm -rf',
            'format',
            'mkfs',
            'dd if=',
            '>/dev/',
            'chmod 777',
            'sudo',
            'su -',
            'nc -l',
            'python -c',
            'eval',
            'exec',
            '$()',
            '`',
            '&&',
            '||',
            ';',
            '|'
        ]
        
        command_lower = command.lower()
        for pattern in dangerous_patterns:
            if pattern in command_lower:
                return ProcessResult(
                    pid=None,
                    returncode=-1,
                    stdout="",
                    stderr=f"Dangerous command pattern detected: {pattern}",
                    execution_time=0.0,
                    security_violation=True
                )
        
        return self.execute_with_monitoring(command, cwd=cwd)
    
    def get_resource_usage_summary(self) -> Dict[str, Any]:
        """Get summary of resource usage across all processes.
        
        Returns:
            Resource usage summary
        """
        if not self.process_history:
            return {"total_processes": 0}
        
        total_processes = len(self.process_history)
        successful_processes = sum(1 for p in self.process_history if p.returncode == 0)
        security_violations = sum(1 for p in self.process_history if p.security_violation)
        timeouts = sum(1 for p in self.process_history if p.terminated_by_timeout)
        
        execution_times = [p.execution_time for p in self.process_history]
        memory_usage = [
            p.memory_usage.get('max_mb', 0) 
            for p in self.process_history 
            if p.memory_usage
        ]
        
        return {
            "total_processes": total_processes,
            "successful_processes": successful_processes,
            "failed_processes": total_processes - successful_processes,
            "security_violations": security_violations,
            "timeout_violations": timeouts,
            "execution_time": {
                "total": sum(execution_times),
                "average": sum(execution_times) / len(execution_times),
                "max": max(execution_times),
                "min": min(execution_times)
            },
            "memory_usage": {
                "max_mb": max(memory_usage) if memory_usage else 0,
                "average_mb": sum(memory_usage) / len(memory_usage) if memory_usage else 0
            }
        }
    
    def cleanup(self):
        """Clean up any remaining processes and monitors."""
        for monitor in self.active_monitors.values():
            monitor.stop_monitoring()
        self.active_monitors.clear()
        self.process_history.clear()


def monitor_process_execution(command: str, 
                            limits: Optional[ProcessLimits] = None,
                            cwd: Optional[Path] = None) -> ProcessResult:
    """Monitor execution of a single command.
    
    Args:
        command: Command to execute and monitor
        limits: Resource limits
        cwd: Working directory
        
    Returns:
        Process execution result
    """
    helper = ProcessTestHelper(limits)
    result = helper.execute_with_monitoring(command, cwd=cwd)
    helper.cleanup()
    return result


def assert_process_limits(result: ProcessResult, limits: ProcessLimits):
    """Assert that process execution respected limits.
    
    Args:
        result: Process execution result
        limits: Expected limits
        
    Raises:
        AssertionError: If limits were violated
    """
    assert result.execution_time <= limits.max_execution_time, \
        f"Process exceeded time limit: {result.execution_time:.2f}s > {limits.max_execution_time}s"
    
    if result.memory_usage:
        max_memory = result.memory_usage.get('max_mb', 0)
        assert max_memory <= limits.max_memory_mb, \
            f"Process exceeded memory limit: {max_memory:.2f}MB > {limits.max_memory_mb}MB"
    
    assert result.cpu_usage <= limits.max_cpu_percent, \
        f"Process exceeded CPU limit: {result.cpu_usage:.2f}% > {limits.max_cpu_percent}%"
    
    assert not result.security_violation, \
        "Process triggered security violation"


def capture_process_output(command: str, 
                         timeout: float = 10.0,
                         cwd: Optional[Path] = None) -> ProcessResult:
    """Capture output from a process execution.
    
    Args:
        command: Command to execute
        timeout: Timeout in seconds
        cwd: Working directory
        
    Returns:
        Process execution result
    """
    limits = ProcessLimits(max_execution_time=timeout)
    return monitor_process_execution(command, limits, cwd)


@pytest.fixture
def process_helper():
    """Provide a process test helper."""
    helper = ProcessTestHelper()
    yield helper
    helper.cleanup()


@pytest.fixture
def safe_process_limits():
    """Provide safe process limits for testing."""
    return ProcessLimits(
        max_execution_time=5.0,
        max_memory_mb=128.0,
        max_cpu_percent=50.0,
        max_open_files=20,
        max_processes=3
    )


class CommandValidator:
    """Validate commands for security before execution."""
    
    def __init__(self, allowed_commands: Optional[List[str]] = None):
        """Initialize command validator.
        
        Args:
            allowed_commands: List of allowed command prefixes
        """
        self.allowed_commands = allowed_commands or [
            'echo', 'cat', 'ls', 'pwd', 'python3', 'pip', 'git'
        ]
        
        self.dangerous_patterns = [
            'rm -rf', 'format', 'mkfs', 'dd if=', '>/dev/',
            'chmod 777', 'sudo', 'su -', 'nc -l', 'curl',
            'wget', 'python -c', 'eval', 'exec'
        ]
        
        self.injection_patterns = [
            '$()', '`', '&&', '||', ';', '|', '\n', '\r'
        ]
    
    def validate_command(self, command: str) -> tuple[bool, Optional[str]]:
        """Validate a command for security.
        
        Args:
            command: Command to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not command or not command.strip():
            return False, "Empty command"
        
        command_parts = command.split()
        base_command = command_parts[0]
        
        # Check if command is allowed
        if not any(base_command.startswith(allowed) for allowed in self.allowed_commands):
            return False, f"Command not in allowed list: {base_command}"
        
        # Check for dangerous patterns
        command_lower = command.lower()
        for pattern in self.dangerous_patterns:
            if pattern in command_lower:
                return False, f"Dangerous pattern detected: {pattern}"
        
        # Check for injection patterns
        for pattern in self.injection_patterns:
            if pattern in command:
                return False, f"Command injection pattern detected: {pattern}"
        
        return True, None