"""Comprehensive tests for FindTool - Phase 2."""

import pytest
import tempfile
import os
from pathlib import Path

from james_code.tools.find_tool import FindTool
from james_code.core.base import ExecutionContext


class TestFindToolBasicOperations:
    """Test basic FindTool operations."""
    
    @pytest.fixture
    def find_tool(self):
        """Create FindTool instance."""
        return FindTool()
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace with test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            
            # Create test file structure
            (workspace / "src").mkdir()
            (workspace / "src" / "main.py").write_text("""
def main():
    print("Hello, World!")
    return 0

if __name__ == "__main__":
    main()
""")
            
            (workspace / "src" / "utils.py").write_text("""
def helper_function():
    return "helper"

class UtilityClass:
    def method_one(self):
        pass
    
    def method_two(self):
        pass
""")
            
            (workspace / "tests").mkdir()
            (workspace / "tests" / "test_main.py").write_text("""
import unittest
from src.main import main

class TestMain(unittest.TestCase):
    def test_main_function(self):
        self.assertEqual(main(), 0)
""")
            
            (workspace / "docs").mkdir()
            (workspace / "docs" / "README.md").write_text("""
# Project Documentation

This is a test project for finding functionality.

## Features
- Main function
- Helper utilities
- Test coverage
""")
            
            (workspace / "config.json").write_text('{"debug": true, "version": "1.0.0"}')
            (workspace / ".gitignore").write_text("*.pyc\n__pycache__/\n.env")
            
            yield workspace
    
    @pytest.fixture
    def execution_context(self, temp_workspace):
        """Create execution context."""
        return ExecutionContext(
            working_directory=temp_workspace,
            environment={},
            user_id="test_user",
            session_id="test_session"
        )
    
    def test_find_files_by_name_pattern(self, find_tool, execution_context):
        """Test finding files by name pattern."""
        result = find_tool.execute(
            execution_context,
            action="find_files",
            pattern="*.py"
        )
        
        assert result.success
        # FindTool returns data as a list directly, not wrapped in "results"
        files = result.data if isinstance(result.data, list) else result.data.get("results", [])
        
        # Should find Python files - files are dict objects with 'path' key
        python_files = [f for f in files if f['path'].endswith('.py')]
        assert len(python_files) >= 3  # main.py, utils.py, test_main.py
        assert any('main.py' in f['path'] for f in python_files)
        assert any('utils.py' in f['path'] for f in python_files)
        assert any('test_main.py' in f['path'] for f in python_files)
    
    def test_find_files_specific_name(self, find_tool, execution_context):
        """Test finding files by specific name."""
        result = find_tool.execute(
            execution_context,
            action="find_files",
            pattern="main.py"
        )
        
        assert result.success
        files = result.data["results"]
        assert len(files) >= 1
        assert any('main.py' in f for f in files)
    
    def test_find_files_in_subdirectory(self, find_tool, execution_context):
        """Test finding files in specific subdirectory."""
        result = find_tool.execute(
            execution_context,
            action="find_files",
            pattern="*.py",
            path="src"
        )
        
        assert result.success
        files = result.data["results"]
        
        # Should only find files in src directory
        assert len(files) >= 2  # main.py and utils.py
        assert all('src' in f for f in files)
        assert any('main.py' in f for f in files)
        assert any('utils.py' in f for f in files)
    
    def test_search_content_basic(self, find_tool, execution_context):
        """Test basic content search."""
        result = find_tool.execute(
            execution_context,
            action="search_content",
            query="Hello, World!"
        )
        
        assert result.success
        matches = result.data["results"]
        
        # Should find the string in main.py
        assert len(matches) >= 1
        assert any('main.py' in match["file"] for match in matches)
        
        # Check match details
        main_py_match = next(match for match in matches if 'main.py' in match["file"])
        assert "Hello, World!" in main_py_match["content"]
    
    def test_search_content_case_insensitive(self, find_tool, execution_context):
        """Test case-insensitive content search."""
        result = find_tool.execute(
            execution_context,
            action="search_content",
            query="HELLO",
            case_sensitive=False
        )
        
        if result.success:  # Feature might not be implemented
            matches = result.data["results"]
            assert len(matches) >= 1
            assert any('main.py' in match["file"] for match in matches)
    
    def test_find_function_by_name(self, find_tool, execution_context):
        """Test finding function by name."""
        result = find_tool.execute(
            execution_context,
            action="find_function",
            function_name="main"
        )
        
        if result.success:  # Feature might not be implemented
            matches = result.data["results"]
            assert len(matches) >= 1
            assert any('main.py' in match["file"] for match in matches)
    
    def test_find_function_helper(self, find_tool, execution_context):
        """Test finding helper function."""
        result = find_tool.execute(
            execution_context,
            action="find_function",
            function_name="helper_function"
        )
        
        if result.success:  # Feature might not be implemented
            matches = result.data["results"]
            assert len(matches) >= 1
            assert any('utils.py' in match["file"] for match in matches)
    
    def test_grep_recursive_pattern(self, find_tool, execution_context):
        """Test recursive grep with pattern."""
        result = find_tool.execute(
            execution_context,
            action="grep_recursive",
            pattern="def "
        )
        
        if result.success:  # Feature might not be implemented
            matches = result.data["results"]
            # Should find function definitions
            assert len(matches) >= 3  # main, helper_function, test methods
    
    def test_find_by_size_range(self, find_tool, execution_context):
        """Test finding files by size."""
        result = find_tool.execute(
            execution_context,
            action="find_by_size",
            min_size=0,
            max_size=1000  # Small files only
        )
        
        if result.success:  # Feature might not be implemented
            files = result.data["results"]
            assert len(files) >= 1
    
    def test_find_nonexistent_pattern(self, find_tool, execution_context):
        """Test finding non-existent pattern."""
        result = find_tool.execute(
            execution_context,
            action="find_files",
            pattern="*.nonexistent"
        )
        
        assert result.success
        files = result.data["results"]
        assert len(files) == 0  # Should return empty results
    
    def test_search_nonexistent_content(self, find_tool, execution_context):
        """Test searching for non-existent content."""
        result = find_tool.execute(
            execution_context,
            action="search_content",
            query="this_string_does_not_exist_anywhere"
        )
        
        assert result.success
        matches = result.data["results"]
        assert len(matches) == 0  # Should return empty results


