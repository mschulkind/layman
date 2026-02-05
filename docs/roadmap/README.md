# Roadmap

This section tracks planned features, known bugs, and improvements for layman.

## Contents

| File | Description |
|------|-------------|
| [bugs.md](bugs.md) | Known bugs and issues |
| [features.md](features.md) | Planned new features |
| [improvements.md](improvements.md) | Codebase improvements |
| [modernization.md](modernization.md) | Project modernization tasks |
| [code-simplification.md](code-simplification.md) | Cyclomatic complexity & SOLID refactoring |
| [type-safety.md](type-safety.md) | Type safety and modernization plan |
| [sway-ipc-optimization.md](sway-ipc-optimization.md) | Sway IPC communication optimization |

## Feature Designs

Detailed design documents for major features:

| File | Description | Priority |
|------|-------------|----------|
| [three-column.md](three-column.md) | XMonad-style three-column layout | High |
| [fake-fullscreen.md](fake-fullscreen.md) | Fullscreen without hiding waybar | High |
| [tabbed-pairs.md](tabbed-pairs.md) | Paired windows in tabbed substructure | High |
| [session-restore.md](session-restore.md) | Save and restore window layouts | Medium |
| [code-simplification.md](code-simplification.md) | Reduce complexity, apply SOLID patterns | Medium |

## Quick Overview

### High Priority

1. **Window width tracking bug** - Can't restore master width when window leaves
2. **Three-column layout** - Like XMonad's ThreeColMid
3. **Fake fullscreen** - Maximize without losing waybar
4. **Tabbed pairs** - Group nvim/vscode windows in tabs

### Medium Priority

5. **Session restore** - Remember window positions across reboots
6. **Code simplification** - Reduce cyclomatic complexity, apply SOLID principles
7. **Type safety** - Resolve all `ty` errors and achieve 100% type coverage
8. **Sway IPC optimization** - Command batching, caching, and event optimization

### Lower Priority

8. **UV modernization** - Full uv project configuration
9. **Test suite** - Automated testing
10. **General improvements** - Code quality, documentation

## Status Legend

| Status | Meaning |
|--------|---------|
| 📋 Planned | Documented, not started |
| 🚧 In Progress | Active development |
| ✅ Complete | Implemented and tested |
| ❌ Blocked | Waiting on external factors |
