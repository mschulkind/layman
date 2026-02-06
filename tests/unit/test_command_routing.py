"""
Tests for Proposal B command routing in Layman.handleCommand().

Verifies that the new command structure routes correctly:
- 'window <cmd>' → strips prefix, passes to layout manager
- 'stack <cmd>' → strips prefix, passes to layout manager
- 'layout set <name>' → sets workspace layout
- 'layout maximize' → passes 'maximize' to layout manager
- 'reload' → reloads config
- Backwards compat: bare 'move/focus' still works
"""

import logging
from unittest.mock import Mock, patch, MagicMock

import pytest

from layman.layman import Layman, WorkspaceState
from layman.config import LaymanConfig
from tests.mocks.i3ipc_mocks import MockConnection, MockCon, MockBindingEvent


@pytest.fixture
def minimal_config(tmp_path):
    config_path = tmp_path / "config.toml"
    config_path.write_text('[layman]\ndefaultLayout = "MasterStack"\n')
    return LaymanConfig(str(config_path))


@pytest.fixture
def layman_instance(minimal_config):
    """Create a Layman instance with mocked connection."""
    with patch("layman.utils.getConfigPath", return_value="/dev/null"):
        instance = Layman.__new__(Layman)
        instance.options = minimal_config
        instance.builtinLayouts = {}
        instance.userLayouts = {}
        instance.workspaceStates = {}
        instance.conn = MockConnection()
        return instance


def setup_workspace_with_manager(layman_instance, workspace_name="1"):
    """Set up a workspace with a mock layout manager on the Layman instance."""
    workspace = MockCon(name=workspace_name, type="workspace")
    manager = Mock()
    manager.overridesMoveBinds = True
    manager.overridesFocusBinds = True
    manager.supportsFloating = False

    state = WorkspaceState(
        windowIds={100, 200, 300},
        layoutManager=manager,
    )
    layman_instance.workspaceStates[workspace_name] = state

    # Mock findFocusedWorkspace to return our workspace
    return workspace, manager, state


class TestWindowCommandRouting:
    """Tests for 'window <cmd>' prefix routing."""

    def test_windowMoveUp_routesToManager(self, layman_instance):
        """'window move up' should pass 'move up' to the layout manager."""
        workspace, manager, _ = setup_workspace_with_manager(layman_instance)

        with patch("layman.utils.findFocusedWorkspace", return_value=workspace):
            layman_instance.handleCommand("window move up")

        manager.onCommand.assert_called_once_with("move up", workspace)

    def test_windowFocusDown_routesToManager(self, layman_instance):
        """'window focus down' should pass 'focus down' to the layout manager."""
        workspace, manager, _ = setup_workspace_with_manager(layman_instance)

        with patch("layman.utils.findFocusedWorkspace", return_value=workspace):
            layman_instance.handleCommand("window focus down")

        manager.onCommand.assert_called_once_with("focus down", workspace)

    def test_windowSwapMaster_routesToManager(self, layman_instance):
        """'window swap master' should pass 'swap master' to the manager."""
        workspace, manager, _ = setup_workspace_with_manager(layman_instance)

        with patch("layman.utils.findFocusedWorkspace", return_value=workspace):
            layman_instance.handleCommand("window swap master")

        manager.onCommand.assert_called_once_with("swap master", workspace)

    def test_windowRotateCw_routesToManager(self, layman_instance):
        """'window rotate cw' should pass 'rotate cw' to the manager."""
        workspace, manager, _ = setup_workspace_with_manager(layman_instance)

        with patch("layman.utils.findFocusedWorkspace", return_value=workspace):
            layman_instance.handleCommand("window rotate cw")

        manager.onCommand.assert_called_once_with("rotate cw", workspace)

    def test_windowMoveToIndex_routesToManager(self, layman_instance):
        """'window move to index 2' should pass 'move to index 2' to the manager."""
        workspace, manager, _ = setup_workspace_with_manager(layman_instance)

        with patch("layman.utils.findFocusedWorkspace", return_value=workspace):
            layman_instance.handleCommand("window move to index 2")

        manager.onCommand.assert_called_once_with("move to index 2", workspace)

    def test_windowMove_noManager_passesToSway(self, layman_instance):
        """'window move up' with no overriding manager should pass to Sway."""
        workspace, manager, state = setup_workspace_with_manager(layman_instance)
        manager.overridesMoveBinds = False

        with patch("layman.utils.findFocusedWorkspace", return_value=workspace):
            layman_instance.handleCommand("window move up")

        # Should have passed 'move up' to Sway, not to manager
        manager.onCommand.assert_not_called()
        assert "move up" in layman_instance.conn.commands_executed


class TestStackCommandRouting:
    """Tests for 'stack <cmd>' prefix routing."""

    def test_stackToggle_routesToManager(self, layman_instance):
        """'stack toggle' should pass 'stack toggle' to the manager."""
        workspace, manager, _ = setup_workspace_with_manager(layman_instance)

        with patch("layman.utils.findFocusedWorkspace", return_value=workspace):
            layman_instance.handleCommand("stack toggle")

        manager.onCommand.assert_called_once_with("toggle", workspace)

    def test_stackSideToggle_routesToManager(self, layman_instance):
        """'stack side toggle' should pass 'side toggle' to the manager."""
        workspace, manager, _ = setup_workspace_with_manager(layman_instance)

        with patch("layman.utils.findFocusedWorkspace", return_value=workspace):
            layman_instance.handleCommand("stack side toggle")

        manager.onCommand.assert_called_once_with("side toggle", workspace)


