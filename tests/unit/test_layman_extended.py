"""Extended tests for Layman class — coverage boost for event handlers and integrations."""

from unittest.mock import Mock, patch, MagicMock

import pytest

from layman.config import LaymanConfig, ConfigError
from layman.focus_history import FocusHistory
from layman.layman import Layman, WorkspaceState
from layman.rules import WindowRule, WindowRuleEngine
from tests.mocks.i3ipc_mocks import (
    MockBindingEvent,
    MockCon,
    MockConnection,
    MockWindowEvent,
    MockWorkspaceEvent,
    create_workspace,
    create_tree_with_workspaces,
)


@pytest.fixture
def minimal_config(tmp_path):
    config_path = tmp_path / "config.toml"
    config_path.write_text('[layman]\ndefaultLayout = "MasterStack"\n')
    return LaymanConfig(str(config_path))


@pytest.fixture
def rules_config(tmp_path):
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        '[layman]\ndefaultLayout = "none"\n\n'
        "[[rules]]\n"
        'match_app_id = "pavucontrol"\n'
        "floating = true\n\n"
        "[[rules]]\n"
        'match_app_id = "waybar"\n'
        "exclude = true\n\n"
        "[[rules]]\n"
        'match_app_id = "zoom"\n'
        'workspace = "4"\n'
    )
    return LaymanConfig(str(config_path))


@pytest.fixture
def layman_instance(minimal_config):
    """Create a Layman instance with mocked internals."""
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
    """Set up a workspace with state on the Layman instance."""
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
# windowCreated Tests
# =============================================================================


class TestWindowCreated:
    def test_windowCreated_addsToState(self, layman_instance):
        workspace, manager, state = setup_workspace(layman_instance, window_ids=set())
        window = MockCon(id=500, name="new_window")
        tree = MockCon(type="root")
        event = MockWindowEvent(change="new", container=window)

        layman_instance.windowCreated(event, tree, workspace, window)

        assert 500 in state.windowIds
        manager.windowAdded.assert_called_once()

    def test_windowCreated_noWindow(self, layman_instance):
        workspace, manager, state = setup_workspace(layman_instance)
        tree = MockCon(type="root")
        event = MockWindowEvent(change="new")
        layman_instance.windowCreated(event, tree, workspace, None)
        manager.windowAdded.assert_not_called()

    def test_windowCreated_noWorkspace(self, layman_instance):
        workspace, manager, state = setup_workspace(layman_instance)
        tree = MockCon(type="root")
        window = MockCon(id=500)
        event = MockWindowEvent(change="new", container=window)
        layman_instance.windowCreated(event, tree, None, window)
        # Should handle gracefully

    def test_windowCreated_excludedWorkspace(self, layman_instance):
        workspace, manager, state = setup_workspace(layman_instance)
        state.isExcluded = True
        window = MockCon(id=500)
        tree = MockCon(type="root")
        event = MockWindowEvent(change="new", container=window)
        layman_instance.windowCreated(event, tree, workspace, window)
        # Window added to IDs but handleWindowAdded checks exclusion
        assert 500 in state.windowIds


# =============================================================================
# Window Rules Integration
# =============================================================================


