# Task List

This is the master task list for all planned work on layman, organized by phase and priority. Each task references the design document it came from.

## Progress Overview

| Phase | Name | Tasks | Done | Status |
|-------|------|-------|------|--------|
| 0 | Already Done | 13 | 13 | ✅ Complete |
| 1 | Critical Bugs | 2 | 2 | ✅ Complete |
| 2 | Code Quality & Refactoring | 8 | 8 | ✅ Complete |
| 3 | Command Naming & UX | 2 | 2 | ✅ Complete |
| 4 | New Layout: Three-Column | 4 | 4 | ✅ Complete |
| 5 | Fake Fullscreen (Global) | 2 | 2 | ✅ Complete |
| 6 | Tabbed Pairs | 3 | 3 | ✅ Complete |
| 7 | Performance | 3 | 3 | ✅ Complete |
| 8 | Session Restore | 4 | 4 | ✅ Complete |
| 9 | Multi-Master | 3 | 3 | ✅ Complete |
| 10 | Polish & Lower Priority | 8 | 8 | ✅ Complete |
| | **Total** | **52** | **52** | **100% complete** |

## Status Legend

| Checkbox | Meaning |
|----------|---------|
| `- [ ]` | Not started |
| `- [x]` | Complete |

Phase headers show ✅ when all tasks in the phase are done.

---

## Phase 0 — Already Done ✅

These are resolved per [decisions.md](../decisions.md) and the current codebase:

- [x] Config validation: exit with clear errors on bad TOML, invalid enums, out-of-range values
- [x] `visibleStackLimit` rename (from `depthLimit`/`substackThreshold`), default 3
- [x] `masterWidth` accepts floats, rejects 0 and 100
- [x] Output-based config (`[output.NAME]`) removed entirely
- [x] `help`, `status`, `status --json` commands added
- [x] `pipePath` configurable
- [x] Command feedback on CLI usage
- [x] IPC error messages ("daemon not running")
- [x] `pyproject.toml` modernized (hatchling, dev deps, pytest config)
- [x] `justfile` with `check`, `lint`, `test`, `format`, `typecheck`
- [x] Test infrastructure with mocks and 231 passing unit tests
- [x] Full user-facing config reference doc
- [x] README rewrite with current commands, options, and layout docs

---

## Phase 1 — Critical Bugs ✅

- [x] **1.** Fix master width not preserved on window removal — [bugs.md](bugs.md)
- [x] **2.** Fix existing windows sometimes missed during arrange — [bugs.md](bugs.md)

### 1. Master width not preserved on window removal

**Problem:** When master closes, `popWindow` reads `window.rect.width` but it's often zero or stale by the time the event arrives. The replacement master gets default width instead of inheriting the old one.

**Plan:** Track `lastKnownMasterWidth` proactively whenever master is focused. Use that stored value in `popWindow` instead of the unreliable `window.rect.width`.

### 2. Existing windows sometimes missed during arrange

**Problem:** When activating MasterStack on a workspace with existing windows, some windows are silently skipped.

**Plan:** Debug the container traversal in `arrangeWindows()`, check for race conditions and floating window filtering issues. Add regression test.

---

## Phase 2 — Code Quality & Refactoring ✅

- [x] **3.** Extract `isExcluded()` to base class — [code-simplification.md](code-simplification.md)
- [x] **4.** Command dispatch table for `onCommand` — [code-simplification.md](code-simplification.md)
- [x] **5.** Break up `moveWindowToIndex` (CC=27) — [code-simplification.md](code-simplification.md)
- [x] **6.** Break up `moveWindowHorizontally` (CC=21) — [code-simplification.md](code-simplification.md)
- [x] **7.** Resolve `ty` type errors (core + utils) — [type-safety.md](type-safety.md)
- [x] **8.** Full type annotations on base `WorkspaceLayoutManager` — [type-safety.md](type-safety.md)
- [x] **9.** Fix minor bugs: focus race condition, inconsistent logging — [bugs.md](bugs.md)
- [x] **9a.** Structured logging with levels and per-module control

### 3. Extract `isExcluded()` to base class

Autotiling and Grid have identical 25-line `isExcluded()` methods. Move to `WorkspaceLayoutManager` so all layouts can use it.

### 4. Command dispatch table for `onCommand`

