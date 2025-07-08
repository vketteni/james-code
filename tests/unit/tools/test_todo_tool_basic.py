"""Basic tests for TodoTool - CRUD operations and functionality."""

import pytest
import tempfile
from pathlib import Path

from james_code.tools.todo_tool import TodoTool
from james_code.core.base import ExecutionContext, ToolResult


class TestTodoToolAPIDiscovery:
    """Test TodoTool API discovery and basic validation."""
    
    @pytest.fixture
    def todo_tool(self):
        """Create TodoTool instance."""
        return TodoTool()
    
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

    def test_tool_schema_discovery(self, todo_tool):
        """Test that we can discover TodoTool schema."""
        schema = todo_tool.get_schema()
        
        assert schema is not None
        assert schema['name'] == 'todo'
        assert 'parameters' in schema
        assert 'properties' in schema['parameters']
        assert 'action' in schema['parameters']['properties']
        
        # Verify discovered actions
        expected_actions = [
            'create_todo', 'list_todos', 'update_todo', 'delete_todo',
            'add_subtask', 'get_todo', 'search_todos', 'get_stats'
        ]
        actual_actions = schema['parameters']['properties']['action']['enum']
        assert set(actual_actions) == set(expected_actions)

    def test_input_validation(self, todo_tool, execution_context):
        """Test input validation for TodoTool."""
        # No action provided
        result = todo_tool.execute(execution_context)
        assert not result.success
        assert "Invalid input parameters" in result.error
        
        # Invalid action
        result = todo_tool.execute(
            execution_context,
            action="invalid_action"
        )
        assert not result.success
        assert "Invalid input parameters" in result.error

    def test_tool_instantiation(self, todo_tool):
        """Test that TodoTool instantiates correctly."""
        assert todo_tool.name == "todo"
        assert "todo" in todo_tool.description.lower()
        assert hasattr(todo_tool, 'execute')
        assert hasattr(todo_tool, 'validate_input')
        assert hasattr(todo_tool, 'get_schema')


