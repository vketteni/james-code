#!/usr/bin/env python3
"""
Living Documentation: File Operations Workflow

This executable example demonstrates common file operations patterns.
It serves as both documentation and a test case to ensure examples stay current.
"""

import sys
import tempfile
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "src"))

from james_code import Agent, AgentConfig
from james_code.core.base import ExecutionContext


def test_basic_file_operations():
    """Test basic READ/WRITE operations."""
    print("🔧 Testing Basic File Operations")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Set up agent
        config = AgentConfig(working_directory=temp_dir, verbose_logging=False)
        agent = Agent(config)
        
        # Get tools
        read_tool = agent.tool_registry.get_tool("read")
        write_tool = agent.tool_registry.get_tool("write")
        
        # Test 1: Create a file
        print("  📝 Creating test file...")
        result = write_tool.execute(
            agent.execution_context,
            action="write_file",
            path="example.txt",
            content="Hello, World!\nThis is a test file.\n"
        )
        assert result.success, f"File creation failed: {result.error}"
        print("  ✅ File created successfully")
        
        # Test 2: Read the file back
        print("  👀 Reading file content...")
        result = read_tool.execute(
            agent.execution_context,
            action="read_file",
            path="example.txt"
        )
        assert result.success, f"File reading failed: {result.error}"
        assert "Hello, World!" in result.data, "File content not as expected"
        print("  ✅ File read successfully")
        
        # Test 3: List directory
        print("  📁 Listing directory...")
        result = read_tool.execute(
            agent.execution_context,
            action="list_directory",
            path="."
        )
        assert result.success, f"Directory listing failed: {result.error}"
        assert any(item["name"] == "example.txt" for item in result.data), "File not found in directory"
        print("  ✅ Directory listed successfully")
        
        return True


def test_surgical_file_updates():
    """Test UPDATE tool for surgical file modifications."""
    print("🔧 Testing Surgical File Updates")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Set up agent
        config = AgentConfig(working_directory=temp_dir, verbose_logging=False)
        agent = Agent(config)
        
        # Get tools
        write_tool = agent.tool_registry.get_tool("write")
        update_tool = agent.tool_registry.get_tool("update")
        read_tool = agent.tool_registry.get_tool("read")
        
        # Create initial file
        initial_content = """def hello():
    print("Hello")

def world():
    print("World")
    
def main():
    hello()
    world()
"""
        
        print("  📝 Creating initial Python file...")
        result = write_tool.execute(
            agent.execution_context,
            action="write_file",
            path="script.py",
            content=initial_content
        )
        assert result.success, f"Initial file creation failed: {result.error}"
        
        # Test 1: Update specific lines
        print("  ✏️ Updating specific lines...")
        result = update_tool.execute(
            agent.execution_context,
            action="update_lines",
            path="script.py",
            start_line=2,
            end_line=2,
            new_content='    print("Hello, Agent!")'
        )
        assert result.success, f"Line update failed: {result.error}"
        print("  ✅ Lines updated successfully")
        
        # Test 2: Replace pattern
        print("  🔄 Replacing pattern...")
        result = update_tool.execute(
            agent.execution_context,
            action="replace_pattern",
            path="script.py",
            pattern="def world():",
            replacement="def world(name='World'):"
        )
        assert result.success, f"Pattern replacement failed: {result.error}"
        print("  ✅ Pattern replaced successfully")
        
        # Test 3: Verify changes
        print("  🔍 Verifying changes...")
        result = read_tool.execute(
            agent.execution_context,
            action="read_file",
            path="script.py"
        )
        assert result.success, f"File verification failed: {result.error}"
        content = result.data
        assert "Hello, Agent!" in content, "Line update not applied"
        assert "def world(name='World'):" in content, "Pattern replacement not applied"
        print("  ✅ Changes verified successfully")
        
        return True


