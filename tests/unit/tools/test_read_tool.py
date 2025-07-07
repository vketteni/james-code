"""Unit tests for the ReadTool."""

import pytest
from pathlib import Path

from james_code.tools.read_tool import ReadTool
from james_code.core.base import ExecutionContext


class TestReadTool:
    """Test ReadTool functionality."""
    
    @pytest.fixture
    def read_tool(self):
        """Create a ReadTool instance."""
        return ReadTool()
    
    @pytest.fixture
    def execution_context(self, temp_workspace):
        """Create an execution context."""
        return ExecutionContext(working_directory=temp_workspace)
    
    def test_read_tool_creation(self, read_tool):
        """Test creating a ReadTool."""
        assert read_tool.name == "read"
        assert "read" in read_tool.description.lower()
    
    def test_read_tool_schema(self, read_tool):
        """Test that ReadTool has proper schema."""
        schema = read_tool.get_schema()
        
        assert schema["name"] == "read"
        assert "parameters" in schema
        assert "properties" in schema["parameters"]
        assert "action" in schema["parameters"]["properties"]
        assert "path" in schema["parameters"]["properties"]
    
    def test_validate_input_valid(self, read_tool):
        """Test input validation with valid parameters."""
        # Valid cases
        assert read_tool.validate_input(action="read_file", path="test.txt")
        assert read_tool.validate_input(action="list_directory", path=".")
        assert read_tool.validate_input(action="file_exists", path="file.py")
        assert read_tool.validate_input(action="get_file_info", path="data.json")
    
    def test_validate_input_invalid(self, read_tool):
        """Test input validation with invalid parameters."""
        # Invalid action
        assert not read_tool.validate_input(action="invalid_action", path="test.txt")
        
        # Missing action
        assert not read_tool.validate_input(path="test.txt")
        
        # Missing path
        assert not read_tool.validate_input(action="read_file")
        
        # Empty parameters
        assert not read_tool.validate_input()
    
    def test_read_file_success(self, read_tool, execution_context, sample_files):
        """Test successful file reading."""
        result = read_tool.execute(
            execution_context,
            action="read_file",
            path="hello.py"
        )
        
        assert result.success
        assert "def hello():" in result.data
        assert "print('Hello, World!')" in result.data
        assert "file_size" in result.metadata
    
    def test_read_file_not_found(self, read_tool, execution_context):
        """Test reading a non-existent file."""
        result = read_tool.execute(
            execution_context,
            action="read_file",
            path="nonexistent.txt"
        )
        
        assert not result.success
        assert "does not exist" in result.error
    
    def test_read_directory_as_file(self, read_tool, execution_context, sample_files):
        """Test trying to read a directory as a file."""
        result = read_tool.execute(
            execution_context,
            action="read_file",
            path="subdir"
        )
        
        assert not result.success
        assert "not a file" in result.error
    
    def test_list_directory_success(self, read_tool, execution_context, sample_files):
        """Test successful directory listing."""
        result = read_tool.execute(
            execution_context,
            action="list_directory",
            path="."
        )
        
        assert result.success
        assert isinstance(result.data, list)
        assert len(result.data) >= 4  # At least the sample files
        
        # Check that files are properly represented
        file_names = [item["name"] for item in result.data]
        assert "hello.py" in file_names
        assert "config.json" in file_names
        assert "subdir" in file_names
        
        # Check file metadata
        hello_file = next(item for item in result.data if item["name"] == "hello.py")
        assert hello_file["type"] == "file"
        assert hello_file["size"] > 0
        assert "modified" in hello_file
    
    def test_list_directory_not_found(self, read_tool, execution_context):
        """Test listing a non-existent directory."""
        result = read_tool.execute(
            execution_context,
            action="list_directory",
            path="nonexistent_dir"
        )
        
        assert not result.success
        assert "does not exist" in result.error
    
    def test_list_file_as_directory(self, read_tool, execution_context, sample_files):
        """Test trying to list a file as directory."""
        result = read_tool.execute(
            execution_context,
            action="list_directory",
            path="hello.py"
        )
        
        assert not result.success
        assert "not a directory" in result.error
    
    def test_file_exists_true(self, read_tool, execution_context, sample_files):
        """Test file_exists for existing file."""
        result = read_tool.execute(
            execution_context,
            action="file_exists",
            path="hello.py"
        )
        
        assert result.success
        assert result.data is True
        assert "path" in result.metadata
    
    def test_file_exists_false(self, read_tool, execution_context):
        """Test file_exists for non-existent file."""
        result = read_tool.execute(
            execution_context,
            action="file_exists",
            path="nonexistent.txt"
        )
        
        assert result.success
        assert result.data is False
    
    def test_get_file_info_success(self, read_tool, execution_context, sample_files):
        """Test getting file information."""
        result = read_tool.execute(
            execution_context,
            action="get_file_info",
            path="hello.py"
        )
        
        assert result.success
        assert isinstance(result.data, dict)
        
        info = result.data
        assert info["name"] == "hello.py"
        assert info["type"] == "file"
        assert info["size"] > 0
        assert "created" in info
        assert "modified" in info
        assert "permissions" in info
    
    def test_get_file_info_not_found(self, read_tool, execution_context):
        """Test getting info for non-existent file."""
        result = read_tool.execute(
            execution_context,
            action="get_file_info",
            path="nonexistent.txt"
        )
        
        assert not result.success
        assert "does not exist" in result.error
    
    def test_path_traversal_security(self, read_tool, execution_context):
        """Test that path traversal attacks are blocked."""
        # Try to access files outside working directory
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\SAM"
        ]
        
        for malicious_path in malicious_paths:
            result = read_tool.execute(
                execution_context,
                action="read_file",
                path=malicious_path
            )
            
            assert not result.success
            assert "outside working directory" in result.error
    
    def test_empty_file_reading(self, read_tool, execution_context, sample_files):
        """Test reading an empty file."""
        result = read_tool.execute(
            execution_context,
            action="read_file",
            path="empty.txt"
        )
        
        assert result.success
        assert result.data == ""
        assert result.metadata["file_size"] == 0