class TestWindowRulesIntegration:
    def test_excludeRule(self, layman_instance):
        layman_instance.ruleEngine = WindowRuleEngine(
            [WindowRule(match_app_id="waybar", exclude=True)]
        )
        workspace, manager, state = setup_workspace(layman_instance, window_ids=set())
        window = MockCon(id=500, app_id="waybar")
        tree = MockCon(type="root")
        event = MockWindowEvent(change="new", container=window)

        layman_instance.windowCreated(event, tree, workspace, window)

        assert 500 not in state.windowIds
        manager.windowAdded.assert_not_called()

    def test_floatingRule(self, layman_instance):
        layman_instance.ruleEngine = WindowRuleEngine(
            [WindowRule(match_app_id="pavucontrol", floating=True)]
        )
        workspace, manager, state = setup_workspace(layman_instance, window_ids=set())
        window = MockCon(id=500, app_id="pavucontrol")
        tree = MockCon(type="root")
        event = MockWindowEvent(change="new", container=window)

        layman_instance.windowCreated(event, tree, workspace, window)

        assert any(
            "floating enable" in c for c in layman_instance.conn.commands_executed
        )
        manager.windowAdded.assert_not_called()

    def test_workspaceRule(self, layman_instance):
        layman_instance.ruleEngine = WindowRuleEngine(
            [WindowRule(match_app_id="zoom", workspace="4")]
        )
        workspace, manager, state = setup_workspace(layman_instance, window_ids=set())
        window = MockCon(id=500, app_id="zoom")
        tree = MockCon(type="root")
        event = MockWindowEvent(change="new", container=window)

        layman_instance.windowCreated(event, tree, workspace, window)

        assert any(
            "workspace 4" in c for c in layman_instance.conn.commands_executed
        )

    def test_noRules_passThrough(self, layman_instance):
        layman_instance.ruleEngine = WindowRuleEngine()
        workspace, manager, state = setup_workspace(layman_instance, window_ids=set())
        window = MockCon(id=500, app_id="firefox")
        tree = MockCon(type="root")
        event = MockWindowEvent(change="new", container=window)

        layman_instance.windowCreated(event, tree, workspace, window)

        assert 500 in state.windowIds
        manager.windowAdded.assert_called_once()


# =============================================================================
# windowClosed Tests
# =============================================================================


class TestWindowClosed:
    def test_windowClosed_removesFromState(self, layman_instance):
        workspace, manager, state = setup_workspace(
            layman_instance, window_ids={100, 200}
        )

        tree = MockCon(
            type="root",
            nodes=[MockCon(type="output", nodes=[workspace])],
        )
        event = MockWindowEvent(change="close", container=MockCon(id=100))

        layman_instance.windowClosed(event, tree, workspace, None)

        assert 100 not in state.windowIds
        manager.windowRemoved.assert_called_once()

    def test_windowClosed_removesFromFocusHistory(self, layman_instance):
        workspace, manager, state = setup_workspace(
            layman_instance, window_ids={100, 200}
        )
        state.focusHistory.push(100)
        state.focusHistory.push(200)

        tree = MockCon(
            type="root",
            nodes=[MockCon(type="output", nodes=[workspace])],
        )
        event = MockWindowEvent(change="close", container=MockCon(id=100))

        layman_instance.windowClosed(event, tree, workspace, None)

        assert 100 not in state.focusHistory

    def test_windowClosed_exitsFakeFullscreen(self, layman_instance):
        workspace, manager, state = setup_workspace(
            layman_instance, window_ids={100, 200}
        )
        state.fakeFullscreen = True
        state.fakeFullscreenWindowId = 100

        tree = MockCon(
            type="root",
            nodes=[MockCon(type="output", nodes=[workspace])],
        )
        event = MockWindowEvent(change="close", container=MockCon(id=100))

        layman_instance.windowClosed(event, tree, workspace, None)

        assert not state.fakeFullscreen
        assert state.fakeFullscreenWindowId is None

    def test_windowClosed_unknownWindow(self, layman_instance):
        workspace, manager, state = setup_workspace(
            layman_instance, window_ids={100}
        )
        tree = MockCon(
            type="root",
            nodes=[MockCon(type="output", nodes=[workspace])],
        )
        event = MockWindowEvent(change="close", container=MockCon(id=999))
        # Should handle gracefully (window not in any state)
        layman_instance.windowClosed(event, tree, workspace, None)


# =============================================================================
# windowFocused Tests
# =============================================================================


