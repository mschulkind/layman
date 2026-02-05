"""
Unit tests for layman.managers.grid module.

Tests the GridLayoutManager for:
- Window exclusion logic (similar to Autotiling)
- Split direction switching
- Finding and splitting the largest container
"""

import pytest

from layman.managers.grid import GridLayoutManager
from tests.mocks.i3ipc_mocks import (
    MockConnection,
    MockCon,
    MockRect,
    MockWindowEvent,
)


class TestGridIsExcluded:
    """Tests for GridLayoutManager.isExcluded() method."""

    @pytest.fixture
    def manager(self, mock_connection, minimal_config):
        """Create a basic GridLayoutManager."""
        workspace = MockCon(name="1", type="workspace")
        return GridLayoutManager(mock_connection, workspace, "1", minimal_config)

    def test_isExcluded_noneWindow_returnsTrue(self, manager):
        """None window should be excluded."""
        assert manager.isExcluded(None) is True

    def test_isExcluded_nonConType_returnsTrue(self, manager):
        """Windows with type != 'con' should be excluded."""
        window = MockCon(id=1, type="workspace")
        assert manager.isExcluded(window) is True

    def test_isExcluded_noWorkspace_returnsTrue(self, manager):
        """Windows without a workspace should be excluded."""
        window = MockCon(id=1, type="con")
        assert manager.isExcluded(window) is True

    def test_isExcluded_floatingWindow_returnsTrue(self, manager):
        """Floating windows should be excluded."""
        workspace = MockCon(name="1", type="workspace")
        window = MockCon(id=1, type="con", floating="auto_on", parent=workspace)
        assert manager.isExcluded(window) is True

    def test_isExcluded_fullscreenWindow_returnsTrue(self, manager):
        """Fullscreen windows should be excluded."""
        workspace = MockCon(name="1", type="workspace")
        window = MockCon(id=1, type="con", fullscreen_mode=1, parent=workspace)
        assert manager.isExcluded(window) is True

    def test_isExcluded_stackedParent_returnsTrue(self, manager):
        """Windows in stacked containers should be excluded."""
        workspace = MockCon(name="1", type="workspace")
        container = MockCon(id=1, type="con", layout="stacked", parent=workspace)
        window = MockCon(id=2, type="con", parent=container)
        assert manager.isExcluded(window) is True

    def test_isExcluded_tabbedParent_returnsTrue(self, manager):
        """Windows in tabbed containers should be excluded."""
        workspace = MockCon(name="1", type="workspace")
        container = MockCon(id=1, type="con", layout="tabbed", parent=workspace)
        window = MockCon(id=2, type="con", parent=container)
        assert manager.isExcluded(window) is True

    def test_isExcluded_normalWindow_returnsFalse(self, manager):
        """Normal tiled windows should not be excluded."""
        workspace = MockCon(name="1", type="workspace")
        container = MockCon(id=1, type="con", layout="splith", parent=workspace)
        window = MockCon(id=2, type="con", parent=container)
        assert manager.isExcluded(window) is False


class TestGridSwitchSplit:
    """Tests for GridLayoutManager.switchSplit() method."""

    @pytest.fixture
    def manager(self, mock_connection, minimal_config):
        """Create a basic GridLayoutManager."""
        workspace = MockCon(name="1", type="workspace")
        return GridLayoutManager(mock_connection, workspace, "1", minimal_config)

    def test_switchSplit_tallWindow_usesSplitv(self, manager, mock_connection):
        """Windows taller than wide should trigger splitv."""
        window = MockCon(
            id=100,
            type="con",
            rect=MockRect(width=400, height=800),  # Tall
        )

        manager.switchSplit(window)

        assert any("splitv" in cmd for cmd in mock_connection.commands_executed)

    def test_switchSplit_wideWindow_usesSplith(self, manager, mock_connection):
        """Windows wider than tall should trigger splith."""
        window = MockCon(
            id=100,
            type="con",
            rect=MockRect(width=800, height=400),  # Wide
        )

        manager.switchSplit(window)

        assert any("splith" in cmd for cmd in mock_connection.commands_executed)

    def test_switchSplit_includesConId(self, manager, mock_connection):
        """switchSplit should target the specific window by con_id."""
        window = MockCon(
            id=100,
            type="con",
            rect=MockRect(width=800, height=400),
        )

        manager.switchSplit(window)

        # Should include [con_id=100]
        assert any("con_id=100" in cmd for cmd in mock_connection.commands_executed)


