.PHONY: format lint check clean install test test-dxt all pipeline dxt requirements build dist

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

# Test DXT build with specific version
test-dxt:
	@if [ -z "$(VERSION)" ]; then \
		echo "Running DXT build test with default version 2.2.0"; \
		VERSION="2.2.0"; \
	else \
		echo "Running DXT build test with version $(VERSION)"; \
		VERSION="$(VERSION)"; \
	fi; \
	python tests/test_dxt_build.py $$VERSION; \
	TEST_RESULT=$$?; \
	echo "Cleaning up test DXT files..."; \
	rm -f dxt/iam_mcp_server-$$VERSION.dxt; \
	exit $$TEST_RESULT

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

# Build DXT bundle
dxt:
	echo "Building DXT bundle..."
	# Use SETUPTOOLS_SCM_PRETEND_VERSION if set, otherwise extract from manifest.json
	@if [ -n "$(SETUPTOOLS_SCM_PRETEND_VERSION)" ]; then \
		VERSION="$(SETUPTOOLS_SCM_PRETEND_VERSION)"; \
	else \
		VERSION=$$(grep '"version"' manifest.json | sed 's/.*"version": "\(.*\)".*/\1/'); \
	fi; \
	echo "Building DXT version: $$VERSION"; \
	rm -f dxt/iam_mcp_server-$$VERSION.dxt; \
	npx @anthropic-ai/dxt pack . dxt/iam_mcp_server-$$VERSION.dxt; \
	npx @anthropic-ai/dxt sign --self-signed dxt/iam_mcp_server-$$VERSION.dxt

# Generate requirements files
requirements:
	uv pip compile pyproject.toml -o requirements.txt
	uv pip compile pyproject.toml --group dev -o requirements-dev.txt

# Build distribution packages
build:
	uv build

# Build everything
dist: clean build dxt

# Run all checks
all: clean install format lint test

# Default target
default: all