class TestWindowFocused:
    def test_windowFocused_tracksHistory(self, layman_instance):
        workspace, manager, state = setup_workspace(layman_instance)
        window = MockCon(id=100, name="w", focused=True)
        workspace.nodes = [window]
        window.parent = workspace

        tree = MockCon(type="root")
        event = MockWindowEvent(change="focus", container=window)

        layman_instance.windowFocused(event, tree, workspace, window)

        assert state.focusHistory.current() == 100

    def test_windowFocused_noWorkspace(self, layman_instance):
        setup_workspace(layman_instance)
        window = MockCon(id=100)
        tree = MockCon(type="root")
        event = MockWindowEvent(change="focus", container=window)
        layman_instance.windowFocused(event, tree, None, window)

    def test_windowFocused_excluded(self, layman_instance):
        workspace, manager, state = setup_workspace(layman_instance)
        state.isExcluded = True
        window = MockCon(id=100, focused=True)
        workspace.nodes = [window]
        window.parent = workspace
        tree = MockCon(type="root")
        event = MockWindowEvent(change="focus", container=window)
        layman_instance.windowFocused(event, tree, workspace, window)
        manager.windowFocused.assert_not_called()

    def test_windowFocused_staleEvent(self, layman_instance):
        workspace, manager, state = setup_workspace(layman_instance)
        other_window = MockCon(id=200, focused=True)
        workspace.nodes = [other_window]
        other_window.parent = workspace

        tree = MockCon(type="root")
        event = MockWindowEvent(change="focus", container=MockCon(id=100))
        layman_instance.windowFocused(event, tree, workspace, MockCon(id=100))
        manager.windowFocused.assert_not_called()


# =============================================================================
# windowFloating Tests
# =============================================================================


class TestWindowFloating:
    def test_windowFloating_withSupportingManager(self, layman_instance):
        workspace, manager, state = setup_workspace(layman_instance)
        window = MockCon(id=100, floating="auto_on", type="floating_con")
        tree = MockCon(type="root")
        event = MockWindowEvent(change="floating", container=window)
        layman_instance.windowFloating(event, tree, workspace, window)
        manager.windowFloating.assert_called_once()

    def test_windowFloating_noManager(self, layman_instance):
        workspace, _, state = setup_workspace(
            layman_instance, with_manager=False, window_ids={100}
        )
        window = MockCon(id=100, floating="auto_on", type="floating_con")
        tree = MockCon(type="root")
        event = MockWindowEvent(change="floating", container=window)
        layman_instance.windowFloating(event, tree, workspace, window)

    def test_windowFloating_noWindowOrWorkspace(self, layman_instance):
        setup_workspace(layman_instance)
        tree = MockCon(type="root")
        event = MockWindowEvent(change="floating")
        layman_instance.windowFloating(event, tree, None, None)

    def test_windowFloating_excluded(self, layman_instance):
        workspace, manager, state = setup_workspace(layman_instance)
        state.isExcluded = True
        window = MockCon(id=100, floating="auto_on", type="floating_con")
        tree = MockCon(type="root")
        event = MockWindowEvent(change="floating", container=window)
        layman_instance.windowFloating(event, tree, workspace, window)
        manager.windowFloating.assert_not_called()


# =============================================================================
# Focus Previous Command
# =============================================================================


class TestFocusPrevious:
    def test_focusPrevious_withHistory(self, layman_instance):
        workspace, manager, state = setup_workspace(layman_instance)
        state.focusHistory.push(100)
        state.focusHistory.push(200)

        with patch("layman.utils.findFocusedWorkspace", return_value=workspace):
            layman_instance.handleCommand("window focus previous")

        assert any(
            "[con_id=100] focus" in c for c in layman_instance.conn.commands_executed
        )

    def test_focusPrevious_noHistory(self, layman_instance):
        workspace, manager, state = setup_workspace(layman_instance)

        with patch("layman.utils.findFocusedWorkspace", return_value=workspace):
            layman_instance.handleCommand("window focus previous")

        # Should not crash, no focus command issued


# =============================================================================
# Preset Commands
# =============================================================================


