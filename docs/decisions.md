# Decisions and Clarifications Needed

This document tracks unclear behaviors, design decisions, and UX improvements identified during testing analysis. As the maintainer, you should review these items and decide how the application should behave.

## Table of Contents

1. [Error Handling Strategy](#error-handling-strategy)
2. [Command Behavior](#command-behavior)
3. [Layout Transitions](#layout-transitions)
4. [Configuration Options](#configuration-options)
5. [Known Bugs Requiring Decisions](#known-bugs-requiring-decisions)
6. [UX Improvement Suggestions](#ux-improvement-suggestions)
7. [API Consistency](#api-consistency)

---

## Error Handling Strategy

### 1. Config Parsing Failure Behavior

**Current:** When TOML parsing fails, `LaymanConfig.parse()` catches the exception and returns an empty dict. The daemon continues with defaults.

**Question:** Should config errors be:
- a) **Silent** (current): Log warning, use defaults
- b) **Loud**: Print error message and exit
- c) **Loud but continue**: Print prominent warning but continue

**Recommendation:** Option (c) - users may not notice their config isn't being used.

```python
# Current code (config.py)
except Exception:
    return {}  # Silent failure
```

### 2. Invalid Option Values

**Current:** Invalid enum values (e.g., `stackLayout = "invalid"`) log an error and use defaults.

**Question:** Is this the right behavior? Should we:
- a) Use default (current)
- b) List valid options in the error message
- c) Exit with a clear error

**Recommendation:** Option (b) - show valid options:
```
Invalid stackLayout: 'invalid'. Valid options: splitv, splith, stacking, tabbed
```

### 3. Unknown Layout Names

**Current:** `setWorkspaceLayout("UnknownLayout")` logs a warning and returns without changing anything.

**Question:** What should happen?
- a) Silent no-op (current)
- b) Fall back to Sway's built-in layout
- c) Return to "none" mode

---

## Command Behavior

### 4. Unknown Commands

**Current:** Unknown layman commands are silently ignored in `onCommand()`.

**Question:** Should unknown commands:
- a) Be silently ignored (current)
- b) Log a warning
- c) Be passed to Sway as-is
- d) Print available commands

**Recommendation:** Option (b) - log for debugging:
```
[MasterStack] Unknown command: 'rotate backwards'
```

### 5. "focus left/right" vs "focus up/down"

**Current:** MasterStack handles "focus up/down" but not "focus left/right" - those fall through to Sway.

**Question:** Is this intentional?

| Command | Handled by | Expected behavior |
|---------|-----------|-------------------|
| focus up | MasterStack | Focus previous in list |
| focus down | MasterStack | Focus next in list |
| focus left | Sway | Focus left container |
| focus right | Sway | Focus right container |

**Suggestion:** Document this clearly or make all focus commands consistent.

### 6. Empty Command After Split

**Current:** Commands are split by `;` and each is processed. Empty strings after split (e.g., from "cmd1;") are passed through.

**Question:** Should empty commands be filtered out?

---

## Layout Transitions

### 7. Window Order on Layout Change

**Current:** When changing from one layout to another, window order may not be preserved in a meaningful way.

**Question:** When switching from Autotiling to MasterStack:
- Which window becomes master?
- Should order be based on creation time, focus time, or position?

**Current behavior:** Uses `workspace.leaves()` order, which is tree traversal order.

**Recommendation:** Use focus history if available, or let user specify:
```
layman layout MasterStack --master-by focus
layman layout MasterStack --master-by position
```

### 8. Floating Windows During Layout Change

**Current:** Floating windows are tracked separately and don't participate in layout.

**Question:** When a layout manager is deactivated:
- Should floating windows remain floating?
- What about windows that were auto-floated by rules?

---

## Configuration Options

### 9. `depthLimit` Has Different Meanings

**Current:**
- In Autotiling: Limits container nesting depth
- In MasterStack: Limits visible stack before creating substack

**Problem:** Same config key, different behaviors. This is confusing.

**Suggestion:** Rename MasterStack's option:
```toml
# Instead of:
depthLimit = 3

# Use:
substackThreshold = 3  # MasterStack-specific
```

### 10. masterWidth Validation

**Current:** Values outside 1-99 are rejected, using default 50.

**Questions:**
- Should 0% (no master) be valid?
- Should 100% (no stack) be valid?
- What about values like 0.5 (50%)? Currently must be int.

### 11. Output-Based Configuration (Disabled)

**Current:** The code has commented-out support for `[output.NAME]` sections.

```python
# Commented out in layman.py
# output = workspace.parent.name
# options = self.config.getForOutput(output, ...)
```

