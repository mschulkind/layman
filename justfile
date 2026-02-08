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

# ============== Quality ==============

# Run all checks (format, lint, test)
check: format lint test demo-check
    @echo "✓ All checks passed"

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
    uv run python -m pytest tests/unit -v

# Run tests with fast fail (stop on first failure)
test-fast:
    uv run python -m pytest tests/unit -v -x

# Run tests with verbose output (show print statements)
test-verbose:
    uv run python -m pytest tests/unit -vvv -s

# Run tests with coverage report
test-cov:
    uv run python -m pytest tests/unit -v --cov --cov-report=term-missing

# Run tests with HTML coverage report
test-cov-html:
    uv run python -m pytest tests/unit -v --cov --cov-report=html
    @echo "Coverage report: htmlcov/index.html"

# Run integration tests (requires running Sway/i3)
test-integration:
    uv run python -m pytest tests/integration -v -m integration

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
    uv run python -m pytest tests/integration -v -m integration || true
    
    # Cleanup
    kill $SWAY_PID 2>/dev/null || true
    rm -rf "$XDG_RUNTIME_DIR"

# Run all tests (unit + integration if Sway available)
test-all:
    uv run python -m pytest tests/ -v

# Run a specific test file
test-file FILE:
    uv run python -m pytest {{FILE}} -v

# Run tests matching a pattern
test-match PATTERN:
    uv run python -m pytest tests/unit -v -k "{{PATTERN}}"

# Run tests and drop into debugger on failure
test-debug:
    uv run python -m pytest tests/unit -v --pdb --pdb-first

# ============== Setup ==============

# Install all dependencies
setup: setup-python setup-node setup-demo
    @echo "✓ Setup complete"

# Setup Python environment
setup-python:
    uv sync

# Setup Node.js dependencies for markdown linting
setup-node:
    pnpm install

# Setup the interactive demo
setup-demo:
    cd site/demo && npm install
    cd site/demo && npx playwright install chromium

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

# Install the built package as a uv tool
install: build
    uv tool install dist/*.whl --force

# Uninstall the uv tool
uninstall:
    uv tool uninstall layman || true

# Reinstall the package
reinstall: uninstall install

# Restart the systemd service
restart-service:
    systemctl --user restart layman

# Full deploy: build, install, restart service
deploy: install restart-service
    @echo "Layman deployed and service restarted"

# Show service status
status:
    systemctl --user status layman

# View service logs
logs:
    journalctl --user -u layman -f

# Clean build artifacts
clean:
    rm -rf dist/ build/ *.egg-info src/*.egg-info
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete

# ============== Interactive Demo ==============

# Run the interactive demo dev server
demo-dev:
    cd site/demo && npm run dev

# Run demo unit tests (Vitest)
demo-test:
    cd site/demo && npm test

# Run demo unit tests with coverage
demo-test-cov:
    cd site/demo && npm run test:coverage

# Run demo E2E browser tests (Playwright)
demo-test-e2e:
    cd site/demo && npx playwright test

# Run demo E2E tests in headed browser (visible)
demo-test-e2e-headed:
    cd site/demo && npx playwright test --headed

# Run all demo tests (unit + E2E)
demo-test-all: demo-test demo-test-e2e
    @echo "✓ All demo tests passed"

# Lint demo code
demo-lint:
    cd site/demo && npm run lint

# Build the demo for production
demo-build:
    cd site/demo && npm run build

# Preview the production demo build
demo-preview:
    cd site/demo && npm run build && npm run preview

# Run all demo checks (lint + unit tests + E2E tests)
demo-check: demo-lint demo-test demo-test-e2e
    @echo "✓ All demo checks passed"

# ============== Utilities ==============

# Show project info
info:
    @echo "Layman - Sway/i3 Layout Manager"
    @echo "Python: $(python3 --version)"
    @echo "uv: $(uv --version)"
    @echo "ruff: $(uv run ruff --version)"
