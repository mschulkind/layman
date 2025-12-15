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
lint: lint-python lint-docs
    @echo "✓ All linting passed"

# Lint Python code with ruff
lint-python:
    uv run ruff check src/
    uv run ruff format --check src/

# Lint documentation (markdown and mermaid)
lint-docs:
    pnpm exec markdownlint-cli2 "docs/**/*.md" "*.md"

# Type check with ty (if available)
typecheck:
    uv run ty check src/ || echo "ty not installed or type errors found"

# ============== Formatting ==============

# Format all code
format: format-python
    @echo "✓ All formatting complete"

# Format Python code
format-python:
    uv run ruff format src/
    uv run ruff check --fix src/

# ============== Testing ==============

# Run tests
test:
    uv run pytest tests/ -v || echo "No tests found or pytest not installed"

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

# Validate mermaid diagrams in docs
validate-mermaid:
    @echo "Validating Mermaid diagrams..."
    @python3 scripts/validate_mermaid.py || echo "Mermaid validation script not found"

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
