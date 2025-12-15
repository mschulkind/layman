# Three-Column Layout

**Status:** 📋 Planned
**Priority:** High
**Inspired by:** XMonad's ThreeColMid layout

## Overview

A three-column layout with windows distributed across left, center (master), and right columns. Similar to XMonad's `ThreeColumns` and `ThreeColMid` layouts.

## Visual Design

### ThreeColMid (Recommended)

Master in center, stacks on sides:

```
┌──────────┬────────────┬──────────┐
│  Left 1  │            │ Right 1  │
├──────────┤   Master   ├──────────┤
│  Left 2  │  (center)  │ Right 2  │
├──────────┤            ├──────────┤
│  Left 3  │            │ Right 3  │
└──────────┴────────────┴──────────┘
```

### ThreeCol (Alternative)

Master on left, two stack columns:

```
┌────────────┬──────────┬──────────┐
│            │ Stack 1  │ Stack 4  │
│   Master   ├──────────┼──────────┤
│   (left)   │ Stack 2  │ Stack 5  │
│            ├──────────┼──────────┤
│            │ Stack 3  │ Stack 6  │
└────────────┴──────────┴──────────┘
```

## Configuration

```toml
[layman]
defaultLayout = "ThreeColumn"

[workspace.1]
defaultLayout = "ThreeColumn"
masterColumn = "center"    # left, center, right
masterWidth = 50           # percent
stackLayout = "splitv"     # splitv, tabbed, stacking
balanceStacks = true       # distribute evenly between stacks
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `masterColumn` | string | `"center"` | Which column is master |
| `masterWidth` | int | `50` | Master column width (percent) |
| `stackLayout` | string | `"splitv"` | Layout for stack columns |
| `balanceStacks` | bool | `true` | Distribute windows evenly |

## Window Distribution

### With balanceStacks = true

New windows alternate between left and right stacks:

```
Window 1 → Center (master)
Window 2 → Right stack
Window 3 → Left stack
Window 4 → Right stack (2nd)
Window 5 → Left stack (2nd)
...
```

### With balanceStacks = false

Fill right stack first, then left:

```
Window 1 → Center (master)
Windows 2-4 → Right stack
Windows 5+ → Left stack
```

## Commands

```
layman layout ThreeColumn        # Activate layout
layman move left                 # Move window to left column
layman move right                # Move window to right column
layman move to master            # Move window to master
layman swap master               # Swap with master
layman focus left                # Focus left column
layman focus right               # Focus right column
layman balance                   # Rebalance stacks
```

## Implementation

### State

```python
class ThreeColumnLayoutManager(WorkspaceLayoutManager):
    shortName = "ThreeColumn"
    overridesMoveBinds = True
    overridesFocusBinds = True

    masterId: Optional[int] = None
    leftStack: list[int] = []
    rightStack: list[int] = []

    masterColumn: str = "center"  # left, center, right
    masterWidth: int = 50
```

### Window Addition Logic

```python
def windowAdded(self, event, workspace, window):
    if self.masterId is None:
        # First window becomes master
        self.masterId = window.id
        return

    # Determine which stack to add to
    if self.balanceStacks:
        if len(self.leftStack) <= len(self.rightStack):
            self.leftStack.append(window.id)
        else:
            self.rightStack.append(window.id)
    else:
        # Fill right first
        self.rightStack.append(window.id)

    self.arrange(workspace)
```

### Arrangement

```python
def arrange(self, workspace):
    if not self.masterId:
        return

    if not self.leftStack and not self.rightStack:
        # Only master, fill workspace
        return

    # Create three-column structure
    # 1. Set master width
    # 2. Split remaining space for stacks
    # 3. Position each window

    total_stack_width = 100 - self.masterWidth
    left_width = total_stack_width // 2
    right_width = total_stack_width - left_width

    # Use sway layout commands to arrange
    ...
```

### Movement Between Columns

```python
def onCommand(self, command, workspace):
    focused = workspace.find_focused()
    if not focused:
        return

    if command == "move left":
        self.moveToColumn(focused, "left")
    elif command == "move right":
        self.moveToColumn(focused, "right")
    elif command == "move to master":
        self.moveToColumn(focused, "master")

def moveToColumn(self, window, target):
    current = self.getWindowColumn(window.id)
    if current == target:
        return

    # Remove from current column
    self.removeFromColumn(window.id)

    # Add to target column
    if target == "master":
        old_master = self.masterId
        self.masterId = window.id
        # Push old master to appropriate stack
        if self.masterColumn == "center":
            self.rightStack.insert(0, old_master)
        else:
            self.leftStack.insert(0, old_master)
    elif target == "left":
        self.leftStack.append(window.id)
    elif target == "right":
        self.rightStack.append(window.id)

    self.arrange(workspace)
```

## Sway Commands

To create three-column structure:

```bash
# Create horizontal container for columns
swaymsg "[con_id=$master] splith"

# Add left and right containers
swaymsg "[con_id=$master] move right"  # If master in center
swaymsg "[con_id=$left1] move left"
swaymsg "[con_id=$right1] move right"

# Set column widths
swaymsg "[con_id=$master] resize set width 50 ppt"
```

## Edge Cases

1. **Single window**: Fill entire workspace
2. **Two windows**: Master + one stack column
3. **Three windows**: One per column
4. **Window removal**: Rebalance stacks, promote from stack to master
5. **Master removal**: Promote from right stack (or left if empty)

## Related

- XMonad's [ThreeColumns](https://hackage.haskell.org/package/xmonad-contrib/docs/XMonad-Layout-ThreeColumns.html)
- dwm's `col` patch
- river's layout system
