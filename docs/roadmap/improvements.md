# Codebase Improvements

## Code Quality

### Add Type Hints

**Status:** 📋 Planned
**Priority:** Medium

Add comprehensive type hints throughout the codebase.

```python
# Before
def setWorkspaceLayout(self, workspace, workspaceName, layoutName=None):

# After
def setWorkspaceLayout(
    self,
    workspace: Optional[Con],
    workspaceName: str,
    layoutName: Optional[str] = None,
) -> None:
```

### Type Checking with ty

**Status:** 📋 Planned
**Priority:** Medium

Use Astral's `ty` for fast type checking.

```bash
uv add ty --dev
uv run ty check src/
```

Benefits:
- Extremely fast (written in Rust)
- Catches type errors early
- Better IDE integration

### Reduce Code Duplication

**Status:** 📋 Planned

Several layout managers have duplicated helper methods:

- `isExcluded()` - Move to base class
- `moveWindow()` / `moveWindowCommand()` - Standardize naming
- Logging methods are already in base class ✓

---

## Architecture

### Event Batching

**Status:** 📋 Planned

Batch rapid events to reduce processing overhead.

```python
# Instead of processing each event immediately,
# collect events for 10ms then process together
```

### State Persistence Layer

**Status:** 📋 Planned

Abstract state storage for session restore feature.

```python
class StateStore:
    def save(self, key: str, data: dict) -> None: ...
    def load(self, key: str) -> Optional[dict]: ...

class FileStateStore(StateStore): ...
class JsonStateStore(StateStore): ...
```

### Layout Manager Factory

**Status:** 📋 Planned

Clean up layout manager instantiation.

```python
class LayoutManagerFactory:
    @staticmethod
    def create(name: str, con, workspace, workspaceName, options):
        registry = {
            "MasterStack": MasterStackLayoutManager,
            "Autotiling": AutotilingLayoutManager,
            "Grid": GridLayoutManager,
        }
        cls = registry.get(name) or load_user_layout(name)
        return cls(con, workspace, workspaceName, options)
```

---

## Testing

### Unit Test Framework

**Status:** 📋 Planned

Set up pytest with i3ipc mocking.

```python
# tests/test_masterstack.py
import pytest
from unittest.mock import Mock

def test_push_window():
    manager = MasterStackLayoutManager(Mock(), Mock(), "1", Mock())
    # Test logic without actual sway connection
```

### Integration Tests

**Status:** 📋 Planned

Test against real (headless) sway instance.

---

## Documentation

### API Docstrings

**Status:** 📋 Planned

Add Google-style docstrings to all public methods.

```python
def windowAdded(self, event: WindowEvent, workspace: Con, window: Con) -> None:
    """Handle a new window being added to the workspace.

    Args:
        event: The i3ipc window event that triggered this call.
        workspace: The workspace container.
        window: The newly added window container.

    Note:
        This is called for both newly created windows and windows
        moved from other workspaces.
    """
```

### Generate API Docs

**Status:** 📋 Planned

Use mkdocs or sphinx to generate API documentation from docstrings.

---

## Error Handling

### Graceful Degradation

**Status:** 📋 Planned

Better recovery from partial failures.

```python
try:
    layout_manager.windowAdded(event, workspace, window)
except Exception as e:
    logging.exception(e)
    # Don't crash, just skip this event
    self.logError(f"Layout manager error: {e}")
```

### Validation

**Status:** 📋 Planned

Validate configuration more thoroughly at startup.

```python
def validate_config(config: LaymanConfig) -> list[str]:
    errors = []
    if masterWidth := config.getDefault("masterWidth"):
        if not (1 <= masterWidth <= 99):
            errors.append(f"masterWidth must be 1-99, got {masterWidth}")
    return errors
```
