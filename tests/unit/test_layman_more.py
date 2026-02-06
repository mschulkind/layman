"""More tests for Layman class — filling remaining coverage gaps."""

from unittest.mock import Mock, patch

import pytest

from layman.config import LaymanConfig
from layman.layman import Layman, WorkspaceState
from layman.rules import WindowRuleEngine
from tests.mocks.i3ipc_mocks import (
    MockBindingEvent,
    MockCon,
    MockConnection,
    MockWindowEvent,
    create_workspace,
)


@pytest.fixture
def minimal_config(tmp_path):
    config_path = tmp_path / "config.toml"
    config_path.write_text('[layman]\ndefaultLayout = "MasterStack"\n')
    return LaymanConfig(str(config_path))


@pytest.fixture
def layman_instance(minimal_config):
    with patch("layman.utils.getConfigPath", return_value="/dev/null"):
        instance = Layman.__new__(Layman)
        instance.options = minimal_config
        instance.builtinLayouts = {}
        instance.userLayouts = {}
        instance.workspaceStates = {}
        instance.conn = MockConnection()
        instance.ruleEngine = WindowRuleEngine()
        return instance


def setup_workspace(layman_instance, name="1", window_ids=None, with_manager=True):
    workspace = MockCon(name=name, type="workspace")
    manager = Mock() if with_manager else None
    if manager:
        manager.overridesMoveBinds = True
        manager.overridesFocusBinds = True
        manager.supportsFloating = True

    state = WorkspaceState(
        windowIds=set(window_ids or [100, 200]),
        layoutManager=manager,
    )
    layman_instance.workspaceStates[name] = state
    return workspace, manager, state


# =============================================================================
# windowMoved Tests
# =============================================================================


class TestWindowMoved:
    def test_movedWithinSameWorkspace(self, layman_instance):
        ws, manager, state = setup_workspace(
            layman_instance, name="1", window_ids={100, 200}
        )
        tree = MockCon(
            type="root",
            nodes=[MockCon(type="output", nodes=[ws])],
        )
        window = MockCon(id=100, name="w")
        event = MockWindowEvent(change="move", container=window)

        layman_instance.windowMoved(event, tree, ws, window)
        manager.windowMoved.assert_called_once()

    def test_movedBetweenWorkspaces(self, layman_instance):
        ws1, manager1, state1 = setup_workspace(
            layman_instance, name="1", window_ids={100, 200}
        )
        ws2, manager2, state2 = setup_workspace(
            layman_instance, name="2", window_ids={300}
        )
        tree = MockCon(
            type="root",
            nodes=[MockCon(type="output", nodes=[ws1, ws2])],
        )
        window = MockCon(id=100, name="w")
        event = MockWindowEvent(change="move", container=window)

        layman_instance.windowMoved(event, tree, ws2, window)

        # Window should be removed from ws1 and added to ws2
        assert 100 not in state1.windowIds
        assert 100 in state2.windowIds

    def test_movedNoWorkspace(self, layman_instance):
        setup_workspace(layman_instance)
        tree = MockCon(type="root")
        window = MockCon(id=100)
        event = MockWindowEvent(change="move", container=window)
        layman_instance.windowMoved(event, tree, None, window)

    def test_movedSameWorkspace_noManager(self, layman_instance):
        ws, _, state = setup_workspace(
            layman_instance, name="1", window_ids={100}, with_manager=False
        )
        tree = MockCon(
            type="root",
            nodes=[MockCon(type="output", nodes=[ws])],
        )
        window = MockCon(id=100, name="w")
        event = MockWindowEvent(change="move", container=window)
        layman_instance.windowMoved(event, tree, ws, window)


# =============================================================================
# windowFloating without supportsFloating
# =============================================================================


