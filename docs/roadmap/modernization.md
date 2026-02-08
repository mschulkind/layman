# Project Modernization

## Package Management with uv

### Current State

The project uses:
- `pyproject.toml` for basic project metadata
- `requirements.txt` for dependencies
- `setuptools` as build backend

### Recommended Changes

#### 1. Full uv Configuration

Update `pyproject.toml`:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "layman"
version = "0.2.0"
description = "A daemon that handles sway/i3 layout management on a per-workspace basis"
readme = "README.md"
license = "GPL-3.0-or-later"
requires-python = ">=3.10"
authors = [
    { name = "Joe Maples", email = "joe@maples.dev" }
]
dependencies = [
    "i3ipc>=2.2.1",
    "setproctitle>=1.3.1",
    "tomli>=2.0.1",
]

[project.scripts]
layman = "layman.__main__:main"

[project.urls]
Homepage = "https://github.com/mschulkind/layman"
Repository = "https://github.com/mschulkind/layman"
Documentation = "https://github.com/mschulkind/layman/tree/master/docs"

[tool.uv]
dev-dependencies = [
    "ruff>=0.8.0",
    "ty>=0.0.1a1",
    "pytest>=8.0.0",
    "pre-commit>=4.0.0",
]
```

#### 2. Remove requirements.txt

With uv, dependencies are managed via `pyproject.toml` and `uv.lock`.

```bash
# Generate lock file
uv lock

# Sync environment
uv sync
```

#### 3. Update Installation Instructions

```bash
# Development
git clone https://github.com/mschulkind/layman
cd layman
uv sync
uv run layman

# User installation
uv tool install layman
```

---

## Type Checking with ty

### What is ty?

[ty](https://github.com/astral-sh/ty) is Astral's new Python type checker, written in Rust. It's:
- Extremely fast (10-100x faster than mypy)
- From the same team as ruff and uv
- Still in alpha but rapidly improving

### Installation

```bash
uv add ty --dev
```

### Usage

```bash
# Check all source files
uv run ty check src/

# Check with specific config
uv run ty check --config pyproject.toml src/
```

### Configuration

```toml
# pyproject.toml
[tool.ty]
python-version = "3.10"
strict = false

# Gradually enable strict checking
[[tool.ty.overrides]]
module = ["layman.managers.*"]
strict = true
```

### Migration Path

1. Run ty and fix obvious errors
2. Add type hints to new code
3. Gradually add hints to existing code
4. Enable stricter checks over time

---

## Linting with Ruff

### Current Setup

No ruff configuration in project.

### Recommended Configuration

```toml
# pyproject.toml
[tool.ruff]
line-length = 88
target-version = "py310"
src = ["src"]

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "F",    # pyflakes
    "I",    # isort
    "UP",   # pyupgrade
    "B",    # flake8-bugbear
    "SIM",  # flake8-simplify
    "RUF",  # Ruff-specific
]
ignore = [
    "E501",  # Line too long (handled by formatter)
]

[tool.ruff.lint.isort]
known-first-party = ["layman"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

---

## Justfile Tasks

### Current State

Empty justfile.

### Recommended Setup

See `justfile` in project root for full implementation.

```just
# List all commands
default:
    @just --list

# Run layman
run:
    uv run layman

# Lint Python code
lint-python:
    uv run ruff check src/
    uv run ruff format --check src/

# Type check
typecheck:
    uv run ty check src/

# Full lint
lint: lint-python lint-docs typecheck
```

---

## CI/CD

### GitHub Actions

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync
      - run: just lint

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync
      - run: just test
```

---

## Pre-commit Hooks

### Setup

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.3
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
```

```bash
uv add pre-commit --dev
uv run pre-commit install
```