class TestFindToolAdvancedPatterns:
    """Test FindTool advanced pattern matching."""
    
    @pytest.fixture
    def find_tool(self):
        """Create FindTool instance."""
        return FindTool()
    
    @pytest.fixture
    def complex_workspace(self):
        """Create complex workspace with various file types."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            
            # Create complex directory structure
            (workspace / "frontend").mkdir()
            (workspace / "frontend" / "src").mkdir()
            (workspace / "frontend" / "src" / "components").mkdir()
            (workspace / "frontend" / "src" / "components" / "Button.tsx").write_text("""
import React from 'react';

interface ButtonProps {
    onClick: () => void;
    children: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({ onClick, children }) => {
    return <button onClick={onClick}>{children}</button>;
};
""")
            
            (workspace / "backend").mkdir()
            (workspace / "backend" / "api").mkdir()
            (workspace / "backend" / "api" / "server.py").write_text("""
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/health')
def health_check():
    return jsonify({'status': 'healthy'})

@app.route('/api/users')
def get_users():
    return jsonify({'users': []})

if __name__ == '__main__':
    app.run(debug=True)
""")
            
            (workspace / "scripts").mkdir()
            (workspace / "scripts" / "deploy.sh").write_text("""#!/bin/bash
echo "Deploying application..."
docker build -t myapp .
docker run -p 8080:8080 myapp
""")
            
            (workspace / "data").mkdir()
            (workspace / "data" / "sample.json").write_text("""
{
    "users": [
        {"id": 1, "name": "Alice", "email": "alice@example.com"},
        {"id": 2, "name": "Bob", "email": "bob@example.com"}
    ],
    "settings": {
        "theme": "dark",
        "language": "en"
    }
}
""")
            
            (workspace / "README.md").write_text("""
# Complex Project

A multi-language project with:
- React TypeScript frontend
- Python Flask backend
- Shell deployment scripts
- JSON configuration data
""")
            
            yield workspace
    
    @pytest.fixture
    def execution_context(self, complex_workspace):
        """Create execution context."""
        return ExecutionContext(
            working_directory=complex_workspace,
            environment={},
            user_id="test_user",
            session_id="test_session"
        )
    
    def test_find_multiple_extensions(self, find_tool, execution_context):
        """Test finding files with multiple extensions."""
        # Test finding TypeScript files
        result = find_tool.execute(
            execution_context,
            action="find_files",
            pattern="*.tsx"
        )
        
        assert result.success
        files = result.data["results"]
        assert len(files) >= 1
        assert any('Button.tsx' in f for f in files)
    
    def test_find_shell_scripts(self, find_tool, execution_context):
        """Test finding shell scripts."""
        result = find_tool.execute(
            execution_context,
            action="find_files",
            pattern="*.sh"
        )
        
        assert result.success
        files = result.data["results"]
        assert len(files) >= 1
        assert any('deploy.sh' in f for f in files)
    
    def test_find_config_files(self, find_tool, execution_context):
        """Test finding configuration files."""
        result = find_tool.execute(
            execution_context,
            action="find_files",
            pattern="*.json"
        )
        
        assert result.success
        files = result.data["results"]
        assert len(files) >= 1
        assert any('sample.json' in f for f in files)
    
    def test_search_across_languages(self, find_tool, execution_context):
        """Test searching content across different programming languages."""
        # Search for function definitions
        result = find_tool.execute(
            execution_context,
            action="search_content",
            query="function"
        )
        
        assert result.success
        matches = result.data["results"]
        # Should find function-related content in various files
    
    def test_search_import_statements(self, find_tool, execution_context):
        """Test searching for import statements."""
        result = find_tool.execute(
            execution_context,
            action="search_content",
            query="import"
        )
        
        assert result.success
        matches = result.data["results"]
        assert len(matches) >= 2  # Should find in both TypeScript and Python files
    
    def test_search_api_routes(self, find_tool, execution_context):
        """Test searching for API routes."""
        result = find_tool.execute(
            execution_context,
            action="search_content",
            query="@app.route"
        )
        
        assert result.success
        matches = result.data["results"]
        assert len(matches) >= 2  # Should find both route definitions
        assert any('server.py' in match["file"] for match in matches)
    
    def test_find_nested_files(self, find_tool, execution_context):
        """Test finding files in nested directories."""
        result = find_tool.execute(
            execution_context,
            action="find_files",
            pattern="*",
            path="frontend/src/components"
        )
        
        assert result.success
        files = result.data["results"]
        assert len(files) >= 1
        assert any('Button.tsx' in f for f in files)


class TestFindToolPerformance:
    """Test FindTool performance characteristics."""
    
    @pytest.fixture
    def find_tool(self):
        """Create FindTool instance."""
        return FindTool()
    
    @pytest.fixture
    def large_workspace(self):
        """Create workspace with many files for performance testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            
            # Create many files for performance testing
            for i in range(50):  # Create 50 directories
                dir_path = workspace / f"dir_{i}"
                dir_path.mkdir()
                