class TestPresetCommands:
    def test_presetSave(self, layman_instance, tmp_path):
        workspace, manager, state = setup_workspace(layman_instance)
        state.layoutName = "MasterStack"

        with (
            patch("layman.utils.findFocusedWorkspace", return_value=workspace),
            patch("layman.utils.getConfigPath", return_value=str(tmp_path / "c.toml")),
        ):
            layman_instance.handleCommand("preset save coding")

        assert hasattr(layman_instance, "presetManager")

    def test_presetLoad(self, layman_instance, tmp_path):
        workspace, manager, state = setup_workspace(layman_instance)
        state.layoutName = "MasterStack"

        with (
            patch("layman.utils.findFocusedWorkspace", return_value=workspace),
            patch("layman.utils.getConfigPath", return_value=str(tmp_path / "c.toml")),
            patch.object(layman_instance, "setWorkspaceLayout") as mock_set,
        ):
            layman_instance.handleCommand("preset save coding")
            layman_instance.handleCommand("preset load coding")

        mock_set.assert_called_once()

    def test_presetList(self, layman_instance, tmp_path):
        workspace, manager, state = setup_workspace(layman_instance)
        with patch("layman.utils.getConfigPath", return_value=str(tmp_path / "c.toml")):
            layman_instance.handleCommand("preset list")

    def test_presetDelete(self, layman_instance, tmp_path):
        workspace, manager, state = setup_workspace(layman_instance)
        state.layoutName = "Grid"

        with (
            patch("layman.utils.findFocusedWorkspace", return_value=workspace),
            patch("layman.utils.getConfigPath", return_value=str(tmp_path / "c.toml")),
        ):
            layman_instance.handleCommand("preset save todelete")
            layman_instance.handleCommand("preset delete todelete")

    def test_presetLoad_notFound(self, layman_instance, tmp_path):
        workspace, manager, state = setup_workspace(layman_instance)
        with (
            patch("layman.utils.findFocusedWorkspace", return_value=workspace),
            patch("layman.utils.getConfigPath", return_value=str(tmp_path / "c.toml")),
        ):
            layman_instance.handleCommand("preset load nonexistent")

    def test_presetSave_noName(self, layman_instance, tmp_path):
        with patch("layman.utils.getConfigPath", return_value=str(tmp_path / "c.toml")):
            layman_instance.handleCommand("preset save")

    def test_presetUnknown(self, layman_instance, tmp_path):
        with patch("layman.utils.getConfigPath", return_value=str(tmp_path / "c.toml")):
            layman_instance.handleCommand("preset badaction something")


# =============================================================================
# Session Commands
# =============================================================================


class TestSessionCommands:
    def test_sessionSave(self, layman_instance, tmp_path):
        workspace, manager, state = setup_workspace(layman_instance)
        with patch("layman.utils.getConfigPath", return_value=str(tmp_path / "c.toml")):
            layman_instance.handleCommand("session save test_session")

    def test_sessionRestore(self, layman_instance, tmp_path):
        workspace, manager, state = setup_workspace(layman_instance)
        with patch("layman.utils.getConfigPath", return_value=str(tmp_path / "c.toml")):
            layman_instance.handleCommand("session save restore_me")
            layman_instance.handleCommand("session restore restore_me")

    def test_sessionList(self, layman_instance, tmp_path):
        with patch("layman.utils.getConfigPath", return_value=str(tmp_path / "c.toml")):
            layman_instance.handleCommand("session list")

    def test_sessionDelete(self, layman_instance, tmp_path):
        with patch("layman.utils.getConfigPath", return_value=str(tmp_path / "c.toml")):
            layman_instance.handleCommand("session save to_delete")
            layman_instance.handleCommand("session delete to_delete")

    def test_sessionUnknown(self, layman_instance, tmp_path):
        with patch("layman.utils.getConfigPath", return_value=str(tmp_path / "c.toml")):
            layman_instance.handleCommand("session badaction")


