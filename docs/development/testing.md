# Testing Plan for Layman

This document outlines the comprehensive testing strategy for the layman project in preparation for refactoring and feature additions.

## Overview

The layman codebase consists of ~1,500 lines of Python code managing Sway/i3 window layouts. Testing is challenging because:

1. **i3ipc dependency**: Most logic requires i3ipc objects (Con, Connection, Events)
2. **Event-driven architecture**: Code responds to window manager events
3. **Side effects**: Layout changes execute IPC commands
4. **State management**: Complex window tracking across workspaces

Our strategy uses **mock-based unit tests** for logic validation and optional **integration tests** for end-to-end verification.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py                    # Shared fixtures
├── mocks/
│   ├── __init__.py
│   ├── i3ipc_mocks.py            # Mock factories for i3ipc objects
│   └── fixtures.py               # Reusable test fixtures
├── unit/
│   ├── __init__.py
│   ├── test_config.py            # Config parsing tests
│   ├── test_utils.py             # Utility function tests
│   ├── test_layman.py            # Main Layman class tests
│   └── managers/
│       ├── __init__.py
│       ├── test_workspace.py     # Base manager tests
│       ├── test_autotiling.py    # Autotiling layout tests
│       ├── test_grid.py          # Grid layout tests
│       └── test_master_stack.py  # MasterStack tests (largest)
├── integration/
│   ├── __init__.py
│   ├── conftest.py               # Sway/i3 integration fixtures
│   └── test_event_handling.py    # End-to-end event tests
└── fixtures/
    └── configs/
        ├── valid_config.toml
        ├── invalid_config.toml
        ├── minimal_config.toml
        └── masterstack_config.toml
```

## Mock Strategy

### MockCon Class

A flexible mock for `i3ipc.Con` that supports tree structures:

```python
class MockCon:
    def __init__(
        self,
        id: int = 1,
        name: str = "window",
        type: str = "con",
        rect: MockRect = None,
        floating: str | None = None,
        fullscreen_mode: int = 0,
        layout: str = "splith",
        parent: "MockCon" = None,
        nodes: list["MockCon"] = None,
        ...
    ):
        ...
    
    def find_by_id(self, id: int) -> Optional["MockCon"]: ...
    def find_focused(self) -> Optional["MockCon"]: ...
    def workspace(self) -> Optional["MockCon"]: ...
    def leaves(self) -> list["MockCon"]: ...
```

### MockConnection Class

Records commands for verification:

```python
class MockConnection:
    def __init__(self, tree: MockCon = None):
        self.tree = tree
        self.commands_executed = []
    
    def command(self, cmd: str) -> list[MockCommandReply]:
        self.commands_executed.append(cmd)
        return [MockCommandReply(success=True)]
    
    def get_tree(self) -> MockCon:
        return self.tree
```

## Test Coverage Goals

| Module | Target | Priority | Complexity |
|--------|--------|----------|------------|
| config.py | 95%+ | High | Low |
| utils.py | 80%+ | Medium | Low |
| managers/workspace.py | 90%+ | High | Low |
| managers/autotiling.py | 90%+ | High | Medium |
| managers/grid.py | 90%+ | High | Medium |
| managers/master_stack.py | 85%+ | Critical | High |
| layman.py | 70%+ | Medium | High |
| listener.py | 40%+ | Low | Low |
| server.py | 40%+ | Low | Low |

## Test Categories

### 1. Config Tests (`test_config.py`)

Test `LaymanConfig` parsing and fallback logic:

- **parse()**: Valid TOML, invalid TOML, missing file, empty file
- **getDefault()**: Key exists, key missing, type preservation
- **getForWorkspace()**: Workspace override, fallback to default, missing both

### 2. Layout Manager Base Tests (`test_workspace.py`)

Test `WorkspaceLayoutManager` base class:

- Initialization with various options
- `command()` execution and logging
- Default method implementations (no-ops)

### 3. Autotiling Tests (`test_autotiling.py`)

- **isExcluded()**: All exclusion conditions
- **switchSplit()**: Height > width → splitv, width > height → splith
- **depthLimit**: Limiting split depth
- Event handlers call switchSplit appropriately

### 4. Grid Tests (`test_grid.py`)

- **isExcluded()**: Same logic as Autotiling
- **windowAdded**: Finds largest container, splits it
- **switchSplit()**: Correct layout selection

### 5. MasterStack Tests (`test_master_stack.py`)

Most comprehensive test file covering:

#### State Management
- `windowIds` list ordering
- `floatingWindowIds` set tracking
- `getWindowListIndex()` returns correct index or None

#### pushWindow() scenarios
- First window → sole entry
- Second window → creates master-stack structure
- Third+ windows → correct stack position
- `positionAfter` parameter placement
- Substack creation when `depthLimit` exceeded

#### popWindow() scenarios
- Removing master → promotes first stack window
- Removing stack window → updates list
- Width preservation (THE BUG - test expected to fail initially)
- Substack rebalancing on removal

#### Movement Commands
- `moveWindowToIndex()` - all source/target combinations
- `moveWindowRelative()` - wrapping at boundaries
- `moveWindowHorizontally()` - interaction with stackSide and stackLayout
- `rotateWindows()` - clockwise and counter-clockwise

#### onCommand() dispatch
- All 14 commands routed correctly
- Invalid "move to index" handling
- Unknown command behavior

#### Features
- `toggleMaximize()` - save/restore master width
- `toggleStackLayout()` - cycle through layouts
- `toggleStackSide()` - swap sides

### 6. Layman Core Tests (`test_layman.py`)

#### Event Handling
- `windowCreated()`: Adds to windowIds, calls handleWindowAdded
- `windowFocused()`: Validates focus, ignores stale events
- `windowClosed()`: Finds workspace by scanning states
- `windowMoved()`: Same vs different workspace handling
- `windowFloating()`: supportsFloating behavior

#### Command Handling
- `onBinding()`: Parses "nop layman" commands
- `handleCommand()`: Routes to layout manager or sway

#### Initialization
- `initWorkspace()`: Creates state, sets default layout
- `setWorkspaceLayout()`: Builtin vs custom layouts

### 7. Utils Tests (`test_utils.py`)

- `findFocusedWindow()`: Returns focused or None
- `findFocusedWorkspace()`: Chains to window.workspace()
- `getConfigPath()`: CLI argument or default

## Regression Tests for Known Bugs

From `docs/roadmap/bugs.md`, create tests that capture known issues:

### 1. Window Width Not Preserved

```python
@pytest.mark.xfail(reason="Known bug: width not preserved on master removal")
def test_popWindow_masterRemoved_preservesWidth():
    """
    BUG: When master is removed, the new master should have
    the same width as the old master. Currently gets default 50%.
    """
    # Setup: master with custom width
    # Action: remove master
    # Assert: new master has preserved width
