# layman

layman is a daemon that handles layout management for [Sway](https://swaywm.org/)/[i3](https://i3wm.org/) on a per-workspace basis. Each workspace can have its own layout manager controlling how tiling windows are arranged.

## Features

- **Per-workspace layouts** — different layout strategies on different workspaces.
- **Built-in layouts** — Autotiling, MasterStack, and Grid.
- **Custom layouts** — write your own in Python.
- **Hot reload** — reload configuration without restarting.
- **Command interface** — control layouts via keybindings or CLI.

## Installation

For Arch users, `layman-git` is available [on the AUR](https://aur.archlinux.org/packages/layman-git) courtesy of [matclab](https://github.com/matclab).

### From source

```bash
git clone https://github.com/frap129/layman
pip install ~/path/to/layman
```

To install in development mode (changes take effect immediately):

```bash
pip install --editable ~/path/to/layman
```

## Quick Start

1. Create a config file at `~/.config/layman/config.toml`:

    ```toml
    [layman]
    defaultLayout = "Autotiling"
    ```

2. Add to your sway/i3 config:

    ```
    exec layman
    ```

3. Reload sway (`$mod+Shift+c`). Layman is now managing your windows.

## Configuration

Layman is configured with a TOML file at `~/.config/layman/config.toml`. The `[layman]` section sets global defaults, and `[workspace.<name>]` sections override options for specific workspaces.

```toml
[layman]
defaultLayout = "MasterStack"
masterWidth = 50
stackLayout = "splitv"
stackSide = "right"
visibleStackLimit = 3

[workspace.1]
defaultLayout = "MasterStack"
masterWidth = 60
stackLayout = "tabbed"

[workspace.2]
defaultLayout = "Autotiling"
depthLimit = 3
```

You can specify a different config path with `-c`:

```bash
layman -c /path/to/config.toml
```

**→ See the [full configuration reference](docs/configuration/config-reference.md) for every option, its type, default value, and valid values.**

Reload configuration at runtime:

```bash
layman reload
```

## Usage

Without arguments, `layman` starts the daemon. With arguments, it sends a command to the running daemon.

```bash
layman                    # start the daemon
layman help               # show all commands
layman layout set MasterStack # set layout on focused workspace
layman reload             # reload config
```

### Sending Commands

There are two ways to send commands to layman:

**1. `nop` bindings (recommended)** — no process overhead, instant response:

```
bindsym $mod+m nop layman layout set MasterStack
```

**2. `exec` bindings** — spawns a process, works even if you want to script layman:

```
bindsym $mod+m exec layman layout set MasterStack
```

### All Commands

| Command | Description |
|---------|-------------|
| `layout set <name>` | Set layout (`MasterStack`, `Autotiling`, `Grid`, `none`) |
| `window move <direction>` | Move window (`up`, `down`, `left`, `right`, `to master`) |
| `window focus <direction>` | Focus window (`up`, `down`, `master`) |
| `window swap master` | Swap focused window with master |
| `window rotate cw` | Rotate layout clockwise |
| `window rotate ccw` | Rotate layout counter-clockwise |
| `stack toggle` | Cycle stack layout (splitv → splith → stacking → tabbed) |
| `stack side toggle` | Toggle stack side (left ↔ right) |
| `layout maximize` | Toggle fake fullscreen |
| `reload` | Reload configuration |
| `status` | Show current workspace state |
| `help` | Show command help |

## Layout Managers

### none

Does nothing. Use this to disable layout management on a workspace.

```
layman layout set none
```

### Autotiling

Based on [nwg-piotr's autotiling](https://github.com/nwg-piotr/autotiling). Alternates between horizontal and vertical splits based on window dimensions, creating a spiral-like pattern.

Config options:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `depthLimit` | int | `0` | Max nesting depth (`0` = unlimited) |

```
layman layout set Autotiling
```

### Grid

![](docs/Grid.gif)

Distributes windows evenly by always splitting the largest container, creating a grid-like pattern.

No layout-specific config options.

```
layman layout set Grid
```

### MasterStack

![](docs/MasterStack.gif)

A master window with a configurable stack. New windows replace master, pushing old master to the stack. Supports stack layout cycling, side toggling, rotation, and a visible stack limit that collapses excess windows into a substack.

Config options:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `masterWidth` | int or float | `50` | Master width as percentage (0–100 exclusive) |
| `stackLayout` | string | `"splitv"` | `"splitv"`, `"splith"`, `"tabbed"`, `"stacking"` |
| `stackSide` | string | `"right"` | `"left"` or `"right"` |
| `visibleStackLimit` | int | `3` | Max visible stack windows before substack (`0` = disabled) |

MasterStack commands:

```
layman layout set MasterStack    # activate MasterStack
layman window swap master           # swap focused with master
layman window move to master        # move focused to master position
layman window move up               # move up in stack
layman window move down             # move down in stack
layman window rotate cw             # rotate clockwise
layman window rotate ccw            # rotate counter-clockwise
layman stack toggle          # cycle stack layout
layman stack side toggle      # toggle stack side
layman window focus master          # focus the master window
layman layout maximize              # toggle fake fullscreen
```

### User Created Layouts

You can create custom layouts without modifying layman. Place a Python file in the same directory as the config file (`~/.config/layman/`). It will be imported automatically at startup and on reload.

Your layout must inherit from `WorkspaceLayoutManager` and have a unique `shortName`. See `src/layman/managers/workspace.py` for the base class, and `src/layman/managers/autotiling.py` for a simple example.

## Example Sway Config

```
# Start layman
exec layman

# Layout switching
bindsym $mod+a nop layman layout set Autotiling
bindsym $mod+m nop layman layout set MasterStack
bindsym $mod+g nop layman layout set Grid
bindsym $mod+n nop layman layout set none

# MasterStack controls
bindsym $mod+Return nop layman window swap master
bindsym $mod+t nop layman stack toggle
bindsym $mod+y nop layman stack side toggle
bindsym $mod+r nop layman window rotate cw
bindsym $mod+Shift+r nop layman window rotate ccw
bindsym $mod+f nop layman layout maximize

# Movement overrides
bindsym $mod+Shift+Left nop layman window move left
bindsym $mod+Shift+Down nop layman window move down
bindsym $mod+Shift+Up nop layman window move up
bindsym $mod+Shift+Right nop layman window move right

# Reload config
bindsym $mod+Shift+c nop layman reload
```

## Documentation

Full documentation is in the [docs/](docs/) directory:

- **[Configuration Reference](docs/configuration/config-reference.md)** — every config option explained
- [Configuration Examples](docs/configuration/examples.md) — example configs for common setups
- [Sway Integration](docs/configuration/sway-integration.md) — keybinding setup
- [Layout Details](docs/layouts/README.md) — in-depth layout documentation
- [Architecture](docs/architecture/README.md) — system design
- [Development](docs/development/README.md) — contributing, testing, tooling
