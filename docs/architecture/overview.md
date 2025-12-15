# Architecture Overview

## System Design

Layman is a layout management daemon for sway/i3 that operates as a separate process, communicating with the window manager via IPC.

```mermaid
graph TB
    subgraph "User Space"
        U[User Input]
        KB[Key Bindings]
        CLI[CLI Commands]
    end

    subgraph "Layman Daemon"
        direction TB
        LT[ListenerThread]
        MS[MessageServer]
        Q[Event Queue]
        LC[Layman Core]

        subgraph "Layout Managers"
            WLM[WorkspaceLayoutManager]
            AT[Autotiling]
            MSL[MasterStack]
            GR[Grid]
            CL[Custom Layouts]
        end

        subgraph "State"
            WS[WorkspaceStates]
            CFG[Configuration]
        end
    end

    subgraph "Window Manager"
        SWAY[Sway/i3]
        IPC[i3ipc Socket]
    end

    U --> KB
    U --> CLI
    KB -->|nop layman| SWAY
    CLI -->|pipe| MS
    SWAY -->|events| IPC
    IPC --> LT
    LT --> Q
    MS --> Q
    Q --> LC
    LC --> WLM
    WLM --> AT
    WLM --> MSL
    WLM --> GR
    WLM --> CL
    LC <--> WS
    LC <--> CFG
    LC -->|commands| IPC
    IPC --> SWAY
```

## Threading Model

Layman uses three threads:

| Thread | Purpose | Blocking |
|--------|---------|----------|
| Main | Event loop processing | Yes (on queue) |
| ListenerThread | i3ipc event subscription | Yes (on events) |
| MessageServer | Named pipe reading | Yes (on pipe) |

All event processing happens on the main thread to ensure thread safety.

## State Management

```mermaid
classDiagram
    class Layman {
        +workspaceStates: dict
        +builtinLayouts: dict
        +userLayouts: dict
        +options: LaymanConfig
        +conn: Connection
    }

    class WorkspaceState {
        +layoutManager: Optional~WLM~
        +layoutName: str
        +windowIds: set~int~
        +isExcluded: bool
    }

    Layman "1" --> "*" WorkspaceState : manages
```

## Window Tracking

Windows are tracked by ID in `WorkspaceState.windowIds`. This allows:

- Finding the workspace for a closed window (not in tree anymore)
- Detecting inter-workspace moves
- Handling floating windows correctly

## Error Handling

Layout managers are wrapped with `layoutManagerReloader`:

```python
@contextmanager
def layoutManagerReloader(layman, workspace, workspaceName):
    try:
        yield None
    except BaseException as e:
        logging.exception(e)
        layman.setWorkspaceLayout(workspace, workspaceName)
```

On any exception, the layout manager is reinitialized to maintain stability.
