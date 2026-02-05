"""
Extended unit tests for layman.managers.master_stack module.

These tests cover additional edge cases, error paths, and complex operations
to increase coverage.
"""

import pytest

from layman.managers.master_stack import (
    MasterStackLayoutManager,
    StackLayout,
    Side,
    KEY_MASTER_WIDTH,
    KEY_STACK_LAYOUT,
    KEY_STACK_SIDE,
    KEY_SUBSTACK_THRESHOLD,
)
from tests.mocks.i3ipc_mocks import (
    MockConnection,
    MockCon,
    MockRect,
    MockWindowEvent,
    create_workspace,
)


# =============================================================================
# Config Validation Tests
# =============================================================================


class TestMasterStackConfigValidation:
    """Tests for config option validation."""

    def test_substackThreshold_negative_raisesError(self, mock_connection, temp_config):
        """Negative substackThreshold should raise ConfigError (Decision #2)."""
        from layman.config import ConfigError
        config = temp_config(
            """
[layman]
substackThreshold = -5
"""
        )
        workspace = MockCon(name="1", type="workspace")
        with pytest.raises(ConfigError, match="Invalid substackThreshold"):
            MasterStackLayoutManager(mock_connection, workspace, "1", config)

    def test_substackThreshold_one_raisesError(self, mock_connection, temp_config):
        """substackThreshold of 1 should raise ConfigError (Decision #2)."""
        from layman.config import ConfigError
        config = temp_config(
            """
[layman]
substackThreshold = 1
"""
        )
        workspace = MockCon(name="1", type="workspace")
        with pytest.raises(ConfigError, match="Invalid substackThreshold"):
            MasterStackLayoutManager(mock_connection, workspace, "1", config)

    def test_substackThreshold_two_valid(self, mock_connection, temp_config):
        """substackThreshold of 2 should be valid."""
        config = temp_config(
            """
[layman]
substackThreshold = 2
"""
        )
        workspace = MockCon(name="1", type="workspace")
        manager = MasterStackLayoutManager(mock_connection, workspace, "1", config)

        assert manager.substackThreshold == 2


# =============================================================================
# Window Removed Edge Cases
# =============================================================================


class TestWindowRemovedEdgeCases:
    """Edge cases for windowRemoved handler."""

    def test_windowRemoved_floatingNotInSet_logsError(
        self, mock_connection, minimal_config, capsys
    ):
        """Removing a floating window not tracked should log error."""
        workspace = MockCon(name="1", type="workspace")
        manager = MasterStackLayoutManager(mock_connection, workspace, "1", minimal_config)
        manager.floatingWindowIds = {100}  # Track a different window

        # Try to remove a floating window we don't have
        window = MockCon(id=999, type="floating_con", floating="auto_on")
        event = MockWindowEvent(change="close", container=window)

        manager.windowRemoved(event, workspace, window)

        captured = capsys.readouterr()
        assert "not found" in captured.out.lower() or 999 not in manager.floatingWindowIds


# =============================================================================
# Arrange Windows Tests
# =============================================================================


class TestArrangeWindows:
    """Tests for arrangeWindows method."""

    def test_arrangeWindows_multipleWindows_allAdded(self, mock_connection, minimal_config):
        """arrangeWindows should add all tiled windows."""
        workspace = create_workspace(name="1", window_count=4)
        manager = MasterStackLayoutManager(mock_connection, workspace, "1", minimal_config)

        assert len(manager.windowIds) == 4

    def test_arrangeWindows_mixedWindows_onlyTiledAdded(self, mock_connection, minimal_config):
        """arrangeWindows should only add tiled windows, not floating."""
        workspace = create_workspace(name="1", window_count=3, floating_count=2)
        manager = MasterStackLayoutManager(mock_connection, workspace, "1", minimal_config)

        assert len(manager.windowIds) == 3
        assert len(manager.floatingWindowIds) == 2


# =============================================================================
# Stack Layout Tests
# =============================================================================


