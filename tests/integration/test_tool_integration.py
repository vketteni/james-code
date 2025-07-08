"""Integration tests for cross-tool workflows and interactions."""

import pytest
import tempfile
from pathlib import Path

from james_code.tools.write_tool import WriteTool
from james_code.tools.read_tool import ReadTool
from james_code.tools.find_tool import FindTool
from james_code.tools.execute_tool import ExecuteTool
from james_code.tools.todo_tool import TodoTool
from james_code.tools.task_tool import TaskTool
from james_code.core.base import ExecutionContext


class TestBasicToolIntegration:
    """Test basic integration between tools."""
    
    @pytest.fixture
    def tools(self):
        """Create instances of all tools."""
        return {
            'write': WriteTool(),
            'read': ReadTool(),
            'find': FindTool(),
            'execute': ExecuteTool(),
            'todo': TodoTool(),
            'task': TaskTool()
        }
    
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

    def test_write_then_read_workflow(self, tools, execution_context):
        """Test writing a file then reading it back - based on actual behavior."""
        # Write a file - returns string "File written: /path"
        write_result = tools['write'].execute(
            execution_context,
            action="write_file",
            path="test.txt",
            content="Hello, integration testing!"
        )
        assert write_result.success
        assert isinstance(write_result.data, str)
        assert "test.txt" in write_result.data
        
        # Read the file back - returns content string directly
        read_result = tools['read'].execute(
            execution_context,
            action="read_file",
            path="test.txt"
        )
        assert read_result.success
        assert isinstance(read_result.data, str)
        assert read_result.data == "Hello, integration testing!"

    def test_write_then_find_workflow(self, tools, execution_context):
        """Test writing files then finding them - based on actual behavior."""
        # Write multiple files
        files_to_create = [
            ("main.py", "def main():\n    print('Hello World')"),
            ("utils.py", "def helper():\n    return 42"),
            ("README.md", "# Project Documentation")
        ]
        
        for filename, content in files_to_create:
            result = tools['write'].execute(
                execution_context,
                action="write_file",
                path=filename,
                content=content
            )
            assert result.success
            assert isinstance(result.data, str)
        
        # Find Python files - returns list of dicts
        find_result = tools['find'].execute(
            execution_context,
            action="find_files",
            pattern="*.py"
        )
        assert find_result.success
        assert isinstance(find_result.data, list)
        assert len(find_result.data) == 2  # main.py and utils.py
        
        # Verify dict structure
        for item in find_result.data:
            assert isinstance(item, dict)
            assert 'path' in item
            assert 'type' in item
            assert 'size' in item
        
        # Search for content - returns list of dicts with matches
        search_result = tools['find'].execute(
            execution_context,
            action="search_content",
            query="Hello World"
        )
        assert search_result.success
        assert isinstance(search_result.data, list)
        assert len(search_result.data) >= 1
        
        # Verify search result structure
        for match in search_result.data:
            assert isinstance(match, dict)
            assert 'file' in match
            assert 'line' in match
            assert 'content' in match

    def test_todo_task_integration(self, tools, execution_context):
        """Test integration between TodoTool and TaskTool - based on actual behavior."""
        # Create a complex task - returns dict with plan structure
        task_result = tools['task'].execute(
            execution_context,
            action="decompose_task",
            description="Build a simple web application with authentication"
        )
        assert task_result.success
        assert isinstance(task_result.data, dict)
        assert 'plan' in task_result.data
        assert 'plan_id' in task_result.data
        
        # Get the plan - verify structure
        plan = task_result.data['plan']
        assert isinstance(plan, dict)
        assert 'steps' in plan
        assert isinstance(plan['steps'], list)
        assert len(plan['steps']) > 0
        
        # Create todos for each step - returns dict for each creation
        todos_created = []
        for step in plan['steps'][:2]:  # Just test first 2 steps
            assert isinstance(step, dict)
            assert 'title' in step
            assert 'description' in step
            
            todo_result = tools['todo'].execute(
                execution_context,
                action="create_todo",
                title=step['title'],
                description=step['description'],
                priority="medium"
            )
            assert todo_result.success
            assert isinstance(todo_result.data, dict)
            assert 'id' in todo_result.data
            todos_created.append(todo_result.data['id'])
        
        # Verify todos were created - returns list of dicts
        list_result = tools['todo'].execute(
            execution_context,
            action="list_todos"
        )
        assert list_result.success
        assert isinstance(list_result.data, list)
        assert len(list_result.data) == len(todos_created)
        
        # Verify todo structure
        for todo in list_result.data:
            assert isinstance(todo, dict)
            assert 'id' in todo
            assert 'title' in todo
            assert 'status' in todo