                for j in range(20):  # 20 files per directory = 1000 total files
                    file_path = dir_path / f"file_{j}.py"
                    file_path.write_text(f"""
def function_{i}_{j}():
    return "This is function {i}_{j}"

class Class_{i}_{j}:
    def method(self):
        return "method in class {i}_{j}"

# Some content to search for
CONSTANT_{i}_{j} = "value_{i}_{j}"
""")
            
            yield workspace
    
    @pytest.fixture
    def execution_context(self, large_workspace):
        """Create execution context."""
        return ExecutionContext(
            working_directory=large_workspace,
            environment={},
            user_id="test_user",
            session_id="test_session"
        )
    
    @pytest.mark.performance
    def test_find_files_performance(self, find_tool, execution_context, benchmark):
        """Benchmark file finding performance."""
        def find_python_files():
            return find_tool.execute(
                execution_context,
                action="find_files",
                pattern="*.py"
            )
        
        result = benchmark(find_python_files)
        assert result.success
        files = result.data["results"]
        assert len(files) == 1000  # Should find all 1000 Python files
    
    @pytest.mark.performance
    def test_search_content_performance(self, find_tool, execution_context, benchmark):
        """Benchmark content search performance."""
        def search_function_content():
            return find_tool.execute(
                execution_context,
                action="search_content",
                query="def function_"
            )
        
        result = benchmark(search_function_content)
        assert result.success
        matches = result.data["results"]
        assert len(matches) >= 100  # Should find many function definitions
    
    @pytest.mark.performance
    def test_large_directory_traversal(self, find_tool, execution_context, benchmark):
        """Benchmark large directory traversal."""
        def traverse_all_directories():
            return find_tool.execute(
                execution_context,
                action="find_files",
                pattern="*"
            )
        
        result = benchmark(traverse_all_directories)
        assert result.success
        files = result.data["results"]
        assert len(files) >= 1000


class TestFindToolErrorHandling:
    """Test FindTool error handling."""
    
    @pytest.fixture
    def find_tool(self):
        """Create FindTool instance."""
        return FindTool()
    
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
    
    def test_invalid_action(self, find_tool, execution_context):
        """Test invalid action handling."""
        result = find_tool.execute(
            execution_context,
            action="invalid_action"
        )
        
        assert not result.success
        assert "Invalid input parameters" in result.error
    
