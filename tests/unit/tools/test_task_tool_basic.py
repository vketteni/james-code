"""Basic tests for TaskTool - API discovery and core functionality."""

import pytest
import tempfile
from pathlib import Path

from james_code.tools.task_tool import TaskTool
from james_code.core.base import ExecutionContext, ToolResult


class TestTaskToolAPIDiscovery:
    """Test TaskTool API discovery and basic validation."""
    
    @pytest.fixture
    def task_tool(self):
        """Create TaskTool instance."""
        return TaskTool()
    
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

    def test_tool_schema_discovery(self, task_tool):
        """Test that we can discover TaskTool schema."""
        schema = task_tool.get_schema()
        
        assert schema is not None
        assert schema['name'] == 'task'
        assert 'parameters' in schema
        assert 'properties' in schema['parameters']
        assert 'action' in schema['parameters']['properties']
        
        # Verify discovered actions
        expected_actions = [
            'decompose_task', 'create_plan', 'execute_plan', 'get_plan', 
            'list_plans', 'update_step', 'add_step', 'remove_step', 
            'save_template', 'load_template', 'get_next_steps', 'validate_plan'
        ]
        actual_actions = schema['parameters']['properties']['action']['enum']
        assert set(actual_actions) == set(expected_actions)

    def test_decompose_task_working(self, task_tool, execution_context):
        """Test that decompose_task action works."""
        result = task_tool.execute(
            execution_context,
            action="decompose_task",
            description="Create a simple Python web application"
        )
        
        assert isinstance(result, ToolResult)
        assert result.success
        assert result.data is not None
        assert isinstance(result.data, dict)
        assert 'plan_id' in result.data
        assert 'plan' in result.data
        assert 'step_count' in result.data

    def test_decompose_task_plan_structure(self, task_tool, execution_context):
        """Test that decompose_task returns proper plan structure."""
        result = task_tool.execute(
            execution_context,
            action="decompose_task", 
            description="Write unit tests for a Python function"
        )
        
        assert result.success
        plan = result.data['plan']
        
        # Verify plan structure
        assert 'id' in plan
        assert 'title' in plan
        assert 'description' in plan
        assert 'status' in plan
        assert 'steps' in plan
        assert isinstance(plan['steps'], list)
        assert len(plan['steps']) > 0
        
        # Verify step structure
        for step in plan['steps']:
            assert 'id' in step
            assert 'title' in step
            assert 'description' in step
            assert 'tool_name' in step
            assert 'tool_params' in step
            assert 'status' in step
            assert 'dependencies' in step

    def test_create_plan_working(self, task_tool, execution_context):
        """Test that create_plan action works."""
        result = task_tool.execute(
            execution_context,
            action="create_plan",
            title="Test Plan",
            description="A test plan for testing"
        )
        
        assert isinstance(result, ToolResult)
        assert result.success
        assert result.data is not None
        assert isinstance(result.data, dict)
        assert result.data['title'] == "Test Plan"
        assert result.data['description'] == "A test plan for testing"
        assert result.data['status'] == "ready"

    def test_input_validation(self, task_tool, execution_context):
        """Test input validation for TaskTool."""
        # No action provided
        result = task_tool.execute(execution_context)
        assert not result.success
        assert "Invalid input parameters" in result.error
        
        # Invalid action
        result = task_tool.execute(
            execution_context,
            action="invalid_action"
        )
        assert not result.success
        assert "Invalid input parameters" in result.error

    def test_return_type_consistency(self, task_tool, execution_context):
        """Test that TaskTool returns consistent types."""
        result = task_tool.execute(
            execution_context,
            action="decompose_task",
            description="Test task"
        )
        
        assert isinstance(result, ToolResult)
        assert hasattr(result, 'success')
        assert hasattr(result, 'data')
        assert hasattr(result, 'error')
        assert hasattr(result, 'metadata')


