# Future Testing Improvements

This document outlines planned testing improvements for the layman project, organized by priority and category.

## Current State

- **226 unit tests** passing
- **61% overall coverage** (limited by layman.py and __main__.py which require integration tests)
- Individual module coverage: 80-100% for testable modules
- CI workflow with GitHub Actions
- Headless Sway support for integration tests

---

## High Priority Improvements

### 1. Property-Based Testing with Hypothesis

**Why**: Layout managers have complex invariants that example-based tests may miss.

**Implementation**:
```python
from hypothesis import given, strategies as st

@given(st.lists(st.integers(min_value=1, max_value=1000), min_size=1, max_size=20))
def test_windowIds_consistency(window_ids):
    """After any sequence of operations, windowIds should remain consistent."""
    manager = create_manager_with_windows(window_ids)
    
    # Perform random operations
    for wid in window_ids[:len(window_ids)//2]:
        manager.popWindow(MockCon(id=wid))
    
    # Invariant: remaining IDs should match what we expect
    assert len(manager.windowIds) == len(window_ids) - len(window_ids)//2
```

**Properties to test**:
- `rotate cw` followed by `rotate ccw` is identity
- `toggleMaximize` twice returns to original state
- windowIds never contains duplicates
- Sum of window counts across workspaces equals total windows

**Tools**: `hypothesis`, `pytest-hypothesis`

---

### 2. Integration Test Infrastructure

**Why**: The main event loop (layman.py) has only 13% coverage.

**Implementation**:

```python
@pytest.fixture
def headless_sway():
    """Start headless Sway for integration tests."""
    import subprocess
    import os
    
    env = os.environ.copy()
    env.update({
        'WLR_BACKENDS': 'headless',
        'WLR_LIBINPUT_NO_DEVICES': '1',
        'XDG_RUNTIME_DIR': '/tmp/sway-test',
    })
    
    proc = subprocess.Popen(['sway', '-c', '/dev/null'], env=env)
    time.sleep(2)
    
    yield proc
    
    proc.terminate()
    proc.wait()

@pytest.fixture
def layman_daemon(headless_sway, tmp_path):
    """Start layman daemon connected to headless Sway."""
    config_file = tmp_path / "config.toml"
    config_file.write_text("[layman]\nlayout = 'MasterStack'")
    
    # Start layman
    proc = subprocess.Popen(['layman', '-c', str(config_file)])
    yield proc
    proc.terminate()
```

**Test scenarios**:
- Daemon starts and connects to Sway
- Layout changes on workspace init
- Window events trigger layout updates
- Commands via named pipe are processed

---

### 3. CI/CD Enhancements

**Why**: Current CI is basic; need coverage gates and caching.

**Implementation** (`.github/workflows/tests.yml` additions):

```yaml
- name: Cache uv dependencies
  uses: actions/cache@v4
  with:
    path: ~/.cache/uv
    key: uv-${{ runner.os }}-${{ hashFiles('uv.lock') }}

- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v4
  with:
    fail_ci_if_error: true
    minimum_coverage: 60

- name: Coverage gate
  run: |
    coverage report --fail-under=60
```

**Additional CI jobs**:
- Matrix testing: Python 3.11, 3.12, 3.13
- Integration tests with headless Sway
- Type checking with mypy/ty
- Lint checking with ruff

---

## Medium Priority Improvements

### 4. Mock Improvements and Factories

**Why**: Current mocks require manual tree setup; factories would reduce boilerplate.

**Implementation**:

```python
class MockTreeBuilder:
    """Build realistic workspace hierarchies."""
    
    def __init__(self, name="1"):
        self.workspace = MockCon(name=name, type="workspace")
        self._next_id = 100
    
    def add_master_stack(self, n_stack=3):
        """Add master window and n stack windows."""
        master = self._create_window()
        stack_container = MockCon(type="con", layout="splitv")
        
        for _ in range(n_stack):
            stack_container.nodes.append(self._create_window())
        
        self.workspace.nodes = [master, stack_container]
        return self
    
    def add_floating(self, count=1):
        """Add floating windows."""
        for _ in range(count):
            self.workspace.floating_nodes.append(
                self._create_window(floating="auto_on")
            )
        return self
    
    def build(self):
        return self.workspace

# Usage
workspace = MockTreeBuilder("1").add_master_stack(3).add_floating(1).build()
```

---

### 5. Error Handling Tests

**Why**: Many exception paths are untested.

**Test scenarios**:
```python
def test_connection_failure_handled():
    """Daemon should log and retry on connection failure."""
    with patch('i3ipc.Connection', side_effect=ConnectionError):
        # Should not crash, should log error
        
def test_command_failure_recoverable():
    """Failed sway commands should not crash daemon."""
    mock_conn.command_return = [MockCommandReply(success=False, error="Test")]
    manager.pushWindow(workspace, window)
    # Should continue functioning

def test_layoutManagerReloader_catches_exceptions():
    """Context manager should reload on any exception."""
    # Already partially tested, expand coverage
```

