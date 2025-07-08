"""Advanced multi-tool workflow tests based on real tool behavior."""

import pytest
import tempfile
from pathlib import Path

from james_code.tools.write_tool import WriteTool
from james_code.tools.read_tool import ReadTool
from james_code.tools.find_tool import FindTool
from james_code.tools.todo_tool import TodoTool
from james_code.tools.task_tool import TaskTool
from james_code.core.base import ExecutionContext


class TestProjectDevelopmentWorkflow:
    """Test complete project development scenarios."""
    
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

    def test_full_project_creation_workflow(self, tools, execution_context):
        """Test a complete project creation from task to implementation."""
        
        # 1. Start with task decomposition
        task_result = tools['task'].execute(
            execution_context,
            action="decompose_task",
            description="Create a Python CLI tool for file processing"
        )
        assert task_result.success
        assert isinstance(task_result.data, dict)
        plan = task_result.data['plan']
        steps = plan['steps']
        assert len(steps) >= 3
        
        # 2. Create todos from task plan
        created_todos = []
        for step in steps[:3]:  # First 3 steps
            todo_result = tools['todo'].execute(
                execution_context,
                action="create_todo",
                title=step['title'],
                description=step['description'],
                priority="high"
            )
            assert todo_result.success
            created_todos.append(todo_result.data)
        
        # 3. Implement project structure
        project_files = {
            "main.py": '''#!/usr/bin/env python3
"""CLI tool for file processing."""

import argparse
import sys
from pathlib import Path

def process_file(filepath):
    """Process a single file."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        return len(content.splitlines())
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return 0

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Process files")
    parser.add_argument("files", nargs="+", help="Files to process")
    args = parser.parse_args()
    
    total_lines = 0
    for filepath in args.files:
        lines = process_file(filepath)
        print(f"{filepath}: {lines} lines")
        total_lines += lines
    
    print(f"Total lines: {total_lines}")

if __name__ == "__main__":
    main()
''',
            "requirements.txt": "# No external dependencies required\n",
            "README.md": '''# File Processing CLI

A simple CLI tool for processing files and counting lines.

## Usage

```bash
python main.py file1.txt file2.txt
```

## Features

- Count lines in multiple files
- Error handling for invalid files
- Summary statistics
''',
            "tests/test_main.py": '''"""Tests for main module."""

import pytest
from pathlib import Path
import tempfile
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import process_file

def test_process_file():
    """Test file processing function."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("Line 1\\nLine 2\\nLine 3\\n")
        temp_path = f.name
    
    try:
        result = process_file(temp_path)
        assert result == 3
    finally:
        os.unlink(temp_path)

def test_process_nonexistent_file():
    """Test handling of nonexistent files."""
    result = process_file("nonexistent.txt")
    assert result == 0
'''
        }
        
        # Create all project files
        for filepath, content in project_files.items():
            # Create directory if needed
            file_path = Path(filepath)
            if file_path.parent != Path('.'):
                tools['write'].execute(
                    execution_context,
                    action="create_directory",
                    path=str(file_path.parent)
                )
            
            write_result = tools['write'].execute(
                execution_context,
                action="write_file",
                path=filepath,
                content=content
            )
            assert write_result.success
        
        # 4. Verify project structure
        find_result = tools['find'].execute(
            execution_context,
            action="find_files",
            pattern="*"
        )
        assert find_result.success
        assert len(find_result.data) >= 4  # At least main.py, requirements.txt, README.md, test_main.py
        
        # Verify specific files exist
        filenames = [item['path'] for item in find_result.data]
        assert "main.py" in filenames
        assert "README.md" in filenames
        assert "requirements.txt" in filenames
        
        # 5. Read and verify main implementation
        read_result = tools['read'].execute(
            execution_context,
            action="read_file",
            path="main.py"
        )
        assert read_result.success
        assert "def main():" in read_result.data
        assert "argparse" in read_result.data
        
        # 6. Search for functions in the codebase
        search_result = tools['find'].execute(
            execution_context,
            action="search_content",
            query="def "
        )
        assert search_result.success
        assert len(search_result.data) >= 3  # main, process_file, test_process_file
        
        # 7. Update todos to completed
        for todo in created_todos:
            update_result = tools['todo'].execute(
                execution_context,
                action="update_todo",
                todo_id=todo['id'],
                status="completed"
            )
            assert update_result.success
        
        # 8. Verify todos were updated
        list_result = tools['todo'].execute(
            execution_context,
            action="list_todos"
        )
        assert list_result.success
        completed_count = sum(1 for todo in list_result.data if todo['status'] == 'completed')
        assert completed_count == len(created_todos)

    def test_code_analysis_workflow(self, tools, execution_context):
        """Test analyzing existing code with multiple tools."""
        
        # 1. Create a codebase to analyze
        codebase_files = {
            "src/calculator.py": '''"""Calculator module with various operations."""

class Calculator:
    """A simple calculator class."""
    
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        """Add two numbers."""
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def multiply(self, a, b):
        """Multiply two numbers."""
        result = a * b
        self.history.append(f"{a} * {b} = {result}")
        return result
    
    def get_history(self):
        """Get calculation history."""
        return self.history.copy()
''',
            "src/utils.py": '''"""Utility functions."""

def validate_number(value):
    """Validate that a value is a number."""
    try:
        float(value)
        return True
    except ValueError:
        return False

def format_result(result):
    """Format calculation result."""
    if isinstance(result, float) and result.is_integer():
        return int(result)
    return round(result, 2)
''',
            "tests/test_calculator.py": '''"""Tests for calculator module."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from calculator import Calculator

def test_add():
    calc = Calculator()
    assert calc.add(2, 3) == 5

def test_multiply():
    calc = Calculator()
    assert calc.multiply(4, 5) == 20
'''
        }
        
        # Create the codebase
        for filepath, content in codebase_files.items():
            file_path = Path(filepath)
            if file_path.parent != Path('.'):
                tools['write'].execute(
                    execution_context,
                    action="create_directory",
                    path=str(file_path.parent)
                )
            
            write_result = tools['write'].execute(
                execution_context,
                action="write_file",
                path=filepath,
                content=content
            )
            assert write_result.success
        
        # 2. Analyze the codebase structure
        # Find all Python files
        py_files = tools['find'].execute(
            execution_context,
            action="find_files",
            pattern="*.py"
        )
        assert py_files.success
        assert len(py_files.data) == 3
        
        # 3. Find all classes
        classes = tools['find'].execute(
            execution_context,
            action="search_content",
            query="class "
        )
        assert classes.success
        class_matches = [match for match in classes.data if "class " in match['content']]
        assert len(class_matches) >= 1  # Calculator class
        
        # 4. Find all functions
        functions = tools['find'].execute(
            execution_context,
            action="search_content",
            query="def "
        )
        assert functions.success
        assert len(functions.data) >= 6  # Multiple def statements
        
        # 5. Create analysis todos
        analysis_todos = [
            "Review Calculator class implementation",
            "Check test coverage for utils module",
            "Document API methods",
            "Add error handling for edge cases"
        ]
        
        created_todos = []
        for todo_title in analysis_todos:
            todo_result = tools['todo'].execute(
                execution_context,
                action="create_todo",
                title=todo_title,
                priority="medium"
            )
            assert todo_result.success
            created_todos.append(todo_result.data['id'])
        
        # 6. Read specific files for detailed analysis
        calc_content = tools['read'].execute(
            execution_context,
            action="read_file",
            path="src/calculator.py"
        )
        assert calc_content.success
        assert "class Calculator:" in calc_content.data
        assert "def add(" in calc_content.data
        
        # 7. Search for potential issues
        # Look for TODO comments
        todos_in_code = tools['find'].execute(
            execution_context,
            action="search_content", 
            query="TODO"
        )
        assert todos_in_code.success
        # May or may not find TODOs, just verify search works
        
        # 8. Create a summary analysis task
        summary_task = tools['task'].execute(
            execution_context,
            action="decompose_task",
            description="Refactor calculator module for better maintainability"
        )
        assert summary_task.success
        refactor_plan = summary_task.data['plan']
        assert len(refactor_plan['steps']) > 0

    def test_documentation_workflow(self, tools, execution_context):
        """Test creating documentation from code analysis."""
        
        # 1. Create a simple module to document
        module_code = '''"""Math utilities module."""

def fibonacci(n):
    """Calculate the nth Fibonacci number.
    
    Args:
        n (int): The position in the Fibonacci sequence
        
    Returns:
        int: The nth Fibonacci number
        
    Raises:
        ValueError: If n is negative
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def factorial(n):
    """Calculate the factorial of n.
    
    Args:
        n (int): A non-negative integer
        
    Returns:
        int: The factorial of n
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    if n <= 1:
        return 1
    return n * factorial(n-1)
'''
        
        # Create the module
        write_result = tools['write'].execute(
            execution_context,
            action="write_file",
            path="math_utils.py",
            content=module_code
        )
        assert write_result.success
        
        # 2. Analyze the module
        # Find all functions
        functions = tools['find'].execute(
            execution_context,
            action="search_content",
            query="def "
        )
        assert functions.success
        function_names = []
        for match in functions.data:
            if "def " in match['content']:
                # Extract function name
                line = match['content'].strip()
                if line.startswith("def "):
                    func_name = line.split("(")[0].replace("def ", "")
                    function_names.append(func_name)
        
        assert "fibonacci" in function_names
        assert "factorial" in function_names
        
        # 3. Create documentation plan
        doc_task = tools['task'].execute(
            execution_context,
            action="decompose_task",
            description="Create comprehensive documentation for math_utils module"
        )
        assert doc_task.success
        doc_plan = doc_task.data['plan']
        
        # 4. Create documentation files
        readme_content = f'''# Math Utils Module

A collection of mathematical utility functions.

## Functions

### fibonacci(n)
Calculate the nth Fibonacci number.

### factorial(n) 
Calculate the factorial of n.

## Usage

```python
from math_utils import fibonacci, factorial

# Calculate 10th Fibonacci number
fib_10 = fibonacci(10)

# Calculate factorial of 5
fact_5 = factorial(5)
```

## Functions Found: {len(function_names)}
- {', '.join(function_names)}
'''
        
        readme_result = tools['write'].execute(
            execution_context,
            action="write_file",
            path="README.md",
            content=readme_content
        )
        assert readme_result.success
        
        # 5. Create examples file
        examples_content = '''"""Examples for math_utils module."""

from math_utils import fibonacci, factorial

def demonstrate_fibonacci():
    """Demonstrate Fibonacci function."""
    print("Fibonacci sequence:")
    for i in range(10):
        print(f"F({i}) = {fibonacci(i)}")

def demonstrate_factorial():
    """Demonstrate factorial function."""
    print("Factorials:")
    for i in range(1, 6):
        print(f"{i}! = {factorial(i)}")

if __name__ == "__main__":
    demonstrate_fibonacci()
    print()
    demonstrate_factorial()
'''
        
        examples_result = tools['write'].execute(
            execution_context,
            action="write_file",
            path="examples.py",
            content=examples_content
        )
        assert examples_result.success
        
        # 6. Verify documentation was created
        docs_files = tools['find'].execute(
            execution_context,
            action="find_files",
            pattern="*.md"
        )
        assert docs_files.success
        assert any(item['path'] == 'README.md' for item in docs_files.data)
        
        # 7. Read back the documentation
        readme_check = tools['read'].execute(
            execution_context,
            action="read_file",
            path="README.md"
        )
        assert readme_check.success
        assert "fibonacci" in readme_check.data
        assert "factorial" in readme_check.data
        assert str(len(function_names)) in readme_check.data
        
        # 8. Create todos for documentation maintenance
        doc_todos = [
            "Add unit tests examples to documentation",
            "Create API reference documentation", 
            "Add performance notes for recursive functions"
        ]
        
        for todo_title in doc_todos:
            todo_result = tools['todo'].execute(
                execution_context,
                action="create_todo",
                title=todo_title,
                description="Documentation maintenance task",
                priority="low"
            )
            assert todo_result.success


