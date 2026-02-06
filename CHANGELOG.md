# Changelog

All notable changes to layman are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased] — 2026-02-06

Major refactoring, bug fixes, and a breaking command naming change.
Phases 0–3 of the [task list](docs/roadmap/task-list.md) are complete.
Test suite grew from 0 to 278 unit tests.

### Breaking Changes

- **Command naming overhaul (Proposal B).** All commands now use subcommand
  groups. Old bare commands are removed. Migration guide:

  | Old command | New command |
  |-------------|-------------|
  | `layout MasterStack` | `layout set MasterStack` |
  | `move up` | `window move up` |
  | `move to master` | `window move to master` |
  | `focus master` | `window focus master` |
  | `swap master` | `window swap master` |
  | `rotate cw` | `window rotate cw` |
  | `stackside toggle` | `stack side toggle` |
  | `maximize` | `layout maximize` |

  Sway config bindings must be updated (see `example_sway_config`).

- **Logging output moved to stderr.** Debug and error messages now go through
  Python's `logging` module to stderr instead of stdout. Scripts parsing stdout
  output may need adjustment.

- **Removed `[output.NAME]` config section.** Per-output configuration was
  removed entirely. Use per-workspace config (`[workspace.NAME]`) instead.

### Bug Fixes

- **Master width not preserved on window removal** (Task 1). When the master
  window was closed, `popWindow` read `window.rect.width` which was often zero
  or stale. Now tracks `lastKnownMasterWidth` proactively on focus and move
  events, and falls back to config `masterWidth` if no width was ever recorded.

- **Master width reverts after mouse resize.** `windowMoved` now detects when
  the master window's width changed (e.g., via mouse drag) and updates
  `lastKnownMasterWidth` so it persists across layout operations.

- **Stale focus events from rapid window switching** (Task 9). The focus event
  handler already had a guard comparing `event.container.id` to the actual
  focused window in the tree. The log level for skipped stale events was
  upgraded from DEBUG to WARNING for better visibility.

- **Floating window tracking in core.** Floating windows are no longer dropped
  from workspace ID tracking, preventing ghost entries and missed removals.

- **`windowRemoved` crash when workspace no longer exists.** Fixed an exception
  when a window removal event arrives for a workspace that was already destroyed.

- **`moveWindowToIndex` bounds check.** Fixed an off-by-one in the index bounds
  validation.

- **Substack rebalancing on single-position moves.** Fixed incorrect rebalancing
  when moving a window into the substack by exactly one position.

- **Exception when removing all windows.** Fixed a crash in `popWindow` when the
  last window on a workspace was removed.

- **Extra nesting removal guard.** Only attempt to remove extra container nesting
  if the nesting actually exists.

### Features

- **Structured logging system** (Task 9a). New `layman.log` module with
  `get_logger()` and `setup_logging()`. Per-module named loggers, configurable
  log levels via config file, CLI override support. Replaces all ad-hoc
  `print()`, `self.log()`, and `self.debug` patterns.

  ```toml
  [layman]
  logLevel = "info"

  [logging]
  "layman.managers.master_stack" = "debug"
  ```

- **Subcommand naming** (Tasks 10–11). New command router in `handleCommand()`
  with `window`/`stack`/`layout`/`reload` prefix groups. Backwards-compatible
  passthrough for bare `move`/`focus`/`maximize` commands during transition.

- **CLI with help and status commands.** `layman help` shows grouped command
  reference. `layman status` and `layman status --json` show current daemon
  state (for waybar integration).

- **CLI command feedback.** Commands sent via the CLI now print confirmation
  (e.g., "Layout set to MasterStack", "Window moved up").

- **Configurable pipe path.** Named pipe location is now configurable via
  `pipePath` in config, defaulting to `/tmp/layman.pipe`.

- **`maximize` command.** Toggle fake fullscreen (tabbed mode) for the current
  workspace in MasterStack layout.

- **`focus up`/`focus down` override.** MasterStack now overrides focus binds
  for correct master/stack navigation.

- **`move to index` command.** Move the focused window to a specific position
  in the window list.

- **`move to master` command.** Move the focused window to the master position.

- **Default workspace layouts for non-layman layouts.** `layout set none`
  correctly resets to sway's native layout handling.

### Refactoring

- **`isExcluded()` extracted to base class** (Task 3). Autotiling and Grid had
  identical 25-line methods. Now lives in `WorkspaceLayoutManager` for all
  layouts to share.

- **Command dispatch table** (Task 4). Replaced the 23-branch `if-elif` chain
  in `MasterStackLayoutManager.onCommand()` with a `dict[str, Callable]`
  dispatch table. Cyclomatic complexity dropped from 23 to ~5.

- **`moveWindowToIndex` decomposition** (Task 5). CC=27 → extracted
  `_moveWindowMaximized()`, `_moveWindowNormal()`, and
  `_rebalanceSubstackAfterMove()`.

- **`moveWindowHorizontally` decomposition** (Task 6). CC=21 → extracted
  `_moveHorizontallyFromMaster()` and `_moveHorizontallyFromStack()`.

- **Full type annotations on `WorkspaceLayoutManager`** (Task 8). All method
  signatures have parameter and return type annotations. `logger` attribute is
  explicitly typed.

- **`ty` type errors resolved** (Task 7). Added `ty.toml` to downgrade
  `unresolved-attribute` to warning (all 83 errors were from `i3ipc`'s missing
  type stubs). Zero type errors.

### Infrastructure

- **278 unit tests** with pytest. Comprehensive coverage of all layout managers,
  config parsing, command routing, logging, server, listener, and utilities.

- **Test mocks** for `i3ipc.Connection`, `Con`, `CommandReply`, and all event
  types in `tests/mocks/i3ipc_mocks.py`.

- **`pyproject.toml` modernized.** Uses hatchling build backend. Dev
  dependencies (pytest, ruff, ty) in `[dependency-groups]`.

- **`justfile`** with `check`, `lint`, `test`, `format`, `typecheck` recipes.
  `just check` runs all quality gates.

- **Markdownlint** configured for all documentation. CI-ready.

- **Full documentation suite** in `docs/` covering architecture, API reference,
  configuration, development setup, layout guides, and roadmap.

- **`ty.toml`** configuration for Red Knot type checker with `i3ipc` stub
  workarounds.

### Documentation

- Complete README rewrite with current commands, options, and layout
  descriptions.
- Full config reference doc (`docs/configuration/config-reference.md`).
- Architecture overview, event flow, IPC documentation.
- Layout guides for MasterStack, Autotiling, and Grid.
- Development setup and testing guide.
- Roadmap with task list tracking 52 tasks across 11 phases.
- All docs and examples updated to Proposal B command naming.

---

## [Pre-refactor] — 2024-02-18

Last state before the 2025–2026 refactoring effort.

### Notable additions (2024-01-29 – 2024-02-18)

- Major overhaul of core event handling logic.
- Major overhaul of MasterStack layout (substacks, visible stack limit).
- Floating window detection for both Sway and i3.
- Timestamped logging.
- Config validation with clear error messages.
- Configurable master width, stack layout, visible stack limit.
- Workspace-specific configuration (`[workspace.NAME]`).
- Window wrapping on move.
- Source files reorganized into `src/layman/` package structure.
