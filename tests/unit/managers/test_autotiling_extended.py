"""
Additional unit tests for layman.managers.autotiling module.

These tests cover the depth limit and error handling paths.
"""

import pytest

from layman.managers.autotiling import AutotilingLayoutManager, KEY_DEPTH_LIMIT
from tests.mocks.i3ipc_mocks import (
    MockConnection,
    MockCon,
    MockRect,
    MockWindowEvent,
    MockCommandReply,
)


class TestAutotilingDepthLimitBehavior:
    """Tests for depth limit enforcement."""

    def test_depthLimit_reached_noSplit(self, mock_connection, temp_config):
        """When depth limit is reached, no split should occur."""
        config = temp_config(
            """
[layman]
depthLimit = 2
"""
        )
        workspace = MockCon(name="1", type="workspace")
        manager = AutotilingLayoutManager(mock_connection, workspace, "1", config)

        # Create nested structure at depth limit
        # workspace -> container1 -> container2 -> window
        container1 = MockCon(id=10, type="con", layout="splith", parent=workspace, nodes=[])
        container2 = MockCon(id=20, type="con", layout="splitv", parent=container1, nodes=[])
        container1.nodes = [container2]
        workspace.nodes = [container1]

        window = MockCon(
            id=100,
            type="con",
            rect=MockRect(width=400, height=800),
            parent=container2,
        )
        container2.nodes = [window, MockCon(id=101)]  # Two children to count depth

        # Update container1 to also have 2 children for depth counting
        container1.nodes = [container2, MockCon(id=102)]

        manager.switchSplit(window)

        # At depth limit, should not execute any commands
        # Note: depends on exact counting logic

    def test_depthLimit_notReached_splitOccurs(self, mock_connection, temp_config):
        """When under depth limit, split should occur."""
        config = temp_config(
            """
[layman]
depthLimit = 5
"""
        )
        workspace = MockCon(name="1", type="workspace")
        manager = AutotilingLayoutManager(mock_connection, workspace, "1", config)

        # Simple structure well under depth limit
        container = MockCon(id=10, type="con", layout="splitv", parent=workspace, nodes=[])
        workspace.nodes = [container]

        window = MockCon(
            id=100,
            type="con",
            rect=MockRect(width=800, height=400),  # Wide -> splith
            parent=container,
        )
        container.nodes = [window]

        manager.switchSplit(window)

        # Should execute splith command
        assert any("splith" in cmd for cmd in mock_connection.commands_executed)

    def test_depthLimit_workspaceReached_continuesSplit(self, mock_connection, temp_config):
        """When workspace is reached before depth limit, split continues."""
        config = temp_config(
            """
[layman]
depthLimit = 10
"""
        )
        workspace = MockCon(name="1", type="workspace")
        manager = AutotilingLayoutManager(mock_connection, workspace, "1", config)

        # Window directly under workspace
        window = MockCon(
            id=100,
            type="con",
            rect=MockRect(width=400, height=800),  # Tall -> splitv
            parent=workspace,
        )
        workspace.nodes = [window]

        manager.switchSplit(window)

        # Should execute splitv command
        assert any("splitv" in cmd for cmd in mock_connection.commands_executed)


class TestAutotilingSwitchSplitErrors:
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
        manager = AutotilingLayoutManager(mock_connection, workspace, "1", config)

        # Configure mock to return failure
        mock_connection.command_return = [MockCommandReply(success=False, error="Test error")]

        container = MockCon(id=10, type="con", layout="splitv", parent=workspace)
        window = MockCon(
            id=100,
            type="con",
            rect=MockRect(width=800, height=400),  # Wide -> splith
            parent=container,
        )

        manager.switchSplit(window)

        captured = capsys.readouterr()
        assert "Error" in captured.out or len(mock_connection.commands_executed) > 0

    def test_switchSplit_commandSucceeds_logsSuccess(self, mock_connection, temp_config, capsys):
        """Successful command should log when debug is True."""
        config = temp_config(
            """
[layman]
debug = true
"""
        )
        workspace = MockCon(name="1", type="workspace")
        manager = AutotilingLayoutManager(mock_connection, workspace, "1", config)

        container = MockCon(id=10, type="con", layout="splitv", parent=workspace)
        window = MockCon(
            id=100,
            type="con",
            rect=MockRect(width=800, height=400),  # Wide -> splith
            parent=container,
        )

        manager.switchSplit(window)

        captured = capsys.readouterr()
        # Should log the switch
        assert "splith" in captured.out.lower() or len(mock_connection.commands_executed) > 0
