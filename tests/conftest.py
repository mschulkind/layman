"""
Shared pytest fixtures for layman tests.

This module provides reusable fixtures for:
- Configuration objects
- Mock i3ipc connections and containers
- Workspace tree structures
- Layout manager instances
"""

import os
from pathlib import Path

import pytest

from layman.config import LaymanConfig

from .mocks.i3ipc_mocks import (
    MockCon,
    MockConnection,
    MockRect,
    MockWindowEvent,
    MockBindingEvent,
    MockWorkspaceEvent,
    create_workspace,
    create_tree_with_workspaces,
)


# =============================================================================
# Path Fixtures
# =============================================================================


@pytest.fixture
def fixtures_path() -> Path:
    """Path to the test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def configs_path(fixtures_path) -> Path:
    """Path to the config fixtures directory."""
    return fixtures_path / "configs"


# =============================================================================
# Configuration Fixtures
# =============================================================================


@pytest.fixture
def minimal_config(configs_path) -> LaymanConfig:
    """Config with just defaults."""
    return LaymanConfig(str(configs_path / "minimal_config.toml"))


@pytest.fixture
def masterstack_config(configs_path) -> LaymanConfig:
    """Config for MasterStack testing."""
    return LaymanConfig(str(configs_path / "masterstack_config.toml"))


@pytest.fixture
def valid_config(configs_path) -> LaymanConfig:
    """Complete valid configuration."""
    return LaymanConfig(str(configs_path / "valid_config.toml"))


@pytest.fixture
def temp_config(tmp_path) -> callable:
    """Factory fixture for creating temporary config files."""

    def _create_config(content: str) -> LaymanConfig:
        config_path = tmp_path / "config.toml"
        config_path.write_text(content)
        return LaymanConfig(str(config_path))

    return _create_config


# =============================================================================
# Mock Connection Fixtures
# =============================================================================


@pytest.fixture
def mock_connection() -> MockConnection:
    """Basic mock connection with empty tree."""
    return MockConnection()


@pytest.fixture
def mock_connection_with_tree(single_window_workspace) -> MockConnection:
    """Mock connection with a single window workspace."""
    root = MockCon(
        type="root",
        nodes=[
            MockCon(
                type="output",
                name="output",
                nodes=[single_window_workspace],
            )
        ],
    )
    return MockConnection(tree=root)


# =============================================================================
# Workspace Fixtures
# =============================================================================


@pytest.fixture
def empty_workspace() -> MockCon:
    """Workspace with no windows."""
    return create_workspace(name="1", window_count=0)


@pytest.fixture
def single_window_workspace() -> MockCon:
    """Workspace with one window."""
    return create_workspace(name="1", window_count=1)


@pytest.fixture
def two_window_workspace() -> MockCon:
    """Workspace with two windows (master + one stack)."""
    return create_workspace(name="1", window_count=2)


@pytest.fixture
def multi_window_workspace() -> MockCon:
    """Workspace with 4 windows (master + 3 stack)."""
    return create_workspace(name="1", window_count=4)


@pytest.fixture
def floating_workspace() -> MockCon:
    """Workspace with tiled and floating windows."""
    return create_workspace(name="1", window_count=2, floating_count=1)


@pytest.fixture
def named_workspace() -> MockCon:
    """Workspace with a string name."""
    return create_workspace(name="coding", window_count=2)


# =============================================================================
# Window Fixtures
# =============================================================================


@pytest.fixture
def mock_window() -> MockCon:
    """A basic mock window container."""
    return MockCon(
        id=100,
        name="Test Window",
        type="con",
        rect=MockRect(width=800, height=600),
    )


@pytest.fixture
def floating_window() -> MockCon:
    """A floating window container."""
    return MockCon(
        id=200,
        name="Floating Window",
        type="floating_con",
        floating="auto_on",
        rect=MockRect(width=400, height=300),
    )


@pytest.fixture
def fullscreen_window() -> MockCon:
    """A fullscreen window container."""
    return MockCon(
        id=300,
        name="Fullscreen Window",
        type="con",
        fullscreen_mode=1,
        rect=MockRect(width=1920, height=1080),
    )


@pytest.fixture
def wide_window() -> MockCon:
    """A window wider than it is tall."""
    return MockCon(
        id=400,
        name="Wide Window",
        type="con",
        rect=MockRect(width=1600, height=400),
    )


@pytest.fixture
def tall_window() -> MockCon:
    """A window taller than it is wide."""
    return MockCon(
        id=500,
        name="Tall Window",
        type="con",
        rect=MockRect(width=400, height=1200),
    )


# =============================================================================
# Event Fixtures
# =============================================================================


@pytest.fixture
def window_new_event(mock_window) -> MockWindowEvent:
    """Window 'new' event."""
    return MockWindowEvent(change="new", container=mock_window)


@pytest.fixture
def window_close_event(mock_window) -> MockWindowEvent:
    """Window 'close' event."""
    return MockWindowEvent(change="close", container=mock_window)


@pytest.fixture
def window_focus_event(mock_window) -> MockWindowEvent:
    """Window 'focus' event."""
    mock_window.focused = True
    return MockWindowEvent(change="focus", container=mock_window)


@pytest.fixture
def window_move_event(mock_window) -> MockWindowEvent:
    """Window 'move' event."""
    return MockWindowEvent(change="move", container=mock_window)


@pytest.fixture
def window_floating_event(floating_window) -> MockWindowEvent:
    """Window 'floating' event."""
    return MockWindowEvent(change="floating", container=floating_window)


@pytest.fixture
def binding_event() -> callable:
    """Factory for binding events."""

    def _create_event(command: str) -> MockBindingEvent:
        return MockBindingEvent(command=command)

    return _create_event


@pytest.fixture
def workspace_init_event(empty_workspace) -> MockWorkspaceEvent:
    """Workspace 'init' event."""
    return MockWorkspaceEvent(change="init", current=empty_workspace)


# =============================================================================
# Tree Structure Fixtures
# =============================================================================


@pytest.fixture
def simple_tree() -> MockCon:
    """Simple tree with one workspace and two windows."""
    return create_tree_with_workspaces(
        [
            {"name": "1", "window_count": 2},
        ]
    )


@pytest.fixture
def multi_workspace_tree() -> MockCon:
    """Tree with multiple workspaces."""
    return create_tree_with_workspaces(
        [
            {"name": "1", "window_count": 3},
            {"name": "2", "window_count": 2},
            {"name": "3", "window_count": 1},
        ]
    )


@pytest.fixture
def complex_tree() -> MockCon:
    """Complex tree with workspaces, floating windows, etc."""
    return create_tree_with_workspaces(
        [
            {"name": "1", "window_count": 4, "floating_count": 1},
            {"name": "2", "window_count": 2, "floating_count": 2},
            {"name": "coding", "window_count": 3},
        ]
    )


# =============================================================================
# Utility Fixtures
# =============================================================================


@pytest.fixture
def window_id_counter():
    """Counter for generating unique window IDs."""

    class Counter:
        def __init__(self, start=1000):
            self.value = start

        def next(self):
            self.value += 1
            return self.value

    return Counter()
