# Tabbed Pairs

**Status:** 📋 Planned
**Priority:** High

## Overview

Group related windows (e.g., nvim + vscode) into tabbed subcontainers. Navigate between pairs with `Mod+h/l` and within pairs with `Mod+j/k`.

## Use Case

For a coding workspace, pair related windows:

```
Pair 1: [nvim1][vscode1]     Pair 2: [nvim2][vscode2]
        ↑ Mod+j/k switches          ↑ Mod+j/k switches
        ←── Mod+h/l switches between pairs ──→
```

## Visual Design

### With MasterStack

```
┌─────────────────────────────────────────────────────────┐
│ [Tab1: nvim1 | vscode1]  [Tab2: nvim2 | vscode2]        │
├──────────────────────────┬──────────────────────────────┤
│                          │                              │
│      Pair 1 Content      │       Pair 2 Content         │
│    (nvim1 or vscode1)    │    (nvim2 or vscode2)        │
│                          │                              │
└──────────────────────────┴──────────────────────────────┘
```

### Tab Structure

```
Workspace
├── Tabbed Container (outer)
│   ├── Tab: Pair 1
│   │   └── Tabbed Container (inner)
│   │       ├── nvim1
│   │       └── vscode1
│   └── Tab: Pair 2
│       └── Tabbed Container (inner)
│           ├── nvim2
│           └── vscode2
```

## Implementation Approaches

### Approach 1: New Layout Manager

Create a `TabbedPairsLayoutManager`:

```python
class TabbedPairsLayoutManager(WorkspaceLayoutManager):
    shortName = "TabbedPairs"
    overridesMoveBinds = True
    overridesFocusBinds = True

    pairs: list[list[int]] = []  # List of [window_id, window_id] pairs
    currentPairIndex: int = 0
```

### Approach 2: MasterStack Extension

Extend MasterStack with pair grouping:

```python
# Additional state in MasterStack
pairedWindows: dict[int, int] = {}  # window_id -> partner_id
```

### Approach 3: Generic Grouping System

Create a grouping system that works with any layout:

```python
class WindowGroup:
    layout: str  # tabbed, stacked, split
    windowIds: list[int]
```

## Recommended: New Layout Manager

### State

```python
@dataclass
class WindowPair:
    primary: int      # Primary window ID
    secondary: int    # Secondary window ID
    containerId: Optional[int] = None  # Tabbed container

class TabbedPairsLayoutManager(WorkspaceLayoutManager):
    shortName = "TabbedPairs"
    overridesMoveBinds = True
    overridesFocusBinds = True

    pairs: list[WindowPair] = []
    unpairedWindows: list[int] = []  # Windows waiting for a partner
    focusedPairIndex: int = 0
```

### Pairing Logic

```python
def windowAdded(self, event, workspace, window):
    # Try to auto-pair based on window class
    partner = self.findAutoPartner(window)

    if partner:
        self.createPair(workspace, partner, window)
    else:
        self.unpairedWindows.append(window.id)
        self.arrange(workspace)

def findAutoPartner(self, window) -> Optional[int]:
    window_class = window.app_id or window.window_class

    # Define pairing rules
    pair_rules = {
        "nvim": ["code", "vscode"],
        "code": ["nvim"],
        "vscode": ["nvim"],
    }

    for class_prefix, partners in pair_rules.items():
        if window_class and class_prefix in window_class.lower():
            # Find unpaired window matching partner class
            for unpaired_id in self.unpairedWindows:
                unpaired = workspace.find_by_id(unpaired_id)
                if unpaired:
                    unpaired_class = unpaired.app_id or unpaired.window_class
                    if any(p in (unpaired_class or "").lower() for p in partners):
                        return unpaired_id
    return None
```

### Creating Pairs

```python
def createPair(self, workspace, window1_id: int, window2_id: int):
    # Remove from unpaired if present
    if window1_id in self.unpairedWindows:
        self.unpairedWindows.remove(window1_id)
    if window2_id in self.unpairedWindows:
        self.unpairedWindows.remove(window2_id)

    # Create tabbed container
    self.command(f"[con_id={window1_id}] split none")
    self.command(f"[con_id={window1_id}] layout tabbed")
    self.moveWindowCommand(window2_id, window1_id)

    pair = WindowPair(primary=window1_id, secondary=window2_id)
    self.pairs.append(pair)

    self.arrange(workspace)
```

### Navigation

```python
def onCommand(self, command, workspace):
    focused = workspace.find_focused()
    if not focused:
        return

    if command == "focus up" or command == "focus down":
        # Switch within pair (between tabs)
        self.focusWithinPair(workspace, focused, command == "focus up")

    elif command == "focus left":
        # Switch to previous pair
        self.focusPair(workspace, self.focusedPairIndex - 1)

    elif command == "focus right":
        # Switch to next pair
        self.focusPair(workspace, self.focusedPairIndex + 1)

def focusWithinPair(self, workspace, window, up: bool):
    pair = self.getPairForWindow(window.id)
    if not pair:
        return

    # Switch focus between paired windows
    if window.id == pair.primary:
        target = pair.secondary
    else:
        target = pair.primary

    self.command(f"[con_id={target}] focus")

def focusPair(self, workspace, index: int):
    if not self.pairs:
        return

    index = index % len(self.pairs)
    self.focusedPairIndex = index

    pair = self.pairs[index]
    self.command(f"[con_id={pair.primary}] focus")
```

## Configuration

```toml
[workspace.coding]
defaultLayout = "TabbedPairs"

[workspace.coding.pairRules]
nvim = ["code", "vscode"]
emacs = ["code", "vscode"]
```

## Commands

```
layman layout set TabbedPairs     # Activate layout
layman pair                   # Manually pair focused with next created
layman unpair                 # Break current pair
layman window focus up               # Focus other window in pair (Mod+k)
layman window focus down             # Focus other window in pair (Mod+j)
layman window focus left             # Focus previous pair (Mod+h)
layman window focus right            # Focus next pair (Mod+l)
```

## Keybindings

```
bindsym $mod+h nop layman window focus left
bindsym $mod+j nop layman window focus down
bindsym $mod+k nop layman window focus up
bindsym $mod+l nop layman window focus right
bindsym $mod+p nop layman pair
bindsym $mod+Shift+p nop layman unpair
```

## Edge Cases

1. **Unpaired window**: Show in separate tab or floating
2. **One window closes**: Unpair the remaining window
3. **More than 2 matching windows**: First unpaired gets paired
4. **Manual pairing**: Override automatic rules
5. **Mix with non-paired windows**: Support both in same workspace