Replace the 23-branch if-elif chain in `MasterStackLayoutManager.onCommand()` with a `dict[str, CommandHandler]` dispatch table. Drops cyclomatic complexity from 23 → ~5. Each command becomes independently testable.

### 5. Break up `moveWindowToIndex`

CC=27. Extract a `MoveType` enum and separate methods for: master↔stack swap, within-stack reorder, substack rebalancing.

### 6. Break up `moveWindowHorizontally`

CC=21. Split into master-side movement and stack-side movement methods.

### 7–8. Type safety

Fix `ty` errors in core event loop, annotate `WorkspaceState`, resolve `None` risks in `utils.py`, then fully annotate the `WorkspaceLayoutManager` base class and verify all layout managers conform.

### 9. Minor bug fixes

- **Focus race condition:** Rapid focus changes can cause stale events. Add event sequence guard.
- **Inconsistent logging:** Standardize all logging on `self.log()` and `self.logCaller()`.

### 9a. Structured logging with levels and per-module control

Replace all ad-hoc `print()` / `self.log()` / `self.debug` logging with Python's `logging` module.

**Log levels:**
- `DEBUG` — Verbose per-event detail: window IDs, rect sizes, command strings, state transitions
- `INFO` — High-level actions: layout set, window added/removed, config loaded
- `WARNING` — Recoverable issues: window not found, stale event skipped
- `ERROR` — Failures: command failed, config error, assertion failed

**Per-module loggers:**
Each module gets its own named logger (e.g., `layman.layman`, `layman.managers.master_stack`, `layman.listener`, `layman.server`). Layout managers also include workspace name in the logger name or log record.

**Config:**
```toml
[layman]
logLevel = "info"                           # global default

[logging]
"layman.managers.master_stack" = "debug"    # per-module override
"layman.listener" = "warning"               # quiet the listener
```

**CLI override:**
```bash
layman --log-level debug                    # override global level from CLI
```

This replaces the boolean `debug` flag, the `self.log()` / `self.logError()` / `self.logCaller()` methods, and the `inspect.stack()` caller-name hack (the `logging` module provides this natively via `%(funcName)s`).

---

## Phase 3 — Command Naming & UX ✅

- [x] **10.** Implement subcommand naming (Proposal B) — [command-naming.md](command-naming.md)
- [x] **11.** Migrate docs and keybinding examples — [command-naming.md](command-naming.md)

### 10–11. Command naming

**Decision: Proposal B — subcommand groups (breaking change).**

Rationale: verb-first is ambiguous when the same verb applies to different nouns. Subcommand-first (`window move up`, `stack toggle`) is unambiguous and extensible.

New command structure:
```
window move up|down|left|right|to master|to index <n>
window focus up|down|master
window swap master
window rotate cw|ccw
stack toggle
stack side toggle
layout set <name>
layout maximize
reload
help
status
```

Old forms will be removed (breaking change).

---

## Phase 4 — New Layout: Three-Column ✅

- [x] **12.** Implement `ThreeColumnLayoutManager` — [three-column.md](three-column.md)
- [x] **13.** Three-column commands — [three-column.md](three-column.md)
- [x] **14.** Three-column edge cases — [three-column.md](three-column.md)
- [x] **15.** Config options & docs for ThreeColumn — [three-column.md](three-column.md)

### 12. Core implementation

**Decision:** Master is always in the center (ThreeColMid style). No `masterColumn` config option.

State: `masterId`, `leftStack`, `rightStack`. Config: `masterWidth`, `stackLayout`, `balanceStacks`.

### 13. Commands

`move left/right`, `move to master`, `swap master`, `focus left/right`, `balance`.

### 14. Edge cases

Single window fills workspace. Two windows → master + one column. Window removal triggers rebalancing. Master removal promotes from right stack (or left if empty).

### 15. Docs

Add to config reference, create layout doc, update README.

---

## Phase 5 — Fake Fullscreen (Global) ✅

- [x] **16.** Generalize fake fullscreen beyond MasterStack — [fake-fullscreen.md](fake-fullscreen.md)
- [x] **17.** Handle edge cases — [fake-fullscreen.md](fake-fullscreen.md)

**Decision:** Tabbed strategy only — no config option needed. MasterStack already has `maximize` (converts to tabbed). This phase makes it a workspace-level feature that works with any layout.

