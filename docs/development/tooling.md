# Development Tooling

## Package Management

### uv (Recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package manager from Astral.

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies
uv sync

# Add dependency
uv add package-name

# Run command in venv
uv run layman
```

## Linting and Formatting

### Ruff

[Ruff](https://github.com/astral-sh/ruff) is an extremely fast Python linter and formatter.

```bash
# Check for issues
uv run ruff check .

# Auto-fix issues
uv run ruff check --fix .

# Format code
uv run ruff format .
```

Configuration in `pyproject.toml`:

```toml
[tool.ruff]
line-length = 88
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]
ignore = ["E501"]

[tool.ruff.format]
quote-style = "double"
```

## Type Checking

### ty (Astral)

[ty](https://github.com/astral-sh/ty) is Astral's new fast type checker.

```bash
# Install
uv add ty --dev

# Run type checking
uv run ty check src/
```

### pyright (Alternative)

```bash
uv add pyright --dev
uv run pyright src/
```

## Task Runner

### just

[just](https://github.com/casey/just) is a command runner.

```bash
# Install just
cargo install just
# Or: pacman -S just / brew install just

# Run default (list commands)
just

# Run specific command
just lint
just format
```

## Documentation Tooling

### Markdown Linting

```bash
# Install markdownlint
pnpm add -D markdownlint-cli2

# Run linting
pnpm exec markdownlint-cli2 "docs/**/*.md"
```

### Mermaid Validation

```bash
# Install mermaid-cli
pnpm add -D @mermaid-js/mermaid-cli

# Validate diagrams
pnpm exec mmdc -i docs/architecture/overview.md -o /dev/null
```

## Git Hooks

### Pre-commit

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.3
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

```bash
# Install
uv add pre-commit --dev
uv run pre-commit install
```

## Debugging

### Python Debugger

```python
# Add breakpoint
breakpoint()  # Python 3.7+

# Or
import pdb; pdb.set_trace()
```

### Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### i3ipc Debugging

```bash
# Subscribe to all events
swaymsg -t subscribe '["window", "workspace", "binding"]' -m

# Query tree
swaymsg -t get_tree | jq .
```