**Question:** Should this be:
- a) Removed entirely
- b) Re-enabled and documented
- c) Left as-is for future work

---

## Known Bugs Requiring Decisions

### 12. Window Width Not Preserved

**Bug:** When master window is removed, new master gets default width instead of preserving the old master's width.

**Decision needed:** What should happen?
- a) Preserve exact pixel width
- b) Preserve percentage of workspace
- c) Reset to configured `masterWidth`

**Recommendation:** Option (b) - preserve percentage, as pixel values don't transfer between different sized workspaces.

### 13. Existing Windows Sometimes Missed

**Bug:** When activating MasterStack on a workspace with existing windows, sometimes windows are missed.

**Investigation needed:** Is this:
- a) A race condition?
- b) Floating windows not being filtered?
- c) Container structure issue?

**Suggestion:** Add debug logging when `arrangeWindows()` finds fewer windows than expected.

---

## UX Improvement Suggestions

### 14. Feedback for User Commands

**Current:** Commands like `layman layout MasterStack` produce no output on success.

**Suggestion:** Add optional confirmation:
```bash
$ layman layout MasterStack
Layout set to MasterStack on workspace 1

$ layman maximize
Window maximized (toggle again to restore)
```

Could be controlled by config:
```toml
[layman]
verbose = true  # Show command feedback
```

### 15. Status Command

**Current:** No way to query current state.

**Suggestion:** Add status command:
```bash
$ layman status
Workspace 1: MasterStack (3 windows, master: Firefox)
Workspace 2: Autotiling (2 windows)
Workspace 3: none
```

### 16. Help Command

**Current:** Running `layman help` or unknown command shows nothing useful.

**Suggestion:** Add help output:
```bash
$ layman help
Layman - Sway/i3 Layout Manager

Commands:
  layout <name>     Set layout (MasterStack, Autotiling, Grid, none)
  move <dir>        Move focused window (up, down, left, right, to master)
  focus <dir>       Focus window (up, down, master)
  stack toggle      Cycle stack layout
  stackside toggle  Swap stack side
  maximize          Toggle fake fullscreen
  reload            Reload configuration
  status            Show current state
  help              Show this message
```

### 17. Named Pipe Location

**Current:** Named pipe is at a hardcoded path.

**Suggestion:** Make configurable or at least document location:
```toml
[layman]
pipePath = "/tmp/layman.pipe"
```

### 18. Better Error Messages for IPC Failures

**Current:** If the daemon isn't running, `layman <command>` fails silently or with a cryptic error.

**Suggestion:** Clear message:
```bash
$ layman layout MasterStack
Error: Layman daemon is not running. Start it with: layman
```

---

## API Consistency

### 19. Command Naming Inconsistency

Current commands have inconsistent naming:

| Command | Style |
|---------|-------|
| `move up` | verb + direction |
| `focus up` | verb + direction |
| `move to master` | verb + preposition + noun |
| `stack toggle` | noun + verb |
| `stackside toggle` | noun + verb |
| `swap master` | verb + noun |
| `rotate cw` | verb + abbreviation |
| `maximize` | verb only |

**Suggestion:** Standardize on verb-first:
```
toggle stack        (instead of stack toggle)
toggle stackside    (instead of stackside toggle)
toggle maximize     (instead of maximize)
```

Or use subcommands:
```
layman stack toggle
layman stack rotate cw
layman master swap
```

### 20. Event Handler Method Names

Current method names mix conventions:
- `windowAdded()` - past tense
- `windowRemoved()` - past tense
- `onCommand()` - "on" prefix
- `handleEvent()` - "handle" prefix

**Suggestion:** Standardize on one pattern (e.g., `on` prefix):
```python
def onWindowAdded(self, event, workspace, window): ...
def onWindowRemoved(self, event, workspace, window): ...
def onCommand(self, command, workspace): ...
```

---

## Summary of Priority Actions

### High Priority (Before Refactoring)
1. Decision #9 (depthLimit naming) - affects config schema
2. Decision #12 (width preservation) - defines expected behavior for tests
3. Decision #4 (unknown commands) - affects user debugging

### Medium Priority (UX Improvements)
4. Suggestion #14 (command feedback)
5. Suggestion #16 (help command)
6. Suggestion #18 (better error messages)

### Lower Priority (Cleanup)
7. Decision #19 (command naming)
8. Decision #20 (method naming)
9. Decision #11 (output-based config)

---

## How to Record Decisions

When you make a decision, update this document with:

```markdown
### X. Decision Title

**Decision:** [Brief description of what was decided]
**Date:** YYYY-MM-DD
**Rationale:** [Why this decision was made]
**Action:** [What code changes are needed, if any]
```

This creates a decision log for future reference.
