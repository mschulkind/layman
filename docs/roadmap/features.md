# Planned Features

## High Priority

### Three-Column Layout

**Status:** 📋 Planned
**Design:** [three-column.md](three-column.md)

XMonad-style three-column layout with windows on left, center, and right.

### Fake Fullscreen

**Status:** 📋 Planned
**Design:** [fake-fullscreen.md](fake-fullscreen.md)

Maximize a window without hiding waybar/status bars.

### Tabbed Pairs

**Status:** 📋 Planned
**Design:** [tabbed-pairs.md](tabbed-pairs.md)

Group related windows (nvim + vscode) in tabbed subcontainers.

### Session Restore

**Status:** 📋 Planned
**Design:** [session-restore.md](session-restore.md)

Save and restore window positions across reboots.

---

## Medium Priority

### Focus History

**Status:** 📋 Planned

Track focus history for better "focus previous" behavior.

```python
focusHistory: list[int] = []  # Window IDs in focus order

def windowFocused(self, event, workspace, window):
    if window.id in self.focusHistory:
        self.focusHistory.remove(window.id)
    self.focusHistory.append(window.id)
```

---

## Lower Priority

### Layout Presets

**Status:** 📋 Planned

Save and restore layout configurations by name.

```
layman preset save coding
layman preset load coding
```

### Window Rules

**Status:** 📋 Planned

Apply rules based on window class/title.

```toml
[rules]
"Firefox" = { floating = true }
"code" = { workspace = "coding" }
```

### Multi-Master

**Status:** 📋 Planned

Support multiple master windows in MasterStack. Masters split the master column vertically — with 2 masters, one on top and one on bottom; additional masters stack the same way.

```
1 master (default):           2 masters:                    3 masters:
┌─────────┬──────────┐        ┌─────────┬──────────┐        ┌─────────┬──────────┐
│         │ Stack 1  │        │ Master1 │ Stack 1  │        │ Master1 │ Stack 1  │
│ Master  ├──────────┤        ├─────────┤──────────┤        ├─────────┤──────────┤
│         │ Stack 2  │        │ Master2 │ Stack 2  │        │ Master2 │ Stack 2  │
│         ├──────────┤        │         ├──────────┤        ├─────────┤──────────┤
│         │ Stack 3  │        │         │ Stack 3  │        │ Master3 │ Stack 3  │
└─────────┴──────────┘        └─────────┴──────────┘        └─────────┴──────────┘
```

Config: `masterCount` (int, default 1). Commands: `master add`, `master remove`.