class TestWindowFloatingNoSupport:
    def test_floating_noSupportingManager_floatingOn(self, layman_instance):
        workspace, manager, state = setup_workspace(layman_instance)
        manager.supportsFloating = False
        window = MockCon(id=100, floating="auto_on", type="floating_con")
        tree = MockCon(type="root")
        event = MockWindowEvent(change="floating", container=window)

        layman_instance.windowFloating(event, tree, workspace, window)
        manager.windowFloating.assert_not_called()

    def test_floating_noSupportingManager_unfloating(self, layman_instance):
        workspace, manager, state = setup_workspace(layman_instance)
        manager.supportsFloating = False
        window = MockCon(id=100, floating=None, type="con")
        tree = MockCon(type="root")
        event = MockWindowEvent(change="floating", container=window)

        layman_instance.windowFloating(event, tree, workspace, window)
        manager.windowFloating.assert_not_called()


# =============================================================================
# setWorkspaceLayoutCommand
# =============================================================================


class TestSetWorkspaceLayoutCommand:
    def test_singleWindow_nativeLayout(self, layman_instance):
        ws = MockCon(name="1", type="workspace")
        state = WorkspaceState(windowIds={100}, layoutName="tabbed")
        layman_instance.workspaceStates["1"] = state

        layman_instance.setWorkspaceLayoutCommand(ws)
        cmds = layman_instance.conn.commands_executed
        assert any("split none" in c for c in cmds)
        assert any("layout tabbed" in c for c in cmds)

    def test_multipleWindows_skipped(self, layman_instance):
        ws = MockCon(name="1", type="workspace")
        state = WorkspaceState(windowIds={100, 200}, layoutName="tabbed")
        layman_instance.workspaceStates["1"] = state

        layman_instance.setWorkspaceLayoutCommand(ws)
        assert len(layman_instance.conn.commands_executed) == 0

    def test_withManager_skipped(self, layman_instance):
        ws = MockCon(name="1", type="workspace")
        state = WorkspaceState(
            windowIds={100}, layoutName="MasterStack", layoutManager=Mock()
        )
        layman_instance.workspaceStates["1"] = state

        layman_instance.setWorkspaceLayoutCommand(ws)
        assert len(layman_instance.conn.commands_executed) == 0


# =============================================================================
# Layout command edge cases
# =============================================================================


class TestLayoutCommandEdgeCases:
    def test_layoutUnknownSubcommand(self, layman_instance):
        workspace, manager, state = setup_workspace(layman_instance)
        with patch("layman.utils.findFocusedWorkspace", return_value=workspace):
            layman_instance.handleCommand("layout badcommand")

    def test_noFocusedWorkspace(self, layman_instance):
        with patch("layman.utils.findFocusedWorkspace", return_value=None):
            layman_instance.handleCommand("window move up")
        assert any("window move up" in c for c in layman_instance.conn.commands_executed)

    def test_bareMoveNoOverride(self, layman_instance):
        workspace, manager, state = setup_workspace(layman_instance)
        manager.overridesMoveBinds = False
        with patch("layman.utils.findFocusedWorkspace", return_value=workspace):
            layman_instance.handleCommand("move up")
        assert any("move up" in c for c in layman_instance.conn.commands_executed)

    def test_bareFocusNoOverride(self, layman_instance):
        workspace, manager, state = setup_workspace(layman_instance)
        manager.overridesFocusBinds = False
        with patch("layman.utils.findFocusedWorkspace", return_value=workspace):
            layman_instance.handleCommand("focus up")
        assert any("focus up" in c for c in layman_instance.conn.commands_executed)

    def test_commandPassedToManager(self, layman_instance):
        workspace, manager, state = setup_workspace(layman_instance)
        with patch("layman.utils.findFocusedWorkspace", return_value=workspace):
            layman_instance.handleCommand("rotate cw")
        manager.onCommand.assert_called_once_with("rotate cw", workspace)

    def test_noManager_ignoresCommand(self, layman_instance):
        workspace, _, state = setup_workspace(
            layman_instance, with_manager=False
        )
        with patch("layman.utils.findFocusedWorkspace", return_value=workspace):
            layman_instance.handleCommand("rotate cw")

    def test_stackCommandNoManager(self, layman_instance):
        workspace, _, state = setup_workspace(
            layman_instance, with_manager=False
        )
        with patch("layman.utils.findFocusedWorkspace", return_value=workspace):
            layman_instance.handleCommand("stack toggle")

    def test_windowCommandNoManager(self, layman_instance):
        workspace, _, state = setup_workspace(
            layman_instance, with_manager=False
        )
        with patch("layman.utils.findFocusedWorkspace", return_value=workspace):
            layman_instance.handleCommand("window swap master")