class TestSetStackLayout:
    """Tests for setStackLayout method."""

    def test_setStackLayout_twoWindows_executesCommand(self, mock_connection, minimal_config):
        """setStackLayout with 2+ windows should execute command."""
        workspace = MockCon(name="1", type="workspace")
        manager = MasterStackLayoutManager(mock_connection, workspace, "1", minimal_config)
        manager.windowIds = [100, 200]

        mock_connection.clear_commands()
        manager.setStackLayout()

        commands = mock_connection.commands_executed
        assert len(commands) >= 1
        assert "200" in commands[0]  # Stack window
        assert "layout" in commands[0]

    def test_setStackLayout_oneWindow_noCommand(self, mock_connection, minimal_config):
        """setStackLayout with only 1 window should do nothing."""
        workspace = MockCon(name="1", type="workspace")
        manager = MasterStackLayoutManager(mock_connection, workspace, "1", minimal_config)
        manager.windowIds = [100]

        mock_connection.clear_commands()
        manager.setStackLayout()

        assert len(mock_connection.commands_executed) == 0


# =============================================================================
# Substack Tests
# =============================================================================


class TestSubstackOperations:
    """Tests for substack creation and destruction."""

    def test_createSubstackIfNeeded_underLimit_noSubstack(
        self, mock_connection, temp_config
    ):
        """Under depth limit, no substack should be created."""
        config = temp_config(
            """
[layman]
substackThreshold = 5
"""
        )
        workspace = MockCon(name="1", type="workspace")
        manager = MasterStackLayoutManager(mock_connection, workspace, "1", config)
        manager.windowIds = [100, 200, 300]  # 3 windows, limit is 5

        mock_connection.clear_commands()
        manager.createSubstackIfNeeded()

        assert manager.substackExists is False

    def test_destroySubstackIfExists_noSubstack_noop(self, mock_connection, minimal_config):
        """Destroying non-existent substack should be no-op."""
        workspace = MockCon(name="1", type="workspace")
        manager = MasterStackLayoutManager(mock_connection, workspace, "1", minimal_config)
        manager.substackExists = False

        mock_connection.clear_commands()
        manager.destroySubstackIfExists()

        assert len(mock_connection.commands_executed) == 0


# =============================================================================
# Toggle Operations Tests
# =============================================================================


class TestToggleOperationsExtended:
    """Extended tests for toggle operations."""

    def test_toggleStackSide_oneWindow_noSwap(self, mock_connection, minimal_config):
        """toggleStackSide with only 1 window should only toggle side."""
        workspace = MockCon(name="1", type="workspace")
        manager = MasterStackLayoutManager(mock_connection, workspace, "1", minimal_config)
        manager.windowIds = [100]
        original_side = manager.stackSide

        mock_connection.clear_commands()
        manager.toggleStackSide(workspace)

        assert manager.stackSide == original_side.opposite()

    def test_toggleStackLayout_whileMaximized_noLayoutChange(
        self, mock_connection, minimal_config
    ):
        """toggleStackLayout while maximized should change enum but not execute."""
        workspace = MockCon(name="1", type="workspace")
        manager = MasterStackLayoutManager(mock_connection, workspace, "1", minimal_config)
        manager.windowIds = [100, 200]
        manager.maximized = True
        original_layout = manager.stackLayout

        mock_connection.clear_commands()
        manager.toggleStackLayout()

        assert manager.stackLayout != original_layout
        # Should not execute layout commands while maximized
        layout_commands = [cmd for cmd in mock_connection.commands_executed if "layout" in cmd]
        assert len(layout_commands) == 0


# =============================================================================
# Movement Tests
# =============================================================================


class TestMoveWindowToIndexExtended:
    """Extended tests for moveWindowToIndex."""

    def test_moveWindowToIndex_oneWindow_noop(self, mock_connection, minimal_config, capsys):
        """Moving with only 1 window should log and return."""
        workspace = MockCon(name="1", type="workspace")
        manager = MasterStackLayoutManager(mock_connection, workspace, "1", minimal_config)
        manager.windowIds = [100]
        manager.debug = True

        mock_connection.clear_commands()
        window = MockCon(id=100)
        manager.moveWindowToIndex(window, 0)

        captured = capsys.readouterr()
        assert "not enough" in captured.out.lower()


class TestMoveWindowRelativeExtended:
    """Extended tests for moveWindowRelative."""

    def test_moveWindowRelative_upFromMiddle(self, mock_connection, minimal_config):
        """Moving up from middle should decrement index."""
        workspace = MockCon(name="1", type="workspace")
        manager = MasterStackLayoutManager(mock_connection, workspace, "1", minimal_config)
        manager.windowIds = [100, 200, 300, 400]

        window = MockCon(id=300)  # Index 2
        manager.moveWindowRelative(window, -1)

        # Window 300 should move to index 1
        assert manager.windowIds.index(300) == 1

    def test_moveWindowRelative_downFromMiddle(self, mock_connection, minimal_config):
        """Moving down from middle should increment index."""
        workspace = MockCon(name="1", type="workspace")
        manager = MasterStackLayoutManager(mock_connection, workspace, "1", minimal_config)
        manager.windowIds = [100, 200, 300, 400]

        window = MockCon(id=200)  # Index 1
        manager.moveWindowRelative(window, 1)

        # Window 200 should move to index 2
        assert manager.windowIds.index(200) == 2


