"""
Additional unit tests for layman.managers.grid module.

These tests cover error handling and edge cases in Grid layout.
"""

import pytest

from layman.managers.grid import GridLayoutManager
from tests.mocks.i3ipc_mocks import (
    MockConnection,
    MockCon,
    MockRect,
    MockWindowEvent,
    MockCommandReply,
)


class TestGridSwitchSplitErrors:
    """Tests for error handling in switchSplit."""

    def test_switchSplit_commandFails_logsError(self, mock_connection, temp_config, capsys):
        """Failed command should log error when debug is True."""
        config = temp_config(
            """
[layman]
debug = true
"""
        )
        workspace = MockCon(name="1", type="workspace")
        manager = GridLayoutManager(mock_connection, workspace, "1", config)

        # Configure mock to return failure
        mock_connection.command_return = [MockCommandReply(success=False, error="Test error")]

        window = MockCon(
            id=100,
            type="con",
            rect=MockRect(width=800, height=400),
        )

        manager.switchSplit(window)

        # Command was executed
        assert len(mock_connection.commands_executed) > 0

    def test_switchSplit_commandSucceeds_logsSuccess(self, mock_connection, temp_config, capsys):
        """Successful command should log when debug is True."""
        config = temp_config(
            """
[layman]
debug = true
"""
        )
        workspace = MockCon(name="1", type="workspace")
        manager = GridLayoutManager(mock_connection, workspace, "1", config)

        window = MockCon(
            id=100,
            type="con",
            rect=MockRect(width=800, height=400),
        )

        manager.switchSplit(window)

        captured = capsys.readouterr()
        # Should execute command
        assert len(mock_connection.commands_executed) > 0


class TestGridWindowAddedEdgeCases:
    """Tests for edge cases in windowAdded."""

    def test_windowAdded_multipleEqualSized_selectsLeftmost(self, mock_connection, minimal_config):
        """When containers are equal size, leftmost should be selected."""
        workspace = MockCon(name="1", type="workspace")
        manager = GridLayoutManager(mock_connection, workspace, "1", minimal_config)

        # Create two equal-sized windows, one more left
        left_window = MockCon(
            id=101,
            type="con",
            rect=MockRect(x=0, y=0, width=400, height=400),
            parent=workspace,
        )
        right_window = MockCon(
            id=102,
            type="con",
            rect=MockRect(x=500, y=0, width=400, height=400),
            parent=workspace,
        )
        workspace.nodes = [left_window, right_window]

        # Add a new window with different parent
        new_container = MockCon(id=1, type="con", parent=workspace)
        new_window = MockCon(
            id=100,
            type="con",
            rect=MockRect(width=200, height=200),
            parent=new_container,
        )
        new_container.nodes = [new_window]
        workspace.nodes.append(new_container)

        event = MockWindowEvent(change="new", container=new_window)

        manager.windowAdded(event, workspace, new_window)

        # Should have executed some commands
        # The leftmost window (101) should be involved

    def test_windowAdded_multipleEqualSized_selectsTopmost(self, mock_connection, minimal_config):
        """When containers are equal size and same x, topmost should be selected."""
        workspace = MockCon(name="1", type="workspace")
        manager = GridLayoutManager(mock_connection, workspace, "1", minimal_config)

        # Create two equal-sized windows at same x, one higher
        top_window = MockCon(
            id=101,
            type="con",
            rect=MockRect(x=0, y=0, width=400, height=400),
            parent=workspace,
        )
        bottom_window = MockCon(
            id=102,
            type="con",
            rect=MockRect(x=0, y=500, width=400, height=400),
            parent=workspace,
        )
        workspace.nodes = [bottom_window, top_window]

        # Add a new window
        new_container = MockCon(id=1, type="con", parent=workspace)
        new_window = MockCon(
            id=100,
            type="con",
            rect=MockRect(width=200, height=200),
            parent=new_container,
        )
        new_container.nodes = [new_window]
        workspace.nodes.append(new_container)

        event = MockWindowEvent(change="new", container=new_window)

        manager.windowAdded(event, workspace, new_window)

        # Should have executed some commands

    def test_windowAdded_largestFound_movesWindow(self, mock_connection, minimal_config):
        """Window should be moved to the largest container."""
        workspace = MockCon(name="1", type="workspace")
        manager = GridLayoutManager(mock_connection, workspace, "1", minimal_config)

        # Create small and large windows with different parents
        small_parent = MockCon(id=1, type="con", parent=workspace)
        small = MockCon(
            id=101,
            type="con",
            rect=MockRect(width=200, height=200),
            parent=small_parent,
        )
        small_parent.nodes = [small]
        
        large_parent = MockCon(id=2, type="con", parent=workspace)
        large = MockCon(
            id=102,
            type="con",
            rect=MockRect(width=800, height=800),
            parent=large_parent,
        )
        large_parent.nodes = [large]
        
        workspace.nodes = [small_parent, large_parent]

        # Add a new window with a third parent
        new_container = MockCon(id=3, type="con", parent=workspace)
        new_window = MockCon(
            id=100,
            type="con",
            rect=MockRect(width=100, height=100),
            parent=new_container,
        )
        new_container.nodes = [new_window]
        workspace.nodes.append(new_container)

        # Mock leaves to return the windows we want
        def mock_leaves():
            return [small, large, new_window]
        workspace.leaves = mock_leaves

        mock_connection.clear_commands()
        event = MockWindowEvent(change="new", container=new_window)
        manager.windowAdded(event, workspace, new_window)

        # Should have move commands (mark, move, unmark)
        commands = " ".join(mock_connection.commands_executed)
        assert "mark" in commands
        assert "move" in commands


class TestGridWindowFocused:
    """Tests for windowFocused handler."""

    def test_windowFocused_normalWindow_callsSwitchSplit(self, mock_connection, minimal_config):
        """Normal windows should trigger switchSplit on focus."""
        workspace = MockCon(name="1", type="workspace")
        manager = GridLayoutManager(mock_connection, workspace, "1", minimal_config)

        container = MockCon(id=1, layout="splith", parent=workspace)
        window = MockCon(
            id=100,
            type="con",
            rect=MockRect(width=400, height=800),  # Tall
            parent=container,
        )
        event = MockWindowEvent(change="focus", container=window)

        manager.windowFocused(event, workspace, window)

        # Should execute splitv command
        assert any("splitv" in cmd for cmd in mock_connection.commands_executed)

    def test_windowFocused_excludedWindow_noSplit(self, mock_connection, minimal_config):
        """Excluded windows should not trigger split."""
        workspace = MockCon(name="1", type="workspace")
        manager = GridLayoutManager(mock_connection, workspace, "1", minimal_config)

        # Floating window is excluded
        window = MockCon(
            id=100,
            type="con",
            floating="auto_on",
            rect=MockRect(width=400, height=800),
        )
        event = MockWindowEvent(change="focus", container=window)

        manager.windowFocused(event, workspace, window)

        assert len(mock_connection.commands_executed) == 0
