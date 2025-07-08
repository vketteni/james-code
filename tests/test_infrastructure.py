"""Test the new testing infrastructure."""

import pytest
from pathlib import Path

from tests.fixtures.complex_scenarios import complex_codebase, git_repository, large_files
from tests.fixtures.security_vectors import security_vectors, malicious_file_contents
from tests.utils.security_helpers import SecurityTestHelper, validate_security_boundary
from tests.utils.filesystem_helpers import FileSystemTestHelper
from tests.utils.assertion_helpers import assert_tool_result_valid


def test_complex_codebase_fixture(complex_codebase):
    """Test that complex codebase fixture works correctly."""
    # Check that main files exist
    assert "src/main.py" in complex_codebase
    assert "requirements.txt" in complex_codebase
    assert "tests/test_engine.py" in complex_codebase
    
    # Verify file contents
    main_file = complex_codebase["src/main.py"]
    assert main_file.exists()
    content = main_file.read_text()
    assert "def main():" in content
    assert "Engine" in content
    
    # Check directory structure
    src_dir = main_file.parent
    assert src_dir.name == "src"
    assert (src_dir / "core").exists()
    assert (src_dir / "utils").exists()


def test_git_repository_fixture(git_repository):
    """Test that git repository fixture works correctly."""
    assert git_repository.exists()
    assert (git_repository / ".git").exists()
    
    # Test that we can get git info
    import subprocess
    result = subprocess.run(
        ["git", "log", "--oneline"], 
        cwd=git_repository, 
        capture_output=True, 
        text=True
    )
    assert result.returncode == 0
    assert len(result.stdout.strip().split('\n')) >= 2  # At least 2 commits


def test_large_files_fixture(large_files):
    """Test that large files fixture works correctly."""
    assert "small.txt" in large_files
    assert "medium.txt" in large_files
    assert "large.txt" in large_files
    assert "huge.txt" in large_files
    
    # Check file sizes
    small_file = large_files["small.txt"]
    large_file = large_files["large.txt"]
    
    assert small_file.stat().st_size >= 1024  # At least 1KB
    assert large_file.stat().st_size >= 1024 * 1024  # At least 1MB


def test_security_vectors_fixture(security_vectors):
    """Test that security vectors fixture works correctly."""
    # Check that all attack types are present
    expected_types = [
        'path_traversal', 'command_injection', 'file_permission_bypass',
        'resource_exhaustion', 'unicode_attacks', 'encoding_attacks'
    ]
    
    for attack_type in expected_types:
        assert attack_type in security_vectors
        assert len(security_vectors[attack_type]) > 0
    
    # Check some specific vectors
    path_traversal = security_vectors['path_traversal']
    assert "../../../etc/passwd" in path_traversal
    assert "..\\..\\..\\windows\\system32\\config\\sam" in path_traversal
    
    command_injection = security_vectors['command_injection']
    assert "ls; rm -rf /" in command_injection
    assert "ls && whoami" in command_injection


def test_malicious_file_contents_fixture(malicious_file_contents):
    """Test that malicious file contents fixture works correctly."""
    expected_types = [
        'zip_bomb', 'fake_exe', 'malicious_script', 
        'null_bytes', 'large_file', 'eicar'
    ]
    
    for content_type in expected_types:
        assert content_type in malicious_file_contents
        assert isinstance(malicious_file_contents[content_type], bytes)
    
    # Check EICAR test string
    eicar = malicious_file_contents['eicar']
    assert b'EICAR-STANDARD-ANTIVIRUS-TEST-FILE' in eicar


def test_filesystem_helper(temp_workspace):
    """Test filesystem helper functionality."""
    helper = FileSystemTestHelper(temp_workspace)
    
    # Test snapshot functionality
    snapshot1 = helper.take_snapshot()
    assert snapshot1.timestamp > 0
    
    # Create a file and take another snapshot
    test_file = temp_workspace / "test.txt"
    test_file.write_text("test content")
    
    snapshot2 = helper.take_snapshot()
    
    # Check for changes
    changes = snapshot1.compare(snapshot2)
    assert len(changes) == 1
    assert changes[0].action == "created"
    assert "test.txt" in changes[0].path


def test_security_helper_path_validation(temp_workspace):
    """Test security helper path validation."""
    # Mock SafetyManager for testing
    class MockSafetyManager:
        def validate_path(self, path):
            # Simple validation: reject paths with ..
            return ".." not in path
    
    helper = SecurityTestHelper(MockSafetyManager())
    
    # Mock ExecutionContext
    class MockContext:
        def __init__(self, workspace):
            self.working_directory = workspace
    
    context = MockContext(temp_workspace)
    
    # Test safe paths
    safe_paths = ["file.txt", "dir/file.txt", "subdir/nested/file.txt"]
    results = helper.test_path_traversal(safe_paths, context)
    
    # All should pass (not be blocked)
    for result in results:
        assert not result.blocked
    
    # Test malicious paths
    malicious_paths = ["../etc/passwd", "../../secret.txt"]
    results = helper.test_path_traversal(malicious_paths, context)
    
    # All should be blocked
    for result in results:
        assert result.blocked


def test_assertion_helpers():
    """Test assertion helper functions."""
    from james_code.core.base import ToolResult
    
    # Test successful result validation
    success_result = ToolResult(
        success=True,
        data="test data",
        metadata={"operation": "test"}
    )
    
    # Should not raise
    assert_tool_result_valid(success_result, expected_success=True)
    
    # Test failed result validation
    failure_result = ToolResult(
        success=False,
        data=None,
        error="Test error message",
        metadata={"operation": "test"}
    )
    
    # Should not raise
    assert_tool_result_valid(failure_result, expected_success=False)


def test_infrastructure_integration(complex_codebase, security_vectors, temp_workspace):
    """Test integration between different infrastructure components."""
    # Use complex codebase with security testing
    fs_helper = FileSystemTestHelper(temp_workspace)
    
    # Take initial snapshot
    initial_snapshot = fs_helper.take_snapshot()
    
    # Simulate some file operations on the complex codebase
    src_files = [path for name, path in complex_codebase.items() if name.startswith("src/")]
    assert len(src_files) > 0
    
    # Read a few files to simulate tool operations
    for file_path in src_files[:3]:  # Just test first 3
        content = file_path.read_text()
        assert len(content) > 0
    
    # Test security vectors on file paths
    path_vectors = security_vectors['path_traversal'][:5]  # Test first 5
    
    # These should all be considered dangerous
    for vector in path_vectors:
        # Simple check: dangerous paths typically contain ..
        is_dangerous = ".." in vector or vector.startswith("/")
        assert is_dangerous, f"Expected {vector} to be flagged as dangerous"


@pytest.mark.performance
def test_infrastructure_performance(large_files):
    """Test performance of infrastructure components."""
    import time
    
    # Test that large file fixture creation is reasonably fast
    start_time = time.time()
    
    # Read the large file
    large_file = large_files["large.txt"]
    content = large_file.read_text()
    
    end_time = time.time()
    read_time = end_time - start_time
    
    # Should read 1MB file in reasonable time (less than 1 second)
    assert read_time < 1.0, f"Large file read took too long: {read_time:.3f}s"
    assert len(content) >= 1024 * 1024, "Large file should be at least 1MB"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])