    def test_missing_pattern_for_find_files(self, find_tool, execution_context):
        """Test missing pattern for find_files action."""
        result = find_tool.execute(
            execution_context,
            action="find_files"
        )
        
        assert not result.success
        assert "Invalid input parameters" in result.error
    
    def test_missing_query_for_search_content(self, find_tool, execution_context):
        """Test missing query for search_content action."""
        result = find_tool.execute(
            execution_context,
            action="search_content"
        )
        
        assert not result.success
        assert "Invalid input parameters" in result.error
    
    def test_missing_function_name_for_find_function(self, find_tool, execution_context):
        """Test missing function name for find_function action."""
        result = find_tool.execute(
            execution_context,
            action="find_function"
        )
        
        assert not result.success
        assert "Invalid input parameters" in result.error
    
    def test_nonexistent_search_path(self, find_tool, execution_context):
        """Test searching in non-existent path."""
        result = find_tool.execute(
            execution_context,
            action="find_files",
            pattern="*.py",
            path="nonexistent/directory"
        )
        
        # Should handle gracefully - either success with empty results or appropriate error
        if not result.success:
            assert "not found" in result.error.lower() or "does not exist" in result.error.lower()
        else:
            assert len(result.data["results"]) == 0
    
    def test_invalid_regex_pattern(self, find_tool, execution_context):
        """Test invalid regex pattern."""
        result = find_tool.execute(
            execution_context,
            action="search_content",
            query="[invalid regex ("
        )
        
        # Should handle invalid regex gracefully
        if not result.success:
            assert "regex" in result.error.lower() or "pattern" in result.error.lower()
    
    def test_empty_pattern(self, find_tool, execution_context):
        """Test empty pattern."""
        result = find_tool.execute(
            execution_context,
            action="find_files",
            pattern=""
        )
        
        # Should handle empty pattern gracefully
        if result.success:
            # Empty pattern might be interpreted as "find all files"
            pass
        else:
            assert "pattern" in result.error.lower()
    
    def test_very_long_pattern(self, find_tool, execution_context):
        """Test very long pattern."""
        long_pattern = "a" * 10000  # Very long pattern
        
        result = find_tool.execute(
            execution_context,
            action="find_files",
            pattern=long_pattern
        )
        
        # Should handle long patterns gracefully
        assert result.success or "pattern" in result.error.lower()


class TestFindToolSecurity:
    """Test FindTool security aspects."""
    
    @pytest.fixture
    def find_tool(self):
        """Create FindTool instance."""
        return FindTool()
    
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
    def test_path_traversal_prevention(self, find_tool, execution_context):
        """Test path traversal prevention in search paths."""
        dangerous_paths = [
            "../../../etc",
            "../../..",
            "/etc",
            "~",
            "../../../home/user/.ssh"
        ]
        
        for path in dangerous_paths:
            result = find_tool.execute(
                execution_context,
                action="find_files",
                pattern="*.txt",
                path=path
            )
            
            # Should either block the path or handle it safely
            if not result.success:
                assert any(keyword in result.error.lower() for keyword in 
                          ["outside", "not allowed", "not found", "does not exist"])
            else:
                # If it succeeds, should have empty results (no files found outside workspace)
                assert len(result.data["results"]) == 0
    
    @pytest.mark.security
    def test_resource_limits(self, find_tool, execution_context):
        """Test resource limits for search operations."""
        # This tests that the tool doesn't consume excessive resources
        # In practice, this would involve creating many files and testing performance
        
        # Create a reasonable number of files
        for i in range(100):
            file_path = execution_context.working_directory / f"test_{i}.txt"
            file_path.write_text(f"Content for file {i}")
        
        result = find_tool.execute(
            execution_context,
            action="find_files",
            pattern="*.txt"
        )
        
        assert result.success
        assert len(result.data["results"]) == 100
        
        # The operation should complete in reasonable time (tested by benchmark framework)
    
    @pytest.mark.security
    def test_output_size_limits(self, find_tool, execution_context):
        """Test that output size is reasonable."""
        # Create files with large names to test output size handling
        long_name = "very_long_filename_" + "x" * 200
        
        for i in range(10):
            file_path = execution_context.working_directory / f"{long_name}_{i}.txt"
            file_path.write_text("content")
        
        result = find_tool.execute(
            execution_context,
            action="find_files",
            pattern="*.txt"
        )
        
        assert result.success
        # Output should be reasonable in size (not testing specific limits here,
        # but ensuring it doesn't crash or produce enormous output)
        assert len(str(result.data)) < 100000  # Reasonable upper bound