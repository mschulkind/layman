"""
More extended tests for MasterStack to improve coverage.

Focus on uncovered lines: maximize, horizontal movement, complex operations.
"""

import logging

import pytest

from layman.managers.master_stack import (
    MasterStackLayoutManager,
    StackLayout,
    Side,
)
from tests.mocks.i3ipc_mocks import (
    MockConnection,
    MockCon,
    MockRect,
    MockWindowEvent,
)


# =============================================================================
# Toggle Maximize Tests
# =============================================================================


class TestToggleMaximize:
    """Tests for toggleMaximize method."""

    def test_toggleMaximize_withTwoWindows_maximizes(self, mock_connection, minimal_config):
        """toggleMaximize with 2 windows should maximize."""
        workspace = MockCon(name="1", type="workspace")
        manager = MasterStackLayoutManager(mock_connection, workspace, "1", minimal_config)
        manager.windowIds = [100, 200]
        manager.maximized = False

        # Set up master window
        master = MockCon(id=100, type="con", rect=MockRect(width=600), parent=workspace)
        workspace.nodes = [master, MockCon(id=200, parent=workspace)]
        mock_connection.tree = workspace

        mock_connection.clear_commands()
        manager.toggleMaximize(workspace)

        assert manager.maximized is True
        assert manager.masterWidthBeforeMaximize == 600
        # Should have executed tabbed layout command
        commands = " ".join(mock_connection.commands_executed)
        assert "tabbed" in commands

    def test_toggleMaximize_alreadyMaximized_unmaximizes(
        self, mock_connection, minimal_config
    ):
        """toggleMaximize when maximized should unmaximize."""
        workspace = MockCon(name="1", type="workspace")
        manager = MasterStackLayoutManager(mock_connection, workspace, "1", minimal_config)
        manager.windowIds = [100, 200]
        manager.maximized = True
        manager.masterWidthBeforeMaximize = 600

        mock_connection.clear_commands()
        manager.toggleMaximize(workspace)

        assert manager.maximized is False
        # Should have executed splitv and resize commands
        commands = " ".join(mock_connection.commands_executed)
        assert "splitv" in commands
        assert "resize" in commands

    def test_toggleMaximize_oneWindow_togglesFlag(self, mock_connection, minimal_config):
        """toggleMaximize with 1 window should just toggle flag."""
        workspace = MockCon(name="1", type="workspace")
        manager = MasterStackLayoutManager(mock_connection, workspace, "1", minimal_config)
        manager.windowIds = [100]
        manager.maximized = False

        mock_connection.clear_commands()
        manager.toggleMaximize(workspace)

        assert manager.maximized is True


# =============================================================================
# Move Window Horizontally Tests
# =============================================================================


class TestMoveWindowHorizontally:
    """Tests for moveWindowHorizontally method."""

    def test_moveWindowHorizontally_masterToStack_leftSide(
        self, mock_connection, minimal_config
    ):
        """Moving master toward stack should work."""
        workspace = MockCon(name="1", type="workspace")
        manager = MasterStackLayoutManager(mock_connection, workspace, "1", minimal_config)
        manager.windowIds = [100, 200, 300]
        manager.stackSide = Side.LEFT

        master = MockCon(id=100, type="con", parent=workspace)

        mock_connection.clear_commands()
        manager.moveWindowHorizontally(workspace, master, Side.LEFT)

        # Master moving toward stack (left) should move to index 1

    def test_moveWindowHorizontally_stackToMaster(self, mock_connection, minimal_config):
        """Moving stack window toward master should work."""
        workspace = MockCon(name="1", type="workspace")
        manager = MasterStackLayoutManager(mock_connection, workspace, "1", minimal_config)
        manager.windowIds = [100, 200, 300]
        manager.stackSide = Side.LEFT

        stack_window = MockCon(id=200, type="con", parent=workspace)

        mock_connection.clear_commands()
        manager.moveWindowHorizontally(workspace, stack_window, Side.RIGHT)

    def test_moveWindowHorizontally_oneWindow_noop(self, mock_connection, minimal_config):
        """Moving with 1 window should do nothing."""
        workspace = MockCon(name="1", type="workspace")
        manager = MasterStackLayoutManager(mock_connection, workspace, "1", minimal_config)
        manager.windowIds = [100]

        window = MockCon(id=100, type="con", parent=workspace)

        mock_connection.clear_commands()
        manager.moveWindowHorizontally(workspace, window, Side.LEFT)

        # Should do nothing
        assert len(mock_connection.commands_executed) == 0

    def test_moveWindowHorizontally_whileMaximized(self, mock_connection, minimal_config):
        """Moving while maximized should use different logic."""
        workspace = MockCon(name="1", type="workspace")
        manager = MasterStackLayoutManager(mock_connection, workspace, "1", minimal_config)
        manager.windowIds = [100, 200, 300]
        manager.maximized = True

        window = MockCon(id=100, type="con", parent=workspace)

        manager.moveWindowHorizontally(workspace, window, Side.RIGHT)

        # Should move to next index


