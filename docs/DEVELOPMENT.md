# Development Guide

Everything you need to contribute to layman.

## Quick Start

```bash
git clone https://github.com/mschulkind/layman
cd layman
just setup    # Install Python + Node dependencies
just check    # Run format + lint + tests
```

## Prerequisites

- **Python 3.10+**
- **[uv](https://github.com/astral-sh/uv)** — Python package manager
- **[just](https://github.com/casey/just)** — command runner
- **Sway or i3** — for manual testing
- **[pnpm](https://pnpm.io/)** — for docs tooling (optional)

## Setup

```bash
# Install uv if needed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and install
git clone https://github.com/mschulkind/layman
cd layman
just setup

# Create a dev config
mkdir -p ~/.config/layman
cp config.toml ~/.config/layman/
```

Enable debug mode in your config:

```toml
[layman]
debug = true
defaultLayout = "MasterStack"
```

## Common Commands

Run `just` with no arguments to see all available commands.

### Development

| Command | Description |
|---------|-------------|
| `just run` | Run the daemon |
| `just run-debug` | Run with debug output logged to `/tmp/layman.log` |
| `just check` | Run **all** quality checks (format + lint + test) |
| `just format` | Auto-format Python code |
| `just lint` | Run all linters (ruff, markdownlint, ty) |
| `just test` | Run unit tests |

### Testing

| Command | Description |
|---------|-------------|
| `just test` | All unit tests |
| `just test-fast` | Stop on first failure |
| `just test-verbose` | Verbose with print output |
| `just test-cov` | Tests with coverage report |
| `just test-cov-html` | HTML coverage report |
| `just test-match PATTERN` | Run tests matching a pattern |
| `just test-file FILE` | Run a specific test file |
| `just test-debug` | Drop into debugger on failure |
| `just test-integration` | Integration tests (requires Sway) |

### Build & Deploy

| Command | Description |
|---------|-------------|
| `just build` | Build the package |
| `just install` | Build and install as a uv tool |
| `just deploy` | Build, install, and restart systemd service |
| `just status` | Show systemd service status |
| `just logs` | Follow systemd service logs |

## Project Structure

```
src/layman/
├── __main__.py          # Entry point
├── layman.py            # Main daemon — event routing, workspace state
├── config.py            # TOML config parsing with fallbacks
├── listener.py          # i3ipc event subscriber thread
├── server.py            # Named pipe command server
├── utils.py             # Shared utilities
├── factory.py           # Layout manager factory
├── focus_history.py     # Focus history tracking
├── rules.py             # Window rules
├── session.py           # Session save/restore
├── presets.py           # Layout presets
└── managers/
    ├── workspace.py     # Base WorkspaceLayoutManager class
    ├── autotiling.py    # Autotiling layout
    ├── master_stack.py  # MasterStack layout
    ├── grid.py          # Grid layout
    ├── three_column.py  # ThreeColumn layout
    └── tabbed_pairs.py  # TabbedPairs layout
```

## Architecture

```
Sway/i3  ──i3ipc events──▶  ListenerThread  ──▶  Queue  ──▶  Layman Core
                                                                  │
Named Pipe ──commands──▶  MessageServer  ──────▶  Queue           │
                                                                  ▼
                                                          Layout Managers
                                                                  │
                                                   i3ipc commands ▼
                                                              Sway/i3
```

1. **Sway** emits window/workspace events
2. **ListenerThread** receives them via i3ipc, queues them
3. **MessageServer** reads `nop` commands from the named pipe, queues them
4. **Layman** processes the queue on the main thread
5. The appropriate **layout manager** handles each event
6. Layout manager issues **i3ipc commands** back to Sway

## Writing Tests

Follow TDD where possible:

1. **Red** — write a failing test
2. **Green** — write minimum code to pass
3. **Refactor** — clean up, ensure tests still pass

Test naming: `test_<method>_<scenario>_<expected>`

```python
def test_pushWindow_firstWindow_addedToList(mock_connection, config):
    manager = MasterStackLayoutManager(...)
    window = MockCon(id=100)
    manager.pushWindow(workspace, window)
    assert window.id in manager.windowIds
```

## Adding a Layout

1. Create `src/layman/managers/my_layout.py` extending `WorkspaceLayoutManager`
2. Register it in `src/layman/managers/__init__.py`
3. Add tests in `tests/unit/managers/test_my_layout.py`
4. Add docs in `docs/layouts/my-layout.md`

See [the custom layouts guide](layouts/custom-layouts.md) for details.

## Code Style

- **PEP 8** enforced by ruff (88-char line length)
- **Type hints** for all function signatures
- **Conventional Commits**: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`

## Debugging

```bash
# Subscribe to sway events
swaymsg -t subscribe '["window", "workspace", "binding"]' -m

# Query the tree
swaymsg -t get_tree | jq .

# Check layman status
layman status
```

## Pull Request Checklist

- [ ] `just check` passes
- [ ] Tests added for new functionality
- [ ] Docs updated if needed
- [ ] Manually tested in Sway/i3
- [ ] Conventional commit messages

## More Documentation

- [Architecture Details](architecture/README.md)
- [API Reference](api/README.md)
- [Testing Strategy](development/testing.md)
