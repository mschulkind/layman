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
layman layout MasterStack # set layout on focused workspace
layman reload             # reload config
```

### Sending Commands

There are two ways to send commands to layman:

**1. `nop` bindings (recommended)** — no process overhead, instant response:

```
bindsym $mod+m nop layman layout MasterStack
```

**2. `exec` bindings** — spawns a process, works even if you want to script layman:

```
bindsym $mod+m exec layman layout MasterStack
```

### All Commands

| Command | Description |
|---------|-------------|
| `layout <name>` | Set layout (`MasterStack`, `Autotiling`, `Grid`, `none`) |
| `move <direction>` | Move window (`up`, `down`, `left`, `right`, `to master`) |
| `focus <direction>` | Focus window (`up`, `down`, `master`) |
| `swap master` | Swap focused window with master |
| `rotate cw` | Rotate layout clockwise |
| `rotate ccw` | Rotate layout counter-clockwise |
| `stack toggle` | Cycle stack layout (splitv → splith → stacking → tabbed) |
| `stackside toggle` | Toggle stack side (left ↔ right) |
| `maximize` | Toggle fake fullscreen |
| `reload` | Reload configuration |
| `status` | Show current workspace state |
| `help` | Show command help |

## Layout Managers

### none

Does nothing. Use this to disable layout management on a workspace.

```
layman layout none
```

### Autotiling

Based on [nwg-piotr's autotiling](https://github.com/nwg-piotr/autotiling). Alternates between horizontal and vertical splits based on window dimensions, creating a spiral-like pattern.

Config options:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `depthLimit` | int | `0` | Max nesting depth (`0` = unlimited) |

```
layman layout Autotiling
```

### Grid

![](docs/Grid.gif)

Distributes windows evenly by always splitting the largest container, creating a grid-like pattern.

No layout-specific config options.

```
layman layout Grid
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
layman layout MasterStack    # activate MasterStack
layman swap master           # swap focused with master
layman move to master        # move focused to master position
layman move up               # move up in stack
layman move down             # move down in stack
layman rotate cw             # rotate clockwise
layman rotate ccw            # rotate counter-clockwise
layman stack toggle          # cycle stack layout
layman stackside toggle      # toggle stack side
layman focus master          # focus the master window
layman maximize              # toggle fake fullscreen
```

### User Created Layouts

You can create custom layouts without modifying layman. Place a Python file in the same directory as the config file (`~/.config/layman/`). It will be imported automatically at startup and on reload.

Your layout must inherit from `WorkspaceLayoutManager` and have a unique `shortName`. See `src/layman/managers/workspace.py` for the base class, and `src/layman/managers/autotiling.py` for a simple example.

## Example Sway Config

```
# Start layman
exec layman

# Layout switching
bindsym $mod+a nop layman layout Autotiling
bindsym $mod+m nop layman layout MasterStack
bindsym $mod+g nop layman layout Grid
bindsym $mod+n nop layman layout none

# MasterStack controls
bindsym $mod+Return nop layman swap master
bindsym $mod+t nop layman stack toggle
bindsym $mod+y nop layman stackside toggle
bindsym $mod+r nop layman rotate cw
bindsym $mod+Shift+r nop layman rotate ccw
bindsym $mod+f nop layman maximize

# Movement overrides
bindsym $mod+Shift+Left nop layman move left
bindsym $mod+Shift+Down nop layman move down
bindsym $mod+Shift+Up nop layman move up
bindsym $mod+Shift+Right nop layman move right

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