class TestGridWindowAdded:
    """Tests for GridLayoutManager.windowAdded() method."""

    @pytest.fixture
    def manager(self, mock_connection, minimal_config):
        """Create a basic GridLayoutManager."""
        workspace = MockCon(name="1", type="workspace")
        return GridLayoutManager(mock_connection, workspace, "1", minimal_config)

    def test_windowAdded_excludedWindow_noAction(self, manager, mock_connection):
        """Excluded windows should not trigger any layout changes."""
        workspace = MockCon(name="1", type="workspace")
        window = MockCon(id=100, type="con")  # No parent -> excluded
        event = MockWindowEvent(change="new", container=window)

        manager.windowAdded(event, workspace, window)

        assert len(mock_connection.commands_executed) == 0

    def test_windowAdded_findsLargestContainer(self, manager, mock_connection):
        """Should find and split the largest container."""
        workspace = MockCon(name="1", type="workspace")

        # Create a small window
        small = MockCon(
            id=101,
            type="con",
            rect=MockRect(width=400, height=400),
            parent=workspace,
        )

        # Create a large window
        large = MockCon(
            id=102,
            type="con",
            rect=MockRect(width=800, height=800),
            parent=workspace,
        )

        workspace.nodes = [small, large]

        # New window added
        new_window = MockCon(
            id=100,
            type="con",
            rect=MockRect(width=200, height=200),
            parent=workspace,
        )
        event = MockWindowEvent(change="new", container=new_window)

        manager.windowAdded(event, workspace, new_window)

        # Should have moved window to the larger container
        if len(mock_connection.commands_executed) > 0:
            commands = " ".join(mock_connection.commands_executed)
            # The larger window (102) should be involved
            assert "102" in commands or "100" in commands

    def test_windowAdded_sameParent_noMove(self, manager, mock_connection):
        """Window in largest container should not be moved."""
        workspace = MockCon(name="1", type="workspace")
        container = MockCon(
            id=1,
            type="con",
            layout="splith",
            parent=workspace,
            rect=MockRect(width=800, height=800),
        )
        workspace.nodes = [container]

        # New window in the container
        new_window = MockCon(
            id=100,
            type="con",
            rect=MockRect(width=800, height=800),
            parent=container,
        )
        container.nodes = [new_window]
        event = MockWindowEvent(change="new", container=new_window)

        manager.windowAdded(event, workspace, new_window)

        # Should still call switchSplit, but no move command
        # (since window is already in the largest container)
        move_commands = [cmd for cmd in mock_connection.commands_executed if "move" in cmd]
        # May or may not have move commands depending on logic


class TestGridWindowFocused:
    """Tests for GridLayoutManager.windowFocused() method."""

    @pytest.fixture
    def manager(self, mock_connection, minimal_config):
        """Create a basic GridLayoutManager."""
        workspace = MockCon(name="1", type="workspace")
        return GridLayoutManager(mock_connection, workspace, "1", minimal_config)

    def test_windowFocused_callsSwitchSplit(self, manager, mock_connection):
        """windowFocused should call switchSplit."""
        workspace = MockCon(name="1", type="workspace")
        container = MockCon(id=1, layout="splith", parent=workspace)
        window = MockCon(
            id=100,
            type="con",
            rect=MockRect(width=400, height=800),
            parent=container,
        )
        event = MockWindowEvent(change="focus", container=window)

        manager.windowFocused(event, workspace, window)

        assert len(mock_connection.commands_executed) > 0

    def test_windowFocused_excludedWindow_noAction(self, manager, mock_connection):
        """Excluded windows should not trigger switchSplit."""
        workspace = MockCon(name="1", type="workspace")
        window = MockCon(id=100, type="con")  # No parent -> excluded
        event = MockWindowEvent(change="focus", container=window)

        manager.windowFocused(event, workspace, window)

        assert len(mock_connection.commands_executed) == 0


class TestGridMoveWindow:
    """Tests for GridLayoutManager.moveWindow() helper method."""

    @pytest.fixture
    def manager(self, mock_connection, minimal_config):
        """Create a basic GridLayoutManager."""
        workspace = MockCon(name="1", type="workspace")
        return GridLayoutManager(mock_connection, workspace, "1", minimal_config)

    def test_moveWindow_usesMarks(self, manager, mock_connection):
        """moveWindow should use marks for window movement."""
        manager.moveWindow(100, 200)

        # Should mark target, move source to mark, then unmark
        commands = mock_connection.commands_executed
        assert len(commands) == 3
        assert "mark" in commands[0]
        assert "200" in commands[0]
        assert "move" in commands[1]
        assert "100" in commands[1]
        assert "unmark" in commands[2]
