# Roadmap: Type Safety and Modernization

This document outlines the plan for resolving type errors and modernizing the codebase using `ty` (Pyright).

## Current Status

Type checking is now enforced via `just typecheck`. Initial runs show significant errors, primarily due to:
1. **Missing Type Hints**: Many internal methods and variables lack explicit types.
2. **i3ipc Library Stubs**: The `i3ipc` library has complex types where attributes like `.name` or `.id` on `Con` objects are sometimes not recognized by static analyzers without proper casting or checks.
3. **Optional Handling**: Frequent use of `Optional` types without proper `None` checks.

## Key Issues to Resolve

### 1. `i3ipc.Con` Attribute Access
Many errors look like:
`Object of type Con has no attribute name`

**Solution**: 
- Use `typing.cast(Con, ...)` where we are certain of the type.
- Add explicit `assert window.name is not None` or similar guards.
- Create a local `Con` protocol or wrapper if the library stubs remain problematic.

### 2. Workspace State Management
The `workspaceStates` dictionary uses string keys but the values are complex `WorkspaceState` objects.

**Solution**:
- Ensure `WorkspaceState` is fully annotated.
- Use `TypedDict` or `dataclasses` for structured state.

### 3. Event Handler Signatures
Event handlers in `layman.py` often receive `Con | None` but then access attributes directly.

**Solution**:
- Use guard clauses (already planned in [code-simplification.md](code-simplification.md)).
- Refine signatures to be more specific where possible.

## Implementation Plan

### Phase 1: Infrastructure (Completed)
- [x] Add `ty` to `pyproject.toml`.
- [x] Add `just typecheck` command.
- [x] Remove "optional" status from type checking.

### Phase 2: Core Type Fixes (Short Term)
- [ ] Fix `layman.py` core event loop types.
- [ ] Add type hints to `WorkspaceState`.
- [ ] Resolve basic `None` pointer risks in `utils.py`.

### Phase 3: Layout Manager Refinement (Medium Term)
- [ ] Add full type annotations to `WorkspaceLayoutManager` base class.
- [ ] Fix complex type errors in `MasterStackLayoutManager` (especially window list management).
- [ ] Ensure all layout managers implement the interface correctly.

### Phase 4: Strict Mode (Long Term)
- [ ] Enable `strict` mode in `pyrightconfig.json` or `pyproject.toml`.
- [ ] Resolve all remaining "unknown" types.

## Success Metrics
- [ ] `just typecheck` passes with zero errors.
- [ ] No `Any` types in core logic.
- [ ] All public APIs fully documented with types.
