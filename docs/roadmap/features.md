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

### Scratchpad Integration

**Status:** 📋 Planned

Better integration with sway's scratchpad for temporary windows.

### Per-Output Configuration

**Status:** 📋 Planned

Re-enable output-based configuration (currently disabled in code).

```toml
[output.HDMI-A-1]
defaultLayout = "MasterStack"
masterWidth = 40
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

### Dynamic Master Count

**Status:** 📋 Planned

Support multiple master windows (like dwm's nmaster).

```
┌────────┬────────┬─────────┐
│ Master │ Master │ Stack 1 │
│   1    │   2    ├─────────┤
│        │        │ Stack 2 │
└────────┴────────┴─────────┘
```

### Gaps Support

**Status:** 📋 Planned

Add configurable gaps between windows.

```toml
[layman]
innerGaps = 5
outerGaps = 10
```

Note: Sway already supports gaps natively, but layout-specific gaps could be useful.
