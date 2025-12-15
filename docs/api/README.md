# API Reference

This section documents the public API of layman's core modules and classes.

## Modules

| File | Description |
|------|-------------|
| [core.md](core.md) | Main `Layman` class and event handling |
| [layout-manager.md](layout-manager.md) | `WorkspaceLayoutManager` base class |
| [config.md](config.md) | `LaymanConfig` configuration parsing |

## Class Hierarchy

```mermaid
classDiagram
    class WorkspaceLayoutManager {
        +shortName: str
        +overridesMoveBinds: bool
        +overridesFocusBinds: bool
        +supportsFloating: bool
        +windowAdded()
        +windowRemoved()
        +windowFocused()
        +windowMoved()
        +windowFloating()
        +onCommand()
    }

    class AutotilingLayoutManager {
        +shortName = "Autotiling"
        +depthLimit: int
        +switchSplit()
    }

    class MasterStackLayoutManager {
        +shortName = "MasterStack"
        +masterWidth: int
        +stackLayout: StackLayout
        +stackSide: Side
        +windowIds: list
    }

    class GridLayoutManager {
        +shortName = "Grid"
        +switchSplit()
        +moveWindow()
    }

    WorkspaceLayoutManager <|-- AutotilingLayoutManager
    WorkspaceLayoutManager <|-- MasterStackLayoutManager
    WorkspaceLayoutManager <|-- GridLayoutManager
```

## Key Types

### WorkspaceState

```python
@dataclass
class WorkspaceState:
    layoutManager: Optional[WorkspaceLayoutManager]
    layoutName: str
    windowIds: set[int]
    isExcluded: bool
```

### Event Types (from i3ipc)

- `WindowEvent`: Window creation, focus, close, move, floating
- `WorkspaceEvent`: Workspace initialization
- `BindingEvent`: Key binding triggers
