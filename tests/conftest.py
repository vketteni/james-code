"""Pytest configuration and fixtures for James Code tests."""

import pytest
import tempfile
from pathlib import Path
from typing import Generator

from james_code import Agent, AgentConfig
from james_code.safety import SafetyConfig


@pytest.fixture
def temp_workspace() -> Generator[Path, None, None]:
    """Create a temporary workspace directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def safe_config(temp_workspace: Path) -> SafetyConfig:
    """Create a safe configuration for testing."""
    return SafetyConfig(
        base_directory=str(temp_workspace),
        enable_audit_logging=False,  # Disable for tests
        strict_mode=False,  # Permissive for testing
        allowed_commands=["echo", "python3", "ls"],
        max_file_size=1024 * 1024  # 1MB limit for tests
    )


@pytest.fixture
def agent_config(temp_workspace: Path, safe_config: SafetyConfig) -> AgentConfig:
    """Create an agent configuration for testing."""
    return AgentConfig(
        working_directory=str(temp_workspace),
        safety_config=safe_config,
        verbose_logging=False,  # Quiet during tests
        auto_planning=False  # Manual control in tests
    )


@pytest.fixture
def agent(agent_config: AgentConfig) -> Agent:
    """Create an agent instance for testing."""
    return Agent(agent_config)


@pytest.fixture
def sample_files(temp_workspace: Path) -> dict:
    """Create sample files for testing."""
    files = {
        "hello.py": "def hello():\n    print('Hello, World!')\n",
        "config.json": '{"setting": "value", "debug": true}',
        "readme.txt": "This is a sample readme file.\nIt has multiple lines.\n",
        "empty.txt": "",
    }
    
    created_files = {}
    for filename, content in files.items():
        file_path = temp_workspace / filename
        file_path.write_text(content, encoding='utf-8')
        created_files[filename] = file_path
    
    # Create a subdirectory with files
    subdir = temp_workspace / "subdir"
    subdir.mkdir()
    
    sub_file = subdir / "nested.py"
    sub_file.write_text("# Nested file\nprint('nested')\n", encoding='utf-8')
    created_files["subdir/nested.py"] = sub_file
    
    return created_files