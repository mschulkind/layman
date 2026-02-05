# Layman Project Justfile
# Run 'just' with no arguments to see all available commands

# Default: list all commands
default:
    @just --list --unsorted

# ============== Development ==============

# Run layman daemon
run:
    uv run layman

# Run layman with debug output
run-debug:
    uv run layman 2>&1 | tee /tmp/layman.log

# ============== Linting ==============

# Run all linters
lint: lint-python lint-docs typecheck
    @echo "✓ All linting passed"

# Lint Python code with ruff
lint-python:
    uv run ruff check src/
    uv run ruff format --check src/

# Analyze cyclomatic complexity
complexity:
    @echo "Cyclomatic Complexity Analysis:"
    uvx radon cc src/layman -a -s
    @echo ""
    @echo "Maintainability Index:"
    uvx radon mi src/layman -s

# Check complexity thresholds (fail on D or F grade)
complexity-check:
    @echo "Checking for high-complexity functions (D or F grade)..."
    @uvx radon cc src/layman -a -s -nc || (echo "✗ Found functions with D/F complexity grade" && exit 1)
    @echo "✓ All functions have acceptable complexity"

# Lint documentation (markdown and mermaid)
lint-docs:
    pnpm exec markdownlint-cli2 "docs/**/*.md" "*.md"
    just validate-mermaid

# Type check with ty
typecheck:
    uv run ty check src/

# ============== Formatting ==============

# Format all code
format: format-python
    @echo "✓ All formatting complete"

# Format Python code
format-python:
    uv run ruff format src/
    uv run ruff check --fix src/

# ============== Testing ==============

# Run all unit tests
test:
    uv run pytest tests/unit -v

# Run tests with fast fail (stop on first failure)
test-fast:
    uv run pytest tests/unit -v -x

# Run tests with verbose output (show print statements)
test-verbose:
    uv run pytest tests/unit -vvv -s

# Run tests with coverage report
test-cov:
    uv run pytest tests/unit -v --cov --cov-report=term-missing

# Run tests with HTML coverage report
test-cov-html:
    uv run pytest tests/unit -v --cov --cov-report=html
    @echo "Coverage report: htmlcov/index.html"

# Run integration tests (requires running Sway/i3)
test-integration:
    uv run pytest tests/integration -v -m integration

# Run integration tests with headless Sway
test-integration-headless:
    #!/usr/bin/env bash
    set -e
    export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/tmp/xdg-runtime-$$}"
    mkdir -p "$XDG_RUNTIME_DIR"
    chmod 0700 "$XDG_RUNTIME_DIR"
    export WLR_BACKENDS=headless
    export WLR_LIBINPUT_NO_DEVICES=1
    export WAYLAND_DISPLAY=wayland-test
    
    # Start headless sway in background
    sway -c /dev/null &
    SWAY_PID=$!
    sleep 2
    
    # Run tests
    uv run pytest tests/integration -v -m integration || true
    
    # Cleanup
    kill $SWAY_PID 2>/dev/null || true
    rm -rf "$XDG_RUNTIME_DIR"

# Run all tests (unit + integration if Sway available)
test-all:
    uv run pytest tests/ -v

# Run a specific test file
test-file FILE:
    uv run pytest {{FILE}} -v

# Run tests matching a pattern
test-match PATTERN:
    uv run pytest tests/unit -v -k "{{PATTERN}}"

# Run tests and drop into debugger on failure
test-debug:
    uv run pytest tests/unit -v --pdb --pdb-first

# ============== Setup ==============

# Install all dependencies
setup: setup-python setup-node
    @echo "✓ Setup complete"

# Setup Python environment
setup-python:
    uv sync

# Setup Node.js dependencies for markdown linting
setup-node:
    pnpm install

# ============== Documentation ==============

# Validate mermaid diagrams by actually rendering them
validate-mermaid:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "Rendering Mermaid diagrams to validate..."
    find docs -name "*.md" -type f | while read -r file; do \
        if grep -q '```mermaid' "$file"; then \
            echo "Validating $file..."; \
            if ! pnpm exec mmdc -i "$file" -o /tmp/mermaid-test.svg 2>&1 | grep -v "Warning:"; then \
                echo "✗ Validation failed for $file"; \
                exit 1; \
            fi; \
        fi; \
    done
    echo "✓ All mermaid diagrams rendered successfully"


# ============== Release ==============

# Build package
build:
    uv build

# Clean build artifacts
clean:
    rm -rf dist/ build/ *.egg-info src/*.egg-info
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete

# ============== Utilities ==============

# Show project info
info:
    @echo "Layman - Sway/i3 Layout Manager"
    @echo "Python: $(python3 --version)"
    @echo "uv: $(uv --version)"
    @echo "ruff: $(uv run ruff --version)"
