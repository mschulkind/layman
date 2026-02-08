<div align="center">

# layman

**Per-workspace tiling layouts for Sway and i3**

Different layouts on every workspace — MasterStack, Autotiling, Grid, and more.

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

[Features](#features) · [Quick Start](#-quick-start) · [Layouts](#-layouts) · [Configuration](#-configuration) · [Commands](#-commands) · [Contributing](docs/DEVELOPMENT.md)

</div>

---

<div align="center">

![MasterStack Demo](docs/MasterStack.gif)

</div>

## Features

- 🖥️ **Per-workspace layouts** — MasterStack for coding, Grid for dashboards, Autotiling for everything else
- ⚡ **Zero-latency** — `nop` bindings for instant response, no process spawning
- 🔄 **Hot reload** — change config and reload without restarting
- 🎛️ **Full runtime control** — switch layouts, rotate windows, toggle stacks via keybindings
- 🐍 **Extensible** — write custom layouts in Python, auto-loaded from your config dir
- 💾 **Minimal** — single daemon process, simple TOML config

## 🚀 Quick Start

### 1. Install

```bash
git clone https://github.com/mschulkind/layman
cd layman
pip install .
```

<details>
<summary><strong>Alternative: install with uv (faster)</strong></summary>

```bash
git clone https://github.com/mschulkind/layman
cd layman
uv sync && uv tool install .
```

</details>

### 2. Create your config

```bash
mkdir -p ~/.config/layman
```

```toml
# ~/.config/layman/config.toml
[layman]
defaultLayout = "MasterStack"
masterWidth = 50
stackLayout = "splitv"
stackSide = "right"

# Per-workspace overrides
[workspace.2]
defaultLayout = "Autotiling"

[workspace.3]
defaultLayout = "Grid"
```

### 3. Add to your Sway config

Add these lines to `~/.config/sway/config`:

```bash
# Start the daemon
exec layman

# Switch layouts
bindsym $mod+m nop layman layout set MasterStack
bindsym $mod+a nop layman layout set Autotiling
bindsym $mod+g nop layman layout set Grid

# MasterStack controls
bindsym $mod+Return nop layman window swap master
bindsym $mod+t nop layman stack toggle
bindsym $mod+l nop layman stack side toggle
```

### 4. Reload Sway

Press `$mod+Shift+c` — you're done!

> 💡 See [example_sway_config](example_sway_config) for a complete keybinding setup including modes, focus history, and all layout controls.

## 🎯 Layouts

### MasterStack

Primary window on one side, stack on the other. New windows become master.

```
┌─────────┬──────────┐
│         │ Stack 1  │
│ Master  ├──────────┤
│         │ Stack 2  │
│         ├──────────┤
│         │ Stack 3  │
└─────────┴──────────┘
```

### Autotiling

Alternates horizontal/vertical splits based on window dimensions. Natural spiral pattern.

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

Splits the largest container, creating balanced even layouts.

```
┌─────────┬─────────┐
│    1    │    2    │
├─────────┼─────────┤
│    3    │    4    │
└─────────┴─────────┘
```

### ThreeColumn · TabbedPairs · Custom

Layman ships with 5 layouts and supports **custom layouts** — drop a Python file in `~/.config/layman/` that extends `WorkspaceLayoutManager` and it loads automatically.

→ [Layout documentation](docs/layouts/README.md)

## ⚙️ Configuration

Layman uses a single TOML file at `~/.config/layman/config.toml`.

| Option | Default | Description |
|--------|---------|-------------|
| `defaultLayout` | `"none"` | Layout for new workspaces |
| `masterWidth` | `50` | Master window width (1–99%) |
| `stackLayout` | `"splitv"` | `splitv`, `splith`, `tabbed`, `stacking` |
| `stackSide` | `"right"` | `left` or `right` |
| `visibleStackLimit` | `3` | Max visible stack windows |
| `depthLimit` | `0` | Autotiling depth limit (0 = unlimited) |
| `excludedWorkspaces` | `[]` | Workspace numbers to ignore |
| `debug` | `false` | Enable debug logging |

Override any option per-workspace with `[workspace.N]` sections.

→ [Full config reference](docs/configuration/config-reference.md) · [Examples](docs/configuration/examples.md)

## 📋 Commands

All commands can be bound via `nop` (recommended, zero overhead) or `exec`:

```bash
bindsym $mod+m nop layman layout set MasterStack    # nop binding (instant)
bindsym $mod+m exec layman layout set MasterStack   # exec binding (works too)
```

| Command | Description |
|---------|-------------|
| `layout set <name>` | Set layout: `MasterStack`, `Autotiling`, `Grid`, `ThreeColumn`, `TabbedPairs`, `none` |
| `layout maximize` | Toggle fake fullscreen |
| `window swap master` | Swap focused window with master |
| `window focus master` | Focus the master window |
| `window move <dir>` | Move window: `up`, `down`, `left`, `right` |
| `window rotate cw/ccw` | Rotate windows clockwise/counter-clockwise |
| `stack toggle` | Cycle stack layout: splitv → splith → stacking → tabbed |
| `stack side toggle` | Toggle stack side: left ↔ right |
| `master add/remove` | Add or remove a master slot |
| `reload` | Reload configuration |
| `status` | Show current workspace state |

## 🔧 Running as a Service

<details>
<summary><strong>Systemd user service (recommended)</strong></summary>

Create `~/.config/systemd/user/layman.service`:

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

```bash
systemctl --user enable --now layman
```

</details>

## 📚 Documentation

| | |
|---|---|
| **[Configuration Reference](docs/configuration/config-reference.md)** | Every option explained |
| [Configuration Examples](docs/configuration/examples.md) | Common setups |
| [Sway Integration](docs/configuration/sway-integration.md) | Full keybinding guide |
| [Layout Details](docs/layouts/README.md) | In-depth layout docs |
| [Custom Layouts](docs/layouts/custom-layouts.md) | Write your own layouts |
| **[Development Guide](docs/DEVELOPMENT.md)** | Setup, testing, contributing |

## Credits

Inspired by [layman](https://github.com/mschulkind/layman) by Joe Maples (frap129).

## License

[GPL v3](LICENSE)
