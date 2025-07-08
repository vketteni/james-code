# Makefile for James Code development

.PHONY: install install-dev test test-unit test-integration test-performance test-security test-benchmark lint format type-check docs clean help version version-list version-patch version-minor version-major version-tag

# Default target
help:
	@echo "Available targets:"
	@echo "  install      - Install package for use"
	@echo "  install-dev  - Install package with development dependencies"
	@echo "  test         - Run all tests"
	@echo "  test-unit    - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  test-performance - Run performance tests"
	@echo "  test-security - Run security tests"
	@echo "  test-benchmark - Run benchmark tests"
	@echo "  test-fast    - Run fast tests (exclude slow and benchmark)"
	@echo "  lint         - Run code linting (ruff)"
	@echo "  format       - Format code (black)"
	@echo "  type-check   - Run type checking (mypy)"
	@echo "  docs         - Generate documentation"
	@echo "  docs-serve   - Serve documentation locally"
	@echo "  clean        - Clean up build artifacts"
	@echo "  all          - Run format, lint, type-check, and test"
	@echo "  version      - Show current version"
	@echo "  version-list - List all version tags"
	@echo "  version-patch - Create patch version tag"
	@echo "  version-minor - Create minor version tag"
	@echo "  version-major - Create major version tag"
	@echo "  version-tag  - Create specific version tag (VERSION=x.y.z)"

# Installation
install:
	poetry install --only=main

install-dev:
	poetry install --with=dev,docs

# Testing
test:
	poetry run pytest

test-unit:
	poetry run pytest tests/unit/ -v

test-integration:
	poetry run pytest tests/integration/ -v

test-performance:
	poetry run pytest -m performance -v

test-security:
	poetry run pytest -m security -v

test-benchmark:
	poetry run pytest --benchmark-only -v

test-fast:
	poetry run pytest -m "not slow and not benchmark" -v

test-coverage:
	poetry run pytest --cov=src/james_code --cov-report=html --cov-report=term

test-with-benchmarks:
	poetry run pytest --benchmark-autosave

# Code quality
lint:
	poetry run ruff check src/ tests/

lint-fix:
	poetry run ruff check --fix src/ tests/

format:
	poetry run black src/ tests/ scripts/

format-check:
	poetry run black --check src/ tests/ scripts/

type-check:
	poetry run mypy src/

# Documentation
docs:
	poetry run python scripts/generate_docs.py

docs-serve:
	poetry run mkdocs serve

docs-build:
	poetry run mkdocs build

# Development workflow
all: format lint type-check test

pre-commit: format lint type-check test-unit

# Package building
build:
	poetry build

publish-test:
	poetry publish --repository=testpypi

publish:
	poetry publish

# Cleanup
clean:
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

# Development setup
setup-dev: install-dev
	poetry run pre-commit install
	@echo "Development environment set up!"
	@echo "Run 'poetry shell' to activate the virtual environment"

# Quick development checks
quick-check: format-check lint type-check test-unit

# Generate lock file
lock:
	poetry lock

# Update dependencies
update:
	poetry update

# Security check
security:
	poetry run pip-audit

# Project statistics
stats:
	@echo "=== Project Statistics ==="
	@echo "Lines of code:"
	@find src/ -name "*.py" -exec wc -l {} + | tail -1
	@echo "Test coverage:"
	@poetry run pytest --cov=src/agent_llm --cov-report=term-missing --quiet
	@echo "Package size:"
	@du -sh src/

# Version management
version:
	@poetry run python scripts/version.py current

version-list:
	@poetry run python scripts/version.py list

version-patch:
	@poetry run python scripts/version.py tag patch

version-minor:
	@poetry run python scripts/version.py tag minor

version-major:
	@poetry run python scripts/version.py tag major

version-tag:
	@if [ -z "$(VERSION)" ]; then \
		echo "Error: VERSION is required. Usage: make version-tag VERSION=1.0.0"; \
		exit 1; \
	fi
	@poetry run python scripts/version.py direct $(VERSION)