# =============================================================================
# Reload Command
# =============================================================================


class TestReloadCommand:
    def test_reload_reloadsRules(self, layman_instance, tmp_path):
        config_path = tmp_path / "config.toml"
        config_path.write_text(
            "[layman]\n"
            'defaultLayout = "none"\n\n'
            "[[rules]]\n"
            'match_app_id = "test"\n'
            "exclude = true\n"
        )
        with (
            patch("layman.utils.getConfigPath", return_value=str(config_path)),
            patch.object(layman_instance, "fetchUserLayouts"),
        ):
            layman_instance.handleCommand("reload")

        assert len(layman_instance.ruleEngine.rules) == 1
        assert layman_instance.ruleEngine.rules[0].match_app_id == "test"


# =============================================================================
# initWorkspace Tests
# =============================================================================


class TestInitWorkspace:
    def test_initWorkspace_new(self, layman_instance):
        ws = create_workspace(name="new_ws", window_count=2, start_id=100)
        with patch.object(layman_instance, "setWorkspaceLayout"):
            layman_instance.initWorkspace(ws)

        assert "new_ws" in layman_instance.workspaceStates
        state = layman_instance.workspaceStates["new_ws"]
        assert len(state.windowIds) == 2

    def test_initWorkspace_alreadyExists(self, layman_instance):
        ws = create_workspace(name="existing", window_count=1, start_id=100)
        layman_instance.workspaceStates["existing"] = WorkspaceState()
        layman_instance.initWorkspace(ws)
        # Should return early without resetting

    def test_initWorkspace_withLayout(self, layman_instance, tmp_path):
        config_path = tmp_path / "config.toml"
        config_path.write_text(
            "[layman]\n"
            'defaultLayout = "none"\n\n'
            "[workspace.test_ws]\n"
            'defaultLayout = "MasterStack"\n'
        )
        layman_instance.options = LaymanConfig(str(config_path))
        layman_instance.builtinLayouts = {"MasterStack": Mock}
        ws = create_workspace(name="test_ws", window_count=0)

        with patch.object(layman_instance, "setWorkspaceLayout") as mock_set:
            layman_instance.initWorkspace(ws)
        mock_set.assert_called_once()


# =============================================================================
# setWorkspaceLayout Tests
# =============================================================================


class TestSetWorkspaceLayout:
    def test_setNativeLayout(self, layman_instance):
        ws = MockCon(name="1", type="workspace")
        layman_instance.workspaceStates["1"] = WorkspaceState(windowIds={100})

        layman_instance.setWorkspaceLayout(ws, "1", "tabbed")

        state = layman_instance.workspaceStates["1"]
        assert state.layoutManager is None
        assert state.layoutName == "tabbed"

    def test_setUnknownLayout_raises(self, layman_instance):
        ws = MockCon(name="1", type="workspace")
        layman_instance.workspaceStates["1"] = WorkspaceState()

        with pytest.raises(ConfigError, match="Unknown layout"):
            layman_instance.setWorkspaceLayout(ws, "1", "NonexistentLayout")

    def test_setExcludedWorkspace(self, layman_instance):
        ws = MockCon(name="1", type="workspace")
        layman_instance.workspaceStates["1"] = WorkspaceState(isExcluded=True)
        # Should log error and return
        layman_instance.setWorkspaceLayout(ws, "1", "MasterStack")


# =============================================================================
# Master Commands
# =============================================================================