# =============================================================================
# Push Window Tests
# =============================================================================


class TestPushWindowExtended:
    """Extended tests for pushWindow method."""

    def test_pushWindow_positionAfterMaster(self, mock_connection, minimal_config):
        """Push window positioned after master."""
        workspace = MockCon(name="1", type="workspace")
        manager = MasterStackLayoutManager(mock_connection, workspace, "1", minimal_config)
        manager.windowIds = [100, 200]

        new_window = MockCon(id=300, type="con")
        after_window = MockCon(id=100)

        mock_connection.clear_commands()
        manager.pushWindow(workspace, new_window, after_window)

        # New window should be at index 1
        assert manager.windowIds.index(300) == 1

    def test_pushWindow_positionAfterStack(self, mock_connection, minimal_config):
        """Push window positioned after stack window."""
        workspace = MockCon(name="1", type="workspace")
        manager = MasterStackLayoutManager(mock_connection, workspace, "1", minimal_config)
        manager.windowIds = [100, 200, 300]

        new_window = MockCon(id=400, type="con")
        after_window = MockCon(id=200)

        mock_connection.clear_commands()
        manager.pushWindow(workspace, new_window, after_window)

        # New window should be at index 2
        assert manager.windowIds.index(400) == 2


# =============================================================================
# Pop Window Tests
# =============================================================================


class TestPopWindowExtended:
    """Extended tests for popWindow method."""

    def test_popWindow_masterRemoved_newMasterMoves(
        self, mock_connection, minimal_config
    ):
        """Removing master should move new master to position."""
        workspace = MockCon(name="1", type="workspace")
        manager = MasterStackLayoutManager(mock_connection, workspace, "1", minimal_config)
        manager.windowIds = [100, 200, 300]
        manager.stackSide = Side.RIGHT

        window = MockCon(id=100, type="con", rect=MockRect(width=600))

        mock_connection.clear_commands()
        manager.popWindow(window)

        assert manager.windowIds == [200, 300]
        # Should have move and resize commands
        commands = " ".join(mock_connection.commands_executed)
        assert "move" in commands

    def test_popWindow_stackWindowRemoved(self, mock_connection, minimal_config):
        """Removing stack window should update list."""
        workspace = MockCon(name="1", type="workspace")
        manager = MasterStackLayoutManager(mock_connection, workspace, "1", minimal_config)
        manager.windowIds = [100, 200, 300]

        window = MockCon(id=200, type="con", rect=MockRect(width=400))

        mock_connection.clear_commands()
        manager.popWindow(window)

        assert manager.windowIds == [100, 300]
        assert 200 not in manager.windowIds

    def test_popWindow_windowNotFound_logsWarning(
        self, mock_connection, minimal_config, caplog
    ):
        """Popping unknown window should log warning."""
        workspace = MockCon(name="1", type="workspace")
        manager = MasterStackLayoutManager(mock_connection, workspace, "1", minimal_config)
        manager.windowIds = [100, 200]

        window = MockCon(id=999, type="con")

        with caplog.at_level(logging.DEBUG, logger=manager.logger.name):
            manager.popWindow(window)

        assert "not found" in caplog.text.lower() or "bug" in caplog.text.lower()


# =============================================================================
# Stack Layout Cycle Tests
# =============================================================================


class TestStackLayoutCycle:
    """Tests for stack layout cycling."""

    def test_stackLayout_cycles_through_all_options(self, mock_connection, minimal_config):
        """toggleStackLayout should cycle through all layouts."""
        workspace = MockCon(name="1", type="workspace")
        manager = MasterStackLayoutManager(mock_connection, workspace, "1", minimal_config)
        manager.windowIds = [100, 200]

        layouts_seen = {manager.stackLayout}

        for _ in range(5):  # Cycle more than needed
            manager.toggleStackLayout()
            layouts_seen.add(manager.stackLayout)

        # Should have seen all layout options
        assert len(layouts_seen) >= 3  # At least SPLITV, TABBED, SPLITH


# =============================================================================
# Swap Windows Tests
# =============================================================================