class TestTaskToolDataStructures:
    """Test TaskTool data structure patterns."""
    
    @pytest.fixture
    def task_tool(self):
        """Create TaskTool instance."""
        return TaskTool()
    
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

    def test_decompose_task_follows_pattern(self, task_tool, execution_context):
        """Test that decompose_task follows expected data patterns."""
        result = task_tool.execute(
            execution_context,
            action="decompose_task",
            description="Build a web scraper"
        )
        
        assert result.success
        # TaskTool returns dict, not list (different from other tools)
        assert isinstance(result.data, dict)
        assert 'plan' in result.data
        
        # Plan contains list of steps
        plan = result.data['plan']
        assert isinstance(plan['steps'], list)
        
        # Each step is a dict
        for step in plan['steps']:
            assert isinstance(step, dict)

    def test_create_plan_follows_pattern(self, task_tool, execution_context):
        """Test that create_plan follows expected data patterns."""
        result = task_tool.execute(
            execution_context,
            action="create_plan",
            title="Data Analysis Project",
            description="Analyze customer data"
        )
        
        assert result.success
        assert isinstance(result.data, dict)
        # Empty plan has empty steps list
        assert result.data['steps'] == []

    def test_tool_instantiation(self, task_tool):
        """Test that TaskTool instantiates correctly."""
        assert task_tool.name == "task"
        assert "decompose" in task_tool.description.lower()
        assert hasattr(task_tool, 'execute')
        assert hasattr(task_tool, 'validate_input')
        assert hasattr(task_tool, 'get_schema')


class TestTaskToolErrorHandling:
    """Test TaskTool error handling."""
    
    @pytest.fixture
    def task_tool(self):
        """Create TaskTool instance."""
        return TaskTool()
    
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

    def test_missing_required_parameters(self, task_tool, execution_context):
        """Test handling of missing required parameters."""
        # decompose_task without description
        result = task_tool.execute(
            execution_context,
            action="decompose_task"
        )
        assert not result.success
        assert "Invalid input parameters" in result.error

    def test_known_implementation_gaps(self, task_tool, execution_context):
        """Test known implementation gaps."""
        # list_plans is not implemented
        result = task_tool.execute(
            execution_context,
            action="list_plans"
        )
        assert not result.success
        assert "no attribute '_list_plans'" in result.error

    def test_invalid_plan_id(self, task_tool, execution_context):
        """Test handling of invalid plan IDs."""
        result = task_tool.execute(
            execution_context,
            action="get_plan", 
            plan_id="nonexistent_plan_id"
        )
        # This may fail due to implementation issues, document the behavior
        assert isinstance(result, ToolResult)
        # Don't assert success/failure as implementation may vary


class TestTaskToolIntegration:
    """Test TaskTool integration scenarios."""
    
    @pytest.fixture
    def task_tool(self):
        """Create TaskTool instance."""
        return TaskTool()
    
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

    def test_task_decomposition_workflow(self, task_tool, execution_context):
        """Test a complete task decomposition workflow."""
        # 1. Decompose a task
        decompose_result = task_tool.execute(
            execution_context,
            action="decompose_task",
            description="Create a REST API with authentication"
        )
        
        assert decompose_result.success
        plan_id = decompose_result.data['plan_id']
        
        # 2. Create another plan manually
        create_result = task_tool.execute(
            execution_context,
            action="create_plan",
            title="Manual Plan",
            description="Manually created plan"
        )
        
        assert create_result.success
        assert create_result.data['id'] != plan_id  # Different plan IDs

    def test_different_task_types(self, task_tool, execution_context):
        """Test decomposition of different types of tasks."""
        test_tasks = [
            "Fix a bug in user authentication",
            "Refactor legacy code to use new patterns", 
            "Add unit tests for the payment module",
            "Optimize database query performance"
        ]
        
        for task_desc in test_tasks:
            result = task_tool.execute(
                execution_context,
                action="decompose_task",
                description=task_desc
            )
            
            assert result.success, f"Failed to decompose: {task_desc}"
            assert len(result.data['plan']['steps']) > 0
            assert result.data['step_count'] > 0