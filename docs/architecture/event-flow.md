# Event Flow

## Event Sources

Layman receives events from two sources:

1. **i3ipc events**: Window and workspace events from sway/i3
2. **Pipe commands**: Commands from CLI or scripts

## Event Queue

Both sources feed into a `SimpleQueue`:

```python
notification: dict[str, Any] = {
    "type": "event" | "command",
    "event": IpcBaseEvent,  # if type == "event"
    "command": str,         # if type == "command"
}
```

## Main Event Loop

```python
while True:
    notification = notificationQueue.get()  # Blocking

    if notification["type"] == "event":
        # Handle window/workspace/binding events
        ...
    elif notification["type"] == "command":
        # Handle CLI commands
        self.onCommand(notification["command"])
```

## Window Event Processing

```mermaid
flowchart TD
    A[Window Event Received] --> B[Get fresh tree from sway]
    B --> C[Find window by ID]
    C --> D{Window found?}
    D -->|No| E[Log and skip]
    D -->|Yes| F[Get window's workspace]
    F --> G{Event type?}
    G -->|new| H[windowCreated]
    G -->|close| I[windowClosed]
    G -->|focus| J[windowFocused]
    G -->|move| K[windowMoved]
    G -->|floating| L[windowFloating]
    H --> M[Add to windowIds]
    M --> N[Call layoutManager.windowAdded]
    I --> O[Find workspace from windowIds]
    O --> P[Remove from windowIds]
    P --> Q[Call layoutManager.windowRemoved]
```

## Race Condition Handling

Windows can be created, moved, and closed rapidly. Layman handles this:

1. **Get fresh tree**: Always fetch current state on each event
2. **Skip stale events**: If window/workspace not found, event is ignored
3. **Track by ID**: `windowIds` set tracks which workspace owns which window

## Command Flow

```mermaid
flowchart TD
    A[Command received] --> B{Contains ';'?}
    B -->|Yes| C[Split by ';']
    B -->|No| D[Process single command]
    C --> E[For each command]
    E --> D
    D --> F{Is layman command?}
    F -->|layout| G[setWorkspaceLayout]
    F -->|reload| H[Reload config]
    F -->|move/focus| I{Manager overrides?}
    F -->|other| J[Pass to layout manager]
    I -->|Yes| J
    I -->|No| K[Execute directly via i3ipc]
```

## Binding Event Flow

When a keybind with `nop layman <command>` is pressed:

1. Sway sends `BindingEvent` with the full command
2. Layman extracts the command after "nop layman"
3. Chained commands (`;` separated) are processed sequentially
4. Each command is routed appropriately