---

## Phase 6 — Tabbed Pairs ✅

- [x] **19.** Implement `TabbedPairsLayoutManager` — [tabbed-pairs.md](tabbed-pairs.md)
- [x] **20.** Pair commands and navigation — [tabbed-pairs.md](tabbed-pairs.md)
- [x] **21.** Pairing rules config — [tabbed-pairs.md](tabbed-pairs.md)

Auto-pair windows by `app_id` (e.g., nvim + vscode). Navigate between pairs with `focus left/right`, within pairs with `focus up/down`. Manual `pair`/`unpair` commands.

---

## Phase 7 — Performance ✅

- [x] **22.** Command batching — [sway-ipc-optimization.md](sway-ipc-optimization.md)
- [x] **23.** Tree cache for workspace lookup — [sway-ipc-optimization.md](sway-ipc-optimization.md)
- [x] **24.** Event debouncing — [sway-ipc-optimization.md](sway-ipc-optimization.md)

### 22. Command batching

Sway supports semicolon-separated commands in a single IPC call. A `CommandBatcher` context manager would join commands and send one round-trip. Estimated 50–75% reduction in IPC calls during layout operations.

### 23. Tree cache

Cache `window_id → workspace_name` mapping to avoid calling `get_tree()` on every single window event. Invalidate on workspace/window events that change the mapping.

### 24. Event debouncing

Collect rapid events within a short window (~10ms) and process them together, avoiding redundant layout recalculations during bursts (e.g., closing multiple windows at once).

---

## Phase 8 — Session Restore ✅

- [x] **25.** Layout state persistence (save/load to JSON) — [session-restore.md](session-restore.md)
- [x] **26.** Window matching (by `app_id`/`window_class`) — [session-restore.md](session-restore.md)
- [x] **27.** Application launch on restore — [session-restore.md](session-restore.md)
- [x] **28.** Session commands and config — [session-restore.md](session-restore.md)

### 25–28. Session restore

Save workspace layouts and window positions to a JSON file. On restore, match newly appearing windows to saved slots by `app_id` or `window_class`. Optionally launch saved applications. Commands: `session save/restore/list/delete`. Config: `sessionFile`, `autoSave`, `autoRestore`.

---

## Phase 9 — Multi-Master ✅

- [x] **29.** Multi-master: config and state
- [x] **30.** Multi-master: add/remove master commands
- [x] **31.** Multi-master: layout arrangement

### 29–31. Multi-master windows

Support multiple master windows in MasterStack (and later ThreeColumn). Masters split vertically — with 2 masters, one is on top and one on bottom; additional masters stack the same way.

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

---

## Phase 10 — Polish & Lower Priority ✅

- [x] **32.** Focus history — [features.md](features.md)
- [x] **33.** Layout manager factory — [improvements.md](improvements.md)
- [x] **34.** API docstrings (Google-style) — [improvements.md](improvements.md)
- [x] **35.** Graceful error recovery (try/except in event handlers) — [improvements.md](improvements.md)
- [x] **36.** `ty` strict mode (zero errors, no `Any` in core) — [type-safety.md](type-safety.md)
- [x] **37.** Layout presets (`layman preset save/load`) — [features.md](features.md)
- [x] **38.** Window rules (`[rules]` config section) — [features.md](features.md)
- [x] **39.** Doc cleanup sweep (stale references across all docs)

---

## Decisions Made

Recorded from Q&A on 2026-02-06:

| # | Question | Decision |
|---|----------|----------|
| Q1 | Command naming proposal | **Proposal B** — subcommand groups (breaking change). Needed for disambiguation. |
| Q2 | Fake fullscreen strategies | **Tabbed only** — no config option, just generalize the existing tabbed approach. |
| Q3 | Phase ordering | **Keep as-is** — bugs first, then refactoring, then features. |
| Q4 | Per-output configuration | **Removed permanently** — destroy all traces. |
| Q5 | Scratchpad integration | **Dropped** — not used. |
| Q6 | Gaps support | **Dropped** — use sway's native gaps instead. |
| Q7 | Three-column master position | **Center only** (ThreeColMid) — no `masterColumn` config. |
| Q8 | Doc cleanup | **Add as explicit task** — sweep all docs for stale references. |
