# 8. Dependency Management and Packaging Strategy

Date: 2025-07-07

## Status

Proposed

## Context

We need to establish dependency management and packaging for the James Code system. Key considerations:

### Current State
- Pure Python implementation with minimal external dependencies
- Modular architecture with clear separation of concerns
- Self-contained tools that could be used independently
- Both library and application use cases

### Packaging Questions
1. **Should this be a Python package?** 
   - Library for embedding in other projects vs standalone application
   - Distribution via PyPI vs other mechanisms
   - Developer experience and ease of use

2. **Dependency management approach?**
   - Poetry vs pip-tools vs requirements.txt
   - Lock files for reproducible builds
   - Development vs production dependencies

3. **Package structure?**
   - Single package vs multiple packages
   - Optional dependencies for different use cases
   - Plugin architecture considerations

## Decision Options

### Option 1: Python Package with Poetry
**Structure**: Proper Python package with poetry for dependency management

**Pros:**
- Professional dependency management with lock files
- Easy installation via `pip install james-code`
- Clear separation of dev/prod dependencies
- Built-in virtual environment management
- Excellent for library distribution
- Modern Python tooling standard

**Cons:**
- Additional complexity for simple use cases
- Poetry learning curve for contributors
- Package publishing overhead

### Option 2: Simple Requirements.txt Approach
**Structure**: Keep current structure with requirements.txt

**Pros:**
- Simple and universally understood
- No additional tooling required
- Easy for quick prototyping
- Lower barrier to entry

**Cons:**
- No lock files for reproducible builds
- Manual dependency version management
- No clear dev/prod separation
- Harder to distribute as library

### Option 3: Hybrid Approach
**Structure**: Package-ready structure with optional poetry support

**Pros:**
- Can be used both ways
- Gradual migration path
- Supports different user preferences

**Cons:**
- Maintenance overhead of supporting both
- Potential inconsistencies between approaches

## Recommended Decision: Option 1 (Python Package with Poetry)

### Rationale

This James Code system has **clear library characteristics**:

1. **Reusable Components**: Tools can be embedded in other projects
2. **Clean API**: Agent class provides clear integration points
3. **Modular Design**: Users might want subsets of functionality
4. **Professional Use Cases**: Production deployments need reproducible builds

### Package Design

```
james-code/
├── pyproject.toml              # Poetry configuration
├── README.md                   # Package description
├── src/
│   └── james_code/             # Main package
│       ├── __init__.py        # Public API
│       ├── core/              # Core components
│       ├── tools/             # Tool implementations
│       └── safety/            # Security framework
├── tests/                     # Test suite
├── docs/                      # Documentation
├── examples/                  # Usage examples
└── scripts/                   # Development scripts
```

### Poetry Configuration Strategy

```toml
[tool.poetry]
name = "james-code"
version = "0.1.0"
description = "Agentic LLM system with READ, WRITE, and EXECUTE tools"
authors = ["Your Team"]
packages = [{include = "james_code", from = "src"}]

[tool.poetry.dependencies]
python = "^3.8"
# Minimal core dependencies only

[tool.poetry.group.dev.dependencies]
pytest = "^7.0"
black = "^23.0"
ruff = "^0.1"
mypy = "^1.0"

[tool.poetry.group.docs.dependencies]
mkdocs = "^1.5"
mkdocs-material = "^9.0"

[tool.poetry.extras]
llm = ["openai", "anthropic"]  # Optional LLM integrations
mcp = ["mcp-client"]           # Optional MCP support
```

### Distribution Strategy

1. **Core Package**: Minimal dependencies, self-contained tools
2. **Optional Extras**: LLM integrations, MCP support, etc.
3. **Development Setup**: Full dev environment with Poetry
4. **User Installation**: Simple `pip install james-code`

## Implementation Plan

### Phase 1: Package Structure
1. Create `pyproject.toml` with Poetry configuration
2. Restructure to standard Python package layout
3. Update imports and module structure
4. Create proper `__init__.py` with public API

### Phase 2: Dependency Management
1. Identify minimal core dependencies
2. Separate dev/docs/optional dependencies
3. Create lock files for reproducible builds
4. Update documentation for installation

### Phase 3: Distribution Ready
1. Package metadata and description
2. Entry points for CLI usage
3. Testing and CI setup
4. Documentation for package usage

## Consequences

**Positive:**
- Professional dependency management
- Easy distribution and installation
- Clear separation of concerns
- Reproducible builds
- Standard Python packaging practices
- Can be embedded in other projects

**Negative:**
- Initial setup complexity
- Poetry learning curve for some developers
- Package publishing considerations
- Additional configuration files

**User Experience:**
```bash
# Simple installation
pip install james-code

# Or with optional features
pip install james-code[llm,mcp]

# Development setup
git clone repo
cd james-code
poetry install
poetry shell
```

**Library Usage:**
```python
from james_code import Agent, AgentConfig
from james_code.tools import ReadTool, WriteTool

# Easy integration into other projects
agent = Agent(config)
result = agent.process_request("analyze this codebase")
```

## Alternative Considerations

### CLI vs Library Design
- **Both**: Package supports both library and CLI usage
- **Entry Points**: Poetry can define CLI commands
- **Flexibility**: Users choose how to interact

### Dependency Philosophy
- **Minimal Core**: Keep core dependencies minimal
- **Optional Extensions**: LLM integrations as extras
- **No Vendor Lock-in**: Support multiple LLM providers

### Future Extensibility
- **Plugin System**: Package structure supports plugins
- **Multiple Distributions**: Core + specialized packages
- **Namespace Packages**: Room for ecosystem growth