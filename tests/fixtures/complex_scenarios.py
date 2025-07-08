"""Enhanced fixtures for complex testing scenarios."""

import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Generator, List
import pytest
import subprocess
import time


@pytest.fixture
def complex_codebase(temp_workspace: Path) -> Dict[str, Path]:
    """Create a realistic multi-file project structure for testing.
    
    Returns:
        Dict mapping file descriptions to their paths
    """
    project_root = temp_workspace / "test_project"
    project_root.mkdir()
    
    # Create a realistic Python project structure
    structure = {
        # Source code
        "src/main.py": '''#!/usr/bin/env python3
"""Main application entry point."""

import sys
import logging
from pathlib import Path

from .core.engine import Engine
from .utils.config import load_config
from .utils.logger import setup_logging


def main():
    """Main application function."""
    config = load_config()
    setup_logging(config.get("log_level", "INFO"))
    
    engine = Engine(config)
    try:
        engine.run()
    except KeyboardInterrupt:
        logging.info("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
''',
        
        "src/core/__init__.py": "",
        "src/core/engine.py": '''"""Core engine implementation."""

import asyncio
import logging
from typing import Dict, Any, Optional

from ..utils.database import Database
from ..utils.cache import Cache


class Engine:
    """Main application engine."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.db = Database(config.get("database_url"))
        self.cache = Cache(config.get("cache_config", {}))
        
    async def initialize(self):
        """Initialize the engine."""
        await self.db.connect()
        await self.cache.connect()
        self.logger.info("Engine initialized")
        
    async def run(self):
        """Run the main application loop."""
        await self.initialize()
        
        try:
            while True:
                await self.process_tasks()
                await asyncio.sleep(0.1)
        finally:
            await self.shutdown()
            
    async def process_tasks(self):
        """Process pending tasks."""
        # TODO: Implement task processing logic
        pass
        
    async def shutdown(self):
        """Gracefully shutdown the engine."""
        await self.db.disconnect()
        await self.cache.disconnect()
        self.logger.info("Engine shutdown complete")
''',
        
        "src/utils/__init__.py": "",
        "src/utils/config.py": '''"""Configuration management utilities."""

import json
import os
from pathlib import Path
from typing import Dict, Any


def load_config(config_path: str = "config.json") -> Dict[str, Any]:
    """Load configuration from file."""
    config_file = Path(config_path)
    
    if not config_file.exists():
        return get_default_config()
        
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        raise RuntimeError(f"Failed to load config: {e}")


def get_default_config() -> Dict[str, Any]:
    """Get default configuration."""
    return {
        "log_level": "INFO",
        "database_url": "sqlite:///app.db",
        "cache_config": {
            "type": "memory",
            "max_size": 1000
        },
        "worker_threads": 4,
        "timeout": 30
    }
''',
        
        "src/utils/logger.py": '''"""Logging utilities."""

import logging
import sys
from typing import Optional


def setup_logging(level: str = "INFO", 
                 format_str: Optional[str] = None) -> None:
    """Set up application logging."""
    if format_str is None:
        format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_str,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("app.log")
        ]
    )
    
    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
''',
        
        "src/utils/database.py": '''"""Database utilities."""

import asyncio
import logging
from typing import Optional, Dict, Any


class Database:
    """Database connection manager."""
    
    def __init__(self, url: str):
        self.url = url
        self.connection = None
        self.logger = logging.getLogger(__name__)
        
    async def connect(self):
        """Connect to database."""
        # Simulate connection
        await asyncio.sleep(0.1)
        self.connection = {"connected": True, "url": self.url}
        self.logger.info(f"Connected to database: {self.url}")
        
    async def disconnect(self):
        """Disconnect from database."""
        if self.connection:
            await asyncio.sleep(0.05)
            self.connection = None
            self.logger.info("Disconnected from database")
            
    async def execute(self, query: str, params: Optional[Dict[str, Any]] = None):
        """Execute a database query."""
        if not self.connection:
            raise RuntimeError("Database not connected")
        
        # Simulate query execution
        await asyncio.sleep(0.01)
        self.logger.debug(f"Executed query: {query}")
        return {"rows_affected": 1}
''',
        
        "src/utils/cache.py": '''"""Cache utilities."""

import asyncio
import logging
from typing import Dict, Any, Optional


class Cache:
    """In-memory cache implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.data = {}
        self.logger = logging.getLogger(__name__)
        
    async def connect(self):
        """Initialize cache."""
        await asyncio.sleep(0.01)
        self.logger.info("Cache initialized")
        
    async def disconnect(self):
        """Cleanup cache."""
        self.data.clear()
        self.logger.info("Cache cleared")
        
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        return self.data.get(key)
        
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache."""
        self.data[key] = value
        self.logger.debug(f"Set cache key: {key}")
        
    async def delete(self, key: str):
        """Delete key from cache."""
        self.data.pop(key, None)
        self.logger.debug(f"Deleted cache key: {key}")
''',
        
        # Configuration files
        "config.json": json.dumps({
            "log_level": "DEBUG",
            "database_url": "sqlite:///test.db",
            "cache_config": {
                "type": "memory",
                "max_size": 500
            },
            "worker_threads": 2,
            "timeout": 10
        }, indent=2),
        
        "config.dev.json": json.dumps({
            "log_level": "DEBUG",
            "database_url": "sqlite:///dev.db", 
            "debug": True
        }, indent=2),
        
        "requirements.txt": '''asyncio>=3.4.3
aiohttp>=3.8.0
pydantic>=1.10.0
pytest>=7.0.0
pytest-asyncio>=0.21.0
''',
        
        "pyproject.toml": '''[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "test-project"
version = "1.0.0"
description = "Test project for complex scenarios"
authors = [{name = "Test Author", email = "test@example.com"}]
dependencies = [
    "asyncio>=3.4.3",
    "aiohttp>=3.8.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "mypy>=1.0.0",
]
''',
        
        # Test files
        "tests/__init__.py": "",
        "tests/conftest.py": '''"""Test configuration."""

import pytest
import asyncio
from pathlib import Path


@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_db():
    """Create temporary database."""
    db_path = Path("test.db")
    yield db_path
    if db_path.exists():
        db_path.unlink()
''',
        
        "tests/test_engine.py": '''"""Test engine functionality."""

import pytest
from unittest.mock import Mock, patch

from src.core.engine import Engine


@pytest.mark.asyncio
async def test_engine_initialization():
    """Test engine initialization."""
    config = {"database_url": "sqlite:///test.db"}
    engine = Engine(config)
    
    with patch.object(engine.db, 'connect') as mock_connect:
        with patch.object(engine.cache, 'connect') as mock_cache_connect:
            await engine.initialize()
            
            mock_connect.assert_called_once()
            mock_cache_connect.assert_called_once()


@pytest.mark.asyncio
async def test_engine_shutdown():
    """Test engine shutdown."""
    config = {"database_url": "sqlite:///test.db"}
    engine = Engine(config)
    
    with patch.object(engine.db, 'disconnect') as mock_disconnect:
        with patch.object(engine.cache, 'disconnect') as mock_cache_disconnect:
            await engine.shutdown()
            
            mock_disconnect.assert_called_once()
            mock_cache_disconnect.assert_called_once()
''',
        
        "tests/test_utils.py": '''"""Test utility functions."""

import pytest
import tempfile
from pathlib import Path

from src.utils.config import load_config, get_default_config


def test_load_config_default():
    """Test loading default config."""
    config = get_default_config()
    assert config["log_level"] == "INFO"
    assert "database_url" in config


def test_load_config_file():
    """Test loading config from file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"test": "value"}')
        f.flush()
        
        config = load_config(f.name)
        assert config["test"] == "value"
        
        Path(f.name).unlink()


def test_load_config_missing_file():
    """Test loading config when file doesn't exist.""" 
    config = load_config("nonexistent.json")
    assert config == get_default_config()
''',
        
        # Documentation
        "README.md": '''# Test Project

This is a test project for complex scenario testing.

## Features

- Async engine with task processing
- Database integration
- Caching system
- Comprehensive logging
- Configuration management

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python -m src.main
```

## Testing

```bash
pytest tests/
```

## Configuration

Edit `config.json` to customize settings:

- `log_level`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `database_url`: Database connection string
- `cache_config`: Cache configuration
- `worker_threads`: Number of worker threads
- `timeout`: Request timeout in seconds
''',
        
        "CHANGELOG.md": '''# Changelog

## [1.0.0] - 2024-01-01

### Added
- Initial release
- Core engine implementation
- Database integration
- Cache system
- Configuration management
- Logging utilities

### Changed
- None

### Deprecated
- None

### Removed
- None

### Fixed
- None

### Security
- None
''',
        
        # Script files
        "scripts/deploy.sh": '''#!/bin/bash
set -e

echo "Starting deployment..."

# Run tests
echo "Running tests..."
pytest tests/

# Build application
echo "Building application..."
python -m build

# Deploy
echo "Deploying application..."
# Deployment logic here

echo "Deployment complete!"
''',
        
        "scripts/setup.py": '''#!/usr/bin/env python3
"""Setup script for development environment."""

import subprocess
import sys
from pathlib import Path


def run_command(cmd):
    """Run a command and handle errors."""
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {cmd}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"✗ {cmd}")
        print(f"Error: {e.stderr}")
        sys.exit(1)


def main():
    """Main setup function."""
    print("Setting up development environment...")
    
    # Install dependencies
    run_command("pip install -r requirements.txt")
    
    # Install development dependencies
    run_command("pip install pytest pytest-asyncio mypy")
    
    # Create necessary directories
    Path("logs").mkdir(exist_ok=True)
    Path("data").mkdir(exist_ok=True)
    
    print("Setup complete!")


if __name__ == "__main__":
    main()
''',
        
        # Data files
        "data/sample.json": json.dumps({
            "users": [
                {"id": 1, "name": "Alice", "email": "alice@example.com"},
                {"id": 2, "name": "Bob", "email": "bob@example.com"}
            ],
            "metadata": {
                "version": "1.0",
                "created": "2024-01-01T00:00:00Z"
            }
        }, indent=2),
        
        "data/config.yaml": '''# Configuration file
database:
  host: localhost
  port: 5432
  name: testdb
  
cache:
  type: redis
  host: localhost
  port: 6379
  
logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
''',
        
        # Various file types for testing
        "docs/api.md": '''# API Documentation

## Endpoints

### GET /api/users
Returns list of users.

### POST /api/users
Creates a new user.

### GET /api/users/{id}
Returns specific user.
''',
        
        ".gitignore": '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Testing
.pytest_cache/
.coverage
htmlcov/

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Application
*.log
*.db
data/cache/
''',
        
        # Hidden files
        ".env": '''# Environment variables
DEBUG=true
SECRET_KEY=test-secret-key
DATABASE_URL=sqlite:///test.db
''',
        
        ".env.example": '''# Environment variables template
DEBUG=false
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@localhost/dbname
''',
    }
    
    # Create all files
    created_files = {}
    for file_path, content in structure.items():
        full_path = project_root / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Make shell scripts executable
        if file_path.endswith('.sh'):
            full_path.write_text(content, encoding='utf-8')
            os.chmod(full_path, 0o755)
        else:
            full_path.write_text(content, encoding='utf-8')
            
        created_files[file_path] = full_path
    
    return created_files


@pytest.fixture
def git_repository(complex_codebase: Dict[str, Path]) -> Path:
    """Create a git repository for version control testing."""
    project_root = list(complex_codebase.values())[0].parent
    
    # Initialize git repository
    subprocess.run(['git', 'init'], cwd=project_root, check=True, capture_output=True)
    subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=project_root, check=True)
    subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=project_root, check=True)
    
    # Create initial commit
    subprocess.run(['git', 'add', '.'], cwd=project_root, check=True, capture_output=True)
    subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=project_root, check=True, capture_output=True)
    
    # Create a few more commits for testing
    readme_path = project_root / "README.md"
    readme_path.write_text(readme_path.read_text() + "\n\n## Updates\n\n- Added new features\n")
    subprocess.run(['git', 'add', 'README.md'], cwd=project_root, check=True, capture_output=True)
    subprocess.run(['git', 'commit', '-m', 'Update README'], cwd=project_root, check=True, capture_output=True)
    
    # Create a branch
    subprocess.run(['git', 'checkout', '-b', 'feature/testing'], cwd=project_root, check=True, capture_output=True)
    feature_file = project_root / "src/features/new_feature.py"
    feature_file.parent.mkdir(parents=True, exist_ok=True)
    feature_file.write_text('"""New feature implementation."""\n\ndef new_feature():\n    return "Hello from new feature!"\n')
    subprocess.run(['git', 'add', 'src/features/new_feature.py'], cwd=project_root, check=True, capture_output=True)
    subprocess.run(['git', 'commit', '-m', 'Add new feature'], cwd=project_root, check=True, capture_output=True)
    
    # Switch back to main
    subprocess.run(['git', 'checkout', 'main'], cwd=project_root, check=True, capture_output=True)
    
    return project_root


@pytest.fixture
def large_files(temp_workspace: Path) -> Dict[str, Path]:
    """Create large files for performance testing."""
    large_files = {}
    
    # Create files of different sizes
    sizes = {
        "small.txt": 1024,          # 1KB
        "medium.txt": 1024 * 100,   # 100KB
        "large.txt": 1024 * 1024,   # 1MB
        "huge.txt": 1024 * 1024 * 5 # 5MB
    }
    
    for filename, size in sizes.items():
        file_path = temp_workspace / filename
        
        # Create file with repeating content
        content = "This is test content for performance testing. " * (size // 50)
        content = content[:size]  # Trim to exact size
        
        file_path.write_text(content, encoding='utf-8')
        large_files[filename] = file_path
    
    # Create a large JSON file
    large_json_path = temp_workspace / "large_data.json"
    large_data = {
        "items": [
            {"id": i, "name": f"Item {i}", "value": i * 10, "active": i % 2 == 0}
            for i in range(10000)
        ],
        "metadata": {
            "count": 10000,
            "generated": "2024-01-01T00:00:00Z"
        }
    }
    large_json_path.write_text(json.dumps(large_data, indent=2), encoding='utf-8')
    large_files["large_data.json"] = large_json_path
    
    return large_files


@pytest.fixture
def nested_directories(temp_workspace: Path) -> Dict[str, Path]:
    """Create complex nested directory structure."""
    base_path = temp_workspace / "nested_structure"
    base_path.mkdir()
    
    # Create deep nested structure
    paths = {}
    
    # Create directory tree
    for i in range(5):
        level_path = base_path
        for j in range(i + 1):
            level_path = level_path / f"level_{j}"
            level_path.mkdir(exist_ok=True)
            
        # Add files at each level
        for k in range(3):
            file_path = level_path / f"file_{k}.txt"
            file_path.write_text(f"Content for level {i}, file {k}")
            paths[f"level_{i}_file_{k}"] = file_path
    
    # Create wide structure
    wide_path = base_path / "wide"
    wide_path.mkdir()
    
    for i in range(20):
        dir_path = wide_path / f"dir_{i:02d}"
        dir_path.mkdir()
        
        for j in range(5):
            file_path = dir_path / f"file_{j}.py"
            file_path.write_text(f'''"""Module {i}-{j}."""

def function_{j}():
    """Function {j} in module {i}."""
    return {i * 10 + j}


class Class{j}:
    """Class {j} in module {i}."""
    
    def method(self):
        """Method in class {j}."""
        return function_{j}()
''')
            paths[f"wide_dir_{i}_file_{j}"] = file_path
    
    return paths


@pytest.fixture
def permission_variations(temp_workspace: Path) -> Dict[str, Path]:
    """Create files with different permission scenarios."""
    perms_path = temp_workspace / "permissions"
    perms_path.mkdir()
    
    files = {}
    
    # Regular readable file
    normal_file = perms_path / "normal.txt"
    normal_file.write_text("Normal file content")
    files["normal"] = normal_file
    
    # Read-only file
    readonly_file = perms_path / "readonly.txt"
    readonly_file.write_text("Read-only file content")
    os.chmod(readonly_file, 0o444)
    files["readonly"] = readonly_file
    
    # Executable file
    executable_file = perms_path / "executable.sh"
    executable_file.write_text("#!/bin/bash\necho 'Hello from executable'")
    os.chmod(executable_file, 0o755)
    files["executable"] = executable_file
    
    # Directory with restricted permissions
    restricted_dir = perms_path / "restricted"
    restricted_dir.mkdir()
    os.chmod(restricted_dir, 0o700)
    files["restricted_dir"] = restricted_dir
    
    # File in restricted directory
    restricted_file = restricted_dir / "secret.txt"
    restricted_file.write_text("Secret content")
    files["restricted_file"] = restricted_file
    
    return files


@pytest.fixture
def mixed_encodings(temp_workspace: Path) -> Dict[str, Path]:
    """Create files with different encodings and special characters."""
    encoding_path = temp_workspace / "encodings"
    encoding_path.mkdir()
    
    files = {}
    
    # UTF-8 file with Unicode characters
    utf8_file = encoding_path / "utf8.txt"
    utf8_content = "Hello, 世界! 🌍 Café naïve résumé"
    utf8_file.write_text(utf8_content, encoding='utf-8')
    files["utf8"] = utf8_file
    
    # ASCII file
    ascii_file = encoding_path / "ascii.txt"
    ascii_file.write_text("Pure ASCII content", encoding='ascii')
    files["ascii"] = ascii_file
    
    # Latin-1 file
    latin1_file = encoding_path / "latin1.txt"
    latin1_content = "Café résumé naïve"
    latin1_file.write_bytes(latin1_content.encode('latin-1'))
    files["latin1"] = latin1_file
    
    # Binary file
    binary_file = encoding_path / "binary.dat"
    binary_file.write_bytes(bytes(range(256)))
    files["binary"] = binary_file
    
    # File with null bytes
    null_file = encoding_path / "null_bytes.txt"
    null_file.write_bytes(b"Content with \x00 null \x00 bytes")
    files["null_bytes"] = null_file
    
    return files