```

### 2. Existing Windows Sometimes Missed

```python
def test_arrangeWindows_existingWindows_allCaptured():
    """
    Verify all existing windows are captured when initializing
    a layout manager on a workspace with windows.
    """
```

### 3. Focus Event Race Condition

```python
def test_windowFocused_staleEvent_ignored():
    """
    When focus changes rapidly, stale focus events should be
    ignored to prevent incorrect layout updates.
    """
```

## Running Tests

### Quick Run (Unit Tests Only)

```bash
just test           # Run all unit tests
just test-fast      # Run with fail-fast
just test-verbose   # Run with verbose output
```

### With Coverage

```bash
just test-cov       # Run with coverage report
just test-cov-html  # Generate HTML coverage report
```

### Integration Tests

```bash
just test-integration  # Requires running Sway/i3
```

### Specific Tests

```bash
uv run pytest tests/unit/test_config.py
uv run pytest tests/unit/managers/test_master_stack.py -k "pushWindow"
```

## Fixtures

### Config Fixtures

Located in `tests/fixtures/configs/`:

- `minimal_config.toml`: Just `[layman]` section with defaults
- `masterstack_config.toml`: Full MasterStack configuration
- `invalid_config.toml`: Malformed TOML for error handling tests
- `valid_config.toml`: Complete valid configuration

### Workspace Fixtures

Created programmatically in `conftest.py`:

- `empty_workspace`: No windows
- `single_window_workspace`: One tiled window
- `multi_window_workspace`: Master + 3 stack windows
- `floating_workspace`: Mix of tiled and floating
- `complex_tree`: Nested containers

## Integration Testing (Optional)

For full integration testing with a real window manager:

### Prerequisites

- Xvfb (virtual X server)
- i3 window manager
- x11-apps (for xterm, xclock test windows)

### Setup

```bash
# Install dependencies (Debian/Ubuntu)
sudo apt install xvfb i3 x11-apps

# Run integration tests
just test-integration
```

### How It Works

1. Xvfb starts on an available display
2. i3 launches with a minimal test config
3. Tests create windows using xterm/xclock
4. layman daemon is started
5. Tests verify layout behavior
6. Everything is cleaned up

## Continuous Integration

GitHub Actions workflow:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync
      - run: uv run pytest tests/unit -v --cov
```

## Test Naming Convention

```
test_<method>_<scenario>_<expectedOutcome>
```

Examples:
- `test_pushWindow_firstWindow_addedToList`
- `test_moveWindowToIndex_masterToStack_swapsWindows`
- `test_parse_invalidToml_returnsEmptyDict`

## Adding New Tests

1. Identify the module/class/method to test
2. Create appropriate mock objects
3. Set up the scenario state
4. Invoke the method under test
5. Assert expected outcomes
6. Verify any side effects (commands executed)

Example:

```python
def test_pushWindow_secondWindow_createsMasterStack(
    mock_connection,
    masterstack_config,
    single_window_workspace
):
    # Arrange
    manager = MasterStackLayoutManager(
        mock_connection,
        single_window_workspace,
        "1",
        masterstack_config
    )
    new_window = MockCon(id=200, name="Second")
    
    # Act
    manager.pushWindow(single_window_workspace, new_window)
    
    # Assert
    assert len(manager.windowIds) == 2
    assert manager.windowIds[0] == 100  # Original is master
    assert manager.windowIds[1] == 200  # New is stack
    assert "splith" in mock_connection.commands_executed[0]
```

## Debugging Tests

### Verbose Output

```bash
uv run pytest -vvv -s  # Show all output, no capture
```

### Drop into Debugger

```bash
uv run pytest --pdb --pdb-first  # Drop into pdb on first failure
```

### Run Single Test

```bash
uv run pytest tests/unit/managers/test_master_stack.py::TestPushWindow::test_secondWindow
```
