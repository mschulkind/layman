# Code Simplification: Cyclomatic Complexity & SOLID Refactoring

This document outlines a plan to reduce cyclomatic complexity and improve adherence to SOLID principles in the layman codebase.

## Current State Analysis

### Cyclomatic Complexity Metrics

Analysis performed with [radon](https://radon.readthedocs.io/):

| File | Method | Complexity | Grade |
|------|--------|------------|-------|
| master_stack.py | `moveWindowToIndex` | 27 | D (high risk) |
| master_stack.py | `onCommand` | 23 | D (high risk) |
| master_stack.py | `moveWindowHorizontally` | 21 | D (high risk) |
| master_stack.py | `pushWindow` | 17 | C (moderate) |
| master_stack.py | `__init__` | 13 | C (moderate) |
| layman.py | `handleCommand` | 13 | C (moderate) |
| layman.py | `run` | 12 | C (moderate) |

**Grade Scale:**
- A (1-5): Low risk, simple
- B (6-10): Low risk, well-structured
- C (11-20): Moderate risk, more complex
- D (21-30): High risk, hard to test
- F (31+): Very high risk, error-prone

### Maintainability Index

| File | Score | Grade |
|------|-------|-------|
| master_stack.py | 8.46 | C (needs improvement) |
| layman.py | 30.60 | A (acceptable) |
| grid.py | 64.39 | A (good) |
| autotiling.py | 69.78 | A (good) |

**Note:** `master_stack.py` has a maintainability index of 8.46, which is critically low. Scores below 20 indicate code that is very difficult to maintain.

## Problem Areas

### 1. Long If-Elif Chains in Command Handling

**Location:** `MasterStackLayoutManager.onCommand()` (23 CC)

```python
# Current pattern - 23 branches
def onCommand(self, command, workspace):
    if command == "move up":
        self.moveWindowRelative(focused, -1)
    elif command == "move down":
        self.moveWindowRelative(focused, 1)
    elif command == "move right":
        self.moveWindowHorizontally(workspace, focused, Side.RIGHT)
    # ... 20+ more elif branches
```

**Issues:**
- Violates Open/Closed Principle (OCP) - adding commands requires modifying this method
- High cyclomatic complexity makes testing difficult
- Each branch increases cognitive load

### 2. Complex Window Movement Logic

**Location:** `MasterStackLayoutManager.moveWindowToIndex()` (27 CC)

This single method handles:
- Master window movement
- Stack window movement
- Substack rebalancing
- Window swapping
- Index boundary conditions

**Issues:**
- Violates Single Responsibility Principle (SRP)
- Deeply nested conditionals (up to 5 levels)
- Difficult to unit test individual behaviors

### 3. God Class Anti-Pattern

**Location:** `Layman` class (669 lines)

The `Layman` class handles:
- Event routing
- Window tracking
- Layout manager lifecycle
- Configuration management
- Logging
- IPC command execution

**Issues:**
- Violates SRP - too many responsibilities
- Hard to test in isolation
- Changes ripple through unrelated functionality

### 4. Duplicated Exclusion Logic

**Location:** `AutotilingLayoutManager.isExcluded()` and `GridLayoutManager.isExcluded()`

Both classes have identical 25-line methods that could be extracted to the base class.

## Refactoring Strategies

### Strategy 1: Command Pattern for Event Handling

Replace if-elif chains with a command dispatch table:

```python
from dataclasses import dataclass
from typing import Callable, Protocol

class CommandHandler(Protocol):
    def execute(self, workspace: Con, window: Con) -> None: ...

@dataclass
class MoveRelative:
    manager: "MasterStackLayoutManager"
    delta: int
    
    def execute(self, workspace: Con, window: Con) -> None:
        self.manager.moveWindowRelative(window, self.delta)

@dataclass  
class MoveHorizontal:
    manager: "MasterStackLayoutManager"
    side: Side
    
    def execute(self, workspace: Con, window: Con) -> None:
        self.manager.moveWindowHorizontally(workspace, window, self.side)

class MasterStackLayoutManager(WorkspaceLayoutManager):
    def __init__(self, ...):
        super().__init__(...)
        self._commands: dict[str, CommandHandler] = {
            "move up": MoveRelative(self, -1),
            "move down": MoveRelative(self, 1),
            "move right": MoveHorizontal(self, Side.RIGHT),
            "move left": MoveHorizontal(self, Side.LEFT),
            "move to master": MoveToIndex(self, 0),
            "focus up": FocusRelative(self, -1),
            "focus down": FocusRelative(self, 1),
            "rotate ccw": Rotate(self, "ccw"),
            "rotate cw": Rotate(self, "cw"),
            "swap master": SwapMaster(self),
            "stack toggle": StackToggle(self),
            "stackside toggle": StackSideToggle(self),
            "focus master": FocusMaster(self),
            "maximize": ToggleMaximize(self),
        }
    
    def onCommand(self, command: str, workspace: Con) -> None:
        focused = workspace.find_focused()
        if not focused or focused.id not in self.windowIds:
            return
            
        # Handle parameterized commands
        if command.startswith("move to index"):
            self._handle_move_to_index(command, focused)
            return
            
        handler = self._commands.get(command)
        if handler:
            handler.execute(workspace, focused)
        else:
            self.log(f"Unknown command: {command}")
```

**Benefits:**
- Reduces `onCommand` complexity from 23 to ~5
- Each command is independently testable
- New commands don't modify existing code (OCP)
- Commands can be reused or composed

### Strategy 2: Extract State Machine for Window Movement

The `moveWindowToIndex` method handles too many state transitions. Extract a state machine:

```python
from enum import Enum, auto
from dataclasses import dataclass

class MoveType(Enum):
    MASTER_TO_STACK = auto()
    STACK_TO_MASTER = auto()
    WITHIN_STACK = auto()
    NEIGHBOR_SWAP = auto()
    TO_SUBSTACK = auto()
    FROM_SUBSTACK = auto()

@dataclass
class MoveContext:
    window: Con
    source_index: int
    target_index: int
    master_id: int
    top_of_stack_id: int
    
    @property
    def move_type(self) -> MoveType:
        if self.source_index == 0:
            return MoveType.MASTER_TO_STACK
        elif self.target_index == 0:
            return MoveType.STACK_TO_MASTER
        elif abs(self.source_index - self.target_index) == 1:
            return MoveType.NEIGHBOR_SWAP
        # ... etc

class WindowMover:
    """Handles window movement with clear state transitions."""
    
    def __init__(self, manager: MasterStackLayoutManager):
        self.manager = manager
        self._handlers = {
            MoveType.MASTER_TO_STACK: self._move_master_to_stack,
            MoveType.STACK_TO_MASTER: self._move_stack_to_master,
            MoveType.WITHIN_STACK: self._move_within_stack,
            MoveType.NEIGHBOR_SWAP: self._swap_neighbors,
        }
    
    def move(self, ctx: MoveContext) -> None:
        handler = self._handlers.get(ctx.move_type)
        if handler:
            handler(ctx)
            self._rebalance_substack_if_needed(ctx)
```

**Benefits:**
- Each move type is isolated and testable
- State transitions are explicit
- Reduces nesting depth from 5 to 2

### Strategy 3: Dependency Injection for Layman Core

Extract responsibilities into injectable services:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

class EventBus(Protocol):
    def subscribe(self, event_type: type, handler: Callable) -> None: ...
    def publish(self, event: Any) -> None: ...

class LayoutRegistry(Protocol):
    def get(self, name: str) -> type[WorkspaceLayoutManager] | None: ...
    def register(self, manager: type[WorkspaceLayoutManager]) -> None: ...

class WorkspaceTracker(Protocol):
    def get_state(self, name: str) -> WorkspaceState: ...
    def init_workspace(self, workspace: Con) -> None: ...

@dataclass
class LaymanConfig:
    event_bus: EventBus
    layout_registry: LayoutRegistry
    workspace_tracker: WorkspaceTracker
    options: config.LaymanConfig

class Layman:
    """Core daemon - now focused only on coordination."""
    
    def __init__(self, cfg: LaymanConfig):
        self.event_bus = cfg.event_bus
        self.layouts = cfg.layout_registry
        self.workspaces = cfg.workspace_tracker
        self.options = cfg.options
        
        # Register event handlers
        self.event_bus.subscribe(WindowEvent, self._on_window_event)
        self.event_bus.subscribe(WorkspaceEvent, self._on_workspace_event)
        self.event_bus.subscribe(BindingEvent, self._on_binding_event)
```

**Benefits:**
- Each service can be mocked for testing
- Follows Dependency Inversion Principle (DIP)
- Clear separation of concerns
- Enables plugin architecture

### Strategy 4: Extract Common Window Utilities

Create a shared utilities module for common patterns:

```python
# src/layman/window_utils.py

def is_floating(window: Con) -> bool:
    """Check if a window is floating (works for both i3 and Sway)."""
    i3_floating = window.floating is not None and "on" in window.floating
    sway_floating = window.type == "floating_con"
    return i3_floating or sway_floating

def is_excluded(window: Con | None) -> bool:
    """Check if a window should be excluded from layout management."""
    if window is None:
        return True
    if window.type != "con":
        return True
    if window.workspace() is None:
        return True
    if is_floating(window):
        return True
    if window.fullscreen_mode == 1:
        return True
    if window.parent.layout in ("stacked", "tabbed"):
        return True
    return False

def find_by_id_safe(workspace: Con, window_id: int) -> Con | None:
    """Find window by ID with proper error handling."""
    try:
        return workspace.find_by_id(window_id)
    except Exception:
        return None
```

**Benefits:**
- Eliminates duplicate code in autotiling.py and grid.py
- Single source of truth for window state checks
- Easier to test and maintain

### Strategy 5: Guard Clauses and Early Returns

Replace nested conditionals with guard clauses:

```python
# Before (nested)
def windowFocused(self, event, tree, workspace, window):
    if workspace:
        state = self.workspaceStates[workspace.name]
        if not state.isExcluded:
            focused = workspace.find_focused()
            if focused and event.container.id == focused.id:
                if state.layoutManager:
                    state.layoutManager.windowFocused(event, workspace, window)

# After (guard clauses)
def windowFocused(self, event, tree, workspace, window):
    if not workspace:
        self.log("no workspace found")
        return
        
    state = self.workspaceStates[workspace.name]
    if state.isExcluded:
        self.log("Workspace excluded")
        return
        
    focused = workspace.find_focused()
    if not focused or event.container.id != focused.id:
        self.log(f"Focus mismatch: expected {event.container.id}, got {focused}")
        return
        
    if not state.layoutManager:
        return
        
    with layoutManagerReloader(self, workspace):
        state.layoutManager.windowFocused(event, workspace, window)
```

**Benefits:**
- Reduces nesting depth
- Makes preconditions explicit
- Easier to follow control flow

## Implementation Phases

### Phase 1: Quick Wins (1-2 days)
1. Extract `is_excluded()` to shared utility module
2. Add guard clauses to reduce nesting in Layman event handlers
3. Extract `is_floating()` helper function

**Complexity Reduction Target:** 10-15%

### Phase 2: Command Pattern (3-5 days)
1. Create command handler protocol and base classes
2. Refactor `MasterStackLayoutManager.onCommand()` to use dispatch table
3. Add unit tests for individual commands

**Complexity Reduction Target:** `onCommand` from 23 → 5

### Phase 3: Window Movement Refactor (5-7 days)
1. Create `MoveContext` dataclass
2. Extract `WindowMover` class with clear state machine
3. Refactor `moveWindowToIndex()` and `moveWindowHorizontally()`
4. Add comprehensive unit tests

**Complexity Reduction Target:** `moveWindowToIndex` from 27 → 10

### Phase 4: Dependency Injection (1-2 weeks)
1. Define service protocols
2. Extract `LayoutRegistry` class
3. Extract `WorkspaceTracker` class
4. Refactor `Layman` to accept dependencies
5. Add integration tests with mock services

**Maintainability Index Target:** Improve all files to 50+

## Tooling Recommendations

### Add to justfile

```just
# Analyze code complexity
complexity:
    uvx radon cc src/layman -a -s
    uvx radon mi src/layman -s

# Check complexity thresholds (fail if D or F grade)
complexity-check:
    uvx radon cc src/layman -a -s --total-average -nc
```

### Add to pyproject.toml

```toml
[tool.ruff.lint]
select = [
    # ... existing rules ...
    "C901",   # McCabe complexity
    "PLR0911", # Too many return statements
    "PLR0912", # Too many branches  
    "PLR0913", # Too many arguments
    "PLR0915", # Too many statements
]

[tool.ruff.lint.mccabe]
max-complexity = 10

[tool.ruff.lint.pylint]
max-branches = 12
max-returns = 6
max-args = 6
```

### Recommended Development Packages

```toml
[dependency-groups]
dev = [
    # ... existing ...
    "radon>=6.0.0",      # Complexity analysis
    "xenon>=0.9.0",      # Complexity threshold enforcement
    "pytest-cov>=4.0.0", # Coverage reporting
]
```

## Success Metrics

| Metric | Current | Target | Method |
|--------|---------|--------|--------|
| Max cyclomatic complexity | 27 | ≤15 | `radon cc -nc` |
| Avg cyclomatic complexity | ~5.2 | ≤4 | `radon cc -a` |
| Min maintainability index | 8.46 | ≥40 | `radon mi` |
| Test coverage | 0% | ≥70% | `pytest --cov` |
| D/F grade methods | 3 | 0 | `radon cc -nc` |

## SOLID Principles Checklist

After refactoring, verify:

- [ ] **S**ingle Responsibility: Each class has one reason to change
- [ ] **O**pen/Closed: New commands/layouts don't modify existing code
- [ ] **L**iskov Substitution: Layout managers are interchangeable
- [ ] **I**nterface Segregation: Protocols define minimal required methods
- [ ] **D**ependency Inversion: Core depends on abstractions, not concretions

## References

- [Radon Documentation](https://radon.readthedocs.io/)
- [Python SOLID Principles](https://realpython.com/solid-principles-python/)
- [Refactoring.Guru - Command Pattern](https://refactoring.guru/design-patterns/command/python/example)
- [Martin Fowler - Refactoring](https://refactoring.com/)
- [Cognitive Complexity vs Cyclomatic Complexity](https://www.sonarsource.com/docs/CognitiveComplexity.pdf)
