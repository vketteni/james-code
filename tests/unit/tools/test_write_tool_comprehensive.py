"""Comprehensive tests for WriteTool - Phase 2."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open

from james_code.tools.write_tool import WriteTool
from james_code.core.base import ExecutionContext
from tests.fixtures.security_vectors import get_path_traversal_vectors
# from tests.fixtures.complex_scenarios import create_complex_codebase
from tests.utils.security_helpers import SecurityTestHelper
from tests.utils.filesystem_helpers import FileSystemTestHelper


class TestWriteToolBasicOperations:
    """Test basic WriteTool operations."""
    
    @pytest.fixture
    def write_tool(self):
        """Create WriteTool instance."""
        return WriteTool()
    
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
    
    def test_write_file_basic(self, write_tool, execution_context):
        """Test basic file writing."""
        content = "Hello, World!"
        result = write_tool.execute(
            execution_context,
            action="write_file",
            path="test.txt",
            content=content
        )
        
        assert result.success
        assert "File written" in result.data
        assert result.metadata["file_size"] == len(content.encode('utf-8'))
        
        # Verify file exists and has correct content
        file_path = execution_context.working_directory / "test.txt"
        assert file_path.exists()
        assert file_path.read_text(encoding='utf-8') == content
    
    def test_write_file_with_directories(self, write_tool, execution_context):
        """Test writing file with parent directory creation."""
        content = "Test content"
        result = write_tool.execute(
            execution_context,
            action="write_file",
            path="subdir/nested/test.txt",
            content=content
        )
        
        assert result.success
        file_path = execution_context.working_directory / "subdir/nested/test.txt"
        assert file_path.exists()
        assert file_path.read_text(encoding='utf-8') == content
    
    def test_write_file_overwrite(self, write_tool, execution_context):
        """Test overwriting existing file."""
        file_path = execution_context.working_directory / "test.txt"
        file_path.write_text("Original content")
        
        new_content = "New content"
        result = write_tool.execute(
            execution_context,
            action="write_file",
            path="test.txt",
            content=new_content
        )
        
        assert result.success
        assert file_path.read_text(encoding='utf-8') == new_content
    
    def test_append_file_basic(self, write_tool, execution_context):
        """Test basic file appending."""
        file_path = execution_context.working_directory / "test.txt"
        original_content = "Original content"
        file_path.write_text(original_content)
        
        append_content = "\nAppended content"
        result = write_tool.execute(
            execution_context,
            action="append_file",
            path="test.txt",
            content=append_content
        )
        
        assert result.success
        assert "Content appended" in result.data
        assert result.metadata["appended_bytes"] == len(append_content.encode('utf-8'))
        
        final_content = file_path.read_text(encoding='utf-8')
        assert final_content == original_content + append_content
    
    def test_append_file_nonexistent(self, write_tool, execution_context):
        """Test appending to non-existent file."""
        result = write_tool.execute(
            execution_context,
            action="append_file",
            path="nonexistent.txt",
            content="content"
        )
        
        assert not result.success
        assert "File does not exist" in result.error
    
    def test_create_directory_basic(self, write_tool, execution_context):
        """Test basic directory creation."""
        result = write_tool.execute(
            execution_context,
            action="create_directory",
            path="test_dir"
        )
        
        assert result.success
        assert "Directory created" in result.data
        assert result.metadata["created"] is True
        
        dir_path = execution_context.working_directory / "test_dir"
        assert dir_path.exists()
        assert dir_path.is_dir()
    
    def test_create_directory_nested(self, write_tool, execution_context):
        """Test nested directory creation."""
        result = write_tool.execute(
            execution_context,
            action="create_directory",
            path="nested/deep/structure"
        )
        
        assert result.success
        dir_path = execution_context.working_directory / "nested/deep/structure"
        assert dir_path.exists()
        assert dir_path.is_dir()
    
    def test_create_directory_existing(self, write_tool, execution_context):
        """Test creating existing directory."""
        dir_path = execution_context.working_directory / "existing_dir"
        dir_path.mkdir()
        
        result = write_tool.execute(
            execution_context,
            action="create_directory",
            path="existing_dir"
        )
        
        assert result.success
        assert "Directory already exists" in result.data
        assert result.metadata["already_existed"] is True
    
    def test_create_directory_file_exists(self, write_tool, execution_context):
        """Test creating directory where file exists."""
        file_path = execution_context.working_directory / "test_file"
        file_path.write_text("content")
        
        result = write_tool.execute(
            execution_context,
            action="create_directory",
            path="test_file"
        )
        
        assert not result.success
        assert "Path exists but is not a directory" in result.error
    
    def test_delete_file_basic(self, write_tool, execution_context):
        """Test basic file deletion."""
        file_path = execution_context.working_directory / "test.txt"
        content = "test content"
        file_path.write_text(content)
        
        result = write_tool.execute(
            execution_context,
            action="delete_file",
            path="test.txt"
        )
        
        assert result.success
        assert "File deleted" in result.data
        assert result.metadata["deleted_size"] == len(content.encode('utf-8'))
        assert not file_path.exists()
    
    def test_delete_file_nonexistent(self, write_tool, execution_context):
        """Test deleting non-existent file."""
        result = write_tool.execute(
            execution_context,
            action="delete_file",
            path="nonexistent.txt"
        )
        
        assert not result.success
        assert "File does not exist" in result.error
    
    def test_delete_file_is_directory(self, write_tool, execution_context):
        """Test deleting directory with delete_file action."""
        dir_path = execution_context.working_directory / "test_dir"
        dir_path.mkdir()
        
        result = write_tool.execute(
            execution_context,
            action="delete_file",
            path="test_dir"
        )
        
        assert not result.success
        assert "Path is not a file" in result.error
    
    def test_delete_directory_basic(self, write_tool, execution_context):
        """Test basic directory deletion."""
        dir_path = execution_context.working_directory / "test_dir"
        dir_path.mkdir()
        
        result = write_tool.execute(
            execution_context,
            action="delete_directory",
            path="test_dir"
        )
        
        assert result.success
        assert "Directory deleted" in result.data
        assert result.metadata["deleted"] is True
        assert not dir_path.exists()
    
    def test_delete_directory_nonexistent(self, write_tool, execution_context):
        """Test deleting non-existent directory."""
        result = write_tool.execute(
            execution_context,
            action="delete_directory",
            path="nonexistent_dir"
        )
        
        assert not result.success
        assert "Directory does not exist" in result.error
    
    def test_delete_directory_not_empty(self, write_tool, execution_context):
        """Test deleting non-empty directory."""
        dir_path = execution_context.working_directory / "test_dir"
        dir_path.mkdir()
        (dir_path / "file.txt").write_text("content")
        
        result = write_tool.execute(
            execution_context,
            action="delete_directory",
            path="test_dir"
        )
        
        assert not result.success
        assert "Directory is not empty" in result.error
    
    def test_delete_directory_is_file(self, write_tool, execution_context):
        """Test deleting file with delete_directory action."""
        file_path = execution_context.working_directory / "test.txt"
        file_path.write_text("content")
        
        result = write_tool.execute(
            execution_context,
            action="delete_directory",
            path="test.txt"
        )
        
        assert not result.success
        assert "Path is not a directory" in result.error


class TestWriteToolSecurityValidation:
    """Test WriteTool security validation."""
    
    @pytest.fixture
    def write_tool(self):
        """Create WriteTool instance."""
        return WriteTool()
    
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
    
    @pytest.fixture
    def security_helper(self):
        """Create security test helper."""
        return SecurityTestHelper()
    
    @pytest.mark.security
    def test_path_traversal_prevention(self, write_tool, execution_context, security_helper):
        """Test path traversal attack prevention."""
        malicious_paths = get_path_traversal_vectors()
        
        for path in malicious_paths[:20]:  # Test subset for performance
            result = write_tool.execute(
                execution_context,
                action="write_file",
                path=path,
                content="malicious content"
            )
            
            assert not result.success, f"Path traversal not blocked: {path}"
            assert "Path outside working directory" in result.error
    
    @pytest.mark.security
    def test_absolute_path_prevention(self, write_tool, execution_context):
        """Test absolute path prevention."""
        dangerous_paths = [
            "/etc/passwd",
            "/tmp/malicious",
            "C:\\Windows\\System32\\config\\SAM",
            "/home/user/.ssh/id_rsa"
        ]
        
        for path in dangerous_paths:
            result = write_tool.execute(
                execution_context,
                action="write_file",
                path=path,
                content="malicious content"
            )
            
            assert not result.success, f"Absolute path not blocked: {path}"
            assert "Path outside working directory" in result.error
    
    @pytest.mark.security
    def test_file_size_limits(self, write_tool, execution_context):
        """Test file size limits enforcement."""
        # Test content exceeding 10MB limit
        large_content = "x" * (11 * 1024 * 1024)  # 11MB
        
        result = write_tool.execute(
            execution_context,
            action="write_file",
            path="large_file.txt",
            content=large_content
        )
        
        assert not result.success
        assert "Content too large" in result.error
    
    @pytest.mark.security
    def test_append_size_limits(self, write_tool, execution_context):
        """Test append operation size limits."""
        # Create file near limit
        file_path = execution_context.working_directory / "test.txt"
        initial_content = "x" * (9 * 1024 * 1024)  # 9MB
        file_path.write_text(initial_content)
        
        # Try to append content that would exceed limit
        append_content = "x" * (2 * 1024 * 1024)  # 2MB
        
        result = write_tool.execute(
            execution_context,
            action="append_file",
            path="test.txt",
            content=append_content
        )
        
        assert not result.success
        assert "would exceed size limit" in result.error
    
    @pytest.mark.security
    def test_dangerous_file_extensions(self, write_tool, execution_context):
        """Test handling of potentially dangerous file extensions."""
        # Note: Current implementation doesn't block by extension
        # This is testing current behavior, not necessarily ideal behavior
        dangerous_extensions = [
            "malware.exe",
            "script.bat",
            "config.ini",
            "key.pem"
        ]
        
        for filename in dangerous_extensions:
            result = write_tool.execute(
                execution_context,
                action="write_file",
                path=filename,
                content="test content"
            )
            
            # Current implementation allows these - documenting behavior
            # In production, might want to add extension filtering
            assert result.success, f"Unexpected failure for {filename}"
    
    @pytest.mark.security
    def test_unicode_and_special_characters(self, write_tool, execution_context):
        """Test handling of unicode and special characters in paths."""
        special_paths = [
            "file\u202e.txt",  # Right-to-left override
            "file\u200b.txt",  # Zero-width space
            "file\u0000.txt",  # Null character
            "file\\.txt",      # Escaped backslash
            "file\n.txt",      # Newline
            "file\r.txt",      # Carriage return
            "file\t.txt",      # Tab
        ]
        
        for path in special_paths:
            result = write_tool.execute(
                execution_context,
                action="write_file",
                path=path,
                content="test content"
            )
            
            # Some special characters should be handled safely
            # Others might cause issues - documenting current behavior
            if "\u0000" in path or "\n" in path or "\r" in path:
                # These typically cause filesystem issues
                assert not result.success, f"Should reject dangerous characters: {repr(path)}"
            else:
                # These should be handled safely
                assert result.success, f"Should handle safe unicode: {repr(path)}"


class TestWriteToolErrorHandling:
    """Test WriteTool error handling scenarios."""
    
    @pytest.fixture
    def write_tool(self):
        """Create WriteTool instance."""
        return WriteTool()
    
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
    
    def test_invalid_action(self, write_tool, execution_context):
        """Test invalid action handling."""
        result = write_tool.execute(
            execution_context,
            action="invalid_action",
            path="test.txt"
        )
        
        assert not result.success
        assert "Invalid input parameters" in result.error
    
    def test_missing_path(self, write_tool, execution_context):
        """Test missing path parameter."""
        result = write_tool.execute(
            execution_context,
            action="write_file",
            content="test content"
        )
        
        assert not result.success
        assert "Invalid input parameters" in result.error
    
    def test_missing_content_for_write(self, write_tool, execution_context):
        """Test missing content for write operation."""
        result = write_tool.execute(
            execution_context,
            action="write_file",
            path="test.txt"
        )
        
        assert not result.success
        assert "Invalid input parameters" in result.error
    
    def test_missing_content_for_append(self, write_tool, execution_context):
        """Test missing content for append operation."""
        result = write_tool.execute(
            execution_context,
            action="append_file",
            path="test.txt"
        )
        
        assert not result.success
        assert "Invalid input parameters" in result.error
    
    @pytest.mark.skipif(os.name == 'nt', reason="Unix-specific permission test")
    def test_permission_denied_write(self, write_tool, execution_context):
        """Test permission denied scenario."""
        # Create read-only directory
        readonly_dir = execution_context.working_directory / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)  # Read-only
        
        try:
            result = write_tool.execute(
                execution_context,
                action="write_file",
                path="readonly/test.txt",
                content="test content"
            )
            
            assert not result.success
            assert "Permission denied" in result.error
        finally:
            # Clean up - restore permissions
            readonly_dir.chmod(0o755)
    
    def test_disk_space_exhaustion_simulation(self, write_tool, execution_context):
        """Test disk space exhaustion simulation."""
        # This is a simulation - we can't actually exhaust disk space in tests
        # Instead, we mock the open function to raise OSError
        
        with patch('builtins.open', side_effect=OSError("No space left on device")):
            result = write_tool.execute(
                execution_context,
                action="write_file",
                path="test.txt",
                content="test content"
            )
            
            assert not result.success
            assert "Error writing file" in result.error
            assert "No space left on device" in result.error


class TestWriteToolPerformance:
    """Test WriteTool performance scenarios."""
    
    @pytest.fixture
    def write_tool(self):
        """Create WriteTool instance."""
        return WriteTool()
    
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
    def test_large_file_writing_performance(self, write_tool, execution_context, benchmark):
        """Benchmark large file writing performance."""
        # 5MB file (within limits)
        large_content = "x" * (5 * 1024 * 1024)
        
        def write_large_file():
            return write_tool.execute(
                execution_context,
                action="write_file",
                path="large_file.txt",
                content=large_content
            )
        
        result = benchmark(write_large_file)
        assert result.success
        assert result.metadata["file_size"] == len(large_content)
    
    @pytest.mark.performance
    def test_many_small_files_performance(self, write_tool, execution_context, benchmark):
        """Benchmark writing many small files."""
        def write_many_files():
            results = []
            for i in range(100):
                result = write_tool.execute(
                    execution_context,
                    action="write_file",
                    path=f"file_{i}.txt",
                    content=f"Content for file {i}"
                )
                results.append(result)
            return results
        
        results = benchmark(write_many_files)
        assert all(result.success for result in results)
        assert len(results) == 100
    
    @pytest.mark.performance
    def test_deep_directory_creation_performance(self, write_tool, execution_context, benchmark):
        """Benchmark deep directory creation performance."""
        def create_deep_directories():
            results = []
            for i in range(10):
                deep_path = "/".join([f"level_{j}" for j in range(i + 1)])
                result = write_tool.execute(
                    execution_context,
                    action="create_directory",
                    path=deep_path
                )
                results.append(result)
            return results
        
        results = benchmark(create_deep_directories)
        assert all(result.success for result in results)
    
    @pytest.mark.performance
    def test_concurrent_file_operations(self, write_tool, execution_context):
        """Test concurrent file operations handling."""
        import threading
        import time
        
        results = []
        errors = []
        
        def write_file_worker(file_id):
            try:
                result = write_tool.execute(
                    execution_context,
                    action="write_file",
                    path=f"concurrent_file_{file_id}.txt",
                    content=f"Content from thread {file_id}"
                )
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Create 10 concurrent threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=write_file_worker, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify results
        assert len(errors) == 0, f"Concurrent operations failed: {errors}"
        assert len(results) == 10
        assert all(result.success for result in results)
        
        # Verify all files were created
        for i in range(10):
            file_path = execution_context.working_directory / f"concurrent_file_{i}.txt"
            assert file_path.exists()
            assert file_path.read_text() == f"Content from thread {i}"


class TestWriteToolIntegration:
    """Test WriteTool integration scenarios."""
    
    @pytest.fixture
    def write_tool(self):
        """Create WriteTool instance."""
        return WriteTool()
    
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
    
    def test_create_complex_project_structure(self, write_tool, execution_context):
        """Test creating complex project structure."""
        # Create a typical project structure
        structure = {
            "src/main.py": "def main():\n    print('Hello, World!')",
            "src/utils.py": "def helper():\n    return 'helper'",
            "tests/test_main.py": "def test_main():\n    assert True",
            "docs/README.md": "# Project Documentation",
            "config/settings.json": '{"debug": true}',
            ".gitignore": "*.pyc\n__pycache__/"
        }
        
        # Create all directories first
        directories = {"src", "tests", "docs", "config"}
        for directory in directories:
            result = write_tool.execute(
                execution_context,
                action="create_directory",
                path=directory
            )
            assert result.success
        
        # Create all files
        for file_path, content in structure.items():
            result = write_tool.execute(
                execution_context,
                action="write_file",
                path=file_path,
                content=content
            )
            assert result.success
            
            # Verify file was created with correct content
            actual_path = execution_context.working_directory / file_path
            assert actual_path.exists()
            assert actual_path.read_text(encoding='utf-8') == content
    
    def test_file_lifecycle_operations(self, write_tool, execution_context):
        """Test complete file lifecycle operations."""
        file_path = "lifecycle_test.txt"
        
        # 1. Create file
        result = write_tool.execute(
            execution_context,
            action="write_file",
            path=file_path,
            content="Initial content"
        )
        assert result.success
        
        # 2. Append to file
        result = write_tool.execute(
            execution_context,
            action="append_file",
            path=file_path,
            content="\nAppended content"
        )
        assert result.success
        
        # 3. Overwrite file
        result = write_tool.execute(
            execution_context,
            action="write_file",
            path=file_path,
            content="Overwritten content"
        )
        assert result.success
        
        # 4. Verify content
        actual_path = execution_context.working_directory / file_path
        assert actual_path.read_text(encoding='utf-8') == "Overwritten content"
        
        # 5. Delete file
        result = write_tool.execute(
            execution_context,
            action="delete_file",
            path=file_path
        )
        assert result.success
        assert not actual_path.exists()
    
    def test_directory_lifecycle_operations(self, write_tool, execution_context):
        """Test complete directory lifecycle operations."""
        dir_path = "lifecycle_dir"
        
        # 1. Create directory
        result = write_tool.execute(
            execution_context,
            action="create_directory",
            path=dir_path
        )
        assert result.success
        
        # 2. Verify directory exists
        actual_path = execution_context.working_directory / dir_path
        assert actual_path.exists()
        assert actual_path.is_dir()
        
        # 3. Delete empty directory
        result = write_tool.execute(
            execution_context,
            action="delete_directory",
            path=dir_path
        )
        assert result.success
        assert not actual_path.exists()