class TestTodoToolCRUDOperations:
    """Test TodoTool CRUD operations."""
    
    @pytest.fixture
    def todo_tool(self):
        """Create TodoTool instance."""
        return TodoTool()
    
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

    def test_create_todo_basic(self, todo_tool, execution_context):
        """Test basic todo creation."""
        result = todo_tool.execute(
            execution_context,
            action="create_todo",
            title="Test Todo",
            description="A test todo item"
        )
        
        assert isinstance(result, ToolResult)
        assert result.success
        assert result.data is not None
        assert isinstance(result.data, dict)
        assert result.data['title'] == "Test Todo"
        assert result.data['description'] == "A test todo item"
        assert 'id' in result.data
        assert result.data['status'] == 'pending'

    def test_create_todo_with_priority(self, todo_tool, execution_context):
        """Test creating todo with priority."""
        result = todo_tool.execute(
            execution_context,
            action="create_todo",
            title="High Priority Task",
            priority="high"
        )
        
        assert result.success
        assert result.data['priority'] == 'high'

    def test_list_todos(self, todo_tool, execution_context):
        """Test listing todos."""
        # Create a todo first
        create_result = todo_tool.execute(
            execution_context,
            action="create_todo",
            title="Todo for listing",
            description="This will be listed"
        )
        assert create_result.success
        
        # List todos
        list_result = todo_tool.execute(
            execution_context,
            action="list_todos"
        )
        
        assert isinstance(list_result, ToolResult)
        assert list_result.success
        assert isinstance(list_result.data, list)
        assert len(list_result.data) >= 1
        
        # Verify our todo is in the list
        todo_found = False
        for todo in list_result.data:
            if todo['title'] == "Todo for listing":
                todo_found = True
                break
        assert todo_found

    def test_get_todo_with_valid_id(self, todo_tool, execution_context):
        """Test getting a specific todo by ID."""
        # Create a todo first
        create_result = todo_tool.execute(
            execution_context,
            action="create_todo",
            title="Specific Todo",
            description="For testing get_todo"
        )
        assert create_result.success
        todo_id = create_result.data['id']
        
        # Get the specific todo
        get_result = todo_tool.execute(
            execution_context,
            action="get_todo",
            todo_id=todo_id
        )
        
        assert get_result.success
        assert get_result.data['id'] == todo_id
        assert get_result.data['title'] == "Specific Todo"

    def test_get_todo_with_invalid_id(self, todo_tool, execution_context):
        """Test getting todo with invalid ID."""
        result = todo_tool.execute(
            execution_context,
            action="get_todo", 
            todo_id="nonexistent_id"
        )
        
        assert not result.success
        assert "Todo not found" in result.error

    def test_update_todo(self, todo_tool, execution_context):
        """Test updating a todo."""
        # Create a todo first
        create_result = todo_tool.execute(
            execution_context,
            action="create_todo",
            title="Original Title",
            description="Original description"
        )
        assert create_result.success
        todo_id = create_result.data['id']
        
        # Update the todo
        update_result = todo_tool.execute(
            execution_context,
            action="update_todo",
            todo_id=todo_id,
            title="Updated Title",
            description="Updated description",
            status="in_progress"
        )
        
        assert update_result.success
        assert update_result.data['title'] == "Updated Title"
        assert update_result.data['description'] == "Updated description"
        assert update_result.data['status'] == "in_progress"

    def test_delete_todo(self, todo_tool, execution_context):
        """Test deleting a todo."""
        # Create a todo first
        create_result = todo_tool.execute(
            execution_context,
            action="create_todo",
            title="Todo to Delete",
            description="This will be deleted"
        )
        assert create_result.success
        todo_id = create_result.data['id']
        
        # Delete the todo
        delete_result = todo_tool.execute(
            execution_context,
            action="delete_todo",
            todo_id=todo_id
        )
        
        assert delete_result.success
        
        # Verify it's gone
        get_result = todo_tool.execute(
            execution_context,
            action="get_todo",
            todo_id=todo_id
        )
        assert not get_result.success
        assert "Todo not found" in get_result.error


class TestTodoToolDataStructures:
    """Test TodoTool data structure patterns."""
    
    @pytest.fixture
    def todo_tool(self):
        """Create TodoTool instance."""
        return TodoTool()
    
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

    def test_create_todo_returns_dict(self, todo_tool, execution_context):
        """Test that create_todo returns proper dict structure."""
        result = todo_tool.execute(
            execution_context,
            action="create_todo",
            title="Structure Test",
            description="Testing data structure"
        )
        
        assert result.success
        assert isinstance(result.data, dict)
        
        # Verify required fields
        required_fields = [
            'id', 'title', 'description', 'status', 'priority',
            'created_at', 'updated_at', 'tags', 'subtasks'
        ]
        for field in required_fields:
            assert field in result.data

    def test_list_todos_returns_list_of_dicts(self, todo_tool, execution_context):
        """Test that list_todos follows consistent pattern."""
        # Create some todos
        for i in range(3):
            todo_tool.execute(
                execution_context,
                action="create_todo",
                title=f"Todo {i}",
                description=f"Description {i}"
            )
        
        # List todos
        result = todo_tool.execute(
            execution_context,
            action="list_todos"
        )
        
        assert result.success
        assert isinstance(result.data, list)
        assert len(result.data) >= 3
        
        # Each item should be a dict
        for todo in result.data:
            assert isinstance(todo, dict)
            assert 'id' in todo
            assert 'title' in todo

    def test_return_type_consistency(self, todo_tool, execution_context):
        """Test that TodoTool returns consistent types."""
        result = todo_tool.execute(
            execution_context,
            action="create_todo",
            title="Consistency Test"
        )
        
        assert isinstance(result, ToolResult)
        assert hasattr(result, 'success')
        assert hasattr(result, 'data')
        assert hasattr(result, 'error')
        assert hasattr(result, 'metadata')