class TestComplexWorkflows:
    """Test complex multi-tool workflows."""
    
    @pytest.fixture
    def tools(self):
        """Create instances of all tools."""
        return {
            'write': WriteTool(),
            'read': ReadTool(),
            'find': FindTool(),
            'execute': ExecuteTool(),
            'todo': TodoTool(),
            'task': TaskTool()
        }
    
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

    def test_project_creation_workflow(self, tools, execution_context):
        """Test a complete project creation workflow."""
        # 1. Decompose the task
        task_result = tools['task'].execute(
            execution_context,
            action="decompose_task",
            description="Create a Python CLI application"
        )
        assert task_result.success
        
        # 2. Create project structure
        project_files = [
            ("main.py", "#!/usr/bin/env python3\ndef main():\n    print('CLI App')"),
            ("requirements.txt", "click>=8.0.0\npytest>=7.0.0"),
            ("README.md", "# CLI Application\n\nA simple CLI application.")
        ]
        
        for filename, content in project_files:
            write_result = tools['write'].execute(
                execution_context,
                action="write_file",
                path=filename,
                content=content
            )
            assert write_result.success
        
        # 3. Verify all files were created
        find_result = tools['find'].execute(
            execution_context,
            action="find_files",
            pattern="*"
        )
        assert find_result.success
        assert len(find_result.data) >= 3
        
        # 4. Read and verify content
        read_result = tools['read'].execute(
            execution_context,
            action="read_file",
            path="main.py"
        )
        assert read_result.success
        assert "CLI App" in read_result.data
        
        # 5. Create todos for next steps
        todo_result = tools['todo'].execute(
            execution_context,
            action="create_todo",
            title="Add tests for CLI application",
            description="Write unit tests using pytest",
            priority="high"
        )
        assert todo_result.success

    def test_development_workflow(self, tools, execution_context):
        """Test a typical development workflow."""
        # 1. Create initial implementation
        initial_code = '''def calculate(a, b):
    """Calculate something."""
    return a + b

if __name__ == "__main__":
    result = calculate(2, 3)
    print(f"Result: {result}")
'''
        
        write_result = tools['write'].execute(
            execution_context,
            action="write_file",
            path="calculator.py",
            content=initial_code
        )
        assert write_result.success
        
        # 2. Find functions in the code
        find_result = tools['find'].execute(
            execution_context,
            action="search_content",
            query="def "
        )
        assert find_result.success
        
        # 3. Create a test plan
        task_result = tools['task'].execute(
            execution_context,
            action="decompose_task",
            description="Add comprehensive tests for calculator module"
        )
        assert task_result.success
        
        # 4. Create test file
        test_code = '''import pytest
from calculator import calculate

def test_calculate_positive():
    assert calculate(2, 3) == 5

def test_calculate_negative():
    assert calculate(-1, 1) == 0
'''
        
        write_test_result = tools['write'].execute(
            execution_context,
            action="write_file",
            path="test_calculator.py",
            content=test_code
        )
        assert write_test_result.success
        
        # 5. Verify project structure
        list_result = tools['find'].execute(
            execution_context,
            action="find_files",
            pattern="*"
        )
        assert list_result.success
        filenames = [item['path'] for item in list_result.data]
        assert "calculator.py" in filenames
        assert "test_calculator.py" in filenames


