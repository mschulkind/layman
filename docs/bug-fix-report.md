# Bug Fix Report

This document describes bugs discovered during the test suite implementation phase and their resolutions.

## Bugs Discovered During Testing

### 1. WorkspaceState.windowIds Type Assumption

**Location**: `layman/layman.py` - `WorkspaceState` dataclass

**Issue**: The initial test assumptions treated `windowIds` as a `list`, but the actual implementation uses a `set`.

**Impact**: Tests were failing due to incorrect assertions (e.g., `assert 100 in state.windowIds` works for both, but operations like `append()` vs `add()` differ).

**Resolution**: Updated all test fixtures and mocks to use `set` semantics:
```python
# Before
windowIds: list[int] = field(default_factory=list)

# Actual (correct)
windowIds: set[int] = field(default_factory=set)
```

**Lesson**: Always verify data structure types from source before writing tests.

---

### 2. MockConnection.find_by_id Not Traversing Tree

**Location**: `tests/mocks/i3ipc_mocks.py` - `MockCon.find_by_id()`

**Issue**: The mock's `find_by_id()` method only searched direct children, not recursively through the tree. This caused tests to fail when managers tried to find windows in nested structures.

**Impact**: Tests for `rotateWindows()`, `focusWindowRelative()`, and other methods that look up windows by ID were failing with `AssertionError` when the window wasn't in immediate children.

**Resolution**: Implemented proper recursive traversal and added `mock_connection.tree` field for setting a searchable tree:
```python
def find_by_id(self, id):
    if self.id == id:
        return self
    for node in self.nodes:
        result = node.find_by_id(id)
        if result:
            return result
    for node in self.floating_nodes:
        result = node.find_by_id(id)
        if result:
            return result
    return None
```

---

### 3. Grid Layout's `leaves()` Method Not Mocked

**Location**: `layman/managers/grid.py` - `windowAdded()` method

**Issue**: The Grid layout manager calls `workspace.leaves()` to find all leaf windows. Tests were failing because `MockCon` didn't implement this method properly.

**Impact**: Grid layout tests for `windowAdded` couldn't find the largest container to split.

**Resolution**: Added `leaves()` method to `MockCon` and allowed tests to override it:
```python
def leaves(self):
    result = []
    if not self.nodes:
        return [self]
    for node in self.nodes:
        result.extend(node.leaves())
    return result
```

---

### 4. Autotiling Depth Limit Counting Logic

**Location**: `layman/managers/autotiling.py` - `switchSplit()` method

**Issue**: Test assumptions about depth counting were incorrect. The autotiling manager only counts depth for containers with more than 1 child (`len(windowParent.nodes) > 1`).

**Impact**: Tests expecting split commands weren't seeing them because the depth limit was being triggered unexpectedly.

**Resolution**: Tests updated to properly set up container structures with multiple children:
```python
# Ensure containers have 2+ children for depth counting
container1.nodes = [container2, MockCon(id=102)]
```

---

### 5. Master-Stack popWindow Resize Behavior

**Location**: `layman/managers/master_stack.py` - `popWindow()` method

**Issue**: Initial tests expected resize commands when removing the last stack window, but the actual implementation only resizes when removing the **master** (first) window.

**Impact**: Tests were failing with empty command lists when they expected resize commands.

**Resolution**: Updated test expectations to match actual behavior - resize only happens when sourceIndex == 0 (master removal):
```python
# Resize happens when master is removed, not stack windows
if sourceIndex == 0 and len(self.windowIds) >= 2:
    # Master was removed, resize new master
```

---

### 6. Command Names in onCommand Handler

**Location**: `layman/managers/master_stack.py` - `onCommand()` method

**Issue**: Tests used incorrect command names like `"focus next"` and `"focus prev"` when the actual commands are `"focus up"` and `"focus down"`.

**Impact**: Tests were not triggering the expected code paths.

**Resolution**: Corrected command names in tests:
```python
# Before
manager.onCommand("focus next", workspace)

# After (correct)
manager.onCommand("focus down", workspace)
```

---

## Potential Bugs Identified (Not Fixed)

These are issues discovered during testing that may indicate bugs in the actual codebase:

### 1. Width Zero Edge Case

**Location**: `master_stack.py:393-394`

**Issue**: There's a check for `window.rect.width == 0` with a log message "window with width 0 popped. likely a bug." This suggests a known edge case that occurs in practice.

**Recommendation**: Investigate when this occurs and add proper handling or prevention.

---

### 2. Missing Window in Toggle Stack Side

**Location**: `master_stack.py:457-458`

**Issue**: The `toggleStackSide()` method logs "Couldn't find the first stack window. Probably a bug." when it can't find windows.

**Recommendation**: Investigate race conditions or state inconsistencies that could cause this.

---

### 3. Floating Window Tracking Inconsistency

**Location**: `master_stack.py:165-166`

**Issue**: When removing a floating window, if it's not in `floatingWindowIds`, an error is logged. This could indicate the window was added without being tracked.

**Recommendation**: Audit all paths where floating windows can be created to ensure consistent tracking.

---

## Testing Improvements Made

1. **Added 226 unit tests** covering all manager modules
2. **Created comprehensive mock library** in `tests/mocks/i3ipc_mocks.py`
3. **Added shared fixtures** in `tests/conftest.py`
4. **Created integration test infrastructure** with headless Sway support
5. **Added GitHub Actions CI workflow** for automated testing

---

## Coverage Achieved

| Module | Coverage |
|--------|----------|
| config.py | 100% |
| utils.py | 100% |
| listener.py | 100% |
| workspace.py | 96% |
| autotiling.py | 93% |
| grid.py | 86% |
| server.py | 83% |
| master_stack.py | 80% |

**Note**: `layman.py` (13%) and `__main__.py` (0%) require integration tests with a running Sway/i3 instance.
