# Configuration Reference

This is the complete reference for layman's configuration file. Layman is configured with a single [TOML](https://toml.io/) file located at `~/.config/layman/config.toml`.

You can specify a different path with:

```bash
layman -c /path/to/config.toml
# or
layman --config /path/to/config.toml
```

> **Important:** If the config file contains invalid TOML syntax, layman will exit with an error. Fix the syntax and restart.

---

## File Structure

The config file has two types of sections:

- **`[layman]`** — Global defaults that apply to all workspaces.
- **`[workspace.<name>]`** — Per-workspace overrides. Any option set here takes priority over the `[layman]` value for that workspace.

```toml
[layman]
# Global defaults go here

[workspace.1]
# Overrides for workspace 1

[workspace.coding]
# Overrides for a named workspace
```

### How Overrides Work

When layman needs a config value for a workspace, it checks in this order:

1. `[workspace.<name>]` — if the key exists here, use it.
2. `[layman]` — fall back to the global default.
3. If neither has the key, use the built-in default.

---

## Global Options

These options go in the `[layman]` section and control the daemon itself.

### `defaultLayout`

The layout manager to assign to new workspaces.

| | |
|---|---|
| **Type** | string |
| **Default** | `"none"` |
| **Valid values** | `"none"`, `"Autotiling"`, `"MasterStack"`, `"Grid"`, or any user-created layout's short name |

```toml
[layman]
defaultLayout = "MasterStack"
```

### `excludedWorkspaces`

Workspace names that layman should ignore entirely. Layman will not manage windows or respond to events on these workspaces.

| | |
|---|---|
| **Type** | array of strings |
| **Default** | `[]` |

```toml
[layman]
excludedWorkspaces = ["9", "10"]
```

### `debug`

Enable verbose debug logging. When enabled, all event handlers and command executions are logged. Can be enabled globally or per-workspace.

| | |
|---|---|
| **Type** | boolean |
| **Default** | `false` |

```toml
[layman]
debug = true
```

### `pipePath`

Path to the named pipe used for IPC commands (e.g., `layman layout MasterStack` from the command line).

| | |
|---|---|
| **Type** | string |
| **Default** | `"/tmp/layman.pipe"` |

```toml
[layman]
pipePath = "/tmp/layman.pipe"
```

You typically don't need to change this unless you're running multiple instances or have a non-standard `/tmp` setup.

---

## Autotiling Options

These options configure the [Autotiling](../layouts/autotiling.md) layout manager. They can be set globally in `[layman]` or per-workspace.

### `depthLimit`

Maximum nesting depth for splits. When the depth limit is reached, Autotiling stops splitting windows further. Set to `0` to allow unlimited nesting.

| | |
|---|---|
| **Type** | integer |
| **Default** | `0` (unlimited) |
| **Valid values** | `0` or any positive integer |

```toml
[layman]
depthLimit = 0      # unlimited nesting (default)

[workspace.2]
depthLimit = 3      # max 3 levels of nesting on workspace 2
```

```
depthLimit = 0 (unlimited):        depthLimit = 2:
┌───┬───────────────────┐          ┌───┬───────────────────┐
│   │         2         │          │   │         2         │
│   ├─────────┬─────────┤          │   ├─────────┬─────────┤
│ 1 │    3    │    4    │          │ 1 │    3    │    4    │
│   │         ├────┬────┤          │   │         │         │
│   │         │ 5  │ 6  │          │   │         │  (no    │
│   │         │    ├────┤          │   │         │  split) │
│   │         │    │ 7  │          └───┴─────────┴─────────┘
└───┴─────────┴────┴────┘
```

---

## MasterStack Options

These options configure the [MasterStack](../layouts/master-stack.md) layout manager. They can be set globally in `[layman]` or per-workspace.

### `masterWidth`

The width of the master window as a percentage of the workspace.

| | |
|---|---|
| **Type** | integer or float |
| **Default** | `50` |
| **Valid values** | Any number greater than 0 and less than 100 |

```toml
[layman]
masterWidth = 50        # 50% (default)

[workspace.1]
masterWidth = 65        # 65% for coding
masterWidth = 33.3      # one-third width is also valid
```

> Values of exactly `0` or `100` are rejected because both a master and a stack must always be visible.

### `stackLayout`

The layout used for the stack container.

| | |
|---|---|
| **Type** | string |
| **Default** | `"splitv"` |
| **Valid values** | `"splitv"`, `"splith"`, `"stacking"`, `"tabbed"` |

```toml
[layman]
stackLayout = "splitv"    # each stack window gets its own row (default)
stackLayout = "splith"    # stack windows side by side
stackLayout = "tabbed"    # stack windows as tabs
stackLayout = "stacking"  # stack windows stacked (title bars only)
```

