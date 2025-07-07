# Contributing to James Code

Thank you for your interest in contributing to James Code! This document provides guidelines and information for contributors.

## Development Setup

### Prerequisites
- Python 3.8 or higher
- Poetry for dependency management
- Git for version control

### Getting Started

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/your-username/james-code.git
   cd james-code
   ```

2. **Set up development environment**
   ```bash
   # Install Poetry if you haven't already
   curl -sSL https://install.python-poetry.org | python3 -

   # Install dependencies and set up pre-commit hooks
   make setup-dev

   # Activate the virtual environment
   poetry shell
   ```

3. **Verify setup**
   ```bash
   make quick-check
   ```

## Development Workflow

### Code Quality Standards

We maintain high code quality through automated tooling:

- **Black** for code formatting
- **Ruff** for linting and import sorting  
- **MyPy** for type checking
- **Pytest** for testing

### Before Committing

Run the pre-commit checks:

```bash
make pre-commit
```

This will:
- Format code with Black
- Lint with Ruff  
- Type check with MyPy
- Run unit tests

### Testing

We use pytest with comprehensive test coverage:

```bash
# Run all tests
make test

# Run only unit tests
make test-unit

# Run with coverage report
make test-coverage
```

#### Test Categories
- **Unit tests** (`tests/unit/`) - Test individual components
- **Integration tests** (`tests/integration/`) - Test component interactions

#### Writing Tests
- Follow the existing test patterns
- Use descriptive test names that explain what is being tested
- Include both positive and negative test cases
- Mock external dependencies appropriately

### Documentation

#### Architecture Decision Records (ADRs)
For significant architectural changes:

1. Create a new ADR in `docs/adr/`
2. Follow the existing template format
3. Include context, decision, and consequences
4. Number sequentially (e.g., `0009-new-decision.md`)

#### Tool Documentation
Our hybrid documentation system automatically generates reference docs:

```bash
# Regenerate documentation after tool changes
make docs
```

For conceptual changes:
- Update relevant files in `docs/tools/concepts/`
- Focus on stable concepts, not implementation details
- Update examples if usage patterns change

#### Code Documentation
- Use clear docstrings for all public APIs
- Include type hints for all function parameters and returns
- Document complex algorithms and business logic

## Contributing Guidelines

### Submitting Changes

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow existing code patterns
   - Add tests for new functionality
   - Update documentation as needed

3. **Run quality checks**
   ```bash
   make all
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

5. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

### Commit Message Format

Use conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding or updating tests
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `chore`: Maintenance tasks

**Examples:**
```
feat(tools): add new search capabilities to FindTool
fix(security): resolve path traversal vulnerability
docs(adr): add decision record for MCP integration
test(tools): add comprehensive tests for UpdateTool
```

### Code Review Process

All changes require code review:

1. **Automated checks** must pass (CI/CD pipeline)
2. **Manual review** by maintainers
3. **Documentation** updates if applicable
4. **Test coverage** maintained or improved

### What We Look For

**Code Quality:**
- Clear, readable code with good naming
- Appropriate error handling
- Type hints and documentation
- Test coverage for new functionality

**Security:**
- No introduction of security vulnerabilities
- Proper input validation and sanitization
- Safe handling of file system operations
- Appropriate use of security framework

**Architecture:**
- Follows existing patterns and conventions
- Maintains separation of concerns
- Considers impact on public API
- ADR for significant architectural changes

## Project Structure

Understanding the codebase:

```
src/james_code/
├── core/           # Core agent and base classes
├── tools/          # Tool implementations
├── safety/         # Security framework
└── cli.py          # Command-line interface

tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
└── conftest.py     # Pytest configuration

docs/
├── adr/            # Architecture Decision Records
└── tools/          # Tool documentation
```

### Key Concepts

- **Tools**: Self-contained units that perform specific operations
- **Safety Manager**: Enforces security constraints across all operations
- **Agent**: Orchestrates tools and manages conversation state
- **Task Management**: Planning and execution of complex multi-step operations

## Security Considerations

This project handles file system operations and command execution, requiring careful attention to security:

### Security Requirements
- All file operations must be within designated directories
- Command execution must be filtered and sandboxed
- Input validation is required for all user inputs
- Security violations must be logged and handled appropriately

### Reporting Security Issues
Please report security vulnerabilities privately to the maintainers before public disclosure.

## Getting Help

- **Documentation**: Check `docs/` directory
- **Issues**: Search existing GitHub issues
- **Discussions**: Use GitHub Discussions for questions
- **Code**: Review existing implementations for patterns

## Recognition

Contributors will be recognized in:
- `CONTRIBUTORS.md` file
- Release notes for significant contributions
- GitHub contributor statistics

Thank you for contributing to James Code! 🤖