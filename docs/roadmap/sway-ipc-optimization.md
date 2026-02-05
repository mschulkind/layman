# Roadmap: Sway IPC Communication Optimization

**Status:** 📋 Planned  
**Priority:** Medium  
**Complexity:** High

This document explores options for optimizing how layman communicates with Sway/i3 via IPC, including more efficient window movement operations and event handling strategies.

## Current Implementation Analysis

### How Layman Currently Uses IPC

Layman uses the `i3ipc-python` library (v2.2.1) to communicate with Sway. The current architecture involves:

1. **Two Socket Connections**:
   - **Command Socket (`_cmd_socket`)**: For sending commands and queries
   - **Subscription Socket (`_sub_socket`)**: For receiving events

2. **Event Listener Thread** ([listener.py](../../src/layman/listener.py)):
   ```python
   self.connection.on(Event.WINDOW_FOCUS, self.handleEvent)
   self.connection.on(Event.WINDOW_NEW, self.handleEvent)
   # ... subscribes to multiple event types
   ```

3. **Event Processing Loop** ([layman.py](../../src/layman/layman.py#L572)):
   - Events are queued from the listener thread
   - Main loop processes events sequentially
   - For each window event, calls `get_tree()` to find window context

4. **Window Commands**: Layout managers use `self.con.command()` to execute Sway commands:
   ```python
   self.command(f'[con_id={window.id}] move left')
   ```

### Current Performance Bottlenecks

| Issue | Impact | Location |
|-------|--------|----------|
| `get_tree()` called for every window event | High latency, O(n) tree traversal | [layman.py#L618](../../src/layman/layman.py#L618) |
| Sequential command execution | Multiple round-trips for layout changes | Layout managers |
| Full tree deserialization | Memory churn, CPU overhead | i3ipc library |
| No event debouncing | Redundant processing during rapid changes | Event loop |
| Blocking socket I/O | Event listener can block | i3ipc Connection |

## Sway IPC Protocol Deep Dive

### Protocol Overview

Sway implements the i3 IPC protocol over a Unix socket. The protocol format is:

```
┌─────────────┬─────────────┬──────────────┬─────────────┐
│ "i3-ipc"    │ payload_len │ message_type │ payload     │
│ (6 bytes)   │ (4 bytes)   │ (4 bytes)    │ (variable)  │
└─────────────┴─────────────┴──────────────┴─────────────┘
```

### Available Message Types

| Type | Name | Description |
|------|------|-------------|
| 0 | `RUN_COMMAND` | Execute sway commands |
| 1 | `GET_WORKSPACES` | List workspaces |
| 2 | `SUBSCRIBE` | Subscribe to events |
| 3 | `GET_OUTPUTS` | List outputs |
| 4 | `GET_TREE` | **Full container tree** (expensive!) |
| 5 | `GET_MARKS` | List marks |
| 6 | `GET_BAR_CONFIG` | Bar configuration |
| 7 | `GET_VERSION` | Sway version |
| 10 | `SEND_TICK` | Send tick event |
| 11 | `SYNC` | Not implemented in Sway |
| 100 | `GET_INPUTS` | List input devices (Sway-only) |
| 101 | `GET_SEATS` | List seats (Sway-only) |

### Event Types

| Type | Name | Useful Data |
|------|------|-------------|
| `0x80000000` | workspace | workspace changes, includes `current` container |
| `0x80000003` | window | window changes, includes `container` object |
| `0x80000005` | binding | keybind executed |

### Key Insight: Window Events Already Include Container Data

The window event payload includes a `container` object with the window's full state:

```json
{
  "change": "new",
  "container": {
    "id": 12,
    "name": "urxvt",
    "type": "con",
    "app_id": "urxvt",
    "pid": 19787,
    "rect": { "x": 0, "y": 23, "width": 960, "height": 1057 },
    "focused": true,
    ...
  }
}
```

**However**, this container does **not** include parent information (workspace, output), which is why layman currently calls `get_tree()`.

## Optimization Strategies

### Strategy 1: Command Batching (High Impact, Medium Effort)

**Problem**: Each layout change triggers multiple IPC commands executed sequentially.

**Solution**: Sway supports semicolon-separated command batching:

```python
# Current (4 round-trips):
conn.command('[con_id=1] move left')
conn.command('[con_id=2] move right')
conn.command('[con_id=3] focus')
conn.command('resize set 50ppt')

# Optimized (1 round-trip):
conn.command('[con_id=1] move left; [con_id=2] move right; [con_id=3] focus; resize set 50ppt')
```

**Implementation**:
```python
class CommandBatcher:
    def __init__(self, connection: Connection):
        self._conn = connection
        self._commands: list[str] = []
    
    def add(self, cmd: str) -> None:
        self._commands.append(cmd)
    
    def execute(self) -> list[CommandReply]:
        if not self._commands:
            return []
        batch = '; '.join(self._commands)
        self._commands.clear()
        return self._conn.command(batch)

# Usage in layout managers:
with command_batcher(self.con) as batch:
    batch.add(f'[con_id={w1.id}] move left')
    batch.add(f'[con_id={w2.id}] move right')
# Single IPC call on context exit
```

**Expected Improvement**: 50-75% reduction in IPC calls during layout operations.

### Strategy 2: Workspace State Caching (High Impact, High Effort)

**Problem**: `get_tree()` is called for every window event to find the workspace.

**Current Flow**:
```
Event → get_tree() → find_by_id() → workspace() → process
```

**Optimized Flow**:
```
Event → check cache → process
         ↓ (cache miss)
       get_tree() → update cache
```

**Implementation**:
```python
class TreeCache:
    def __init__(self, connection: Connection):
        self._conn = connection
        self._window_to_workspace: dict[int, str] = {}
        self._workspace_windows: dict[str, set[int]] = {}
        self._last_tree: Con | None = None
        self._dirty = True
    
    def get_workspace_for_window(self, window_id: int) -> str | None:
        """O(1) lookup instead of O(n) tree traversal."""
        return self._window_to_workspace.get(window_id)
    
    def invalidate(self) -> None:
        """Mark cache as stale."""
        self._dirty = True
    
    def refresh(self) -> Con:
        """Fetch fresh tree and rebuild cache."""
        self._last_tree = self._conn.get_tree()
        self._rebuild_mappings()
        self._dirty = False
        return self._last_tree
    
    def _rebuild_mappings(self) -> None:
        self._window_to_workspace.clear()
        self._workspace_windows.clear()
        for workspace in self._last_tree.workspaces():
            ws_name = workspace.name
            self._workspace_windows[ws_name] = set()
            for window in workspace.leaves():
                self._window_to_workspace[window.id] = ws_name
                self._workspace_windows[ws_name].add(window.id)
```

**Cache Invalidation Rules**:
- `window::new` → Add window to cache, mark workspace dirty
- `window::close` → Remove window from cache
- `window::move` → Update window's workspace mapping
- `workspace::init` → Add workspace to cache

**Expected Improvement**: 80-90% reduction in `get_tree()` calls.

### Strategy 3: Async Event Processing with i3ipc.aio (Medium Impact, Medium Effort)

**Problem**: Current event loop uses blocking I/O.

**Solution**: Use `i3ipc.aio.Connection` for true async:

```python
from i3ipc.aio import Connection
import asyncio

async def main():
    conn = await Connection().connect()
    
    async def on_window(i3, event):
        # Non-blocking event handler
        workspace = await find_workspace_async(event.container.id)
        await process_event(event, workspace)
    
    conn.on('window', on_window)
    await conn.main()

asyncio.run(main())
```

**Benefits**:
- Event handlers can await I/O without blocking
- Multiple events can be processed concurrently
- Better integration with async frameworks

**Challenges**:
- Requires significant refactoring of event loop
- Layout manager callbacks need async conversion
- Thread safety considerations change

### Strategy 4: Event Debouncing/Coalescing (Medium Impact, Low Effort)

**Problem**: Rapid window operations trigger many events:
```
move left → window::move event
split h   → no event
move up   → window::move event
focus     → window::focus event
```

**Solution**: Collect events for a short window, then process:

```python
class EventCoalescer:
    def __init__(self, delay_ms: float = 10):
        self._delay = delay_ms / 1000
        self._pending: dict[int, WindowEvent] = {}
        self._timer: Timer | None = None
    
    def add(self, event: WindowEvent) -> None:
        window_id = event.container.id
        # Later events for same window supersede earlier ones
        self._pending[window_id] = event
        self._schedule_flush()
    
    def _schedule_flush(self) -> None:
        if self._timer:
            self._timer.cancel()
        self._timer = Timer(self._delay, self._flush)
        self._timer.start()
    
    def _flush(self) -> None:
        events = list(self._pending.values())
        self._pending.clear()
        for event in events:
            self._process(event)
```

**Expected Improvement**: 20-40% reduction in redundant event processing.

### Strategy 5: Marks for Tracking (Low Impact, Low Effort)

**Problem**: Need to find windows by ID across tree queries.

**Solution**: Use Sway marks to tag managed windows:

```python
# Tag window with unique mark
conn.command(f'[con_id={window.id}] mark --add layman_{workspace_name}_{window.id}')

# Later, find directly by mark (no tree traversal needed)
conn.command(f'[con_mark="layman_{workspace_name}_{window.id}"] focus')
```

**Caveat**: Limited benefit as marks still require tree query to resolve to container object.

### Strategy 6: Direct Wayland Protocols (Experimental, High Effort)

**Context**: Sway implements various Wayland protocols that could provide more direct access:

| Protocol | Purpose | Status |
|----------|---------|--------|
| `wlr-foreign-toplevel-management-v1` | List and control toplevels | wlroots-specific |
| `ext-foreign-toplevel-list-v1` | Standard toplevel list | Newer, less support |
| `wlr-layer-shell` | Layer surfaces | For bars/overlays |

**Assessment**: These protocols are primarily for external tools (taskbars, docks). The i3 IPC remains the proper interface for window management operations. The i3 IPC is well-optimized and using Wayland protocols would require:
- Writing Python Wayland bindings or using `pywayland`
- Significant complexity for marginal gains
- Breaking i3 compatibility

**Recommendation**: Not recommended for layman.

## Comparison: Python Libraries for Sway IPC

| Library | Language | Async | Typing | Maintained | Notes |
|---------|----------|-------|--------|------------|-------|
| [i3ipc-python](https://github.com/altdesktop/i3ipc-python) | Python | ✅ (i3ipc.aio) | ✅ | ✅ Active | Current choice, well-maintained |
| [i3ipc](https://crates.io/crates/i3ipc) (Rust) | Rust | ✅ | ✅ | ⚠️ Limited | Would require PyO3 bindings |
| [swayipc](https://crates.io/crates/swayipc) (Rust) | Rust | ✅ | ✅ | ✅ Active | Sway-specific, no Python bindings |
| Direct socket | Python | Manual | Manual | N/A | Maximum control, most work |

**Recommendation**: Continue with `i3ipc-python`, leveraging its async module.

## Implementation Plan

### Phase 1: Quick Wins (1-2 days)

- [ ] **Command Batching**: Implement `CommandBatcher` context manager
- [ ] **Batch Layout Operations**: Update `MasterStackLayoutManager` to batch moves
- [ ] **Benchmark**: Measure IPC call reduction

### Phase 2: Caching Layer (3-5 days)

- [ ] **TreeCache Class**: Implement window-to-workspace mapping cache
- [ ] **Cache Integration**: Replace `get_tree()` calls with cache lookups
- [ ] **Invalidation Logic**: Handle edge cases (workspace rename, etc.)
- [ ] **Fallback**: Graceful degradation on cache miss

### Phase 3: Event Optimization (2-3 days)

- [ ] **Event Coalescer**: Debounce rapid events
- [ ] **Priority Queue**: Process focus events before move events
- [ ] **Configurable Delay**: Allow tuning via config

### Phase 4: Async Migration (1-2 weeks)

- [ ] **Async Event Loop**: Migrate to `i3ipc.aio.Connection`
- [ ] **Async Layout Managers**: Convert callback signatures
- [ ] **Concurrent Processing**: Enable parallel event handling where safe

### Phase 5: Advanced (Future)

- [ ] **Partial Tree Queries**: Explore if Sway could support workspace-only tree
- [ ] **Upstream Contributions**: Propose efficiency improvements to i3ipc-python

## Metrics & Success Criteria

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| IPC calls per window move | 3-5 | 1-2 | Log analysis |
| `get_tree()` calls per minute | ~60 | ~10 | Instrumentation |
| Event processing latency | ~15ms | ~5ms | Timing logs |
| CPU usage (idle) | ~1% | ~0.5% | `top`/`htop` |

## Configuration Options

New config options to control IPC behavior:

```toml
[performance]
# Enable command batching
batch_commands = true

# Event coalescing delay in milliseconds (0 to disable)
event_debounce_ms = 10

# Tree cache TTL in seconds (0 to disable caching)
tree_cache_ttl = 5

# Use async event processing
async_events = false  # Experimental
```

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Cache staleness | Medium | High | Conservative invalidation, fallback to get_tree() |
| Event ordering bugs | Medium | Medium | Careful coalescing logic, preserve order within window |
| Async complexity | Medium | Medium | Incremental migration, feature flag |
| i3 compatibility | Low | Medium | Test with both i3 and Sway |

## References

- [Sway IPC Protocol Documentation](https://man.archlinux.org/man/sway-ipc.7.en)
- [i3 IPC Documentation](https://i3wm.org/docs/ipc.html)
- [i3ipc-python Documentation](https://i3ipc-python.readthedocs.io/en/latest/)
- [i3ipc-python GitHub](https://github.com/altdesktop/i3ipc-python)
- [wlr-foreign-toplevel-management Protocol](https://wayland.app/protocols/wlr-foreign-toplevel-management-unstable-v1)

## Related Documents

- [Code Simplification](code-simplification.md) - Refactoring patterns
- [Type Safety](type-safety.md) - Type annotation plans
- [Improvements](improvements.md) - General codebase improvements
