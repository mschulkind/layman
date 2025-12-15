# MasterStack Layout

MasterStack is inspired by dwm/dwl/river, implementing a master window with a configurable stack.

## How It Works

- **Master**: Main window on one side (default: left)
- **Stack**: Remaining windows on the other side
- New windows replace master, pushing old master to top of stack
- Configurable stack layouts: splitv, splith, tabbed, stacking

```mermaid
graph LR
    subgraph Layout
        M[Master]
        S1[Stack 1]
        S2[Stack 2]
        S3[Stack 3]
    end
    M --- S1
    S1 --- S2
    S2 --- S3
```

## Visual Example

```
Default (stackSide = right):     stackSide = left:
┌─────────┬──────────┐           ┌──────────┬─────────┐
│         │  Stack 1 │           │  Stack 1 │         │
│ Master  ├──────────┤           ├──────────┤  Master │
│         │  Stack 2 │           │  Stack 2 │         │
│         ├──────────┤           ├──────────┤         │
│         │  Stack 3 │           │  Stack 3 │         │
└─────────┴──────────┘           └──────────┴─────────┘
```

## Configuration

```toml
[layman]
defaultLayout = "MasterStack"
masterWidth = 50
stackLayout = "splitv"
stackSide = "right"
depthLimit = 0

[workspace.1]
defaultLayout = "MasterStack"
masterWidth = 60       # Master takes 60% width
stackLayout = "tabbed" # Tabbed stack
stackSide = "left"     # Stack on left
depthLimit = 4         # Max 4 visible stack windows
```

### Options

| Option | Type | Default | Values |
|--------|------|---------|--------|
| `masterWidth` | int | `50` | 1-99 (percent) |
| `stackLayout` | string | `"splitv"` | splitv, splith, tabbed, stacking |
| `stackSide` | string | `"right"` | left, right |
| `depthLimit` | int | `0` | 0 = unlimited |

## Stack Layouts

### splitv (default)

```
┌─────────┬──────────┐
│         │ Stack 1  │
│ Master  ├──────────┤
│         │ Stack 2  │
│         ├──────────┤
│         │ Stack 3  │
└─────────┴──────────┘
```

### splith

```
┌─────────┬────┬────┬────┐
│         │ S1 │ S2 │ S3 │
│ Master  │    │    │    │
│         │    │    │    │
└─────────┴────┴────┴────┘
```

### tabbed

```
┌─────────┬──────────────┐
│         │[S1][S2][S3]  │
│ Master  │              │
│         │   Stack 1    │
│         │              │
└─────────┴──────────────┘
```

### stacking

```
┌─────────┬──────────────┐
│         │ ┌──────────┐ │
│         │ │ Stack 3  │ │
│ Master  │ │ Stack 2  │ │
│         │ │ Stack 1  │ │
│         │ └──────────┘ │
└─────────┴──────────────┘
```

## Commands

### Layout Control

```
layman layout MasterStack    # Activate MasterStack
layman stack toggle          # Cycle: splitv → splith → tabbed → stacking
layman stackside toggle      # Toggle: left ↔ right
layman maximize              # Toggle maximize mode
```

### Window Movement

```
layman swap master           # Swap focused with master
layman move to master        # Move focused to master position
layman move up               # Move focused up in stack
layman move down             # Move focused down in stack
layman move left             # Move towards/away from master
layman move right            # Move towards/away from master
layman move to index <n>     # Move to specific position (0 = master)
```

### Window Focus

```
layman focus master          # Focus master window
layman focus up              # Focus previous window
layman focus down            # Focus next window
```

### Rotation

```
layman rotate cw             # Rotate clockwise
layman rotate ccw            # Rotate counter-clockwise
```

## Depth Limit (Substack)

When `depthLimit > 0` and using `splitv`, excess stack windows go into a stacking subcontainer:

```
depthLimit = 3:
┌─────────┬──────────┐
│         │ Stack 1  │  ← Visible
│ Master  ├──────────┤
│         │ Stack 2  │  ← Visible
│         ├──────────┤
│         │ Stack 3  │  ← Visible
│         ├──────────┤
│         │[4][5][6] │  ← Substack (stacking)
└─────────┴──────────┘
```

## Maximize Mode

Toggle with `layman maximize`:

- Turns entire workspace into tabbed layout
- Master becomes first tab
- Stack windows become remaining tabs
- Width preserved for unmaximize

## Key Bindings Example

```
bindsym $mod+m nop layman layout MasterStack
bindsym $mod+Return nop layman swap master
bindsym $mod+t nop layman stack toggle
bindsym $mod+y nop layman stackside toggle
bindsym $mod+r nop layman rotate cw
bindsym $mod+Shift+r nop layman rotate ccw
bindsym $mod+f nop layman maximize
```