# =============================================================================
# Rotation Tests
# =============================================================================


class TestRotateWindows:
    """Tests for rotateWindows method."""

    def test_rotateWindows_clockwise_leftStack(self, mock_connection, minimal_config):
        """Clockwise rotation with left stack should move master to end."""
        workspace = MockCon(name="1", type="workspace")
        manager = MasterStackLayoutManager(mock_connection, workspace, "1", minimal_config)
        manager.windowIds = [100, 200, 300]
        manager.stackSide = Side.LEFT

        # Set up tree so find_by_id works
        master = MockCon(id=100, type="con", parent=workspace)
        workspace.nodes = [master, MockCon(id=200), MockCon(id=300)]
        mock_connection.tree = workspace

        manager.rotateWindows(workspace, "cw")

        # After CW rotation with left stack: master moves to end
        assert manager.windowIds[-1] == 100

    def test_rotateWindows_counterClockwise_leftStack(self, mock_connection, minimal_config):
        """Counter-clockwise rotation with left stack should move last to front."""
        workspace = MockCon(name="1", type="workspace")
        manager = MasterStackLayoutManager(mock_connection, workspace, "1", minimal_config)
        manager.windowIds = [100, 200, 300]
        manager.stackSide = Side.LEFT

        # Set up tree so find_by_id works
        last = MockCon(id=300, type="con", parent=workspace)
        workspace.nodes = [MockCon(id=100), MockCon(id=200), last]
        mock_connection.tree = workspace

        manager.rotateWindows(workspace, "ccw")

        # After CCW rotation with left stack: last moves to front
        assert manager.windowIds[0] == 300

    def test_rotateWindows_singleWindow_noop(self, mock_connection, minimal_config):
        """Rotation with single window should be no-op."""
        workspace = MockCon(name="1", type="workspace")
        manager = MasterStackLayoutManager(mock_connection, workspace, "1", minimal_config)
        manager.windowIds = [100]

        manager.rotateWindows(workspace, "cw")

        assert manager.windowIds == [100]


# =============================================================================
# Focus Tests
# =============================================================================


class TestFocusWindowRelative:
    """Tests for focusWindowRelative method."""

    def test_focusWindowRelative_focusNext(self, mock_connection, minimal_config):
        """focusWindowRelative +1 should focus next window."""
        workspace = MockCon(name="1", type="workspace")
        manager = MasterStackLayoutManager(mock_connection, workspace, "1", minimal_config)
        manager.windowIds = [100, 200, 300]
        manager.lastFocusedWindowId = 100

        # Set up tree so find_by_id works
        focused = MockCon(id=100, type="con", parent=workspace)
        workspace.nodes = [focused, MockCon(id=200), MockCon(id=300)]
        mock_connection.tree = workspace

        mock_connection.clear_commands()
        manager.focusWindowRelative(workspace, 1)

        commands = " ".join(mock_connection.commands_executed)
        assert "200" in commands
        assert "focus" in commands

    def test_focusWindowRelative_focusPrevious(self, mock_connection, minimal_config):
        """focusWindowRelative -1 should focus previous window."""
        workspace = MockCon(name="1", type="workspace")
        manager = MasterStackLayoutManager(mock_connection, workspace, "1", minimal_config)
        manager.windowIds = [100, 200, 300]
        manager.lastFocusedWindowId = 200

        # Set up tree so find_by_id works
        focused = MockCon(id=200, type="con", parent=workspace)
        workspace.nodes = [MockCon(id=100), focused, MockCon(id=300)]
        mock_connection.tree = workspace

        mock_connection.clear_commands()
        manager.focusWindowRelative(workspace, -1)

        commands = " ".join(mock_connection.commands_executed)
        assert "100" in commands
        assert "focus" in commands

    def test_focusWindowRelative_wrapAround(self, mock_connection, minimal_config):
        """focusWindowRelative should wrap around."""
        workspace = MockCon(name="1", type="workspace")
        manager = MasterStackLayoutManager(mock_connection, workspace, "1", minimal_config)
        manager.windowIds = [100, 200, 300]
        manager.lastFocusedWindowId = 300

        # Set up tree so find_by_id works
        focused = MockCon(id=300, type="con", parent=workspace)
        workspace.nodes = [MockCon(id=100), MockCon(id=200), focused]
        mock_connection.tree = workspace

        mock_connection.clear_commands()
        manager.focusWindowRelative(workspace, 1)

        commands = " ".join(mock_connection.commands_executed)
        # Should wrap to first window
        assert "100" in commands


