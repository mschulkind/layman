"""
Integration tests for layman event handling.

These tests verify that the complete event flow works correctly,
from i3ipc events through to layout manager actions.

HEADLESS SWAY SETUP:
To run integration tests with a real Sway instance, set:
    WLR_BACKENDS=headless
    WLR_LIBINPUT_NO_DEVICES=1
    WAYLAND_DISPLAY=wayland-test

Then start sway:
    sway -c /dev/null &

These tests will be skipped if Sway is not available.

Run with: just test-integration
"""

import os
import pytest
import subprocess
import time
from unittest.mock import Mock, patch, MagicMock


# Check if we can run integration tests
def check_sway_available():
    """Check if Sway is running and accessible."""
    try:
        result = subprocess.run(
            ["swaymsg", "-t", "get_version"],
            capture_output=True,
            timeout=2,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


SWAY_AVAILABLE = check_sway_available()

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


class TestHeadlessSwayIntegration:
    """Integration tests requiring headless Sway."""

    @pytest.fixture
    def sway_connection(self):
        """Create a real i3ipc connection if available."""
        if not SWAY_AVAILABLE:
            pytest.skip("Sway not available. Set WLR_BACKENDS=headless")

        import i3ipc
        try:
            con = i3ipc.Connection()
            yield con
        except Exception as e:
            pytest.skip(f"Could not connect to Sway: {e}")

    @pytest.mark.skipif(not SWAY_AVAILABLE, reason="Sway not available")
    def test_get_tree(self, sway_connection):
        """Should be able to get the window tree."""
        tree = sway_connection.get_tree()
        assert tree is not None
        assert tree.type in ["root", "output"]

    @pytest.mark.skipif(not SWAY_AVAILABLE, reason="Sway not available")
    def test_get_workspaces(self, sway_connection):
        """Should be able to get workspace list."""
        workspaces = sway_connection.get_workspaces()
        assert isinstance(workspaces, list)

    @pytest.mark.skipif(not SWAY_AVAILABLE, reason="Sway not available")
    def test_get_outputs(self, sway_connection):
        """Should be able to get output list."""
        outputs = sway_connection.get_outputs()
        assert isinstance(outputs, list)

    @pytest.mark.skipif(not SWAY_AVAILABLE, reason="Sway not available")
    def test_execute_command(self, sway_connection):
        """Should be able to execute Sway commands."""
        result = sway_connection.command("nop test")
        assert isinstance(result, list)


class TestMockedEventHandling:
    """Tests for event handling using mocks (no real Sway needed)."""

    def test_binding_event_parsing(self):
        """Test that binding events are parsed correctly."""
        from tests.mocks.i3ipc_mocks import MockBindingEvent

        event = MockBindingEvent(command="nop layman layout maximize")

        assert event.binding.command == "nop layman layout maximize"
        assert event.binding.command.startswith("nop layman")

    def test_window_event_parsing(self):
        """Test that window events are parsed correctly."""
        from tests.mocks.i3ipc_mocks import MockWindowEvent, MockCon

        container = MockCon(id=100, type="con", name="Test Window")
        event = MockWindowEvent(change="new", container=container)

        assert event.change == "new"
        assert event.container.id == 100

    def test_event_queue_flow(self):
        """Test that events flow through the queue correctly."""
        from queue import SimpleQueue

        queue = SimpleQueue()

        # Simulate event being added
        event = {"type": "event", "event": Mock(change="focus")}
        queue.put(event)

        # Verify retrieval
        retrieved = queue.get_nowait()
        assert retrieved["type"] == "event"
        assert retrieved["event"].change == "focus"

    def test_command_queue_flow(self):
        """Test that commands flow through the queue correctly."""
        from queue import SimpleQueue

        queue = SimpleQueue()

        # Simulate command being added
        command = {"type": "command", "command": "layout MasterStack"}
        queue.put(command)

        # Verify retrieval
        retrieved = queue.get_nowait()
        assert retrieved["type"] == "command"
        assert retrieved["command"] == "layout MasterStack"


class TestLayoutManagerEventIntegration:
    """Tests for layout manager event integration."""

    def test_window_added_triggers_layout(self, mock_connection, minimal_config):
        """Adding a window should trigger layout operations."""
        from layman.managers.master_stack import MasterStackLayoutManager
        from tests.mocks.i3ipc_mocks import MockCon, MockWindowEvent

        workspace = MockCon(name="1", type="workspace")
        manager = MasterStackLayoutManager(mock_connection, workspace, "1", minimal_config)

        # Add first window
        window1 = MockCon(id=100, type="con")
        event1 = MockWindowEvent(change="new", container=window1)
        manager.windowAdded(event1, workspace, window1)

        assert 100 in manager.windowIds

        # Add second window
        window2 = MockCon(id=200, type="con")
        event2 = MockWindowEvent(change="new", container=window2)
        manager.windowAdded(event2, workspace, window2)

        assert len(manager.windowIds) == 2
        # Commands should have been executed for layout
        assert len(mock_connection.commands_executed) > 0

    def test_window_removed_triggers_layout(self, mock_connection, minimal_config):
        """Removing a window should trigger layout operations."""
        from layman.managers.master_stack import MasterStackLayoutManager
        from tests.mocks.i3ipc_mocks import MockCon, MockWindowEvent, MockRect

        workspace = MockCon(name="1", type="workspace")
        manager = MasterStackLayoutManager(mock_connection, workspace, "1", minimal_config)
        manager.windowIds = [100, 200, 300]

        # Remove a stack window
        window = MockCon(id=200, type="con", rect=MockRect(width=400))
        event = MockWindowEvent(change="close", container=window)
        manager.windowRemoved(event, workspace, window)

        assert 200 not in manager.windowIds
        assert len(manager.windowIds) == 2

    def test_focus_changes_trigger_tracking(self, mock_connection, minimal_config):
        """Focus changes should be tracked."""
        from layman.managers.master_stack import MasterStackLayoutManager
        from tests.mocks.i3ipc_mocks import MockCon, MockWindowEvent

        workspace = MockCon(name="1", type="workspace")
        manager = MasterStackLayoutManager(mock_connection, workspace, "1", minimal_config)
        manager.windowIds = [100, 200, 300]

        window = MockCon(id=200, type="con")
        event = MockWindowEvent(change="focus", container=window)
        manager.windowFocused(event, workspace, window)

        assert manager.lastFocusedWindowId == 200


class TestLaymanIntegration:
    """Integration tests for full layman functionality."""

    @pytest.mark.skip(reason="Requires running Sway/i3")
    def test_layman_starts_without_crash(self):
        """Layman daemon should start without errors."""
        pass

    @pytest.mark.skip(reason="Requires running Sway/i3")
    def test_masterstack_layout_applies(self):
        """MasterStack layout should correctly arrange windows."""
        pass

    @pytest.mark.skip(reason="Requires running Sway/i3")
    def test_autotiling_layout_applies(self):
        """Autotiling layout should correctly alternate splits."""
        pass

    @pytest.mark.skip(reason="Requires running Sway/i3")
    def test_command_handling(self):
        """Commands via named pipe should be processed."""
        pass

    @pytest.mark.skip(reason="Requires running Sway/i3")
    def test_config_reload(self):
        """Config reload should apply new settings."""
        pass