class TestMasterCommands:
    def test_masterAdd_routesToManager(self, layman_instance):
        workspace, manager, _ = setup_workspace(layman_instance)
        with patch("layman.utils.findFocusedWorkspace", return_value=workspace):
            layman_instance.handleCommand("master add")
        manager.onCommand.assert_called_once_with("master add", workspace)

    def test_masterRemove_routesToManager(self, layman_instance):
        workspace, manager, _ = setup_workspace(layman_instance)
        with patch("layman.utils.findFocusedWorkspace", return_value=workspace):
            layman_instance.handleCommand("master remove")
        manager.onCommand.assert_called_once_with("master remove", workspace)

    def test_master_noManager(self, layman_instance):
        workspace, _, state = setup_workspace(
            layman_instance, with_manager=False
        )
        with patch("layman.utils.findFocusedWorkspace", return_value=workspace):
            layman_instance.handleCommand("master add")


# =============================================================================
# Fake Fullscreen
# =============================================================================


class TestFakeFullscreen:
    def test_enterFakeFullscreen(self, layman_instance):
        workspace, manager, state = setup_workspace(layman_instance)
        focused = MockCon(id=100, name="focused", focused=True)
        with patch("layman.utils.findFocusedWindow", return_value=focused):
            layman_instance.toggleFakeFullscreen(workspace, state)

        assert state.fakeFullscreen is True
        assert state.fakeFullscreenWindowId == 100
        manager.onCommand.assert_called_with("maximize", workspace)

    def test_exitFakeFullscreen(self, layman_instance):
        workspace, manager, state = setup_workspace(layman_instance)
        state.fakeFullscreen = True
        state.fakeFullscreenWindowId = 100
        layman_instance.toggleFakeFullscreen(workspace, state)

        assert state.fakeFullscreen is False
        manager.onCommand.assert_called_with("maximize", workspace)

    def test_fakeFullscreen_noManager(self, layman_instance):
        workspace, _, state = setup_workspace(
            layman_instance, with_manager=False, window_ids={100}
        )
        focused = MockCon(id=100, name="focused", focused=True)
        focused.parent = MockCon(type="con", layout="splith")
        tree = MockCon(type="root", nodes=[focused])
        layman_instance.conn = MockConnection(tree=tree)

        with patch("layman.utils.findFocusedWindow", return_value=focused):
            layman_instance.toggleFakeFullscreen(workspace, state)

        assert state.fakeFullscreen is True
        assert any("layout tabbed" in c for c in layman_instance.conn.commands_executed)

    def test_fakeFullscreen_noFocusedWindow(self, layman_instance):
        workspace, manager, state = setup_workspace(layman_instance)
        with patch("layman.utils.findFocusedWindow", return_value=None):
            layman_instance.toggleFakeFullscreen(workspace, state)
        assert state.fakeFullscreen is False


# =============================================================================
# onWorkspaceInit
# =============================================================================


class TestOnWorkspaceInit:
    def test_onWorkspaceInit(self, layman_instance):
        ws = create_workspace(name="new_ws", window_count=0)
        event = MockWorkspaceEvent(change="init", current=ws)
        with patch.object(layman_instance, "setWorkspaceLayout"):
            layman_instance.onWorkspaceInit(event)
        assert "new_ws" in layman_instance.workspaceStates


# =============================================================================
# handleWindowAdded / handleWindowRemoved
# =============================================================================


class TestHandleWindowHelpers:
    def test_handleWindowAdded_excluded(self, layman_instance):
        workspace, manager, state = setup_workspace(layman_instance)
        state.isExcluded = True
        window = MockCon(id=500)
        event = MockWindowEvent(change="new", container=window)
        layman_instance.handleWindowAdded(event, workspace, window)
        manager.windowAdded.assert_not_called()

    def test_handleWindowAdded_noManager(self, layman_instance):
        workspace, _, state = setup_workspace(
            layman_instance, with_manager=False, window_ids={100}
        )
        state.layoutName = "splith"
        window = MockCon(id=500)
        event = MockWindowEvent(change="new", container=window)
        layman_instance.handleWindowAdded(event, workspace, window)

    def test_handleWindowRemoved_excluded(self, layman_instance):
        workspace, manager, state = setup_workspace(layman_instance)
        state.isExcluded = True
        event = MockWindowEvent(change="close", container=MockCon(id=100))
        layman_instance.handleWindowRemoved(event, workspace, None, None)
        manager.windowRemoved.assert_not_called()

    def test_handleWindowRemoved_noManager(self, layman_instance):
        workspace, _, state = setup_workspace(
            layman_instance, with_manager=False, window_ids={100}
        )
        state.layoutName = "splith"
        event = MockWindowEvent(change="close", container=MockCon(id=100))
        layman_instance.handleWindowRemoved(event, workspace, None, None)