---

### 6. Named Pipe Testing

**Why**: MessageServer is only 83% covered.

**Implementation**:
```python
def test_concurrent_commands(temp_pipe):
    """Multiple commands sent simultaneously should all be processed."""
    import threading
    
    def send_command(cmd):
        with open(temp_pipe, 'w') as f:
            f.write(cmd)
    
    threads = [
        threading.Thread(target=send_command, args=(f"command-{i}",))
        for i in range(10)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    # Verify all commands were received

def test_malformed_commands():
    """Invalid commands should be logged, not crash."""
    send_command("")
    send_command("\x00\x00\x00")
    send_command("a" * 1000000)  # Very long
```

---

## Lower Priority Improvements

### 7. Mutation Testing

**Why**: Verify test quality beyond line coverage.

**Tools**: `mutmut` or `cosmic-ray`

```bash
# Run mutation testing
mutmut run --paths-to-mutate=src/layman/managers/

# View results
mutmut results
```

**Target**: Achieve >80% mutation score for layout managers.

---

### 8. Visual Regression Testing

**Why**: Catch layout bugs that command tests miss.

**Implementation**:
```python
@pytest.fixture
def screenshot_manager(headless_sway):
    """Take and compare screenshots."""
    def capture(name):
        subprocess.run(['grim', f'/tmp/layman-test/{name}.png'])
    
    def compare(name, expected):
        # Use PIL or ImageMagick to compare
        pass
    
    return capture, compare

def test_masterstack_visual(screenshot_manager, layman_daemon):
    """Visual test for MasterStack layout."""
    # Create windows
    spawn_windows(3)
    
    # Capture and compare
    screenshot_manager.capture('masterstack-3win')
    screenshot_manager.compare('masterstack-3win', 'expected/masterstack-3win.png')
```

---

### 9. Performance Benchmarks

**Why**: Ensure responsive window management.

```python
import pytest

@pytest.mark.benchmark
def test_event_processing_latency(benchmark, manager):
    """Event processing should be under 5ms."""
    event = MockWindowEvent(change="new", container=MockCon(id=100))
    
    result = benchmark(manager.windowAdded, event, workspace, window)
    
    assert benchmark.stats['mean'] < 0.005  # 5ms

@pytest.mark.benchmark  
def test_rapid_window_creation(benchmark, manager):
    """Handle 100 windows without degradation."""
    def create_100_windows():
        for i in range(100):
            manager.windowAdded(event, workspace, MockCon(id=i))
    
    benchmark(create_100_windows)
```

---

### 10. Snapshot/Golden Testing

**Why**: Catch command sequence regressions.

```python
def test_masterstack_commands_snapshot(snapshot):
    """Command sequence should match expected."""
    manager = create_manager()
    
    # Add 3 windows
    for i in range(3):
        manager.windowAdded(event, workspace, MockCon(id=100+i))
    
    # Compare command sequence to saved snapshot
    snapshot.assert_match(
        '\n'.join(mock_connection.commands_executed),
        'masterstack_3_windows.txt'
    )
```

---

## Testing Roadmap

### Phase 1: Foundation (Weeks 1-2)
- [ ] Implement property-based tests for layout invariants
- [ ] Set up Codecov integration with coverage gates
- [ ] Add CI caching for faster builds

### Phase 2: Integration (Weeks 3-4)
- [ ] Create headless Sway test fixtures
- [ ] Write integration tests for event loop
- [ ] Test named pipe command processing

### Phase 3: Quality (Weeks 5-6)
- [ ] Implement mock factories (MockTreeBuilder)
- [ ] Add error handling tests
- [ ] Run mutation testing, fix weak tests

### Phase 4: Advanced (Ongoing)
- [ ] Performance benchmarks
- [ ] Visual regression testing
- [ ] Compatibility matrix (Sway versions)

---

## Testing Tools Summary

| Tool | Purpose | Priority |
|------|---------|----------|
| hypothesis | Property-based testing | High |
| pytest-cov | Coverage reporting | High |
| codecov | Coverage tracking | High |
| mutmut | Mutation testing | Medium |
| pytest-benchmark | Performance testing | Low |
| grim | Screenshot capture | Low |
| pytest-snapshot | Golden tests | Low |
| pytest-xdist | Parallel testing | Medium |

---

## Metrics Goals

| Metric | Current | Target |
|--------|---------|--------|
| Unit test count | 226 | 350+ |
| Overall coverage | 61% | 80%+ |
| Manager coverage | 80-93% | 90%+ |
| Integration tests | ~10 | 50+ |
| Mutation score | Unknown | 80%+ |
| CI run time | ~1min | <2min |
