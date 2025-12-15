# Testing

## Current State

Layman currently does not have a formal test suite. This document outlines testing strategies for future implementation.

## Manual Testing

### Basic Functionality

1. Start layman: `uv run layman`
2. Open terminal on workspace 1
3. Set layout: `layman layout MasterStack`
4. Open more windows and verify layout behavior

### Layout Manager Testing

#### Autotiling

- Open windows and verify alternating splits
- Test depth limit with nested containers
- Verify floating windows are excluded

#### MasterStack

- Verify master/stack separation
- Test swap master command
- Test stack layout cycling
- Test stack side toggle
- Test rotation commands
- Verify maximize functionality

#### Grid

- Verify largest window splitting
- Check grid pattern formation

### Event Testing

```bash
# Monitor events (in separate terminal)
swaymsg -t subscribe '["window", "workspace"]' -m

# Trigger events and verify layman response
```

## Unit Testing Strategy

### Mocking i3ipc

```python
from unittest.mock import Mock, MagicMock
import pytest

@pytest.fixture
def mock_connection():
    conn = Mock()
    conn.command = MagicMock(return_value=[Mock(success=True)])
    conn.get_tree = MagicMock(return_value=mock_tree())
    return conn

def test_window_added(mock_connection):
    manager = MasterStackLayoutManager(
        mock_connection,
        mock_workspace(),
        "1",
        mock_config()
    )
    # Test windowAdded behavior
```

### Testing Layout Logic

```python
def test_masterstack_push_window():
    # Test window ordering logic without i3ipc
    manager = MasterStackLayoutManager(...)
    manager.windowIds = [1, 2, 3]

    # Simulate push
    manager.pushWindow(workspace, new_window)

    assert manager.windowIds == [1, 2, 3, 4]
```

## Integration Testing

### Docker/Container Testing

```dockerfile
FROM archlinux:latest
RUN pacman -Syu --noconfirm sway xorg-server-xvfb python-pip
# Setup virtual display for sway
```

### CI Testing

GitHub Actions workflow:

```yaml
name: Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync
      - run: uv run pytest
```

## Future Test Coverage Goals

- [ ] Unit tests for each layout manager
- [ ] Configuration parsing tests
- [ ] Event handling tests
- [ ] Command parsing tests
- [ ] Integration tests with mock sway
