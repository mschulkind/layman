# Creating Custom Layouts

Layman supports user-defined layout managers loaded from the config directory.

## Quick Start

1. Create a Python file in `~/.config/layman/`
2. Define a class inheriting from `WorkspaceLayoutManager`
3. Set a unique `shortName`
4. Use with `layman layout <shortName>`

## Example: Simple Layout

```python
# ~/.config/layman/centered.py
from layman.managers.workspace import WorkspaceLayoutManager

shortName = "Centered"

class CenteredLayoutManager(WorkspaceLayoutManager):
    shortName = "Centered"

    def windowAdded(self, event, workspace, window):
        # Center new windows
        self.command(f"[con_id={window.id}] resize set 80 ppt 90 ppt")
        self.command(f"[con_id={window.id}] move position center")
```

## WorkspaceLayoutManager API

### Class Variables

```python
class MyLayout(WorkspaceLayoutManager):
    shortName = "MyLayout"           # Required: unique identifier
    overridesMoveBinds = False       # Intercept move commands?
    overridesFocusBinds = False      # Intercept focus commands?
    supportsFloating = False         # Handle floating separately?
```

### Constructor

```python
def __init__(self, con, workspace, workspaceName, options):
    super().__init__(con, workspace, workspaceName, options)
    # Initialize your state here
    self.myState = []
```

Parameters:

- `con`: i3ipc.Connection for commands
- `workspace`: Current workspace container (may be None)
- `workspaceName`: Name of the workspace
- `options`: LaymanConfig for reading config values

### Event Hooks

```python
def windowAdded(self, event, workspace, window):
    """Called when a window is added to the workspace."""
    pass

def windowRemoved(self, event, workspace, window):
    """Called when a window leaves the workspace."""
    pass

def windowFocused(self, event, workspace, window):
    """Called when a window receives focus."""
    pass

def windowMoved(self, event, workspace, window):
    """Called when a window moves within the workspace."""
    pass

def windowFloating(self, event, workspace, window):
    """Called when floating state changes (if supportsFloating=True)."""
    pass

def onCommand(self, command, workspace):
    """Called for custom commands."""
    pass
```

### Helper Methods

```python
# Execute i3ipc command
self.command("resize set width 50 ppt")

# Logging (only when debug=true)
self.log("Debug message")
self.logCaller("Debug message from calling function")
self.logError("Error message (always shown)")
```

## Example: Three Column Layout

```python
# ~/.config/layman/three_column.py
from layman.managers.workspace import WorkspaceLayoutManager

shortName = "ThreeColumn"

class ThreeColumnLayoutManager(WorkspaceLayoutManager):
    shortName = "ThreeColumn"
    overridesMoveBinds = True

    def __init__(self, con, workspace, workspaceName, options):
        super().__init__(con, workspace, workspaceName, options)
        self.leftColumn = []
        self.centerColumn = []
        self.rightColumn = []

    def windowAdded(self, event, workspace, window):
        # Add to center by default, rebalance
        self.centerColumn.append(window.id)
        self.rebalance(workspace)

    def windowRemoved(self, event, workspace, window):
        for column in [self.leftColumn, self.centerColumn, self.rightColumn]:
            if window.id in column:
                column.remove(window.id)
                break
        self.rebalance(workspace)

    def onCommand(self, command, workspace):
        if command == "move left":
            self.moveToColumn(workspace, "left")
        elif command == "move right":
            self.moveToColumn(workspace, "right")
        # etc.

    def rebalance(self, workspace):
        # Arrange windows in three columns
        pass

    def moveToColumn(self, workspace, direction):
        # Move focused window between columns
        pass
```

## Reading Configuration

Access config values in your layout:

```python
def __init__(self, con, workspace, workspaceName, options):
    super().__init__(con, workspace, workspaceName, options)

    # Read custom option
    self.myOption = options.getForWorkspace(workspaceName, "myOption")

    # With default
    self.myOption = options.getForWorkspace(workspaceName, "myOption") or "default"
```

Config file:

```toml
[layman]
myOption = "global_value"

[workspace.1]
defaultLayout = "MyLayout"
myOption = "workspace_specific"
```

## Tips

1. **Track window IDs**: Keep a list/set of managed windows
2. **Handle edge cases**: Check for None values, empty lists
3. **Use marks**: sway marks are useful for positioning
4. **Log extensively**: Enable debug during development
5. **Test with few windows first**: Start simple

## Common Patterns

### Move Window to Mark

```python
def moveToMark(self, windowId, targetId):
    self.command(f"[con_id={targetId}] mark --add move_target")
    self.command(f"[con_id={windowId}] move window to mark move_target")
    self.command(f"[con_id={targetId}] unmark move_target")
```

### Swap Windows

```python
def swapWindows(self, id1, id2):
    self.command(f"[con_id={id1}] swap container with con_id {id2}")
```

### Set Container Layout

```python
def setLayout(self, windowId, layout):
    self.command(f"[con_id={windowId}] layout {layout}")
```

## Debugging

Enable debug for your workspace:

```toml
[workspace.1]
defaultLayout = "MyLayout"
debug = true
```

Watch output:

```bash
layman 2>&1 | grep MyLayout
```