# =============================================================================
# Fake fullscreen exit (no manager, restore layout)
# =============================================================================


class TestFakeFullscreenNoManager:
    def test_enterAndExit_nativeLayout(self, layman_instance):
        workspace, _, state = setup_workspace(
            layman_instance, with_manager=False, window_ids={100, 200}
        )
        focused = MockCon(id=100, name="focused", focused=True)
        parent = MockCon(type="con", layout="splith", nodes=[focused])
        focused.parent = parent
        tree = MockCon(type="root", nodes=[parent])
        layman_instance.conn = MockConnection(tree=tree)

        with patch("layman.utils.findFocusedWindow", return_value=focused):
            layman_instance.toggleFakeFullscreen(workspace, state)

        assert state.fakeFullscreen is True
        assert any("layout tabbed" in c for c in layman_instance.conn.commands_executed)

        # Exit
        layman_instance.conn.clear_commands()
        layman_instance.toggleFakeFullscreen(workspace, state)
        assert state.fakeFullscreen is False
        assert any("layout splith" in c for c in layman_instance.conn.commands_executed)


# =============================================================================
# setWorkspaceLayout edge cases
# =============================================================================


class TestSetWorkspaceLayoutEdgeCases:
    def test_setLayoutNoLayoutName_usesExisting(self, layman_instance):
        ws = MockCon(name="1", type="workspace")
        mock_class = Mock()
        mock_class.shortName = "MasterStack"
        layman_instance.builtinLayouts = {"MasterStack": mock_class}
        layman_instance.workspaceStates["1"] = WorkspaceState(
            layoutName="MasterStack"
        )
        layman_instance.setWorkspaceLayout(ws, "1")
        mock_class.assert_called_once()

    def test_setLayout_userLayout(self, layman_instance):
        ws = MockCon(name="1", type="workspace")
        mock_class = Mock()
        mock_class.shortName = "MyLayout"
        layman_instance.userLayouts = {"MyLayout": mock_class}
        layman_instance.workspaceStates["1"] = WorkspaceState()
        layman_instance.setWorkspaceLayout(ws, "1", "MyLayout")
        mock_class.assert_called_once()


# =============================================================================
# createConfig
# =============================================================================


class TestCreateConfig:
    def test_createConfig_existingPath(self, layman_instance, tmp_path):
        config_dir = tmp_path / "layman"
        config_dir.mkdir()
        config_path = config_dir / "config.toml"

        with (
            patch("layman.utils.getConfigPath", return_value=str(config_path)),
            patch("shutil.copyfile") as mock_copy,
        ):
            layman_instance.createConfig()
        mock_copy.assert_called_once()

    def test_createConfig_alreadyExists(self, layman_instance, tmp_path):
        config_path = tmp_path / "config.toml"
        config_path.write_text("[layman]\n")
        with patch("layman.utils.getConfigPath", return_value=str(config_path)):
            layman_instance.createConfig()


# =============================================================================
# _loadRules tests
# =============================================================================


class TestLoadRules:
    def test_loadRules_empty(self, layman_instance):
        layman_instance._loadRules()
        assert len(layman_instance.ruleEngine.rules) == 0

    def test_loadRules_nonListValue(self, layman_instance, tmp_path):
        config_path = tmp_path / "config.toml"
        config_path.write_text('[layman]\ndefaultLayout = "none"\nrules = "bad"\n')
        # This is invalid TOML for top-level [[rules]], but in [layman] as a string
        layman_instance.options = LaymanConfig(str(config_path))
        layman_instance._loadRules()
        assert len(layman_instance.ruleEngine.rules) == 0
