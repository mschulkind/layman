"""
Unit tests for layman.managers.workspace module.

Tests the WorkspaceLayoutManager base class for:
- Initialization
- Command execution
- Default method implementations
- Logging functionality
"""

import logging

import pytest
from unittest.mock import Mock, patch

from layman.managers.workspace import WorkspaceLayoutManager
from tests.mocks.i3ipc_mocks import MockConnection, MockCon, MockWindowEvent


class TestWorkspaceLayoutManagerInit:
    """Tests for WorkspaceLayoutManager initialization."""

    def test_init_setsConnectionAndWorkspaceName(self, mock_connection, minimal_config):
        """Constructor should set con and workspaceName."""
        workspace = MockCon(name="1", type="workspace")

        manager = WorkspaceLayoutManager(
            mock_connection, workspace, "1", minimal_config
        )

        assert manager.con == mock_connection
        assert manager.workspaceName == "1"

    def test_init_nullWorkspace_stillWorks(self, mock_connection, minimal_config):
        """Should initialize even with None workspace."""
        manager = WorkspaceLayoutManager(
            mock_connection, None, "test", minimal_config
        )

        assert manager.workspaceName == "test"

    def test_init_hasLogger(self, mock_connection, valid_config):
        """Should set up a logger attribute."""
        workspace = MockCon(name="1", type="workspace")

        manager = WorkspaceLayoutManager(
            mock_connection, workspace, "1", valid_config
        )

        assert hasattr(manager, "logger")
        assert "1" in manager.logger.name

    def test_init_loggerPerWorkspace(self, mock_connection, minimal_config):
        """Different workspaces should get different loggers."""
        m1 = WorkspaceLayoutManager(mock_connection, None, "1", minimal_config)
        m2 = WorkspaceLayoutManager(mock_connection, None, "2", minimal_config)

        assert m1.logger.name != m2.logger.name
        assert "1" in m1.logger.name
        assert "2" in m2.logger.name


class TestWorkspaceLayoutManagerClassAttributes:
    """Tests for class-level attributes."""

    def test_shortName_isNone(self):
        """Default shortName should be 'none'."""
        assert WorkspaceLayoutManager.shortName == "none"

    def test_overridesMoveBinds_isFalse(self):
        """Default overridesMoveBinds should be False."""
        assert WorkspaceLayoutManager.overridesMoveBinds is False

    def test_overridesFocusBinds_isFalse(self):
        """Default overridesFocusBinds should be False."""
        assert WorkspaceLayoutManager.overridesFocusBinds is False

    def test_supportsFloating_isFalse(self):
        """Default supportsFloating should be False."""
        assert WorkspaceLayoutManager.supportsFloating is False


class TestWorkspaceLayoutManagerCommand:
    """Tests for WorkspaceLayoutManager.command() method."""

    def test_command_executesViaConnection(self, mock_connection, minimal_config):
        """command() should execute via the i3ipc connection."""
        manager = WorkspaceLayoutManager(mock_connection, None, "1", minimal_config)

        manager.command("focus left")

        assert "focus left" in mock_connection.commands_executed

    def test_command_multipleCommands_allExecuted(
        self, mock_connection, minimal_config
    ):
        """Multiple commands should all be executed."""
        manager = WorkspaceLayoutManager(mock_connection, None, "1", minimal_config)

        manager.command("focus left")
        manager.command("focus right")
        manager.command("split h")

        assert len(mock_connection.commands_executed) == 3
        assert "focus left" in mock_connection.commands_executed
        assert "focus right" in mock_connection.commands_executed
        assert "split h" in mock_connection.commands_executed


class TestWorkspaceLayoutManagerEventHandlers:
    """Tests for default event handler implementations."""

    def test_windowAdded_doesNothing(self, mock_connection, minimal_config):
        """Default windowAdded should be a no-op."""
        manager = WorkspaceLayoutManager(mock_connection, None, "1", minimal_config)
        event = MockWindowEvent()
        workspace = MockCon(name="1", type="workspace")
        window = MockCon(id=100)

        # Should not raise
        manager.windowAdded(event, workspace, window)

        # No commands should be executed
        assert len(mock_connection.commands_executed) == 0

    def test_windowRemoved_doesNothing(self, mock_connection, minimal_config):
        """Default windowRemoved should be a no-op."""
        manager = WorkspaceLayoutManager(mock_connection, None, "1", minimal_config)
        event = MockWindowEvent()
        workspace = MockCon(name="1", type="workspace")
        window = MockCon(id=100)

        manager.windowRemoved(event, workspace, window)

        assert len(mock_connection.commands_executed) == 0

    def test_windowFocused_doesNothing(self, mock_connection, minimal_config):
        """Default windowFocused should be a no-op."""
        manager = WorkspaceLayoutManager(mock_connection, None, "1", minimal_config)
        event = MockWindowEvent()
        workspace = MockCon(name="1", type="workspace")
        window = MockCon(id=100)

        manager.windowFocused(event, workspace, window)

        assert len(mock_connection.commands_executed) == 0

    def test_windowMoved_doesNothing(self, mock_connection, minimal_config):
        """Default windowMoved should be a no-op."""
        manager = WorkspaceLayoutManager(mock_connection, None, "1", minimal_config)
        event = MockWindowEvent()
        workspace = MockCon(name="1", type="workspace")
        window = MockCon(id=100)

        manager.windowMoved(event, workspace, window)

        assert len(mock_connection.commands_executed) == 0

    def test_windowFloating_doesNothing(self, mock_connection, minimal_config):
        """Default windowFloating should be a no-op."""
        manager = WorkspaceLayoutManager(mock_connection, None, "1", minimal_config)
        event = MockWindowEvent()
        workspace = MockCon(name="1", type="workspace")
        window = MockCon(id=100)

        manager.windowFloating(event, workspace, window)

        assert len(mock_connection.commands_executed) == 0

    def test_onCommand_doesNothing(self, mock_connection, minimal_config):
        """Default onCommand should be a no-op."""
        manager = WorkspaceLayoutManager(mock_connection, None, "1", minimal_config)
        workspace = MockCon(name="1", type="workspace")

        manager.onCommand("some command", workspace)

        assert len(mock_connection.commands_executed) == 0


