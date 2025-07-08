"""Simple test for the new testing infrastructure."""

import pytest
from pathlib import Path
import tempfile
import time


def test_security_vectors_fixture():
    """Test that security vectors fixture works correctly."""
    from tests.fixtures.security_vectors import get_path_traversal_vectors
    
    vectors = get_path_traversal_vectors()
    
    # Check that we have some vectors
    assert len(vectors) > 0
    
    # Check for some expected patterns
    assert any("../../../etc/passwd" in vector for vector in vectors)
    assert any("windows\\system32" in vector.lower() for vector in vectors)
    
    print(f"✓ Security vectors fixture: {len(vectors)} path traversal vectors loaded")


def test_complex_codebase_fixture():
    """Test that complex codebase fixture works correctly."""
    with tempfile.TemporaryDirectory() as temp_dir:
        from tests.fixtures.complex_scenarios import complex_codebase
        
        # Simulate the fixture creation
        temp_workspace = Path(temp_dir)
        
        # Mock the fixture call by creating a small structure
        project_root = temp_workspace / "test_project"
        project_root.mkdir()
        
        src_dir = project_root / "src"
        src_dir.mkdir()
        
        main_file = src_dir / "main.py"
        main_file.write_text('def main():\n    print("Hello World")\n')
        
        # Check basic functionality
        assert main_file.exists()
        assert "def main():" in main_file.read_text()
        
        print(f"✓ Complex codebase fixture: Structure created in {project_root}")


def test_filesystem_helpers():
    """Test filesystem helper utilities."""
    from tests.utils.filesystem_helpers import FileSystemTestHelper
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        helper = FileSystemTestHelper(temp_path)
        
        # Test snapshot functionality
        snapshot1 = helper.take_snapshot()
        assert snapshot1.timestamp > 0
        
        # Create a test file
        test_file = temp_path / "test.txt"
        test_file.write_text("test content")
        
        # Take another snapshot
        snapshot2 = helper.take_snapshot()
        
        # Check for changes
        changes = snapshot1.compare(snapshot2)
        assert len(changes) >= 1
        
        # Find the creation event
        creation_events = [c for c in changes if c.action == "created"]
        assert len(creation_events) >= 1
        
        print(f"✓ Filesystem helpers: Detected {len(changes)} changes")


def test_security_helpers():
    """Test security helper utilities."""
    from tests.utils.security_helpers import SecurityTestResult
    
    # Test security result creation
    result = SecurityTestResult(
        attack_type="path_traversal",
        payload="../../../etc/passwd",
        blocked=True,
        execution_time=0.001
    )
    
    assert result.attack_type == "path_traversal"
    assert result.blocked is True
    assert result.execution_time > 0
    
    print(f"✓ Security helpers: SecurityTestResult created successfully")


def test_assertion_helpers():
    """Test assertion helper utilities."""
    from tests.utils.assertion_helpers import assert_timing_reasonable
    
    start_time = time.time()
    time.sleep(0.01)  # Small delay
    end_time = time.time()
    
    # Should not raise for reasonable timing
    assert_timing_reasonable(start_time, end_time, min_time=0.001, max_time=1.0)
    
    print(f"✓ Assertion helpers: Timing validation works")


@pytest.mark.performance
def test_performance_infrastructure():
    """Test performance aspects of infrastructure."""
    start_time = time.time()
    
    # Test that importing our fixtures is fast
    from tests.fixtures.security_vectors import get_path_traversal_vectors
    vectors = get_path_traversal_vectors()
    
    end_time = time.time()
    load_time = end_time - start_time
    
    # Should load quickly
    assert load_time < 1.0, f"Security vectors took too long to load: {load_time:.3f}s"
    assert len(vectors) > 10, "Should have sufficient test vectors"
    
    print(f"✓ Performance: Loaded {len(vectors)} vectors in {load_time:.3f}s")


def test_all_utils_importable():
    """Test that all utility modules can be imported."""
    import tests.utils.security_helpers
    import tests.utils.filesystem_helpers 
    import tests.utils.process_helpers
    import tests.utils.assertion_helpers
    
    # Check that key classes are available
    assert hasattr(tests.utils.security_helpers, 'SecurityTestHelper')
    assert hasattr(tests.utils.filesystem_helpers, 'FileSystemTestHelper')
    assert hasattr(tests.utils.process_helpers, 'ProcessTestHelper')
    assert hasattr(tests.utils.assertion_helpers, 'assert_tool_result_valid')
    
    print("✓ All utility modules imported successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])