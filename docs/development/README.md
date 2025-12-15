# Development

This section covers development setup, testing, and contribution guidelines.

## Contents

| File | Description |
|------|-------------|
| [setup.md](setup.md) | Development environment setup |
| [testing.md](testing.md) | Testing strategies and commands |
| [tooling.md](tooling.md) | Development tools and linting |
| [contributing.md](contributing.md) | Contribution guidelines |

## Quick Start

```bash
# Clone the repository
git clone https://github.com/frap129/layman
cd layman

# Install with uv
uv sync

# Run in development mode
uv run layman

# Run linting
just lint

# Run tests (if available)
just test
```

## Project Structure

```
layman/
├── src/layman/
│   ├── __init__.py
│   ├── __main__.py      # Entry point
│   ├── layman.py        # Main daemon class
│   ├── config.py        # Configuration parsing
│   ├── listener.py      # i3ipc event listener
│   ├── server.py        # Named pipe server
│   ├── utils.py         # Utility functions
│   └── managers/        # Layout managers
│       ├── __init__.py
│       ├── workspace.py      # Base class
│       ├── autotiling.py     # Autotiling layout
│       ├── master_stack.py   # MasterStack layout
│       └── grid.py           # Grid layout
├── docs/                # Documentation
├── config.toml          # Example config
├── pyproject.toml       # Python project config
├── justfile             # Task runner
└── README.md
```

## Technology Stack

| Tool | Purpose |
|------|---------|
| Python 3 | Primary language |
| i3ipc | Sway/i3 communication |
| tomli | TOML config parsing |
| setproctitle | Process naming |
| uv | Package management |
| ruff | Linting and formatting |
| ty | Type checking (optional) |