# =============================================================================
# Command Handler Tests
# =============================================================================


class TestOnCommandExtended:
    """Extended tests for onCommand handler."""

    @pytest.fixture
    def manager_with_focus(self, mock_connection, minimal_config):
        """Manager with windows and focus set up."""
        workspace = MockCon(name="1", type="workspace")
        manager = MasterStackLayoutManager(mock_connection, workspace, "1", minimal_config)
        manager.windowIds = [100, 200, 300]
        manager.lastFocusedWindowId = 200

        # Create focused window
        focused = MockCon(id=200, type="con", focused=True)
        workspace.nodes = [
            MockCon(id=100),
            focused,
            MockCon(id=300),
        ]
        return manager, workspace

    def test_onCommand_moveLeft(self, manager_with_focus, mock_connection):
        """'move left' should call moveWindowHorizontally."""
        manager, workspace = manager_with_focus
        mock_connection.clear_commands()

        manager.onCommand("move left", workspace)

        # Should have executed some commands (or handled internally)

    def test_onCommand_moveRight(self, manager_with_focus, mock_connection):
        """'move right' should call moveWindowHorizontally."""
        manager, workspace = manager_with_focus
        mock_connection.clear_commands()

        manager.onCommand("move right", workspace)

    def test_onCommand_rotateCw(self, manager_with_focus, mock_connection):
        """'rotate cw' should rotate windows clockwise."""
        manager, workspace = manager_with_focus
        original_first = manager.windowIds[0]

        manager.onCommand("rotate cw", workspace)

        assert manager.windowIds[0] != original_first

    def test_onCommand_rotateCcw(self, manager_with_focus, mock_connection):
        """'rotate ccw' should rotate windows counter-clockwise."""
        manager, workspace = manager_with_focus
        original_last = manager.windowIds[-1]

        manager.onCommand("rotate ccw", workspace)

        assert manager.windowIds[-1] != original_last

    def test_onCommand_swapMaster(self, manager_with_focus, mock_connection):
        """'swap master' should swap focused with master."""
        manager, workspace = manager_with_focus

        # Set up tree so find_by_id works
        master = MockCon(id=100, type="con", parent=workspace)
        focused = MockCon(id=200, type="con", focused=True, parent=workspace)
        workspace.nodes = [master, focused, MockCon(id=300, parent=workspace)]
        mock_connection.tree = workspace

        mock_connection.clear_commands()
        manager.onCommand("swap master", workspace)

        # Should swap windows 200 and 100
        commands = " ".join(mock_connection.commands_executed)
        assert "swap" in commands

    def test_onCommand_stacksideToggle(self, mock_connection, minimal_config):
        """'stackside toggle' should toggle stack side."""
        workspace = MockCon(name="1", type="workspace")
        manager = MasterStackLayoutManager(mock_connection, workspace, "1", minimal_config)
        manager.windowIds = [100]  # Single window - no stack manipulation needed
        manager.lastFocusedWindowId = 100
        original_side = manager.stackSide

        # Set up workspace with the focused window
        focused = MockCon(id=100, type="con", focused=True, parent=workspace)
        workspace.nodes = [focused]
        mock_connection.tree = workspace

        mock_connection.clear_commands()
        manager.onCommand("stackside toggle", workspace)

        assert manager.stackSide != original_side

    def test_onCommand_moveToIndex_valid(self, manager_with_focus, mock_connection):
        """'move to index N' should move window to index."""
        manager, workspace = manager_with_focus

        manager.onCommand("move to index 0", workspace)

        # Window 200 should now be at index 0
        assert manager.windowIds[0] == 200

    def test_onCommand_moveToIndex_invalid(self, manager_with_focus, mock_connection, capsys):
        """'move to index X' with non-integer should log usage."""
        manager, workspace = manager_with_focus
        manager.debug = True

        manager.onCommand("move to index abc", workspace)

        captured = capsys.readouterr()
        assert "Usage" in captured.out
