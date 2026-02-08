# Development Setup

## Prerequisites

- Python 3.10+
- Sway or i3 (for testing)
- uv (recommended) or pip

## Installation with uv

```bash
# Install uv if not present
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone https://github.com/mschulkind/layman
cd layman
uv sync

# Run layman
uv run layman
```

## Installation with pip

```bash
git clone https://github.com/mschulkind/layman
cd layman
pip install -e .

# Run layman
layman
```

## Development Mode

With editable install, changes take effect immediately:

```bash
# Using uv
uv pip install -e .

# Using pip
pip install -e .
```

## Dependencies

### Runtime Dependencies

```toml
dependencies = [
    "i3ipc",        # Sway/i3 IPC
    "setproctitle", # Process naming
    "tomli",        # TOML parsing
]
```

### Development Dependencies

```toml
[tool.uv]
dev-dependencies = [
    "ruff",     # Linting/formatting
    "ty",       # Type checking
    "pytest",   # Testing
]
```

## Configuration for Development

Create a development config:

```bash
mkdir -p ~/.config/layman
cp config.toml ~/.config/layman/
```

Edit `~/.config/layman/config.toml`:

```toml
[layman]
debug = true
defaultLayout = "MasterStack"
```

## Running with Debug Output

```bash
# All output to terminal
uv run layman

# Log to file
uv run layman 2>&1 | tee /tmp/layman.log

# Watch logs
tail -f /tmp/layman.log
```

## IDE Setup

### VS Code

Recommended extensions:

- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)
- Ruff (charliermarsh.ruff)

Settings (`.vscode/settings.json`):

```json
{
    "python.defaultInterpreterPath": ".venv/bin/python",
    "[python]": {
        "editor.defaultFormatter": "charliermarsh.ruff",
        "editor.formatOnSave": true
    }
}
```

### Neovim

With nvim-lspconfig:

```lua
require('lspconfig').pyright.setup{}
require('lspconfig').ruff.setup{}
```

## Troubleshooting

### i3ipc not connecting

```bash
# Check sway socket
echo $SWAYSOCK
# Should output something like /run/user/1000/sway-ipc.1000.sock

# Verify sway is running
swaymsg -t get_version
```

### Module not found errors

```bash
# Ensure virtual environment is active
source .venv/bin/activate

# Or use uv run
uv run layman
```
