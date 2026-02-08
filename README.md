<div align="center">

# layman

**Intelligent layout management for Sway and i3**

Per-workspace tiling layouts that adapt to how you work.

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

[Features](#features) • [Installation](#installation) • [Quick Start](#quick-start) • [Configuration](#configuration) • [Commands](#commands) • [Layouts](#layouts)

</div>

---

![MasterStack Demo](docs/MasterStack.gif)

## Features

- 🖥️ **Per-workspace layouts** — MasterStack on workspace 1, Grid on workspace 2, Autotiling on workspace 3
- ⚡ **Zero-latency commands** — use `nop` bindings for instant response without spawning processes
- 🔄 **Hot reload** — change your config and reload without restarting
- 🎛️ **Runtime control** — switch layouts, rotate windows, toggle stack sides on the fly
- 🐍 **Extensible** — write custom layouts in Python
- 💾 **Minimal footprint** — single daemon, simple TOML config

## Installation

### From Source (recommended)

```bash
git clone https://github.com/frap129/layman
cd layman
pip install .
```

### With uv (faster)

```bash
git clone https://github.com/frap129/layman
cd layman
uv sync
uv tool install .
```

## Quick Start

**1. Create your config file:**

```bash
mkdir -p ~/.config/layman
cat > ~/.config/layman/config.toml << 'EOF'
[layman]
defaultLayout = "MasterStack"
EOF
```

**2. Add to your Sway config** (`~/.config/sway/config`):

```bash
# Start layman daemon
exec layman

# Switch layouts
bindsym $mod+m nop layman layout set MasterStack
bindsym $mod+a nop layman layout set Autotiling
bindsym $mod+g nop layman layout set Grid

# MasterStack controls
bindsym $mod+Return nop layman window swap master
bindsym $mod+t nop layman stack toggle
```

**3. Reload Sway** (`$mod+Shift+c`) — you're done!

## Configuration

Layman uses a single TOML file at `~/.config/layman/config.toml`.

```toml
[layman]
defaultLayout = "MasterStack"    # Layout for new workspaces
masterWidth = 50                 # Master window width (%)
stackLayout = "splitv"           # splitv, splith, tabbed, stacking
stackSide = "right"              # left or right
visibleStackLimit = 3            # Collapse extra windows into substack

# Per-workspace overrides
[workspace.1]
defaultLayout = "MasterStack"
masterWidth = 60

[workspace.2]
defaultLayout = "Autotiling"
depthLimit = 3

[workspace.3]
defaultLayout = "Grid"
```

Reload your config anytime:

```bash
layman reload
```

→ **[Full Configuration Reference](docs/configuration/config-reference.md)**

## Commands

| Command | Description |
|---------|-------------|
| `layout set <name>` | Set layout: `MasterStack`, `Autotiling`, `Grid`, `none` |
| `window swap master` | Swap focused window with master |
| `window move <dir>` | Move window: `up`, `down`, `left`, `right`, `to master` |
| `window focus master` | Focus the master window |
| `window rotate cw/ccw` | Rotate layout clockwise/counter-clockwise |
| `stack toggle` | Cycle: splitv → splith → stacking → tabbed |
| `stack side toggle` | Toggle stack left ↔ right |
| `layout maximize` | Toggle fake fullscreen |
| `reload` | Reload configuration |
| `status` | Show workspace state |
| `help` | Show all commands |

### Binding Commands

**`nop` bindings** (recommended) — zero overhead, instant:

```bash
bindsym $mod+m nop layman layout set MasterStack
```

**`exec` bindings** — works for scripting:

```bash
bindsym $mod+m exec layman layout set MasterStack
```

## Layouts

### MasterStack

![MasterStack](docs/MasterStack.gif)

Primary window on one side, stack on the other. New windows become master, pushing the old master to the stack.

```
┌─────────┬──────────┐
│         │  Stack 1 │
│  Master ├──────────┤
│         │  Stack 2 │
│         ├──────────┤
│         │  Stack 3 │
└─────────┴──────────┘
```

### Autotiling

Alternates between horizontal and vertical splits based on window dimensions, creating a natural spiral pattern.

```
┌───┬───────────────────┐
│   │         2         │
│   ├─────────┬─────────┤
│ 1 │    3    │    4    │
│   │         ├────┬────┤
│   │         │ 5  │ 6  │
└───┴─────────┴────┴────┘
```

### Grid

![Grid](docs/Grid.gif)

Distributes windows evenly by always splitting the largest container.

```
┌─────────┬─────────┐
│    1    │    2    │
├─────────┼─────────┤
│    3    │    4    │
└─────────┴─────────┘
```

### Custom Layouts

Create your own! Place a Python file in `~/.config/layman/` that inherits from `WorkspaceLayoutManager`. It loads automatically on startup and reload.

→ **[Layout Development Guide](docs/layouts/README.md)**

## Running as a Service

For systemd users, create `~/.config/systemd/user/layman.service`:

```ini
[Unit]
Description=Layman Layout Manager
After=graphical-session.target

[Service]
ExecStart=/usr/local/bin/layman
Restart=on-failure

[Install]
WantedBy=graphical-session.target
```

Then:

```bash
systemctl --user enable --now layman
```

## Documentation

| Topic | Description |
|-------|-------------|
| **[Configuration Reference](docs/configuration/config-reference.md)** | Every option explained |
| [Configuration Examples](docs/configuration/examples.md) | Common setups |
| [Sway Integration](docs/configuration/sway-integration.md) | Full keybinding examples |
| [Layout Details](docs/layouts/README.md) | In-depth layout docs |
| [Development Guide](docs/CONTRIBUTING.md) | Contributing, testing, architecture |

## Credits

Inspired by [layman](https://github.com/frap129/layman) by Joe Maples (frap129).

## License

[GPL v3](LICENSE)