class TestErrorHandlingWorkflows:
    """Test error handling in complex workflows."""
    
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

    def test_graceful_error_recovery(self, tools, execution_context):
        """Test that workflows can recover from individual tool failures."""
        
        # 1. Create a valid file
        write_result = tools['write'].execute(
            execution_context,
            action="write_file",
            path="valid.txt",
            content="This is valid content"
        )
        assert write_result.success
        
        # 2. Try to read a non-existent file (should fail gracefully)
        read_error = tools['read'].execute(
            execution_context,
            action="read_file",
            path="nonexistent.txt"
        )
        assert not read_error.success
        assert read_error.error is not None
        assert read_error.data is None
        
        # 3. Continue workflow with valid operations
        find_result = tools['find'].execute(
            execution_context,
            action="find_files",
            pattern="*.txt"
        )
        assert find_result.success
        assert len(find_result.data) == 1
        assert find_result.data[0]['path'] == 'valid.txt'
        
        # 4. Create todo to track the error
        todo_result = tools['todo'].execute(
            execution_context,
            action="create_todo",
            title="Investigate missing file: nonexistent.txt",
            priority="high"
        )
        assert todo_result.success
        
        # 5. Verify workflow continues normally
        read_valid = tools['read'].execute(
            execution_context,
            action="read_file",
            path="valid.txt"
        )
        assert read_valid.success
        assert read_valid.data == "This is valid content"

    def test_partial_workflow_completion(self, tools, execution_context):
        """Test handling when some workflow steps fail."""
        
        # 1. Create task plan
        task_result = tools['task'].execute(
            execution_context,
            action="decompose_task",
            description="Process a batch of files with error handling"
        )
        assert task_result.success
        plan = task_result.data['plan']
        
        # 2. Create some files, simulate some missing
        successful_files = []
        failed_files = []
        
        test_files = ["file1.txt", "file2.txt", "file3.txt"]
        
        # Create only first two files
        for i, filename in enumerate(test_files[:2]):
            write_result = tools['write'].execute(
                execution_context,
                action="write_file",
                path=filename,
                content=f"Content of {filename}"
            )
            if write_result.success:
                successful_files.append(filename)
            else:
                failed_files.append(filename)
        
        # Try to read all files (third will fail)
        for filename in test_files:
            read_result = tools['read'].execute(
                execution_context,
                action="read_file",
                path=filename
            )
            if not read_result.success:
                failed_files.append(filename)
        
        # 3. Create todos for successful and failed operations
        created_todo_ids = []
        for filename in successful_files:
            todo_result = tools['todo'].execute(
                execution_context,
                action="create_todo",
                title=f"Successfully processed {filename}",
                priority="low"
            )
            assert todo_result.success
            created_todo_ids.append(todo_result.data['id'])
        
        # Mark successful todos as completed
        for todo_id in created_todo_ids:
            update_result = tools['todo'].execute(
                execution_context,
                action="update_todo",
                todo_id=todo_id,
                status="completed"
            )
            assert update_result.success
        
        for filename in failed_files:
            todo_result = tools['todo'].execute(
                execution_context,
                action="create_todo",
                title=f"Failed to process {filename}",
                priority="high"
            )
            assert todo_result.success
        
        # 4. Verify we have the right counts
        list_result = tools['todo'].execute(
            execution_context,
            action="list_todos"
        )
        assert list_result.success
        
        completed_todos = [t for t in list_result.data if t['status'] == 'completed']
        pending_todos = [t for t in list_result.data if t['status'] == 'pending']
        
        assert len(completed_todos) == len(successful_files)
        assert len(pending_todos) == len(failed_files)
        
        # 5. Find files that actually exist
        find_result = tools['find'].execute(
            execution_context,
            action="find_files",
            pattern="*.txt"
        )
        assert find_result.success
        assert len(find_result.data) == len(successful_files)


