# ThreeColumn Layout

ThreeColumn provides a three-column layout with a master window in the center flanked by two stacks.

## How It Works

- **Master**: Main window occupies the center column
- **Left Stack**: Stack of windows to the left of master
- **Right Stack**: Stack of windows to the right of master
- New windows are distributed between stacks to maintain balance (configurable)
- If master is closed, it is promoted from the right stack first, then left

## Visual Example

```
┌──────────┬──────────┬──────────┐
│  Stack 1 │          │  Stack 3 │
├──────────┤  Master  ├──────────┤
│  Stack 2 │          │  Stack 4 │
└──────────┴──────────┴──────────┘
```

## Configuration

```toml
[layman]
defaultLayout = "ThreeColumn"
masterWidth = 50          # Master column width percentage
stackLayout = "splitv"    # Stack layout: splitv, splith, tabbed, stacking
balanceStacks = true      # Auto-balance windows between left and right stacks

[workspace.1]
defaultLayout = "ThreeColumn"
masterWidth = 40
stackLayout = "tabbed"
balanceStacks = false     # All stack windows go to right stack
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `masterWidth` | int/float | `50` | Master column width as percentage (0–100 exclusive) |
| `stackLayout` | string | `"splitv"` | Layout for both stack columns: `splitv`, `splith`, `tabbed`, `stacking` |
| `balanceStacks` | bool | `true` | Auto-distribute windows evenly between stacks |

## Commands

All commands use the `nop layman window <cmd>` or `nop layman <cmd>` format:

| Command | Description |
|---------|-------------|
| `window move left` | Move focused window to the left column |
| `window move right` | Move focused window to the right column |
| `window move to master` | Move focused window to master (swaps with current master) |
| `window move up` | Move window up within its current column |
| `window move down` | Move window down within its current column |
| `window focus left` | Focus the left column |
| `window focus right` | Focus the right column |
| `window focus up` | Focus previous window in column |
| `window focus down` | Focus next window in column |
| `window focus master` | Focus the master window |
| `window swap master` | Swap focused window with master |
| `window rotate cw` | Rotate all windows clockwise through columns |
| `window rotate ccw` | Rotate all windows counter-clockwise |
| `stack toggle` | Cycle stack layout (splitv → splith → stacking → tabbed) |
| `layout maximize` | Toggle fake fullscreen (tabbed all) |
| `balance` | Rebalance windows between left and right stacks |

## Sway Configuration Example

```
bindsym $mod+h nop layman window focus left
bindsym $mod+l nop layman window focus right
bindsym $mod+k nop layman window focus up
bindsym $mod+j nop layman window focus down
bindsym $mod+m nop layman window focus master

bindsym $mod+Shift+h nop layman window move left
bindsym $mod+Shift+l nop layman window move right
bindsym $mod+Shift+k nop layman window move up
bindsym $mod+Shift+j nop layman window move down
bindsym $mod+Return  nop layman window swap master

bindsym $mod+r nop layman window rotate cw
bindsym $mod+Shift+r nop layman window rotate ccw
bindsym $mod+b nop layman balance
```
