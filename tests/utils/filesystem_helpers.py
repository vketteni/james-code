"""Filesystem testing helper utilities."""

import os
import shutil
import stat
import time
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Generator
from dataclasses import dataclass, field
import hashlib
import json

import pytest


@dataclass
class FileSystemChange:
    """Represents a filesystem change."""
    action: str  # created, modified, deleted, moved
    path: str
    timestamp: float
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FileSystemSnapshot:
    """Snapshot of filesystem state."""
    timestamp: float
    files: Dict[str, Dict[str, Any]]  # path -> {size, mtime, hash, permissions}
    directories: List[str]
    
    def compare(self, other: 'FileSystemSnapshot') -> List[FileSystemChange]:
        """Compare with another snapshot to find changes.
        
        Args:
            other: Another filesystem snapshot
            
        Returns:
            List of changes between snapshots
        """
        changes = []
        
        # Find new files
        for path in other.files:
            if path not in self.files:
                changes.append(FileSystemChange(
                    action="created",
                    path=path,
                    timestamp=other.timestamp,
                    details=other.files[path]
                ))
        
        # Find deleted files
        for path in self.files:
            if path not in other.files:
                changes.append(FileSystemChange(
                    action="deleted",
                    path=path,
                    timestamp=other.timestamp,
                    details=self.files[path]
                ))
        
        # Find modified files
        for path in self.files:
            if path in other.files:
                old_file = self.files[path]
                new_file = other.files[path]
                
                if old_file['hash'] != new_file['hash']:
                    changes.append(FileSystemChange(
                        action="modified",
                        path=path,
                        timestamp=other.timestamp,
                        details={
                            "old": old_file,
                            "new": new_file
                        }
                    ))
        
        # Find new directories
        for directory in other.directories:
            if directory not in self.directories:
                changes.append(FileSystemChange(
                    action="created",
                    path=directory,
                    timestamp=other.timestamp,
                    details={"type": "directory"}
                ))
        
        # Find deleted directories
        for directory in self.directories:
            if directory not in other.directories:
                changes.append(FileSystemChange(
                    action="deleted",
                    path=directory,
                    timestamp=other.timestamp,
                    details={"type": "directory"}
                ))
        
        return changes


