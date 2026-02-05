"""
Unit tests for layman.managers.autotiling module.

Tests the AutotilingLayoutManager for:
- Window exclusion logic
- Split direction switching
- Depth limit handling
- Event handler behavior
"""

import pytest

from layman.managers.autotiling import AutotilingLayoutManager, KEY_DEPTH_LIMIT
from tests.mocks.i3ipc_mocks import (
    MockConnection,
    MockCon,
    MockRect,
    MockWindowEvent,
)


class TestAutotilingIsExcluded:
    """Tests for AutotilingLayoutManager.isExcluded() method."""

    @pytest.fixture
    def manager(self, mock_connection, minimal_config):
        """Create a basic AutotilingLayoutManager."""
        workspace = MockCon(name="1", type="workspace")
        return AutotilingLayoutManager(
            mock_connection, workspace, "1", minimal_config
        )

    def test_isExcluded_noneWindow_returnsTrue(self, manager):
        """None window should be excluded."""
        assert manager.isExcluded(None) is True

    def test_isExcluded_nonConType_returnsTrue(self, manager):
        """Windows with type != 'con' should be excluded."""
        window = MockCon(id=1, type="workspace")
        assert manager.isExcluded(window) is True

        window = MockCon(id=2, type="floating_con")
        assert manager.isExcluded(window) is True

    def test_isExcluded_noWorkspace_returnsTrue(self, manager):
        """Windows without a workspace should be excluded."""
        # Window with no parent (can't find workspace)
        window = MockCon(id=1, type="con")
        assert manager.isExcluded(window) is True

    def test_isExcluded_floatingWindow_returnsTrue(self, manager):
        """Floating windows should be excluded."""
        workspace = MockCon(name="1", type="workspace")
        window = MockCon(id=1, type="con", floating="auto_on", parent=workspace)
        assert manager.isExcluded(window) is True

        window = MockCon(id=2, type="con", floating="user_on", parent=workspace)
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


class TestAutotilingSwitchSplit:
    """Tests for AutotilingLayoutManager.switchSplit() method."""

    @pytest.fixture
    def manager(self, mock_connection, minimal_config):
        """Create a basic AutotilingLayoutManager."""
        workspace = MockCon(name="1", type="workspace")
        return AutotilingLayoutManager(
            mock_connection, workspace, "1", minimal_config
        )

    def test_switchSplit_tallWindow_usesSplitv(self, manager, mock_connection):
        """Windows taller than wide should trigger splitv."""
        workspace = MockCon(name="1", type="workspace")
        container = MockCon(id=1, layout="splith", parent=workspace)
        window = MockCon(
            id=100,
            type="con",
            rect=MockRect(width=400, height=800),  # Tall
            parent=container,
        )

        manager.switchSplit(window)

        assert any("splitv" in cmd for cmd in mock_connection.commands_executed)

    def test_switchSplit_wideWindow_usesSplith(self, manager, mock_connection):
        """Windows wider than tall should trigger splith."""
        workspace = MockCon(name="1", type="workspace")
        container = MockCon(id=1, layout="splitv", parent=workspace)
        window = MockCon(
            id=100,
            type="con",
            rect=MockRect(width=800, height=400),  # Wide
            parent=container,
        )

        manager.switchSplit(window)

        assert any("splith" in cmd for cmd in mock_connection.commands_executed)

    def test_switchSplit_squareWindow_usesSplith(self, manager, mock_connection):
        """Square windows should trigger splith (width == height)."""
        workspace = MockCon(name="1", type="workspace")
        container = MockCon(id=1, layout="splitv", parent=workspace)
        window = MockCon(
            id=100,
            type="con",
            rect=MockRect(width=600, height=600),  # Square
            parent=container,
        )

        manager.switchSplit(window)

        assert any("splith" in cmd for cmd in mock_connection.commands_executed)

    def test_switchSplit_excludedWindow_noCommand(self, manager, mock_connection):
        """Excluded windows should not trigger any command."""
        window = MockCon(id=100, type="con")  # No parent, will be excluded

        manager.switchSplit(window)

        assert len(mock_connection.commands_executed) == 0

    def test_switchSplit_sameLayout_skipsCommand(self, manager, mock_connection):
        """Should skip command if layout already matches."""
        workspace = MockCon(name="1", type="workspace")
        container = MockCon(id=1, layout="splith", parent=workspace)
        window = MockCon(
            id=100,
            type="con",
            rect=MockRect(width=800, height=400),  # Wide -> splith
            parent=container,
        )

        manager.switchSplit(window)

        # No command should be executed since layout already matches
        assert len(mock_connection.commands_executed) == 0


class TestAutotilingDepthLimit:
    """Tests for depth limit functionality."""

    def test_depthLimit_zero_noLimit(self, mock_connection, temp_config):
        """depthLimit of 0 should not limit depth."""
        config = temp_config(
            """
[layman]
depthLimit = 0
"""
        )
        workspace = MockCon(name="1", type="workspace")
        manager = AutotilingLayoutManager(mock_connection, workspace, "1", config)

        # Create deeply nested structure
        current = workspace
        for i in range(10):
            child = MockCon(id=100 + i, type="con", parent=current, nodes=[])
            current.nodes = [child]
            current = child

        # Last window should still trigger split
        window = MockCon(
            id=200,
            type="con",
            rect=MockRect(width=400, height=800),
            parent=current,
        )

        manager.switchSplit(window)

        assert len(mock_connection.commands_executed) > 0

    def test_depthLimit_readsFromConfig(self, mock_connection, temp_config):
        """depthLimit should be read from config."""
        config = temp_config(
            """
[layman]
depthLimit = 3
"""
        )
        workspace = MockCon(name="1", type="workspace")
        manager = AutotilingLayoutManager(mock_connection, workspace, "1", config)

        assert manager.depthLimit == 3


class TestAutotilingEventHandlers:
    """Tests for event handler methods."""

    @pytest.fixture
    def manager(self, mock_connection, minimal_config):
        """Create a basic AutotilingLayoutManager."""
        workspace = MockCon(name="1", type="workspace")
        return AutotilingLayoutManager(
            mock_connection, workspace, "1", minimal_config
        )

    def test_windowAdded_callsSwitchSplit(self, manager, mock_connection):
        """windowAdded should call switchSplit on the window."""
        workspace = MockCon(name="1", type="workspace")
        container = MockCon(id=1, layout="splith", parent=workspace)
        window = MockCon(
            id=100,
            type="con",
            rect=MockRect(width=400, height=800),
            parent=container,
        )
        event = MockWindowEvent(change="new", container=window)

        manager.windowAdded(event, workspace, window)

        assert len(mock_connection.commands_executed) > 0

    def test_windowFocused_callsSwitchSplit(self, manager, mock_connection):
        """windowFocused should call switchSplit on the window."""
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

    def test_windowMoved_callsSwitchSplit(self, manager, mock_connection):
        """windowMoved should call switchSplit on the window."""
        workspace = MockCon(name="1", type="workspace")
        container = MockCon(id=1, layout="splith", parent=workspace)
        window = MockCon(
            id=100,
            type="con",
            rect=MockRect(width=400, height=800),
            parent=container,
        )
        event = MockWindowEvent(change="move", container=window)

        manager.windowMoved(event, workspace, window)

        assert len(mock_connection.commands_executed) > 0