class TestLayoutCommandRouting:
    """Tests for 'layout set' and 'layout maximize' routing."""

    def test_layoutSetMasterStack(self, layman_instance):
        """'layout set MasterStack' should call setWorkspaceLayout."""
        workspace, manager, _ = setup_workspace_with_manager(layman_instance)

        with (
            patch("layman.utils.findFocusedWorkspace", return_value=workspace),
            patch.object(layman_instance, "setWorkspaceLayout") as mock_set,
        ):
            layman_instance.handleCommand("layout set MasterStack")

        mock_set.assert_called_once_with(workspace, "1", "MasterStack")

    def test_layoutMaximize_routesToManager(self, layman_instance):
        """'layout maximize' should toggle fake fullscreen via the layout manager."""
        workspace, manager, _ = setup_workspace_with_manager(layman_instance)
        focused_window = MockCon(id=100, name="focused", focused=True)

        with (
            patch("layman.utils.findFocusedWorkspace", return_value=workspace),
            patch("layman.utils.findFocusedWindow", return_value=focused_window),
        ):
            layman_instance.handleCommand("layout maximize")

        manager.onCommand.assert_called_once_with("maximize", workspace)


class TestReloadCommand:
    """Tests for 'reload' command."""

    def test_reload_reloadsConfig(self, layman_instance, tmp_path):
        """'reload' should reload the config."""
        config_path = tmp_path / "config.toml"
        config_path.write_text('[layman]\ndefaultLayout = "none"\n')

        with (
            patch("layman.utils.getConfigPath", return_value=str(config_path)),
            patch.object(layman_instance, "fetchUserLayouts"),
        ):
            layman_instance.handleCommand("reload")

        # Should not crash


class TestBackwardsCompatibility:
    """Tests for bare move/focus commands (old style)."""

    def test_bareMoveUp_stillWorks(self, layman_instance):
        """Bare 'move up' should still route to manager (backwards compat)."""
        workspace, manager, _ = setup_workspace_with_manager(layman_instance)

        with patch("layman.utils.findFocusedWorkspace", return_value=workspace):
            layman_instance.handleCommand("move up")

        manager.onCommand.assert_called_once_with("move up", workspace)

    def test_bareFocusDown_stillWorks(self, layman_instance):
        """Bare 'focus down' should still route to manager (backwards compat)."""
        workspace, manager, _ = setup_workspace_with_manager(layman_instance)

        with patch("layman.utils.findFocusedWorkspace", return_value=workspace):
            layman_instance.handleCommand("focus down")

        manager.onCommand.assert_called_once_with("focus down", workspace)

    def test_bareMaximize_stillWorks(self, layman_instance):
        """Bare 'maximize' should still route to manager (backwards compat)."""
        workspace, manager, _ = setup_workspace_with_manager(layman_instance)

        with patch("layman.utils.findFocusedWorkspace", return_value=workspace):
            layman_instance.handleCommand("maximize")

        manager.onCommand.assert_called_once_with("maximize", workspace)

    def test_bareStackToggle_stillWorks(self, layman_instance):
        """Bare 'stack toggle' should route via stack prefix handling."""
        workspace, manager, _ = setup_workspace_with_manager(layman_instance)

        with patch("layman.utils.findFocusedWorkspace", return_value=workspace):
            layman_instance.handleCommand("stack toggle")

        manager.onCommand.assert_called_once_with("toggle", workspace)


class TestBindingEventRouting:
    """Tests for nop layman binding events with new commands."""

    def test_nopLayman_windowMoveUp(self, layman_instance):
        """'nop layman window move up' should route correctly."""
        workspace, manager, _ = setup_workspace_with_manager(layman_instance)

        binding = MockBindingEvent(command="nop layman window move up")

        with patch("layman.utils.findFocusedWorkspace", return_value=workspace):
            layman_instance.onBinding(binding)

        manager.onCommand.assert_called_once_with("move up", workspace)

    def test_nopLayman_layoutSetAutotiling(self, layman_instance):
        """'nop layman layout set Autotiling' should set layout."""
        workspace, manager, _ = setup_workspace_with_manager(layman_instance)

        binding = MockBindingEvent(command="nop layman layout set Autotiling")

        with (
            patch("layman.utils.findFocusedWorkspace", return_value=workspace),
            patch.object(layman_instance, "setWorkspaceLayout") as mock_set,
        ):
            layman_instance.onBinding(binding)

        mock_set.assert_called_once_with(workspace, "1", "Autotiling")

    def test_nopLayman_stackSideToggle(self, layman_instance):
        """'nop layman stack side toggle' should route correctly."""
        workspace, manager, _ = setup_workspace_with_manager(layman_instance)

        binding = MockBindingEvent(command="nop layman stack side toggle")

        with patch("layman.utils.findFocusedWorkspace", return_value=workspace):
            layman_instance.onBinding(binding)

        manager.onCommand.assert_called_once_with("side toggle", workspace)