class TestPerformanceWorkflows:
    """Test performance characteristics of complex workflows."""
    
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

    @pytest.mark.performance
    def test_large_codebase_analysis(self, tools, execution_context):
        """Test analyzing a larger codebase efficiently."""
        import time
        
        start_time = time.time()
        
        # 1. Create multiple modules
        modules = {
            f"module_{i}.py": f'''"""Module {i} with various functions."""

def function_a_{i}():
    """Function A in module {i}."""
    return {i} * 2

def function_b_{i}():
    """Function B in module {i}.""" 
    return {i} * 3

class Class_{i}:
    """Class {i}."""
    
    def method_1(self):
        """Method 1."""
        return {i}
    
    def method_2(self):
        """Method 2."""
        return {i} + 1
''' for i in range(10)
        }
        
        # Create all modules
        for filename, content in modules.items():
            write_result = tools['write'].execute(
                execution_context,
                action="write_file",
                path=filename,
                content=content
            )
            assert write_result.success
        
        module_creation_time = time.time() - start_time
        
        # 2. Analyze the codebase
        analysis_start = time.time()
        
        # Find all Python files
        py_files = tools['find'].execute(
            execution_context,
            action="find_files",
            pattern="*.py"
        )
        assert py_files.success
        assert len(py_files.data) == 10
        
        # Find all functions
        functions = tools['find'].execute(
            execution_context,
            action="search_content",
            query="def "
        )
        assert functions.success
        assert len(functions.data) >= 30  # 3 functions per module * 10 modules
        
        # Find all classes
        classes = tools['find'].execute(
            execution_context,
            action="search_content",
            query="class "
        )
        assert classes.success
        assert len(classes.data) >= 10  # 1 class per module
        
        analysis_time = time.time() - analysis_start
        
        # 3. Create comprehensive task plan
        task_start = time.time()
        
        task_result = tools['task'].execute(
            execution_context,
            action="decompose_task",
            description="Refactor large codebase for better maintainability"
        )
        assert task_result.success
        
        task_time = time.time() - task_start
        
        # 4. Performance assertions
        total_time = time.time() - start_time
        
        # These are reasonable performance expectations
        assert module_creation_time < 2.0  # Creating 10 modules should be fast
        assert analysis_time < 1.0  # Analysis should be sub-second
        assert task_time < 0.5  # Task decomposition should be fast
        assert total_time < 3.0  # Entire workflow should complete quickly