class TestToolDataConsistency:
    """Test that tools return consistent data formats."""
    
    @pytest.fixture
    def tools(self):
        """Create instances of all tools."""
        return {
            'write': WriteTool(),
            'read': ReadTool(),
            'find': FindTool(),
            'todo': TodoTool(),
            'task': TaskTool()
        }
    
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

    def test_all_tools_return_tool_result(self, tools, execution_context):
        """Test that all tools return ToolResult objects."""
        # Test WriteTool
        write_result = tools['write'].execute(
            execution_context,
            action="write_file",
            path="test.txt",
            content="test"
        )
        assert hasattr(write_result, 'success')
        assert hasattr(write_result, 'data')
        assert hasattr(write_result, 'error')
        assert hasattr(write_result, 'metadata')
        
        # Test ReadTool  
        read_result = tools['read'].execute(
            execution_context,
            action="read_file",
            path="test.txt"
        )
        assert hasattr(read_result, 'success')
        assert hasattr(read_result, 'data')
        
        # Test FindTool
        find_result = tools['find'].execute(
            execution_context,
            action="find_files",
            pattern="*.txt"
        )
        assert hasattr(find_result, 'success')
        assert hasattr(find_result, 'data')
        
        # Test TodoTool
        todo_result = tools['todo'].execute(
            execution_context,
            action="create_todo",
            title="Test Todo"
        )
        assert hasattr(todo_result, 'success')
        assert hasattr(todo_result, 'data')
        
        # Test TaskTool
        task_result = tools['task'].execute(
            execution_context,
            action="create_plan",
            title="Test Plan",
            description="Test description"
        )
        assert hasattr(task_result, 'success')
        assert hasattr(task_result, 'data')

    def test_successful_operations_have_data(self, tools, execution_context):
        """Test that successful operations return data."""
        # Create a file
        write_result = tools['write'].execute(
            execution_context,
            action="write_file",
            path="test.txt",
            content="test content"
        )
        assert write_result.success
        assert write_result.data is not None
        
        # Read the file
        read_result = tools['read'].execute(
            execution_context,
            action="read_file",
            path="test.txt"
        )
        assert read_result.success
        assert read_result.data is not None
        assert isinstance(read_result.data, str)
        
        # Find files
        find_result = tools['find'].execute(
            execution_context,
            action="find_files",
            pattern="*.txt"
        )
        assert find_result.success
        assert find_result.data is not None
        assert isinstance(find_result.data, list)

    def test_failed_operations_have_errors(self, tools, execution_context):
        """Test that failed operations return error messages."""
        # Try to read non-existent file
        read_result = tools['read'].execute(
            execution_context,
            action="read_file",
            path="nonexistent.txt"
        )
        assert not read_result.success
        assert read_result.error is not None
        assert read_result.data is None
        
        # Try invalid action
        invalid_result = tools['write'].execute(
            execution_context,
            action="invalid_action",
            path="test.txt"
        )
        assert not invalid_result.success
        assert invalid_result.error is not None


class TestSecurityIntegration:
    """Test security constraints across tool interactions."""
    
    @pytest.fixture
    def tools(self):
        """Create instances of all tools."""
        return {
            'write': WriteTool(),
            'read': ReadTool(),
            'find': FindTool()
        }
    
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

    def test_path_traversal_consistency(self, tools, execution_context):
        """Test that all tools consistently prevent path traversal."""
        dangerous_path = "../../../etc/passwd"
        
        # WriteTool should block
        write_result = tools['write'].execute(
            execution_context,
            action="write_file",
            path=dangerous_path,
            content="malicious"
        )
        assert not write_result.success
        
        # ReadTool should block
        read_result = tools['read'].execute(
            execution_context,
            action="read_file",
            path=dangerous_path
        )
        assert not read_result.success
        
        # FindTool should not find files outside workspace
        find_result = tools['find'].execute(
            execution_context,
            action="find_files",
            pattern=dangerous_path
        )
        # FindTool may succeed but return empty results
        assert find_result.success
        assert len(find_result.data) == 0

    def test_working_directory_isolation(self, tools, execution_context):
        """Test that tools are properly isolated to working directory."""
        # Create file in working directory
        write_result = tools['write'].execute(
            execution_context,
            action="write_file", 
            path="safe_file.txt",
            content="This is safe"
        )
        assert write_result.success
        
        # Verify file exists in workspace
        find_result = tools['find'].execute(
            execution_context,
            action="find_files",
            pattern="safe_file.txt"
        )
        assert find_result.success
        assert len(find_result.data) == 1
        
        # Verify we can read it
        read_result = tools['read'].execute(
            execution_context,
            action="read_file",
            path="safe_file.txt"
        )
        assert read_result.success
        assert "This is safe" in read_result.data