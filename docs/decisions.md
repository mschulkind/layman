# Decisions and Clarifications - RESOLVED

This document tracks decisions that have been implemented. Each decision is marked with its resolution.

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

### 1. Config Parsing Failure Behavior ✅ RESOLVED

**Decision:** Option B - Exit with error
**Date:** 2026-02-04
**Implementation:** `config.py` now raises `ConfigError` when TOML parsing fails.

### 2. Invalid Option Values ✅ RESOLVED

**Decision:** Option C - Exit with clear error showing valid options
**Date:** 2026-02-04
**Implementation:** `ConfigError` raised with message showing valid enum values.

### 3. Unknown Layout Names ✅ RESOLVED

**Decision:** Raise `ConfigError` exception
**Date:** 2026-02-04
**Implementation:** `setWorkspaceLayout()` raises `ConfigError` with list of available layouts.

---

## Command Behavior

### 4. Unknown Commands ✅ RESOLVED

**Decision:** Log a warning/error
**Date:** 2026-02-04
**Implementation:** `onCommand()` in master_stack.py logs unknown commands via `logError()`.

### 5. "focus left/right" vs "focus up/down"

**Decision:** Keep as-is (intentional)
**Rationale:** Focus left/right falls through to Sway intentionally.

### 6. Empty Command After Split ✅ RESOLVED

**Decision:** Filter out empty commands
**Date:** 2026-02-04
**Implementation:** `onBinding()` and `onCommand()` skip empty strings after split.

---

## Layout Transitions

### 7. Window Order on Layout Change ✅ RESOLVED

**Decision:** Focused window becomes master
**Date:** 2026-02-04
**Implementation:** `arrangeWindows()` moves focused window to front of list.

### 8. Floating Windows During Layout Change

**Decision:** Leave floating windows as-is
**Rationale:** Floating windows are tracked separately and don't need changes.

---

## Configuration Options

### 9. Visible stack limit option ✅ RESOLVED

**Decision:** Introduce `visibleStackLimit` (default 3) and retire `depthLimit`/`substackThreshold`
**Date:** 2026-02-05
**Implementation:** 
- Config key renamed to `visibleStackLimit` with default 3 (0 used only if explicitly set)
- Validation enforces a positive integer and the logic to create substacks references this limit
- Updated config.toml, docs, and tests to reflect the new name and default

### 10. masterWidth Validation ✅ RESOLVED

**Decision:** Accept floats (like 33.3), reject 0 and 100
**Date:** 2026-02-04
**Implementation:** Validation accepts `int` or `float` in range (0, 100) exclusive.

### 11. Output-Based Configuration ✅ RESOLVED

**Decision:** Remove entirely
**Date:** 2026-02-04
**Implementation:** Removed commented `[output.NAME]` code and `KEY_EXCLUDED_OUTPUTS`.

---

## Known Bugs Requiring Decisions

### 12. Window Width Not Preserved

**Decision:** Deferred - this is in the roadmap as a larger design task.

### 13. Existing Windows Sometimes Missed ✅ RESOLVED

**Decision:** Add debug logging
**Date:** 2026-02-04
**Implementation:** `arrangeWindows()` logs error when window count doesn't match.

---

## UX Improvement Suggestions

### 14. Feedback for User Commands ✅ RESOLVED

**Decision:** Add feedback by default (no config needed)
**Date:** 2026-02-04
**Implementation:** `__main__.py` prints confirmation for layout, maximize, reload, move commands.

### 15. Status Command ✅ RESOLVED

**Decision:** Add with JSON option for waybar/scripts
**Date:** 2026-02-04
**Implementation:** Added `status` and `status --json` commands (placeholder for now).

### 16. Help Command ✅ RESOLVED

**Decision:** Add help output
**Date:** 2026-02-04
**Implementation:** `layman help` shows full command reference.

### 17. Named Pipe Location ✅ RESOLVED

**Decision:** Make configurable and document
**Date:** 2026-02-04
**Implementation:**
- Added `pipePath` config option in `[layman]` section
- Default remains `/tmp/layman.pipe`
- `MessageServer` accepts custom path

### 18. Better Error Messages for IPC Failures ✅ RESOLVED

**Decision:** Show clear "daemon not running" message
**Date:** 2026-02-04
**Implementation:** `__main__.py` catches `FileNotFoundError` and shows helpful message.

---

## API Consistency

### 19. Command Naming Inconsistency

**Decision:** Start a new design document
**Date:** 2026-02-04
**Implementation:** Created `docs/roadmap/command-naming.md` with proposals.

### 20. Event Handler Method Names

**Decision:** Keep existing pattern (past tense for events)
**Rationale:** Current naming is consistent within its own pattern. Changing would require widespread refactoring with little benefit.

---

## Summary

| Decision | Status | Date |
|----------|--------|------|
| #1 Config parse failure | ✅ Implemented | 2026-02-04 |
| #2 Invalid option values | ✅ Implemented | 2026-02-04 |
| #3 Unknown layout names | ✅ Implemented | 2026-02-04 |
| #4 Unknown commands | ✅ Implemented | 2026-02-04 |
| #5 Focus left/right | Keep as-is | - |
| #6 Empty commands | ✅ Implemented | 2026-02-04 |
| #7 Layout change order | ✅ Implemented | 2026-02-04 |
| #8 Floating windows | Keep as-is | - |
| #9 depthLimit naming | ✅ Implemented | 2026-02-04 |
| #10 masterWidth validation | ✅ Implemented | 2026-02-04 |
| #11 Output-based config | ✅ Removed | 2026-02-04 |
| #12 Width preservation | Deferred | - |
| #13 Missed windows logging | ✅ Implemented | 2026-02-04 |
| #14 Command feedback | ✅ Implemented | 2026-02-04 |
| #15 Status command | ✅ Implemented | 2026-02-04 |
| #16 Help command | ✅ Implemented | 2026-02-04 |
| #17 Pipe path config | ✅ Implemented | 2026-02-04 |
| #18 IPC error messages | ✅ Implemented | 2026-02-04 |
| #19 Command naming | Design doc created | 2026-02-04 |
| #20 Method naming | Keep as-is | - |
