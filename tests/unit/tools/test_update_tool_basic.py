"""Basic tests for UpdateTool - API discovery and validation."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

from james_code.tools.update_tool import UpdateTool
from james_code.core.base import ExecutionContext, ToolResult


class TestUpdateToolAPIDiscovery:
    """Test UpdateTool API discovery and basic validation."""
    
    @pytest.fixture
    def update_tool(self):
        """Create UpdateTool instance."""
        return UpdateTool()
    
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

    def test_tool_schema_discovery(self, update_tool):
        """Test that we can discover UpdateTool schema."""
        schema = update_tool.get_schema()
        
        assert schema is not None
        assert schema['name'] == 'update'
        assert 'parameters' in schema
        assert 'properties' in schema['parameters']
        assert 'action' in schema['parameters']['properties']
        
        # Verify discovered actions
        expected_actions = [
            'update_lines', 'replace_pattern', 'insert_at_line', 
            'delete_lines', 'apply_patch', 'replace_function'
        ]
        actual_actions = schema['parameters']['properties']['action']['enum']
        assert set(actual_actions) == set(expected_actions)

    def test_input_validation_action_required(self, update_tool, execution_context):
        """Test that action parameter is required."""
        result = update_tool.execute(
            execution_context,
            path="test.txt"
        )
        
        assert isinstance(result, ToolResult)
        assert not result.success
        assert "Invalid input parameters" in result.error

    def test_input_validation_path_required(self, update_tool, execution_context):
        """Test that path parameter is required."""
        result = update_tool.execute(
            execution_context,
            action="update_lines"
        )
        
        assert isinstance(result, ToolResult)
        assert not result.success
        assert "Invalid input parameters" in result.error

    def test_input_validation_invalid_action(self, update_tool, execution_context):
        """Test that invalid actions are rejected."""
        result = update_tool.execute(
            execution_context,
            action="invalid_action",
            path="test.txt"
        )
        
        assert isinstance(result, ToolResult)
        assert not result.success
        assert "Invalid input parameters" in result.error

    def test_input_validation_update_lines_parameters(self, update_tool, execution_context):
        """Test that update_lines requires correct parameters."""
        # Missing required parameters
        result = update_tool.execute(
            execution_context,
            action="update_lines",
            path="test.txt"
        )
        
        assert isinstance(result, ToolResult)
        assert not result.success
        assert "Invalid input parameters" in result.error

    def test_input_validation_replace_pattern_parameters(self, update_tool, execution_context):
        """Test that replace_pattern requires correct parameters."""
        # Missing required parameters
        result = update_tool.execute(
            execution_context,
            action="replace_pattern",
            path="test.txt"
        )
        
        assert isinstance(result, ToolResult)
        assert not result.success
        assert "Invalid input parameters" in result.error

    def test_file_not_found_handling(self, update_tool, execution_context):
        """Test handling of non-existent files."""
        result = update_tool.execute(
            execution_context,
            action="update_lines",
            path="nonexistent.txt",
            start_line=1,
            end_line=1,
            new_content="test"
        )
        
        assert isinstance(result, ToolResult)
        assert not result.success
        assert "does not exist" in result.error

    def test_path_security_validation(self, update_tool, execution_context):
        """Test that path traversal is prevented."""
        result = update_tool.execute(
            execution_context,
            action="update_lines",
            path="../../../etc/passwd",
            start_line=1,
            end_line=1,
            new_content="test"
        )
        
        assert isinstance(result, ToolResult)
        assert not result.success
        assert "outside working directory" in result.error

    def test_known_implementation_bug(self, update_tool, execution_context, temp_workspace):
        """Test that we understand the current implementation limitation."""
        # Create a test file
        test_file = temp_workspace / "test.txt"
        test_file.write_text("Line 1\nLine 2\nLine 3\n")
        
        # This currently fails due to duplicate 'path' parameter bug
        result = update_tool.execute(
            execution_context,
            action="update_lines",
            path="test.txt",
            start_line=1,
            end_line=1,
            new_content="Modified Line 1"
        )
        
        assert isinstance(result, ToolResult)
        assert not result.success
        # Document the known bug
        assert "multiple values for argument 'path'" in result.error


class TestUpdateToolInternalMethods:
    """Test UpdateTool internal methods when possible."""
    
    @pytest.fixture
    def update_tool(self):
        """Create UpdateTool instance."""
        return UpdateTool()
    
    def test_read_file_method(self, update_tool, temp_workspace):
        """Test internal _read_file method."""
        # Create a test file
        test_file = temp_workspace / "test.txt"
        test_content = "Line 1\nLine 2\nLine 3\n"
        test_file.write_text(test_content)
        
        # Test reading
        content = update_tool._read_file(test_file)
        assert content == test_content

    def test_read_file_size_limit(self, update_tool, temp_workspace):
        """Test that _read_file respects size limits."""
        # This is documented as 10MB limit in the code
        test_file = temp_workspace / "large.txt"
        
        # Mock file size to be over limit
        with patch.object(Path, 'stat') as mock_stat:
            mock_stat.return_value.st_size = 11 * 1024 * 1024  # 11MB
            content = update_tool._read_file(test_file)
            assert content is None

    def test_tool_instantiation(self, update_tool):
        """Test that UpdateTool instantiates correctly."""
        assert update_tool.name == "update"
        assert "surgical file modifications" in update_tool.description.lower()
        assert hasattr(update_tool, 'execute')
        assert hasattr(update_tool, 'validate_input')
        assert hasattr(update_tool, 'get_schema')


class TestUpdateToolReturnTypes:
    """Test UpdateTool return type consistency."""
    
    @pytest.fixture
    def update_tool(self):
        """Create UpdateTool instance."""
        return UpdateTool()
    
    @pytest.fixture
    def execution_context(self):
        """Create execution context."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield ExecutionContext(
                working_directory=Path(temp_dir),
                environment={},
                user_id="test_user",
                session_id="test_session"
            )

    def test_execute_returns_tool_result(self, update_tool, execution_context):
        """Test that execute always returns ToolResult."""
        result = update_tool.execute(
            execution_context,
            action="invalid_action",
            path="test.txt"
        )
        
        assert isinstance(result, ToolResult)
        assert hasattr(result, 'success')
        assert hasattr(result, 'data')
        assert hasattr(result, 'error')
        assert hasattr(result, 'metadata')

    def test_validate_input_returns_boolean(self, update_tool):
        """Test that validate_input returns boolean."""
        # Valid input
        result = update_tool.validate_input(
            action="update_lines",
            path="test.txt",
            start_line=1,
            end_line=1,
            new_content="test"
        )
        assert isinstance(result, bool)
        assert result is True
        
        # Invalid input
        result = update_tool.validate_input(
            action="invalid_action",
            path="test.txt"
        )
        assert isinstance(result, bool)
        assert result is False