class TestTodoToolAdvancedFeatures:
    """Test TodoTool advanced features."""
    
    @pytest.fixture
    def todo_tool(self):
        """Create TodoTool instance."""
        return TodoTool()
    
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

    def test_add_subtask(self, todo_tool, execution_context):
        """Test adding subtasks to todos."""
        # Create parent todo
        parent_result = todo_tool.execute(
            execution_context,
            action="create_todo",
            title="Parent Task",
            description="Main task with subtasks"
        )
        assert parent_result.success
        parent_id = parent_result.data['id']
        
        # Add subtask
        subtask_result = todo_tool.execute(
            execution_context,
            action="add_subtask",
            todo_id=parent_id,
            subtask_title="Subtask 1",
            subtask_description="First subtask"
        )
        
        assert subtask_result.success

    def test_search_todos(self, todo_tool, execution_context):
        """Test searching todos."""
        # Create todos with searchable content
        todo_tool.execute(
            execution_context,
            action="create_todo",
            title="Important Meeting",
            description="Meeting with client"
        )
        
        todo_tool.execute(
            execution_context,
            action="create_todo",
            title="Code Review",
            description="Review pull request"
        )
        
        # Search for todos
        search_result = todo_tool.execute(
            execution_context,
            action="search_todos",
            query="meeting"
        )
        
        assert search_result.success
        assert isinstance(search_result.data, list)
        # Should find at least the meeting todo
        meeting_found = any("meeting" in todo['title'].lower() for todo in search_result.data)
        assert meeting_found

    def test_get_stats(self, todo_tool, execution_context):
        """Test getting todo statistics."""
        # Create todos with different statuses
        todo_tool.execute(
            execution_context,
            action="create_todo",
            title="Pending Task",
            status="pending"
        )
        
        todo_tool.execute(
            execution_context,
            action="create_todo",
            title="Completed Task",
            status="completed"
        )
        
        # Get stats
        stats_result = todo_tool.execute(
            execution_context,
            action="get_stats"
        )
        
        assert stats_result.success
        assert isinstance(stats_result.data, dict)
        # Should contain count information
        assert 'total_count' in stats_result.data or 'counts' in stats_result.data

    def test_create_todo_with_tags(self, todo_tool, execution_context):
        """Test creating todo with tags."""
        result = todo_tool.execute(
            execution_context,
            action="create_todo",
            title="Tagged Todo",
            description="Todo with tags",
            tags=["urgent", "work", "client"]
        )
        
        assert result.success
        assert result.data['tags'] == ["urgent", "work", "client"]

    def test_todo_workflow_integration(self, todo_tool, execution_context):
        """Test a complete todo workflow."""
        # 1. Create todo
        create_result = todo_tool.execute(
            execution_context,
            action="create_todo",
            title="Workflow Test",
            description="Testing complete workflow",
            priority="high"
        )
        assert create_result.success
        todo_id = create_result.data['id']
        
        # 2. Update todo to in_progress
        update_result = todo_tool.execute(
            execution_context,
            action="update_todo",
            todo_id=todo_id,
            status="in_progress"
        )
        assert update_result.success
        
        # 3. Add subtask
        subtask_result = todo_tool.execute(
            execution_context,
            action="add_subtask",
            todo_id=todo_id,
            subtask_title="Review requirements"
        )
        assert subtask_result.success
        
        # 4. Complete todo
        complete_result = todo_tool.execute(
            execution_context,
            action="update_todo",
            todo_id=todo_id,
            status="completed"
        )
        assert complete_result.success
        
        # 5. Verify final state
        final_result = todo_tool.execute(
            execution_context,
            action="get_todo",
            todo_id=todo_id
        )
        assert final_result.success
        assert final_result.data['status'] == "completed"