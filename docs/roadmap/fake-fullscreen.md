# Fake Fullscreen

**Status:** 📋 Planned
**Priority:** High

## Overview

"Fake fullscreen" maximizes a window to fill the workspace without hiding the status bar (waybar). This is useful when you want to focus on one window but keep system information visible.

## Current Behavior

Sway's native fullscreen (`fullscreen toggle`):
- Hides all bars (waybar, etc.)
- Window covers entire screen
- Other windows completely hidden

## Desired Behavior

Fake fullscreen:
- Window fills the workspace area
- Waybar/status bars remain visible
- Quick toggle back to previous layout
- Optionally remember which window was "fullscreened"

```
Before:                          Fake Fullscreen:
┌────────────────────────────┐   ┌────────────────────────────┐
│ Waybar                     │   │ Waybar                     │
├─────────┬──────────────────┤   ├────────────────────────────┤
│         │     Window 2     │   │                            │
│ Window 1├──────────────────┤ → │        Window 1            │
│         │     Window 3     │   │     (fills workspace)      │
│         │                  │   │                            │
└─────────┴──────────────────┘   └────────────────────────────┘
```

## Implementation Approaches

### Approach 1: Layout-Level Maximize (Current)

MasterStack already has a `maximize` command that converts to tabbed layout:

```python
def toggleMaximize(self, workspace):
    if not self.maximized:
        self.command(f"[con_id={self.windowIds[0]}] layout tabbed")
        # All windows in tabs, only one visible
    else:
        # Restore previous layout
    self.maximized = not self.maximized
```

**Pros:** Already implemented for MasterStack
**Cons:** Specific to MasterStack, doesn't work for other layouts

### Approach 2: Global Fake Fullscreen Command

Add a workspace-level fake fullscreen:

```python
# In Layman class
def toggleFakeFullscreen(self, workspace, window):
    state = self.workspaceStates[workspace.name]

    if state.fakeFullscreenId:
        # Restore layout
        state.fakeFullscreenId = None
        self.setWorkspaceLayout(workspace, workspace.name)
    else:
        # Save state and maximize
        state.fakeFullscreenId = window.id
        state.savedLayout = self.serializeLayout(workspace)
        self.command(f"[con_id={window.id}] fullscreen disable")
        # Hide other windows by moving to scratchpad or making very small
```

### Approach 3: Container Manipulation

Use container layout tricks:

```python
def fakefullscreen(self, workspace, window):
    # Option A: Move other windows to scratchpad
    for w in workspace.leaves():
        if w.id != window.id:
            self.command(f"[con_id={w.id}] move scratchpad")

    # Option B: Set focus window to fill space
    self.command(f"[con_id={window.id}] resize set 100 ppt 100 ppt")
```

### Approach 4: Inhibit Fullscreen

Use sway's `inhibit_fullscreen`:

```
# In sway config
for_window [app_id=".*"] inhibit_fullscreen
```

This doesn't help us, but understanding the option is useful.

## Recommended Implementation

### State Extension

```python
@dataclass
class WorkspaceState:
    layoutManager: Optional[WorkspaceLayoutManager] = None
    layoutName: str = "none"
    windowIds: set[int] = field(default_factory=set)
    isExcluded: bool = False
    # New fields
    fakeFullscreen: bool = False
    fakeFullscreenWindowId: Optional[int] = None
    savedLayoutState: Optional[dict] = None
```

### Command Handler

```python
def handleCommand(self, command: str):
    if command == "fakefullscreen":
        workspace = utils.findFocusedWorkspace(self.conn)
        window = utils.findFocusedWindow(self.conn)
        self.toggleFakeFullscreen(workspace, window)
        return
```

### Toggle Logic

```python
def toggleFakeFullscreen(self, workspace, window):
    state = self.workspaceStates[workspace.name]

    if state.fakeFullscreen:
        # Restore
        if state.layoutManager:
            # Let layout manager handle restore
            state.layoutManager.restoreFromFakeFullscreen(state.savedLayoutState)
        else:
            # Restore basic layout
            self.restoreWindows(workspace, state.savedLayoutState)
        state.fakeFullscreen = False
    else:
        # Save and maximize
        if state.layoutManager:
            state.savedLayoutState = state.layoutManager.saveState()
            state.layoutManager.enterFakeFullscreen(window)
        else:
            state.savedLayoutState = self.saveWindowLayout(workspace)
            self.maximizeWindow(workspace, window)
        state.fakeFullscreen = True
        state.fakeFullscreenWindowId = window.id
```

## Configuration

```toml
[layman]
# Default fake fullscreen behavior
fakeFullscreenBehavior = "tabbed"  # tabbed, hide, scratchpad

[workspace.1]
fakeFullscreenBehavior = "hide"
```

## Commands

```
layman fakefullscreen         # Toggle fake fullscreen for focused window
layman fakefullscreen on      # Enter fake fullscreen
layman fakefullscreen off     # Exit fake fullscreen
```

## Keybinding Example

```
bindsym $mod+f nop layman fakefullscreen
bindsym $mod+Shift+f fullscreen toggle   # Real fullscreen
```

## Edge Cases

1. **Close faked window**: Exit fake fullscreen, restore remaining windows
2. **New window created**: Add to layout, optionally exit fake fullscreen
3. **Layout change**: Exit fake fullscreen first
4. **Workspace switch**: Fake fullscreen persists per-workspace
