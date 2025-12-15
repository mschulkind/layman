# WorkspaceLayoutManager API

The base class for all layout managers. Custom layouts inherit from this class.

## Class Definition

```python
class WorkspaceLayoutManager:
    shortName: ClassVar[str] = "none"
    overridesMoveBinds: ClassVar[bool] = False
    overridesFocusBinds: ClassVar[bool] = False
    supportsFloating: ClassVar[bool] = False

    con: i3ipc.Connection
    workspaceName: str
```

## Class Variables

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `shortName` | `str` | `"none"` | Unique identifier for the layout (used in commands) |
| `overridesMoveBinds` | `bool` | `False` | Whether to intercept move commands |
| `overridesFocusBinds` | `bool` | `False` | Whether to intercept focus commands |
| `supportsFloating` | `bool` | `False` | Whether to use `windowFloating` instead of add/remove |

## Constructor

```python
def __init__(
    self,
    con: i3ipc.Connection,
    workspace: Optional[i3ipc.Con],
    workspaceName: str,
    options: LaymanConfig,
)
```

**Parameters:**

- `con`: i3ipc connection for executing commands
- `workspace`: The workspace container (may be None if empty and unfocused)
- `workspaceName`: Name of the workspace
- `options`: Loaded configuration

## Event Hooks

### windowAdded

```python
def windowAdded(
    self,
    event: i3ipc.WindowEvent,
    workspace: i3ipc.Con,
    window: i3ipc.Con,
)
```

Called when a window is added to the workspace (created or moved in).

### windowRemoved

```python
def windowRemoved(
    self,
    event: i3ipc.WindowEvent,
    workspace: Optional[i3ipc.Con],
    window: i3ipc.Con,
)
```

Called when a window leaves the workspace. Workspace may be None if last window removed while unfocused.

### windowFocused

```python
def windowFocused(
    self,
    event: i3ipc.WindowEvent,
    workspace: i3ipc.Con,
    window: i3ipc.Con,
)
```

Called when a window on the workspace receives focus.

### windowMoved

```python
def windowMoved(
    self,
    event: i3ipc.WindowEvent,
    workspace: i3ipc.Con,
    window: i3ipc.Con,
)
```

Called when a window moves within the same workspace.

### windowFloating

```python
def windowFloating(
    self,
    event: i3ipc.WindowEvent,
    workspace: i3ipc.Con,
    window: i3ipc.Con,
)
```

Called when floating state toggles (only if `supportsFloating=True`).

### onCommand

```python
def onCommand(self, command: str, workspace: i3ipc.Con)
```

Called when a layman command is executed while this workspace is focused.

## Helper Methods

### command

```python
def command(self, command: str)
```

Execute an i3ipc command and log results.

### log / logCaller / logError

Logging methods that include class name and workspace context.

## Creating Custom Layouts

1. Create a Python file in `~/.config/layman/`
2. Define a class inheriting from `WorkspaceLayoutManager`
3. Set `shortName` to a unique identifier
4. Override event hooks as needed

```python
from layman.managers.workspace import WorkspaceLayoutManager

shortName = "MyLayout"

class MyLayoutManager(WorkspaceLayoutManager):
    shortName = "MyLayout"

    def windowAdded(self, event, workspace, window):
        # Your logic here
        pass
```