```
splitv (default):         splith:              tabbed:              stacking:
┌──────┬────────┐         ┌──────┬──┬──┬──┐   ┌──────┬──────────┐  ┌──────┬──────────┐
│      │ Stack1 │         │      │S1│S2│S3│   │      │[1][2][3] │  │      │┌────────┐│
│Master├────────┤         │Master│  │  │  │   │Master│          │  │Master││ Stack 3 ││
│      │ Stack2 │         │      │  │  │  │   │      │ Stack 1  │  │      ││ Stack 2 ││
│      ├────────┤         │      │  │  │  │   │      │          │  │      ││ Stack 1 ││
│      │ Stack3 │         │      │  │  │  │   │      │          │  │      │└────────┘│
└──────┴────────┘         └──────┴──┴──┴──┘   └──────┴──────────┘  └──────┴──────────┘
```

You can cycle through layouts at runtime with `layman stack toggle`.

### `stackSide`

Which side of the workspace the stack appears on.

| | |
|---|---|
| **Type** | string |
| **Default** | `"right"` |
| **Valid values** | `"left"`, `"right"` |

```toml
[layman]
stackSide = "right"   # stack on the right (default)

[workspace.1]
stackSide = "left"    # stack on the left
```

```
stackSide = "right" (default):    stackSide = "left":
┌─────────┬──────────┐           ┌──────────┬─────────┐
│         │  Stack 1 │           │  Stack 1 │         │
│ Master  ├──────────┤           ├──────────┤  Master │
│         │  Stack 2 │           │  Stack 2 │         │
└─────────┴──────────┘           └──────────┴─────────┘
```

You can toggle sides at runtime with `layman stackside toggle`.

### `visibleStackLimit`

The maximum number of individually visible stack windows before extra windows are collapsed into a stacking subcontainer. This only takes effect when `stackLayout` is `"splitv"`.

| | |
|---|---|
| **Type** | integer |
| **Default** | `3` |
| **Valid values** | `0` (disabled) or any positive integer |

```toml
[layman]
visibleStackLimit = 3     # show 3 stack windows, collapse the rest (default)

[workspace.1]
visibleStackLimit = 5     # more visible stack windows on workspace 1
visibleStackLimit = 0     # disable substack entirely
```

```
visibleStackLimit = 3 (with 6 windows):
┌─────────┬──────────┐
│         │ Stack 1  │  ← visible
│ Master  ├──────────┤
│         │ Stack 2  │  ← visible
│         ├──────────┤
│         │ Stack 3  │  ← visible
│         ├──────────┤
│         │[4][5][6] │  ← substack (collapsed, stacking layout)
└─────────┴──────────┘
```

> **Note:** The substack only activates with the `splitv` stack layout. Other stack layouts (tabbed, stacking, splith) already handle many windows compactly.

---

## Complete Example

```toml
[layman]
defaultLayout = "Autotiling"
excludedWorkspaces = ["10"]
debug = false
pipePath = "/tmp/layman.pipe"

# Autotiling
depthLimit = 0

# MasterStack
masterWidth = 50
stackLayout = "splitv"
stackSide = "right"
visibleStackLimit = 3

# Workspace 1: MasterStack with wide master
[workspace.1]
defaultLayout = "MasterStack"
masterWidth = 60
stackLayout = "tabbed"
stackSide = "right"

# Workspace 2: Autotiling with limited nesting
[workspace.2]
defaultLayout = "Autotiling"
depthLimit = 3

# Workspace 3: Grid
[workspace.3]
defaultLayout = "Grid"

# Workspace 4: MasterStack with left stack
[workspace.4]
defaultLayout = "MasterStack"
stackSide = "left"
masterWidth = 40
visibleStackLimit = 5

# Named workspace
[workspace.coding]
defaultLayout = "MasterStack"
masterWidth = 65
stackLayout = "splitv"
debug = true
```

---

## Validation and Errors

Layman validates all configuration values at startup. Invalid values cause layman to exit with a clear error message telling you what's wrong and what the valid options are.

| Option | Validation |
|--------|-----------|
| Config file syntax | Must be valid TOML |
| `masterWidth` | Must be a number, `0 < value < 100` |
| `stackLayout` | Must be one of: `splitv`, `splith`, `stacking`, `tabbed` |
| `stackSide` | Must be one of: `left`, `right` |
| `visibleStackLimit` | Must be a non-negative integer |

Examples of error messages:

```
Invalid masterWidth '150'. Must be a number between 0 and 100 exclusive.
Invalid stackLayout 'diagonal'. Valid options: splitv, splith, stacking, tabbed
```

---

## Reloading Configuration

You can reload the config file without restarting layman:

```bash
layman reload
```

Or bind it to a key in your sway/i3 config:

```
bindsym $mod+Shift+c nop layman reload
```

> **Note:** Reloading updates the config, but existing layout managers keep their current settings. To apply changes to a workspace that already has a layout, re-set the layout: `layman layout MasterStack`.