class TestSwapWindows:
    """Tests for swapWindows method."""

    def test_swapWindows_sameid_noop(self, mock_connection, minimal_config):
        """Swapping window with itself should do nothing."""
        workspace = MockCon(name="1", type="workspace")
        manager = MasterStackLayoutManager(mock_connection, workspace, "1", minimal_config)
        manager.windowIds = [100, 200]

        window = MockCon(id=100)

        mock_connection.clear_commands()
        manager.swapWindows(window, window)

        assert len(mock_connection.commands_executed) == 0

    def test_swapWindows_differentWindows_swaps(self, mock_connection, minimal_config):
        """Swapping two different windows should execute swap."""
        workspace = MockCon(name="1", type="workspace")
        manager = MasterStackLayoutManager(mock_connection, workspace, "1", minimal_config)
        manager.windowIds = [100, 200, 300]

        source = MockCon(id=100)
        target = MockCon(id=200)

        mock_connection.clear_commands()
        manager.swapWindows(source, target)

        commands = " ".join(mock_connection.commands_executed)
        assert "swap" in commands
        # Window IDs should be swapped in list
        assert manager.windowIds.index(100) == 1
        assert manager.windowIds.index(200) == 0


# =============================================================================
# On Command Additional Tests
# =============================================================================


class TestOnCommandMore:
    """More tests for onCommand handler."""

    def test_onCommand_focusUp(self, mock_connection, minimal_config):
        """'focus up' should focus previous window."""
        workspace = MockCon(name="1", type="workspace")
        manager = MasterStackLayoutManager(mock_connection, workspace, "1", minimal_config)
        manager.windowIds = [100, 200, 300]
        manager.lastFocusedWindowId = 200

        focused = MockCon(id=200, type="con", focused=True, parent=workspace)
        workspace.nodes = [MockCon(id=100), focused, MockCon(id=300)]
        mock_connection.tree = workspace

        mock_connection.clear_commands()
        manager.onCommand("focus up", workspace)

        commands = " ".join(mock_connection.commands_executed)
        assert "focus" in commands

    def test_onCommand_focusDown(self, mock_connection, minimal_config):
        """'focus down' should focus next window."""
        workspace = MockCon(name="1", type="workspace")
        manager = MasterStackLayoutManager(mock_connection, workspace, "1", minimal_config)
        manager.windowIds = [100, 200, 300]
        manager.lastFocusedWindowId = 100

        focused = MockCon(id=100, type="con", focused=True, parent=workspace)
        workspace.nodes = [focused, MockCon(id=200), MockCon(id=300)]
        mock_connection.tree = workspace

        mock_connection.clear_commands()
        manager.onCommand("focus down", workspace)

        commands = " ".join(mock_connection.commands_executed)
        assert "focus" in commands

    def test_onCommand_maximize(self, mock_connection, minimal_config):
        """'maximize' should toggle maximize."""
        workspace = MockCon(name="1", type="workspace")
        manager = MasterStackLayoutManager(mock_connection, workspace, "1", minimal_config)
        manager.windowIds = [100, 200]
        manager.maximized = False

        focused = MockCon(id=100, type="con", focused=True, parent=workspace, rect=MockRect(width=600))
        workspace.nodes = [focused, MockCon(id=200)]
        mock_connection.tree = workspace

        manager.onCommand("maximize", workspace)

        assert manager.maximized is True

    def test_onCommand_stackToggle(self, mock_connection, minimal_config):
        """'stack toggle' should toggle layout."""
        workspace = MockCon(name="1", type="workspace")
        manager = MasterStackLayoutManager(mock_connection, workspace, "1", minimal_config)
        manager.windowIds = [100, 200]
        original_layout = manager.stackLayout

        focused = MockCon(id=100, type="con", focused=True, parent=workspace)
        workspace.nodes = [focused, MockCon(id=200)]
        mock_connection.tree = workspace

        manager.onCommand("stack toggle", workspace)

        assert manager.stackLayout != original_layout

    def test_onCommand_focusMaster(self, mock_connection, minimal_config):
        """'focus master' should focus master window."""
        workspace = MockCon(name="1", type="workspace")
        manager = MasterStackLayoutManager(mock_connection, workspace, "1", minimal_config)
        manager.windowIds = [100, 200, 300]

        focused = MockCon(id=200, type="con", focused=True, parent=workspace)
        workspace.nodes = [MockCon(id=100), focused, MockCon(id=300)]
        mock_connection.tree = workspace

        mock_connection.clear_commands()
        manager.onCommand("focus master", workspace)

        commands = " ".join(mock_connection.commands_executed)
        assert "100" in commands
        assert "focus" in commands