class TestWorkspaceLayoutManagerLogging:
    """Tests for logging methods."""

    def test_log_emitsDebugMessage(self, mock_connection, valid_config, caplog):
        """log() should emit a DEBUG level message."""
        manager = WorkspaceLayoutManager(mock_connection, None, "1", valid_config)

        with caplog.at_level(logging.DEBUG, logger=manager.logger.name):
            manager.log("test message")

        assert "test message" in caplog.text

    def test_log_belowLevel_suppressed(self, mock_connection, minimal_config, caplog):
        """log() messages should be suppressed when logger level is above DEBUG."""
        manager = WorkspaceLayoutManager(mock_connection, None, "1", minimal_config)
        manager.logger.setLevel(logging.WARNING)

        with caplog.at_level(logging.WARNING, logger=manager.logger.name):
            manager.log("test message")

        assert "test message" not in caplog.text

    def test_logError_emitsErrorMessage(self, mock_connection, minimal_config, caplog):
        """logError() should emit an ERROR level message."""
        manager = WorkspaceLayoutManager(mock_connection, None, "1", minimal_config)

        with caplog.at_level(logging.DEBUG, logger=manager.logger.name):
            manager.logError("error message")

        assert "error message" in caplog.text
        assert any(r.levelno == logging.ERROR for r in caplog.records)

    def test_logCaller_emitsDebugMessage(self, mock_connection, valid_config, caplog):
        """logCaller() should emit a DEBUG level message."""
        manager = WorkspaceLayoutManager(mock_connection, None, "1", valid_config)

        with caplog.at_level(logging.DEBUG, logger=manager.logger.name):
            manager.logCaller("caller message")

        assert "caller message" in caplog.text


class TestIsExcluded:
    """Tests for isExcluded() method on the base class.

    This method was extracted from Autotiling and Grid layout managers
    where it was duplicated identically.
    """

    @pytest.fixture
    def manager(self, mock_connection, minimal_config):
        return WorkspaceLayoutManager(mock_connection, None, "1", minimal_config)

    def test_isExcluded_noneWindow_returnsTrue(self, manager):
        """None window should be excluded."""
        assert manager.isExcluded(None) is True

    def test_isExcluded_nonConType_returnsTrue(self, manager):
        """Non-con types (e.g., workspace) should be excluded."""
        window = MockCon(type="workspace")
        assert manager.isExcluded(window) is True

    def test_isExcluded_noWorkspace_returnsTrue(self, manager):
        """Window with no workspace parent should be excluded."""
        window = MockCon(type="con")
        # window.workspace() returns None since no parent is a workspace
        assert manager.isExcluded(window) is True

    def test_isExcluded_floatingWindow_returnsTrue(self, manager):
        """Floating windows should be excluded."""
        workspace = MockCon(name="1", type="workspace")
        window = MockCon(type="con", floating="auto_on", parent=workspace)
        assert manager.isExcluded(window) is True

    def test_isExcluded_fullscreenWindow_returnsTrue(self, manager):
        """Fullscreen windows should be excluded."""
        workspace = MockCon(name="1", type="workspace")
        window = MockCon(type="con", fullscreen_mode=1, parent=workspace)
        assert manager.isExcluded(window) is True

    def test_isExcluded_stackedParent_returnsTrue(self, manager):
        """Windows in a stacked parent should be excluded."""
        workspace = MockCon(name="1", type="workspace")
        parent = MockCon(type="con", layout="stacked", parent=workspace)
        window = MockCon(type="con", parent=parent)
        assert manager.isExcluded(window) is True

    def test_isExcluded_tabbedParent_returnsTrue(self, manager):
        """Windows in a tabbed parent should be excluded."""
        workspace = MockCon(name="1", type="workspace")
        parent = MockCon(type="con", layout="tabbed", parent=workspace)
        window = MockCon(type="con", parent=parent)
        assert manager.isExcluded(window) is True

    def test_isExcluded_normalWindow_returnsFalse(self, manager):
        """Normal tiled window should not be excluded."""
        workspace = MockCon(name="1", type="workspace")
        window = MockCon(type="con", parent=workspace)
        assert manager.isExcluded(window) is False