def test_search_and_modify_workflow():
    """Test integrated FIND → READ → UPDATE workflow."""
    print("🔧 Testing Search and Modify Workflow")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Set up agent
        config = AgentConfig(working_directory=temp_dir, verbose_logging=False)
        agent = Agent(config)
        
        # Get tools
        write_tool = agent.tool_registry.get_tool("write")
        find_tool = agent.tool_registry.get_tool("find")
        update_tool = agent.tool_registry.get_tool("update")
        
        # Create multiple Python files
        files_to_create = {
            "module1.py": "def old_function():\n    return 'old'\n",
            "module2.py": "from module1 import old_function\nprint(old_function())\n",
            "test_module.py": "def test_old_function():\n    assert old_function() == 'old'\n"
        }
        
        print("  📝 Creating test files...")
        for filename, content in files_to_create.items():
            result = write_tool.execute(
                agent.execution_context,
                action="write_file",
                path=filename,
                content=content
            )
            assert result.success, f"Failed to create {filename}: {result.error}"
        
        # Test 1: Find all Python files
        print("  🔍 Finding Python files...")
        result = find_tool.execute(
            agent.execution_context,
            action="find_files",
            pattern="*.py"
        )
        assert result.success, f"File search failed: {result.error}"
        assert len(result.data) == 3, f"Expected 3 files, found {len(result.data)}"
        print("  ✅ Found all Python files")
        
        # Test 2: Search for old_function usage
        print("  🔍 Searching for function usage...")
        result = find_tool.execute(
            agent.execution_context,
            action="search_content",
            query="old_function",
            file_types=["*.py"]
        )
        assert result.success, f"Content search failed: {result.error}"
        assert len(result.data) >= 3, f"Expected at least 3 matches, found {len(result.data)}"
        print("  ✅ Found function usage")
        
        # Test 3: Update function name in all files
        print("  🔄 Updating function name across files...")
        files_with_function = set()
        for match in result.data:
            files_with_function.add(match["file"])
        
        for file_path in files_with_function:
            update_result = update_tool.execute(
                agent.execution_context,
                action="replace_pattern",
                path=file_path,
                pattern="old_function",
                replacement="new_function"
            )
            assert update_result.success, f"Failed to update {file_path}: {update_result.error}"
        
        print("  ✅ Updated function name across all files")
        
        # Test 4: Verify changes
        print("  🔍 Verifying changes...")
        verification_result = find_tool.execute(
            agent.execution_context,
            action="search_content",
            query="new_function",
            file_types=["*.py"]
        )
        assert verification_result.success, f"Verification search failed: {verification_result.error}"
        assert len(verification_result.data) >= 3, "Not all functions were renamed"
        
        # Ensure old function name is gone
        old_check = find_tool.execute(
            agent.execution_context,
            action="search_content",
            query="old_function",
            file_types=["*.py"]
        )
        assert old_check.success, f"Old function check failed: {old_check.error}"
        assert len(old_check.data) == 0, "Old function name still exists"
        
        print("  ✅ All changes verified successfully")
        
        return True


def test_task_driven_file_operations():
    """Test task management integration with file operations."""
    print("🔧 Testing Task-Driven File Operations")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Set up agent
        config = AgentConfig(working_directory=temp_dir, verbose_logging=False)
        agent = Agent(config)
        
        # Get tools
        todo_tool = agent.tool_registry.get_tool("todo")
        task_tool = agent.tool_registry.get_tool("task")
        
        # Test 1: Create a todo for file operations
        print("  📋 Creating file operation todo...")
        result = todo_tool.execute(
            agent.execution_context,
            action="create_todo",
            title="Create project structure",
            description="Set up basic Python project structure",
            priority="high",
            tags=["setup", "files"]
        )
        assert result.success, f"Todo creation failed: {result.error}"
        todo_id = result.data["id"]
        print("  ✅ Todo created successfully")
        
        # Test 2: Add subtasks
        print("  📋 Adding subtasks...")
        subtasks = [
            "Create main.py",
            "Create requirements.txt", 
            "Create README.md"
        ]
        
        for subtask_title in subtasks:
            result = todo_tool.execute(
                agent.execution_context,
                action="add_subtask",
                todo_id=todo_id,
                subtask_title=subtask_title
            )
            assert result.success, f"Subtask creation failed: {result.error}"
        
        print("  ✅ Subtasks added successfully")
        
        # Test 3: Task decomposition
        print("  🧩 Testing task decomposition...")
        result = task_tool.execute(
            agent.execution_context,
            action="decompose_task",
            description="Create a Python calculator module",
            task_type="development"
        )
        assert result.success, f"Task decomposition failed: {result.error}"
        plan_data = result.data["plan"]
        assert len(plan_data["steps"]) > 0, "No steps generated"
        print("  ✅ Task decomposed successfully")
        
        # Test 4: List todos
        print("  📋 Listing todos...")
        result = todo_tool.execute(
            agent.execution_context,
            action="list_todos"
        )
        assert result.success, f"Todo listing failed: {result.error}"
        assert len(result.data) >= 4, "Not all todos found"  # 1 main + 3 subtasks
        print("  ✅ Todos listed successfully")
        
        return True


def main():
    """Run all workflow tests."""
    print("🚀 File Operations Workflow - Living Documentation Tests")
    print("=" * 60)
    
    tests = [
        test_basic_file_operations,
        test_surgical_file_updates,
        test_search_and_modify_workflow,
        test_task_driven_file_operations
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            print(f"\n{test_func.__name__.replace('_', ' ').title()}")
            print("-" * 40)
            
            if test_func():
                print("  🎉 Test PASSED")
                passed += 1
            else:
                print("  ❌ Test FAILED")
                failed += 1
                
        except Exception as e:
            print(f"  💥 Test ERROR: {str(e)}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All workflow tests passed! Documentation examples are working correctly.")
        return True
    else:
        print("❌ Some tests failed. Documentation examples need attention.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)