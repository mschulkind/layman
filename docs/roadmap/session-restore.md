# Session Restore

**Status:** 📋 Planned
**Priority:** Medium

## Overview

Save window positions and layouts, then restore them on reboot or session start. This includes:

1. Which applications were open
2. Which workspace they were on
3. Their layout positions
4. Layout manager configuration

## Challenges

### 1. Window Identity

After reboot, windows have new IDs. We need to match by:
- Application ID (`app_id` in Wayland)
- Window class (`window_class` in X11)
- Window title (may change)
- Process command line

### 2. Application State

We can restore window positions, but not application state:
- Open files
- Scroll positions
- Unsaved changes

Some apps support their own session restore.

### 3. Startup Order

Applications launch at different speeds. We need to:
- Wait for windows to appear
- Handle windows appearing in wrong order
- Timeout gracefully

## Implementation Plan

### Phase 1: Layout State Persistence

Save and restore layout manager state only (not applications).

```python
# Save state
state = {
    "workspaces": {
        "1": {
            "layout": "MasterStack",
            "config": {
                "masterWidth": 60,
                "stackLayout": "tabbed",
            },
            "windows": [
                {"match": {"app_id": "foot"}, "position": "master"},
                {"match": {"app_id": "firefox"}, "position": "stack:0"},
            ]
        }
    }
}
```

### Phase 2: Window Matching

Match new windows to saved positions:

```python
def matchWindow(self, window: Con, saved_windows: list[dict]) -> Optional[dict]:
    for saved in saved_windows:
        match = saved["match"]
        if "app_id" in match and window.app_id == match["app_id"]:
            return saved
        if "class" in match and window.window_class == match["class"]:
            return saved
    return None
```

### Phase 3: Application Launch

Optionally launch saved applications:

```python
# session.json
{
    "applications": [
        {"command": "foot", "workspace": "1"},
        {"command": "firefox", "workspace": "2"},
        {"command": "code ~/projects", "workspace": "1"}
    ]
}
```

## State File Format

```json
{
    "version": 1,
    "timestamp": "2024-01-15T10:30:00Z",
    "workspaces": {
        "1": {
            "layout": "MasterStack",
            "layoutConfig": {
                "masterWidth": 55,
                "stackLayout": "splitv",
                "stackSide": "right"
            },
            "windows": [
                {
                    "match": {
                        "app_id": "foot",
                        "title_contains": "nvim"
                    },
                    "position": {
                        "index": 0,
                        "role": "master"
                    }
                },
                {
                    "match": {
                        "app_id": "firefox"
                    },
                    "position": {
                        "index": 1,
                        "role": "stack"
                    }
                }
            ]
        },
        "2": {
            "layout": "Autotiling",
            "layoutConfig": {
                "depthLimit": 3
            },
            "windows": []
        }
    }
}
```

## API

### Commands

```
layman session save [name]       # Save current session
layman session restore [name]    # Restore session
layman session list              # List saved sessions
layman session delete <name>     # Delete a session
```

### Configuration

```toml
[layman]
sessionFile = "~/.config/layman/session.json"
autoSave = true          # Save on exit
autoSaveInterval = 300   # Save every 5 minutes
autoRestore = false      # Restore on startup
```

## Implementation

### Save Session

```python
def saveSession(self, name: str = "default"):
    session = {
        "version": 1,
        "timestamp": datetime.now().isoformat(),
        "workspaces": {}
    }

    for workspace_name, state in self.workspaceStates.items():
        workspace_data = {
            "layout": state.layoutName,
            "layoutConfig": {},
            "windows": []
        }

        if state.layoutManager:
            workspace_data["layoutConfig"] = state.layoutManager.getConfig()

            for window_id in state.windowIds:
                window = self.conn.get_tree().find_by_id(window_id)
                if window:
                    workspace_data["windows"].append({
                        "match": {
                            "app_id": window.app_id,
                            "class": window.window_class,
                        },
                        "position": state.layoutManager.getWindowPosition(window_id)
                    })

        session["workspaces"][workspace_name] = workspace_data

    # Save to file
    with open(self.getSessionPath(name), 'w') as f:
        json.dump(session, f, indent=2)
```

### Restore Session

```python
def restoreSession(self, name: str = "default"):
    path = self.getSessionPath(name)
    if not os.path.exists(path):
        self.log(f"Session {name} not found")
        return

    with open(path) as f:
        session = json.load(f)

    # Store pending matches for incoming windows
    self.pendingMatches = {}

    for workspace_name, data in session["workspaces"].items():
        # Set layout
        self.setWorkspaceLayout(None, workspace_name, data["layout"])

        # Store expected windows
        self.pendingMatches[workspace_name] = data["windows"]

def windowCreated(self, event, tree, workspace, window):
    # Check if this window matches a pending restore
    if workspace and workspace.name in self.pendingMatches:
        for pending in self.pendingMatches[workspace.name]:
            if self.matchWindow(window, pending["match"]):
                # Position according to saved state
                self.positionWindow(workspace, window, pending["position"])
                self.pendingMatches[workspace.name].remove(pending)
                break

    # Continue with normal handling
    ...
```

## Systemd Integration

### Auto-save on logout

```ini
# ~/.config/systemd/user/layman-save.service
[Unit]
Description=Save layman session

[Service]
Type=oneshot
ExecStart=/usr/bin/layman session save
```

```bash
# Link to shutdown target
systemctl --user enable layman-save.service
```

### Auto-restore on login

Add to sway config:
```
exec layman session restore
```

Or with delay:
```
exec sleep 2 && layman session restore
```

## Limitations

1. **Application state not saved**: Only window positions
2. **Title matching fragile**: Titles change based on content
3. **Timing issues**: Windows may appear in different order
4. **Multi-monitor**: Output assignments may change

## Related Work

- [i3-resurrect](https://github.com/JonnyHaystack/i3-resurrect)
- [i3-save-tree](https://i3wm.org/docs/layout-saving.html)
- tmux-resurrect (for terminal sessions)
