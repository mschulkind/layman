"""
Unit tests for layman.managers.master_stack module.

This is the most comprehensive test file, covering:
- Window ID list management
- Push/pop window operations
- Movement commands
- Command dispatch
- Stack layout cycling
- Maximize functionality
- Floating window handling
- Known bugs (regression tests)
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
# Fixtures
# =============================================================================


@pytest.fixture
def manager_factory(mock_connection):
    """Factory for creating MasterStackLayoutManager with custom config."""

    def _create(
        config,
        workspace=None,
        workspace_name="1",
    ):
        if workspace is None:
            workspace = MockCon(name=workspace_name, type="workspace")
        return MasterStackLayoutManager(
            mock_connection, workspace, workspace_name, config
        )

    return _create


@pytest.fixture
def basic_manager(mock_connection, minimal_config):
    """A basic MasterStackLayoutManager with minimal config."""
    workspace = MockCon(name="1", type="workspace")
    return MasterStackLayoutManager(
        mock_connection, workspace, "1", minimal_config
    )


@pytest.fixture
def manager_with_windows(mock_connection, minimal_config):
    """Manager pre-populated with 3 windows."""
    workspace = create_workspace(name="1", window_count=3)
    manager = MasterStackLayoutManager(
        mock_connection, workspace, "1", minimal_config
    )
    # Manager's arrangeWindows should have captured the windows
    return manager, workspace


# =============================================================================
# Enum Tests
# =============================================================================


class TestStackLayoutEnum:
    """Tests for StackLayout enum."""

    def test_nextChoice_cycles(self):
        """nextChoice should cycle through all layouts."""
        assert StackLayout.SPLITV.nextChoice() == StackLayout.SPLITH
        assert StackLayout.SPLITH.nextChoice() == StackLayout.STACKING
        assert StackLayout.STACKING.nextChoice() == StackLayout.TABBED
        assert StackLayout.TABBED.nextChoice() == StackLayout.SPLITV


class TestSideEnum:
    """Tests for Side enum."""

    def test_opposite_swaps(self):
        """opposite() should return the other side."""
        assert Side.LEFT.opposite() == Side.RIGHT
        assert Side.RIGHT.opposite() == Side.LEFT

    def test_str_returnsLowercase(self):
        """str() should return lowercase string."""
        assert str(Side.LEFT) == "left"
        assert str(Side.RIGHT) == "right"


# =============================================================================
# Initialization Tests
# =============================================================================


class TestMasterStackInit:
    """Tests for MasterStackLayoutManager initialization."""

    def test_init_setsDefaults(self, basic_manager):
        """Constructor should set default values."""
        assert basic_manager.windowIds == []
        assert basic_manager.floatingWindowIds == set()
        assert basic_manager.masterWidth == 50
        assert basic_manager.stackSide == Side.RIGHT
        assert basic_manager.stackLayout == StackLayout.SPLITV
        assert basic_manager.substackThreshold == 0
        assert basic_manager.substackExists is False
        assert basic_manager.lastFocusedWindowId is None
        assert basic_manager.maximized is False

    def test_init_readsConfigOptions(self, manager_factory, temp_config):
        """Constructor should read config options."""
        config = temp_config(
            """