# =============================================================================
# Binding Event Edge Cases
# =============================================================================


class TestBindingEdgeCases:
    def test_bindingWithChainedCommands(self, layman_instance):
        workspace, manager, _ = setup_workspace(layman_instance)
        binding = MockBindingEvent(
            command="nop layman window move up; nop layman window move down"
        )
        with patch("layman.utils.findFocusedWorkspace", return_value=workspace):
            layman_instance.onBinding(binding)
        assert manager.onCommand.call_count == 2

    def test_bindingWithMixedCommands(self, layman_instance):
        workspace, manager, _ = setup_workspace(layman_instance)
        binding = MockBindingEvent(
            command="nop layman layout maximize; mode default"
        )
        focused = MockCon(id=100, focused=True)
        with (
            patch("layman.utils.findFocusedWorkspace", return_value=workspace),
            patch("layman.utils.findFocusedWindow", return_value=focused),
        ):
            layman_instance.onBinding(binding)

    def test_nonLaymanBinding_ignored(self, layman_instance):
        binding = MockBindingEvent(command="exec terminal")
        layman_instance.onBinding(binding)

    def test_emptyCommand_filtered(self, layman_instance):
        workspace, manager, _ = setup_workspace(layman_instance)
        binding = MockBindingEvent(command="nop layman window move up; ;")
        with patch("layman.utils.findFocusedWorkspace", return_value=workspace):
            layman_instance.onBinding(binding)
        assert manager.onCommand.call_count == 1


# =============================================================================
# onCommand (pipe command)
# =============================================================================


class TestOnCommand:
    def test_onCommand_single(self, layman_instance):
        workspace, manager, _ = setup_workspace(layman_instance)
        with patch("layman.utils.findFocusedWorkspace", return_value=workspace):
            layman_instance.onCommand("window move up")
        manager.onCommand.assert_called_once()

    def test_onCommand_chained(self, layman_instance):
        workspace, manager, _ = setup_workspace(layman_instance)
        with patch("layman.utils.findFocusedWorkspace", return_value=workspace):
            layman_instance.onCommand("window move up; window move down")
        assert manager.onCommand.call_count == 2

    def test_onCommand_empty(self, layman_instance):
        layman_instance.onCommand("")


# =============================================================================
# fetchUserLayouts
# =============================================================================


class TestFetchUserLayouts:
    def test_fetchUserLayouts_emptyDir(self, layman_instance, tmp_path):
        config_dir = tmp_path / "layman"
        config_dir.mkdir()
        config_path = config_dir / "config.toml"
        config_path.write_text("[layman]\n")
        with patch("layman.utils.getConfigPath", return_value=str(config_path)):
            layman_instance.fetchUserLayouts()
        assert layman_instance.userLayouts == {}


# =============================================================================
# getLayoutByShortName
# =============================================================================


class TestGetLayoutByShortName:
    def test_builtin(self, layman_instance):
        mock_class = Mock()
        layman_instance.builtinLayouts = {"MasterStack": mock_class}
        assert layman_instance.getLayoutByShortName("MasterStack") == mock_class

    def test_userLayout(self, layman_instance):
        mock_class = Mock()
        layman_instance.userLayouts = {"MyLayout": mock_class}
        assert layman_instance.getLayoutByShortName("MyLayout") == mock_class

    def test_notFound(self, layman_instance):
        assert layman_instance.getLayoutByShortName("Nonexistent") is None
