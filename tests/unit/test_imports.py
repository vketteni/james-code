"""Test that all imports work correctly."""

import pytest


def test_main_package_imports():
    """Test that main package imports work."""
    from james_code import Agent, AgentConfig
    from james_code import Tool, ToolResult, ExecutionContext
    from james_code import SafetyManager, SafetyConfig
    from james_code import ReadTool, WriteTool, ExecuteTool
    from james_code import FindTool, UpdateTool, TodoTool, TaskTool
    
    # Check that classes are properly imported
    assert Agent is not None
    assert AgentConfig is not None
    assert Tool is not None
    assert ToolResult is not None
    assert SafetyManager is not None
    assert ReadTool is not None


def test_core_module_imports():
    """Test that core modules can be imported directly."""
    from james_code.core import Agent, AgentConfig
    from james_code.core.base import Tool, ToolResult
    from james_code.core.agent import Agent as DirectAgent
    
    # Verify they're the same classes
    assert Agent is DirectAgent


def test_tools_module_imports():
    """Test that tools can be imported individually."""
    from james_code.tools.read_tool import ReadTool
    from james_code.tools.write_tool import WriteTool
    from james_code.tools.execute_tool import ExecuteTool
    from james_code.tools.find_tool import FindTool
    from james_code.tools.update_tool import UpdateTool
    from james_code.tools.todo_tool import TodoTool
    from james_code.tools.task_tool import TaskTool
    
    # Verify all tools are classes
    assert isinstance(ReadTool(), ReadTool)
    assert isinstance(WriteTool(), WriteTool)


def test_safety_module_imports():
    """Test that safety modules can be imported."""
    from james_code.safety import SafetyManager, SafetyConfig
    from james_code.safety.safety_manager import SafetyManager as DirectSafetyManager
    
    # Verify they're the same classes
    assert SafetyManager is DirectSafetyManager


def test_version_attribute():
    """Test that version is accessible."""
    import james_code
    
    assert hasattr(james_code, '__version__')
    assert isinstance(james_code.__version__, str)
    assert james_code.__version__ == "0.1.0"


def test_all_attribute():
    """Test that __all__ is properly defined."""
    import james_code
    
    assert hasattr(james_code, '__all__')
    assert isinstance(james_code.__all__, list)
    assert len(james_code.__all__) > 0
    
    # Check that all items in __all__ are actually available
    for item in james_code.__all__:
        assert hasattr(james_code, item), f"{item} not found in james_code module"