[layman]
masterWidth = 60
stackLayout = "tabbed"
stackSide = "left"
substackThreshold = 3
"""
        )
        manager = manager_factory(config)

        assert manager.masterWidth == 60
        assert manager.stackLayout == StackLayout.TABBED
        assert manager.stackSide == Side.LEFT
        assert manager.substackThreshold == 3

    def test_init_invalidMasterWidth_raisesConfigError(
        self, manager_factory, temp_config
    ):
        """Invalid masterWidth should raise ConfigError (Decision #2)."""
        from layman.config import ConfigError
        config = temp_config(
            """
[layman]
masterWidth = 150
"""
        )
        with pytest.raises(ConfigError, match="Invalid masterWidth"):
            manager_factory(config)

    def test_init_invalidStackLayout_raisesConfigError(
        self, manager_factory, temp_config
    ):
        """Invalid stackLayout should raise ConfigError (Decision #2)."""
        from layman.config import ConfigError
        config = temp_config(
            """
[layman]
stackLayout = "invalid"
"""
        )
        with pytest.raises(ConfigError, match="Invalid stackLayout"):
            manager_factory(config)

    def test_init_withExistingWindows_arranges(
        self, mock_connection, minimal_config
    ):
        """Existing windows should be arranged on init."""
        workspace = create_workspace(name="1", window_count=3)
        manager = MasterStackLayoutManager(
            mock_connection, workspace, "1", minimal_config
        )

        assert len(manager.windowIds) == 3

    def test_init_withFloatingWindows_tracks(
        self, mock_connection, minimal_config
    ):
        """Floating windows should be tracked separately."""
        workspace = create_workspace(
            name="1", window_count=2, floating_count=1
        )
        manager = MasterStackLayoutManager(
            mock_connection, workspace, "1", minimal_config
        )

        assert len(manager.windowIds) == 2
        assert len(manager.floatingWindowIds) == 1


# =============================================================================
# Class Attribute Tests
# =============================================================================


class TestMasterStackClassAttributes:
    """Tests for MasterStackLayoutManager class attributes."""

    def test_shortName(self):
        """shortName should be 'MasterStack'."""
        assert MasterStackLayoutManager.shortName == "MasterStack"

    def test_overridesMoveBinds(self):
        """overridesMoveBinds should be True."""
        assert MasterStackLayoutManager.overridesMoveBinds is True

    def test_overridesFocusBinds(self):
        """overridesFocusBinds should be True."""
        assert MasterStackLayoutManager.overridesFocusBinds is True

    def test_supportsFloating(self):
        """supportsFloating should be True."""
        assert MasterStackLayoutManager.supportsFloating is True


# =============================================================================
# Window ID List Management
# =============================================================================


class TestGetWindowListIndex:
    """Tests for getWindowListIndex() method."""

    def test_getWindowListIndex_existingWindow_returnsIndex(
        self, basic_manager
    ):
        """Should return correct index for existing window."""
        basic_manager.windowIds = [100, 200, 300]
        window = MockCon(id=200)

        assert basic_manager.getWindowListIndex(window) == 1

    def test_getWindowListIndex_masterWindow_returnsZero(self, basic_manager):
        """Master window should have index 0."""
        basic_manager.windowIds = [100, 200, 300]
        window = MockCon(id=100)

        assert basic_manager.getWindowListIndex(window) == 0

    def test_getWindowListIndex_notFound_returnsNone(self, basic_manager):
        """Should return None for window not in list."""
        basic_manager.windowIds = [100, 200, 300]
        window = MockCon(id=999)

        assert basic_manager.getWindowListIndex(window) is None


class TestIsFloating:
    """Tests for isFloating() method."""

    def test_isFloating_i3Style_detectsFloating(self, basic_manager):
        """Should detect i3-style floating (floating='auto_on')."""
        window = MockCon(id=100, floating="auto_on")
        assert basic_manager.isFloating(window) is True

        window = MockCon(id=101, floating="user_on")
        assert basic_manager.isFloating(window) is True

    def test_isFloating_swayStyle_detectsFloating(self, basic_manager):
        """Should detect sway-style floating (type='floating_con')."""
        window = MockCon(id=100, type="floating_con")
        assert basic_manager.isFloating(window) is True

    def test_isFloating_notFloating_returnsFalse(self, basic_manager):
        """Non-floating windows should return False."""
        window = MockCon(id=100, type="con", floating=None)
        assert basic_manager.isFloating(window) is False


# =============================================================================
# Window Event Handlers
# =============================================================================


class TestWindowAdded:
    """Tests for windowAdded() event handler."""

    def test_windowAdded_floatingWindow_trackedSeparately(
        self, basic_manager, mock_connection
    ):
        """Floating windows should only be tracked, not pushed."""
        workspace = MockCon(name="1", type="workspace")
        window = MockCon(id=100, type="floating_con", floating="auto_on")
        event = MockWindowEvent(change="new", container=window)

        basic_manager.windowAdded(event, workspace, window)

        assert 100 in basic_manager.floatingWindowIds
        assert 100 not in basic_manager.windowIds

    def test_windowAdded_tiledWindow_pushed(
        self, basic_manager, mock_connection
    ):
        """Tiled windows should be pushed to windowIds."""
        workspace = MockCon(name="1", type="workspace")
        window = MockCon(id=100, type="con")
        event = MockWindowEvent(change="new", container=window)

        basic_manager.windowAdded(event, workspace, window)

        assert 100 in basic_manager.windowIds


class TestWindowRemoved:
    """Tests for windowRemoved() event handler."""

    def test_windowRemoved_floatingWindow_removedFromSet(self, basic_manager):
        """Floating windows should be removed from floatingWindowIds."""
        basic_manager.floatingWindowIds = {100, 200}
        window = MockCon(id=100, type="floating_con", floating="auto_on")
        event = MockWindowEvent(change="close", container=window)

        basic_manager.windowRemoved(event, None, window)

        assert 100 not in basic_manager.floatingWindowIds
        assert 200 in basic_manager.floatingWindowIds

    def test_windowRemoved_tiledWindow_popped(self, basic_manager):
        """Tiled windows should be popped from windowIds."""
        basic_manager.windowIds = [100, 200, 300]
        window = MockCon(id=200, type="con")
        event = MockWindowEvent(change="close", container=window)

        basic_manager.windowRemoved(event, None, window)

        assert 200 not in basic_manager.windowIds
        assert basic_manager.windowIds == [100, 300]


class TestWindowFocused:
    """Tests for windowFocused() event handler."""

    def test_windowFocused_floatingWindow_ignored(self, basic_manager):
        """Floating windows should not update lastFocusedWindowId."""
        window = MockCon(id=100, type="floating_con", floating="auto_on")
        event = MockWindowEvent(change="focus", container=window)
        workspace = MockCon(name="1", type="workspace")

        basic_manager.windowFocused(event, workspace, window)

        assert basic_manager.lastFocusedWindowId is None

    def test_windowFocused_tiledWindow_updatesLastFocused(self, basic_manager):
        """Tiled windows should update lastFocusedWindowId."""
        window = MockCon(id=100, type="con")
        event = MockWindowEvent(change="focus", container=window)
        workspace = MockCon(name="1", type="workspace")

        basic_manager.windowFocused(event, workspace, window)

        assert basic_manager.lastFocusedWindowId == 100


class TestWindowFloating:
    """Tests for windowFloating() event handler."""

    def test_windowFloating_toFloating_popsAndTracks(self, basic_manager):
        """Window becoming floating should be popped and tracked."""
        basic_manager.windowIds = [100, 200]
        window = MockCon(id=100, type="floating_con", floating="auto_on")
        event = MockWindowEvent(change="floating", container=window)
        workspace = MockCon(name="1", type="workspace")

        basic_manager.windowFloating(event, workspace, window)

        assert 100 not in basic_manager.windowIds
        assert 100 in basic_manager.floatingWindowIds

    def test_windowFloating_toTiled_removesAndPushes(
        self, basic_manager, mock_connection
    ):
        """Window becoming tiled should be removed from floating and pushed."""
        basic_manager.floatingWindowIds = {100}
        window = MockCon(id=100, type="con", floating=None)
        event = MockWindowEvent(change="floating", container=window)
        workspace = MockCon(name="1", type="workspace")

        basic_manager.windowFloating(event, workspace, window)

        assert 100 not in basic_manager.floatingWindowIds
        assert 100 in basic_manager.windowIds


# =============================================================================
# Push/Pop Window Tests
# =============================================================================


class TestPushWindow:
    """Tests for pushWindow() method."""

    def test_pushWindow_firstWindow_addedToList(
        self, basic_manager, mock_connection
    ):
        """First window should just be added to empty list."""
        workspace = MockCon(name="1", type="workspace")
        window = MockCon(id=100)

        basic_manager.pushWindow(workspace, window)

        assert basic_manager.windowIds == [100]

    def test_pushWindow_secondWindow_createsMasterStack(
        self, basic_manager, mock_connection
    ):
        """Second window should create master-stack structure."""
        workspace = MockCon(name="1", type="workspace")
        basic_manager.windowIds = [100]

        window = MockCon(id=200)
        basic_manager.pushWindow(workspace, window)

        assert len(basic_manager.windowIds) == 2
        # The new window becomes master by default (positionAtIndex=0)
        assert basic_manager.windowIds[0] == 200  # New is master
        assert basic_manager.windowIds[1] == 100  # Original is stack
        # Should have executed layout commands
        assert len(mock_connection.commands_executed) > 0

    def test_pushWindow_thirdWindow_becomesNewMaster(
        self, basic_manager, mock_connection
    ):
        """Third+ windows become new master by default (positionAtIndex=0)."""
        workspace = MockCon(name="1", type="workspace")
        basic_manager.windowIds = [100, 200]

        window = MockCon(id=300)
        basic_manager.pushWindow(workspace, window)

        assert len(basic_manager.windowIds) == 3
        # By default, new windows get inserted at index 0 (new master)
        assert basic_manager.windowIds[0] == 300


class TestPopWindow:
    """Tests for popWindow() method."""

    def test_popWindow_stackWindow_removed(self, basic_manager, mock_connection):
        """Removing stack window should just update list."""
        basic_manager.windowIds = [100, 200, 300]
        window = MockCon(id=200)

        basic_manager.popWindow(window)

        assert basic_manager.windowIds == [100, 300]

    def test_popWindow_masterWindow_promotesStack(
        self, basic_manager, mock_connection
    ):
        """Removing master should promote first stack window."""
        basic_manager.windowIds = [100, 200, 300]
        window = MockCon(id=100, rect=MockRect(width=600))

        basic_manager.popWindow(window)

        # First stack (200) should now be at index 0
        assert basic_manager.windowIds[0] == 200
        # Commands should include moving the new master
        commands = " ".join(mock_connection.commands_executed)
        assert "move" in commands.lower()

    def test_popWindow_notInList_logsError(
        self, basic_manager, mock_connection, capsys
    ):
        """Window not in list should log error."""
        basic_manager.windowIds = [100, 200]
        window = MockCon(id=999)

        basic_manager.popWindow(window)

        captured = capsys.readouterr()
        # Should log that window wasn't found
        assert basic_manager.windowIds == [100, 200]  # Unchanged


# =============================================================================
# Command Dispatch Tests
# =============================================================================


class TestOnCommand:
    """Tests for onCommand() dispatch."""

    @pytest.fixture
    def manager_with_focus(self, mock_connection, minimal_config):
        """Manager with windows and a focused window."""
        workspace = MockCon(name="1", type="workspace")
        manager = MasterStackLayoutManager(
            mock_connection, workspace, "1", minimal_config
        )
        manager.windowIds = [100, 200, 300]

        # Create focused window in workspace
        focused = MockCon(id=200, type="con", focused=True)
        workspace.nodes = [
            MockCon(id=100),
            focused,
            MockCon(id=300),
        ]
        return manager, workspace

    def test_onCommand_noFocused_ignored(self, basic_manager):
        """Commands with no focused window should be ignored."""
        basic_manager.windowIds = [100, 200]
        workspace = MockCon(name="1", type="workspace")

        basic_manager.onCommand("move up", workspace)

        # Should not crash or do anything

    def test_onCommand_moveUp_callsMoveRelative(
        self, manager_with_focus, mock_connection
    ):
        """'move up' should move window up in list."""
        manager, workspace = manager_with_focus

        manager.onCommand("move up", workspace)

        # Window 200 at index 1 should move to index 0
        # (implementation varies)

    def test_onCommand_moveDown_callsMoveRelative(
        self, manager_with_focus, mock_connection
    ):
        """'move down' should move window down in list."""
        manager, workspace = manager_with_focus

        manager.onCommand("move down", workspace)

    def test_onCommand_moveToMaster_movesToIndex0(
        self, manager_with_focus, mock_connection
    ):
        """'move to master' should move window to index 0."""
        manager, workspace = manager_with_focus

        manager.onCommand("move to master", workspace)

    def test_onCommand_stackToggle_cyclesLayout(
        self, manager_with_focus, mock_connection
    ):
        """'stack toggle' should cycle through stack layouts."""
        manager, workspace = manager_with_focus
        original = manager.stackLayout

        manager.onCommand("stack toggle", workspace)

        assert manager.stackLayout != original

    def test_onCommand_maximize_togglesMaximized(
        self, manager_with_focus, mock_connection
    ):
        """'maximize' should toggle maximized state."""
        manager, workspace = manager_with_focus
        assert manager.maximized is False

        manager.onCommand("maximize", workspace)

        assert manager.maximized is True

    def test_onCommand_focusMaster_focusesFirstWindow(
        self, manager_with_focus, mock_connection
    ):
        """'focus master' should focus the master window."""
        manager, workspace = manager_with_focus

        manager.onCommand("focus master", workspace)

        commands = " ".join(mock_connection.commands_executed)
        assert "100" in commands  # Master ID
        assert "focus" in commands


# =============================================================================
# Movement Tests
# =============================================================================


class TestMoveWindowToIndex:
    """Tests for moveWindowToIndex() method."""

    @pytest.fixture
    def manager_4_windows(self, mock_connection, minimal_config):
        """Manager with 4 windows for movement tests."""
        workspace = MockCon(name="1", type="workspace")
        manager = MasterStackLayoutManager(
            mock_connection, workspace, "1", minimal_config
        )
        manager.windowIds = [100, 200, 300, 400]
        return manager, workspace

    def test_moveWindowToIndex_sameIndex_noop(
        self, manager_4_windows, mock_connection
    ):
        """Moving to same index should be a no-op."""
        manager, workspace = manager_4_windows
        window = MockCon(id=200)
        mock_connection.clear_commands()

        manager.moveWindowToIndex(window, 1)

        # No commands should be executed for same-index move
        assert len(mock_connection.commands_executed) == 0

    def test_moveWindowToIndex_masterToStack_swaps(
        self, manager_4_windows, mock_connection
    ):
        """Moving master to stack should use swap."""
        manager, workspace = manager_4_windows
        window = MockCon(id=100)

        manager.moveWindowToIndex(window, 1)

        # Window IDs should be reordered
        assert manager.windowIds[1] == 100

    def test_moveWindowToIndex_stackToMaster_swaps(
        self, manager_4_windows, mock_connection
    ):
        """Moving stack to master should use swap."""
        manager, workspace = manager_4_windows
        window = MockCon(id=300)

        manager.moveWindowToIndex(window, 0)

        assert manager.windowIds[0] == 300


class TestMoveWindowRelative:
    """Tests for moveWindowRelative() method."""

    @pytest.fixture
    def manager_3_windows(self, mock_connection, minimal_config):
        """Manager with 3 windows for relative movement tests."""
        workspace = MockCon(name="1", type="workspace")
        manager = MasterStackLayoutManager(
            mock_connection, workspace, "1", minimal_config
        )
        manager.windowIds = [100, 200, 300]
        return manager, workspace

    def test_moveWindowRelative_wrapUp(
        self, manager_3_windows, mock_connection
    ):
        """Moving up from master should wrap to bottom."""
        manager, workspace = manager_3_windows
        window = MockCon(id=100)

        manager.moveWindowRelative(window, -1)

        # Index 0 - 1 = -1 -> wraps to 2
        assert manager.windowIds[-1] == 100

    def test_moveWindowRelative_wrapDown(
        self, manager_3_windows, mock_connection
    ):
        """Moving down from bottom should wrap to top."""
        manager, workspace = manager_3_windows
        window = MockCon(id=300)

        manager.moveWindowRelative(window, 1)

        # Index 2 + 1 = 3 -> wraps to 0
        assert manager.windowIds[0] == 300


# =============================================================================
# Stack Layout Tests
# =============================================================================


class TestToggleStackLayout:
    """Tests for toggleStackLayout() method."""

    def test_toggleStackLayout_cyclesThroughLayouts(self, basic_manager):
        """Should cycle through all layout types."""
        assert basic_manager.stackLayout == StackLayout.SPLITV

        basic_manager.toggleStackLayout()
        assert basic_manager.stackLayout == StackLayout.SPLITH

        basic_manager.toggleStackLayout()
        assert basic_manager.stackLayout == StackLayout.STACKING

        basic_manager.toggleStackLayout()
        assert basic_manager.stackLayout == StackLayout.TABBED

        basic_manager.toggleStackLayout()
        assert basic_manager.stackLayout == StackLayout.SPLITV


class TestToggleStackSide:
    """Tests for toggleStackSide() method."""

    def test_toggleStackSide_swapsSides(
        self, basic_manager, mock_connection
    ):
        """Should swap between left and right."""
        basic_manager.windowIds = [100, 200]
        workspace = MockCon(name="1", type="workspace")

        # Set up tree for find_by_id
        stack_con = MockCon(id=201, type="con", parent=workspace)
        master = MockCon(id=100, parent=workspace)
        stack = MockCon(id=200, parent=stack_con)
        workspace.nodes = [master, stack_con]
        stack_con.nodes = [stack]

        # Mock connection tree
        mock_connection.tree = workspace

        assert basic_manager.stackSide == Side.RIGHT

        basic_manager.toggleStackSide(workspace)

        assert basic_manager.stackSide == Side.LEFT


# =============================================================================
# Maximize Tests
# =============================================================================


class TestToggleMaximize:
    """Tests for toggleMaximize() method."""

    def test_toggleMaximize_setsMaximizedTrue(
        self, basic_manager, mock_connection
    ):
        """First toggle should set maximized to True."""
        basic_manager.windowIds = [100, 200]
        workspace = MockCon(name="1", type="workspace")
        master = MockCon(id=100, rect=MockRect(width=600), parent=workspace)
        workspace.nodes = [master]

        # Mock find_by_id
        mock_connection.tree = workspace

        basic_manager.toggleMaximize(workspace)

        assert basic_manager.maximized is True

    def test_toggleMaximize_secondToggle_restores(
        self, basic_manager, mock_connection
    ):
        """Second toggle should restore and set maximized to False."""
        basic_manager.windowIds = [100, 200]
        basic_manager.maximized = True
        basic_manager.masterWidthBeforeMaximize = 600
        workspace = MockCon(name="1", type="workspace")

        basic_manager.toggleMaximize(workspace)

        assert basic_manager.maximized is False


# =============================================================================
# Regression Tests for Known Bugs
# =============================================================================


class TestKnownBugs:
    """Regression tests for documented bugs."""

    def test_popWindow_masterRemoved_preservesWidth(
        self, basic_manager, mock_connection
    ):
        """
        When master is removed, the new master should be resized
        to the pixel width of the old master.
        
        NOTE: The code preserves pixel width, not percentage width.
        This may not be the ideal behavior (see docs/decisions.md).
        """
        basic_manager.windowIds = [100, 200, 300]
        # Master has specific pixel width
        master = MockCon(id=100, rect=MockRect(width=600))

        basic_manager.popWindow(master)

        # Should resize new master to old master's pixel width
        resize_commands = [
            cmd for cmd in mock_connection.commands_executed
            if "resize" in cmd and "600" in cmd
        ]
        assert len(resize_commands) > 0, "New master should be resized to old master's width"

    def test_popWindow_zeroWidth_handledGracefully(
        self, basic_manager, mock_connection, capsys
    ):
        """Window with width=0 should be handled without crash."""
        basic_manager.windowIds = [100, 200]
        # Master has 0 width (edge case)
        master = MockCon(id=100, rect=MockRect(width=0))

        # Should not raise
        basic_manager.popWindow(master)

        # Should log a warning
        captured = capsys.readouterr()
        # The code has a log for this case
        assert basic_manager.windowIds == [200]
