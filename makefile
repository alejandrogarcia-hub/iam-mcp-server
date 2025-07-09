.PHONY: format lint check clean install test all

# Python source files
PYTHON_FILES = src/*

# Install dependencies
install:
	uv add --dev ruff pytest

# Format code using ruff
format:
	uv run ruff format $(PYTHON_FILES)

# Run ruff linter
lint:
	uv run ruff check $(PYTHON_FILES)
	uv run ruff check --select I $(PYTHON_FILES)  # Import order
	uv run ruff check --select ERA $(PYTHON_FILES)  # Eradicate commented-out code
	uv run ruff check --select UP $(PYTHON_FILES)  # pyupgrade (modernize code)

lint_fix:
	uv run ruff check --fix $(PYTHON_FILES)
	uv run ruff check --fix --select I $(PYTHON_FILES)  # Import order
	uv run ruff check --fix --select ERA $(PYTHON_FILES)  # Eradicate commented-out code
	uv run ruff check --fix --select UP $(PYTHON_FILES)  # pyupgrade (modernize code)

# Fix auto-fixable issues
fix:
	uv run ruff check --fix $(PYTHON_FILES)

# Run all checks without modifying files
check:
	uv run ruff format --check $(PYTHON_FILES)
	uv run ruff check $(PYTHON_FILES)

# Run tests
test:
	uv run pytest

# Clean up python cache files
clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +
	find . -type d -name "*.egg" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".ruff_cache" -exec rm -r {} +


pipeline: format lint_fix test clean

# Run all checks
all: clean install format lint test

# Default target
default: all