class FileSystemTestHelper:
    """Helper class for filesystem testing operations."""
    
    def __init__(self, base_path: Path):
        """Initialize filesystem test helper.
        
        Args:
            base_path: Base path for filesystem operations
        """
        self.base_path = Path(base_path)
        self.snapshots: List[FileSystemSnapshot] = []
        self.monitored_paths: List[Path] = []
    
    def take_snapshot(self, paths: Optional[List[Path]] = None) -> FileSystemSnapshot:
        """Take a snapshot of filesystem state.
        
        Args:
            paths: Specific paths to snapshot (default: monitored paths)
            
        Returns:
            Filesystem snapshot
        """
        if paths is None:
            paths = self.monitored_paths if self.monitored_paths else [self.base_path]
        
        files = {}
        directories = []
        
        for path in paths:
            if path.is_file():
                files[str(path)] = self._get_file_info(path)
            elif path.is_dir():
                directories.append(str(path))
                # Recursively add all files in directory
                for item in path.rglob("*"):
                    if item.is_file():
                        files[str(item)] = self._get_file_info(item)
                    elif item.is_dir():
                        directories.append(str(item))
        
        snapshot = FileSystemSnapshot(
            timestamp=time.time(),
            files=files,
            directories=sorted(set(directories))
        )
        
        self.snapshots.append(snapshot)
        return snapshot
    
    def _get_file_info(self, path: Path) -> Dict[str, Any]:
        """Get file information for snapshot.
        
        Args:
            path: File path
            
        Returns:
            File information dictionary
        """
        try:
            stat_info = path.stat()
            
            # Calculate file hash
            with open(path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            
            return {
                "size": stat_info.st_size,
                "mtime": stat_info.st_mtime,
                "permissions": stat.filemode(stat_info.st_mode),
                "hash": file_hash,
                "owner_readable": os.access(path, os.R_OK),
                "owner_writable": os.access(path, os.W_OK),
                "owner_executable": os.access(path, os.X_OK)
            }
        except (OSError, IOError) as e:
            return {
                "error": str(e),
                "accessible": False
            }
    
    def monitor_path(self, path: Path):
        """Add a path to be monitored for changes.
        
        Args:
            path: Path to monitor
        """
        self.monitored_paths.append(path)
    
    def get_changes_since_snapshot(self, snapshot_index: int = -2) -> List[FileSystemChange]:
        """Get changes since a specific snapshot.
        
        Args:
            snapshot_index: Index of snapshot to compare against (default: second to last)
            
        Returns:
            List of filesystem changes
        """
        if len(self.snapshots) < 2:
            return []
        
        old_snapshot = self.snapshots[snapshot_index]
        new_snapshot = self.snapshots[-1]
        
        return old_snapshot.compare(new_snapshot)
    
    def assert_no_unauthorized_changes(self, allowed_paths: List[str]):
        """Assert that no unauthorized filesystem changes occurred.
        
        Args:
            allowed_paths: List of paths where changes are allowed
            
        Raises:
            AssertionError: If unauthorized changes detected
        """
        if len(self.snapshots) < 2:
            return
        
        changes = self.get_changes_since_snapshot()
        unauthorized_changes = []
        
        for change in changes:
            path_allowed = False
            for allowed_path in allowed_paths:
                if change.path.startswith(allowed_path):
                    path_allowed = True
                    break
            
            if not path_allowed:
                unauthorized_changes.append(change)
        
        if unauthorized_changes:
            change_descriptions = [
                f"{change.action}: {change.path}" for change in unauthorized_changes
            ]
            raise AssertionError(
                f"Unauthorized filesystem changes detected: {', '.join(change_descriptions)}"
            )
    
    def create_secure_test_file(self, filename: str, content: str, 
                              permissions: int = 0o644) -> Path:
        """Create a test file with specific permissions.
        
        Args:
            filename: Name of file to create
            content: File content
            permissions: File permissions (octal)
            
        Returns:
            Path to created file
        """
        file_path = self.base_path / filename
        file_path.write_text(content, encoding='utf-8')
        os.chmod(file_path, permissions)
        return file_path
    
    def create_test_directory_tree(self, structure: Dict[str, Any]) -> Dict[str, Path]:
        """Create a directory tree from a structure definition.
        
        Args:
            structure: Dictionary defining directory structure
            
        Returns:
            Dictionary mapping names to created paths
        """
        created_paths = {}
        
        def _create_recursive(current_path: Path, current_structure: Dict[str, Any]):
            for name, content in current_structure.items():
                item_path = current_path / name
                
                if isinstance(content, dict):
                    # It's a directory
                    item_path.mkdir(exist_ok=True)
                    created_paths[name] = item_path
                    _create_recursive(item_path, content)
                else:
                    # It's a file
                    item_path.write_text(str(content), encoding='utf-8')
                    created_paths[name] = item_path
        
        _create_recursive(self.base_path, structure)
        return created_paths
    
    def verify_file_integrity(self, file_path: Path, expected_hash: str) -> bool:
        """Verify file integrity using hash.
        
        Args:
            file_path: Path to file to verify
            expected_hash: Expected SHA256 hash
            
        Returns:
            True if file integrity is verified
        """
        try:
            with open(file_path, 'rb') as f:
                actual_hash = hashlib.sha256(f.read()).hexdigest()
            return actual_hash == expected_hash
        except (OSError, IOError):
            return False
    
    def simulate_filesystem_error(self, path: Path, error_type: str):
        """Simulate filesystem errors for testing.
        
        Args:
            path: Path where error should occur
            error_type: Type of error to simulate
        """
        if error_type == "permission_denied":
            # Remove all permissions
            os.chmod(path, 0o000)
        elif error_type == "readonly":
            # Make readonly
            os.chmod(path, 0o444)
        elif error_type == "disk_full":
            # Can't easily simulate, but we can document the intention
            pass
    
    def cleanup(self):
        """Clean up test filesystem state."""
        self.snapshots.clear()
        self.monitored_paths.clear()


def create_test_file_tree(base_path: Path, structure: Dict[str, Union[str, Dict]]) -> Dict[str, Path]:
    """Create a test file tree structure.
    
    Args:
        base_path: Base directory for the tree
        structure: Dictionary defining the structure
        
    Returns:
        Dictionary mapping relative paths to absolute paths
    """
    created_files = {}
    
    def _create_items(current_path: Path, items: Dict[str, Union[str, Dict]], prefix: str = ""):
        for name, content in items.items():
            full_path = current_path / name
            relative_path = f"{prefix}/{name}" if prefix else name
            
            if isinstance(content, dict):
                # Directory
                full_path.mkdir(exist_ok=True)
                created_files[relative_path] = full_path
                _create_items(full_path, content, relative_path)
            else:
                # File
                full_path.write_text(str(content), encoding='utf-8')
                created_files[relative_path] = full_path
    
    _create_items(base_path, structure)
    return created_files


def assert_file_operations_safe(base_path: Path, operation_results: List[Any]):
    """Assert that file operations were performed safely.
    
    Args:
        base_path: Base path for operations
        operation_results: List of operation results to check
        
    Raises:
        AssertionError: If unsafe operations detected
    """
    for result in operation_results:
        # Check that operations stayed within base path
        if hasattr(result, 'metadata') and 'path' in result.metadata:
            operation_path = Path(result.metadata['path'])
            try:
                operation_path.resolve().relative_to(base_path.resolve())
            except ValueError:
                raise AssertionError(
                    f"File operation outside base path: {operation_path} not in {base_path}"
                )
        
        # Check for security violations in error messages
        if not result.success and result.error:
            security_indicators = [
                "permission denied",
                "access denied",
                "outside working directory",
                "path traversal"
            ]
            
            error_lower = result.error.lower()
            has_security_error = any(indicator in error_lower for indicator in security_indicators)
            
            if not has_security_error:
                # This might be an unexpected error
                pass  # Could add more specific checks here


def monitor_file_changes(path: Path, duration: float = 1.0) -> Generator[FileSystemChange, None, None]:
    """Monitor filesystem changes in real-time.
    
    Args:
        path: Path to monitor
        duration: Duration to monitor in seconds
        
    Yields:
        Filesystem changes as they occur
    """
    # This is a simplified implementation
    # In a real implementation, you might use inotify on Linux or similar
    
    initial_state = {}
    if path.exists():
        if path.is_file():
            initial_state[str(path)] = path.stat().st_mtime
        elif path.is_dir():
            for item in path.rglob("*"):
                if item.is_file():
                    initial_state[str(item)] = item.stat().st_mtime
    
    end_time = time.time() + duration
    
    while time.time() < end_time:
        time.sleep(0.1)  # Check every 100ms
        
        current_state = {}
        if path.exists():
            if path.is_file():
                current_state[str(path)] = path.stat().st_mtime
            elif path.is_dir():
                for item in path.rglob("*"):
                    if item.is_file():
                        current_state[str(item)] = item.stat().st_mtime
        
        # Find changes
        for file_path, mtime in current_state.items():
            if file_path not in initial_state:
                yield FileSystemChange(
                    action="created",
                    path=file_path,
                    timestamp=time.time()
                )
            elif initial_state[file_path] != mtime:
                yield FileSystemChange(
                    action="modified",
                    path=file_path,
                    timestamp=time.time()
                )
        
        for file_path in initial_state:
            if file_path not in current_state:
                yield FileSystemChange(
                    action="deleted",
                    path=file_path,
                    timestamp=time.time()
                )
        
        initial_state = current_state.copy()


@pytest.fixture
def fs_helper(temp_workspace):
    """Provide a filesystem test helper."""
    helper = FileSystemTestHelper(temp_workspace)
    yield helper
    helper.cleanup()


@pytest.fixture
def monitored_directory(temp_workspace):
    """Provide a monitored directory for testing."""
    monitor_dir = temp_workspace / "monitored"
    monitor_dir.mkdir()
    
    helper = FileSystemTestHelper(monitor_dir)
    helper.monitor_path(monitor_dir)
    helper.take_snapshot()  # Initial snapshot
    
    yield monitor_dir, helper
    
    helper.cleanup()


class PermissionTestHelper:
    """Helper for testing file permission scenarios."""
    
    @staticmethod
    def create_readonly_file(path: Path, content: str) -> Path:
        """Create a read-only file.
        
        Args:
            path: File path
            content: File content
            
        Returns:
            Path to created file
        """
        path.write_text(content, encoding='utf-8')
        os.chmod(path, 0o444)  # Read-only for owner, group, others
        return path
    
    @staticmethod
    def create_executable_file(path: Path, content: str) -> Path:
        """Create an executable file.
        
        Args:
            path: File path
            content: File content
            
        Returns:
            Path to created file
        """
        path.write_text(content, encoding='utf-8')
        os.chmod(path, 0o755)  # Read/write/execute for owner, read/execute for others
        return path
    
    @staticmethod
    def create_restricted_directory(path: Path) -> Path:
        """Create a directory with restricted permissions.
        
        Args:
            path: Directory path
            
        Returns:
            Path to created directory
        """
        path.mkdir(exist_ok=True)
        os.chmod(path, 0o700)  # Only owner can access
        return path
    
    @staticmethod
    def remove_permissions(path: Path):
        """Remove all permissions from a path.
        
        Args:
            path: Path to modify
        """
        os.chmod(path, 0o000)
    
    @staticmethod
    def restore_permissions(path: Path, is_file: bool = True):
        """Restore normal permissions.
        
        Args:
            path: Path to modify
            is_file: Whether the path is a file (vs directory)
        """
        if is_file:
            os.chmod(path, 0o644)  # Normal file permissions
        else:
            os.chmod(path, 0o755)  # Normal directory permissions