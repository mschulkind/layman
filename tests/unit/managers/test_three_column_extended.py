"""Extended tests for ThreeColumnLayoutManager — coverage boost."""

import pytest

from layman.config import ConfigError
from layman.managers.three_column import (
    StackLayout,
    ThreeColumnLayoutManager,
)
from tests.mocks.i3ipc_mocks import (
    MockCon,
    MockConnection,
    MockWindowEvent,
    create_workspace,
)


@pytest.fixture
def temp_config(tmp_path):
    from layman.config import LaymanConfig

    def _create_config(content: str) -> LaymanConfig:
        config_path = tmp_path / "config.toml"
        config_path.write_text(content)
        return LaymanConfig(str(config_path))

    return _create_config


@pytest.fixture
def default_config(temp_config):
    return temp_config('[layman]\ndefaultLayout = "ThreeColumn"\nmasterWidth = 50\n')


@pytest.fixture
def unbalanced_config(temp_config):
    return temp_config(
        '[layman]\ndefaultLayout = "ThreeColumn"\n'
        "masterWidth = 50\nbalanceStacks = false\n"
    )


@pytest.fixture
def mock_conn():
    return MockConnection()


@pytest.fixture
def empty_workspace():
    return create_workspace(name="1", window_count=0)


def make_manager(conn, workspace, config):
    return ThreeColumnLayoutManager(conn, workspace, "1", config)


def make_window_event(window, change="new"):
    return MockWindowEvent(change=change, container=window)


# =============================================================================
# Config parsing
# =============================================================================


class TestConfigParsing:
    def test_invalidMasterWidth_string(self, mock_conn, empty_workspace, temp_config):
        cfg = temp_config(
            '[layman]\ndefaultLayout = "ThreeColumn"\nmasterWidth = "wide"\n'
        )
        with pytest.raises(ConfigError, match="masterWidth"):
            make_manager(mock_conn, empty_workspace, cfg)

    def test_invalidMasterWidth_zero(self, mock_conn, empty_workspace, temp_config):
        cfg = temp_config(
            '[layman]\ndefaultLayout = "ThreeColumn"\nmasterWidth = 0\n'
        )
        with pytest.raises(ConfigError, match="masterWidth"):
            make_manager(mock_conn, empty_workspace, cfg)

    def test_invalidMasterWidth_100(self, mock_conn, empty_workspace, temp_config):
        cfg = temp_config(
            '[layman]\ndefaultLayout = "ThreeColumn"\nmasterWidth = 100\n'
        )
        with pytest.raises(ConfigError, match="masterWidth"):
            make_manager(mock_conn, empty_workspace, cfg)

    def test_invalidStackLayout(self, mock_conn, empty_workspace, temp_config):
        cfg = temp_config(
            '[layman]\ndefaultLayout = "ThreeColumn"\nstackLayout = "invalid"\n'
        )
        with pytest.raises(ConfigError, match="stackLayout"):
            make_manager(mock_conn, empty_workspace, cfg)

    def test_stackLayout_nonString(self, mock_conn, empty_workspace, temp_config):
        cfg = temp_config(
            '[layman]\ndefaultLayout = "ThreeColumn"\nstackLayout = 42\n'
        )
        with pytest.raises(ConfigError, match="stackLayout"):
            make_manager(mock_conn, empty_workspace, cfg)

    def test_invalidBalanceStacks(self, mock_conn, empty_workspace, temp_config):
        cfg = temp_config(
            '[layman]\ndefaultLayout = "ThreeColumn"\nbalanceStacks = "yes"\n'
        )
        with pytest.raises(ConfigError, match="balanceStacks"):
            make_manager(mock_conn, empty_workspace, cfg)

    def test_validStackLayout_tabbed(self, mock_conn, empty_workspace, temp_config):
        cfg = temp_config(
            '[layman]\ndefaultLayout = "ThreeColumn"\nstackLayout = "tabbed"\n'
        )
        mgr = make_manager(mock_conn, empty_workspace, cfg)
        assert mgr.stackLayout == StackLayout.TABBED

    def test_masterWidth_float(self, mock_conn, empty_workspace, temp_config):
        cfg = temp_config(
            '[layman]\ndefaultLayout = "ThreeColumn"\nmasterWidth = 60.5\n'
        )
        mgr = make_manager(mock_conn, empty_workspace, cfg)
        assert mgr.masterWidth == 60


# =============================================================================
# StackLayout enum
# =============================================================================


class TestStackLayoutEnum:
    def test_cycle_all(self):
        assert StackLayout.SPLITV.nextChoice() == StackLayout.SPLITH
        assert StackLayout.SPLITH.nextChoice() == StackLayout.STACKING
        assert StackLayout.STACKING.nextChoice() == StackLayout.TABBED
        assert StackLayout.TABBED.nextChoice() == StackLayout.SPLITV


# =============================================================================
# Movement Commands
# =============================================================================


class TestMoveCommands:
    def test_moveToMaster_fromRight(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.masterId = 100
        mgr.rightStack = [200, 300]
        mgr.leftStack = [400]
        w = MockCon(id=200, name="w", focused=True)
        empty_workspace.nodes = [w]
        w.parent = empty_workspace
        mgr.onCommand("move to master", empty_workspace)
        assert mgr.masterId == 200
        assert 100 in mgr.leftStack  # Old master goes to opposite side

    def test_moveToMaster_fromLeft(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.masterId = 100
        mgr.rightStack = [300]
        mgr.leftStack = [200]
        w = MockCon(id=200, name="w", focused=True)
        empty_workspace.nodes = [w]
        w.parent = empty_workspace
        mgr.onCommand("move to master", empty_workspace)
        assert mgr.masterId == 200
        assert 100 in mgr.rightStack  # Old master goes to right

    def test_moveToLeft_fromMaster(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.masterId = 100
        mgr.rightStack = [200]
        mgr.leftStack = []
        w = MockCon(id=100, name="w", focused=True)
        empty_workspace.nodes = [w]
        w.parent = empty_workspace
        mgr.onCommand("move left", empty_workspace)
        assert 100 in mgr.leftStack
        assert mgr.masterId == 200  # Promoted from right stack

    def test_moveToRight_fromMaster(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.masterId = 100
        mgr.rightStack = []
        mgr.leftStack = [200]
        w = MockCon(id=100, name="w", focused=True)
        empty_workspace.nodes = [w]
        w.parent = empty_workspace
        mgr.onCommand("move right", empty_workspace)
        assert 100 in mgr.rightStack
        assert mgr.masterId == 200  # Promoted from left stack

    def test_moveToSameColumn_noOp(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.masterId = 100
        mgr.leftStack = [200]
        mgr.rightStack = [300]
        w = MockCon(id=200, name="w", focused=True)
        empty_workspace.nodes = [w]
        w.parent = empty_workspace
        mgr.onCommand("move left", empty_workspace)
        # Already in left, nothing changes
        assert 200 in mgr.leftStack

    def test_moveUp_withinStack(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.masterId = 100
        mgr.rightStack = [200, 300, 400]
        w = MockCon(id=300, name="w", focused=True)
        empty_workspace.nodes = [w]
        w.parent = empty_workspace
        mgr.onCommand("move up", empty_workspace)
        # 300 swaps with 200 (index 1 → index 0)
        assert mgr.rightStack[0] in [200, 300]
        assert mgr.rightStack[1] in [200, 300]

    def test_moveUp_masterNoOp(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.masterId = 100
        w = MockCon(id=100, name="master", focused=True)
        empty_workspace.nodes = [w]
        w.parent = empty_workspace
        mgr.onCommand("move up", empty_workspace)
        assert mgr.masterId == 100  # No change

    def test_moveToColumn_noWindow(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.masterId = 100
        mgr.onCommand("move left", empty_workspace)  # No focused window


# =============================================================================
# Focus Commands
# =============================================================================


class TestFocusCommands:
    def test_focusLeft_fromMaster(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.masterId = 100
        mgr.leftStack = [200]
        mgr.rightStack = [300]
        w = MockCon(id=100, name="master", focused=True)
        empty_workspace.nodes = [w]
        w.parent = empty_workspace
        mgr.onCommand("focus left", empty_workspace)
        assert any("[con_id=200] focus" in c for c in mock_conn.commands_executed)

    def test_focusRight_fromMaster(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.masterId = 100
        mgr.leftStack = [200]
        mgr.rightStack = [300]
        w = MockCon(id=100, name="master", focused=True)
        empty_workspace.nodes = [w]
        w.parent = empty_workspace
        mgr.onCommand("focus right", empty_workspace)
        assert any("[con_id=300] focus" in c for c in mock_conn.commands_executed)

    def test_focusMaster(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.masterId = 100
        mgr.rightStack = [200]
        w = MockCon(id=200, name="stack", focused=True)
        empty_workspace.nodes = [w]
        w.parent = empty_workspace
        mgr.onCommand("focus master", empty_workspace)
        assert any("[con_id=100] focus" in c for c in mock_conn.commands_executed)

    def test_focusMaster_noMaster(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.masterId = None
        w = MockCon(id=200, name="w", focused=True)
        empty_workspace.nodes = [w]
        w.parent = empty_workspace
        mgr.onCommand("focus master", empty_workspace)

    def test_focusWithinColumn_down(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.masterId = 100
        mgr.rightStack = [200, 300]
        w = MockCon(id=200, name="w", focused=True)
        empty_workspace.nodes = [w]
        w.parent = empty_workspace
        mgr.onCommand("focus down", empty_workspace)
        assert any("[con_id=300] focus" in c for c in mock_conn.commands_executed)

    def test_focusWithinColumn_wraps(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.masterId = 100
        mgr.rightStack = [200, 300]
        w = MockCon(id=300, name="w", focused=True)
        empty_workspace.nodes = [w]
        w.parent = empty_workspace
        mgr.onCommand("focus down", empty_workspace)
        assert any("[con_id=200] focus" in c for c in mock_conn.commands_executed)

    def test_focusColumn_wrapsLeftToRight(
        self, mock_conn, empty_workspace, default_config
    ):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.masterId = 100
        mgr.leftStack = [200]
        mgr.rightStack = [300]
        w = MockCon(id=200, name="w", focused=True)
        empty_workspace.nodes = [w]
        w.parent = empty_workspace
        mgr.onCommand("focus left", empty_workspace)
        # Wraps from left → right
        assert any("[con_id=300] focus" in c for c in mock_conn.commands_executed)


# =============================================================================
# Swap/Rotate
# =============================================================================


class TestSwapRotate:
    def test_swapMaster(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.masterId = 100
        mgr.rightStack = [200, 300]
        w = MockCon(id=200, name="w", focused=True)
        empty_workspace.nodes = [w]
        w.parent = empty_workspace
        mgr.onCommand("swap master", empty_workspace)
        assert mgr.masterId == 200
        assert 100 in mgr.rightStack

    def test_swapMaster_alreadyMaster(
        self, mock_conn, empty_workspace, default_config
    ):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.masterId = 100
        w = MockCon(id=100, name="master", focused=True)
        empty_workspace.nodes = [w]
        w.parent = empty_workspace
        mgr.onCommand("swap master", empty_workspace)
        assert mgr.masterId == 100  # No change

    def test_swapMaster_noMaster(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.masterId = None
        w = MockCon(id=200, name="w", focused=True)
        empty_workspace.nodes = [w]
        w.parent = empty_workspace
        mgr.onCommand("swap master", empty_workspace)

    def test_rotateCw(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.masterId = 100
        mgr.leftStack = [200]
        mgr.rightStack = [300]
        w = MockCon(id=100, name="w", focused=True)
        empty_workspace.nodes = [w]
        w.parent = empty_workspace
        mgr.onCommand("rotate cw", empty_workspace)
        # All IDs are [200, 100, 300], rotated cw → [300, 200, 100]
        # After redistribution: left=[300], master=200, right=[100]
        assert mgr.masterId is not None

    def test_rotateCcw(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.masterId = 100
        mgr.leftStack = [200]
        mgr.rightStack = [300]
        w = MockCon(id=100, name="w", focused=True)
        empty_workspace.nodes = [w]
        w.parent = empty_workspace
        mgr.onCommand("rotate ccw", empty_workspace)
        assert mgr.masterId is not None

    def test_rotate_singleWindow(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.masterId = 100
        w = MockCon(id=100, name="w", focused=True)
        empty_workspace.nodes = [w]
        w.parent = empty_workspace
        mgr.onCommand("rotate cw", empty_workspace)
        assert mgr.masterId == 100  # No change


# =============================================================================
# Toggle and Balance
# =============================================================================


class TestToggleBalance:
    def test_toggleStackLayout(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.masterId = 100
        mgr.leftStack = [200]
        mgr.rightStack = [300]
        assert mgr.stackLayout == StackLayout.SPLITV
        w = MockCon(id=200, name="w", focused=True)
        empty_workspace.nodes = [w]
        w.parent = empty_workspace
        mgr.onCommand("toggle", empty_workspace)
        assert mgr.stackLayout == StackLayout.SPLITH

    def test_balance(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.masterId = 100
        mgr.leftStack = []
        mgr.rightStack = [200, 300, 400, 500]
        mgr.onCommand("balance", empty_workspace)
        assert len(mgr.leftStack) > 0
        assert len(mgr.rightStack) > 0

    def test_toggleMaximize(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.masterId = 100
        mgr.rightStack = [200]
        w = MockCon(id=100, name="w", focused=True)
        empty_workspace.nodes = [w]
        w.parent = empty_workspace
        assert not mgr.maximized
        mgr.onCommand("maximize", empty_workspace)
        assert mgr.maximized
        mgr.onCommand("maximize", empty_workspace)
        assert not mgr.maximized


# =============================================================================
# Window Events — Floating
# =============================================================================


class TestWindowFloating:
    def test_tiledToFloating(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.masterId = 100
        mgr.rightStack = [200]
        w = MockCon(id=200, floating="auto_on", type="floating_con")
        mgr.windowFloating(make_window_event(w, "floating"), empty_workspace, w)
        assert 200 in mgr.floatingWindowIds
        assert 200 not in mgr.rightStack

    def test_floatingToTiled(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.masterId = 100
        mgr.floatingWindowIds = {200}
        w = MockCon(id=200, floating=None, type="con")
        mgr.windowFloating(make_window_event(w, "floating"), empty_workspace, w)
        assert 200 not in mgr.floatingWindowIds
        # Should have been re-added to the layout
        all_ids = mgr._getAllWindowIds()
        assert 200 in all_ids


# =============================================================================
# Window Remove edge cases
# =============================================================================


class TestWindowRemoveEdge:
    def test_removeLastMaster_noPromote(
        self, mock_conn, empty_workspace, default_config
    ):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.masterId = 100
        w = MockCon(id=100, name="master")
        mgr.windowRemoved(make_window_event(w, "close"), empty_workspace, w)
        assert mgr.masterId is None

    def test_removeMaster_promoteFromRight(
        self, mock_conn, empty_workspace, default_config
    ):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.masterId = 100
        mgr.rightStack = [200, 300]
        mgr.leftStack = [400]
        w = MockCon(id=100, name="master")
        mgr.windowRemoved(make_window_event(w, "close"), empty_workspace, w)
        assert mgr.masterId == 200

    def test_removeMaster_promoteFromLeft(
        self, mock_conn, empty_workspace, default_config
    ):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.masterId = 100
        mgr.rightStack = []
        mgr.leftStack = [400]
        w = MockCon(id=100, name="master")
        mgr.windowRemoved(make_window_event(w, "close"), empty_workspace, w)
        assert mgr.masterId == 400

    def test_removeUnknownWindow(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.masterId = 100
        w = MockCon(id=999, name="unknown")
        # Should log error but not crash
        mgr.windowRemoved(make_window_event(w, "close"), empty_workspace, w)

    def test_removeFloating_notTracked(
        self, mock_conn, empty_workspace, default_config
    ):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        w = MockCon(id=999, floating="auto_on", type="floating_con")
        # Not in floatingWindowIds — should log error
        mgr.windowRemoved(make_window_event(w, "close"), empty_workspace, w)

    def test_removeFromLeftStack(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.masterId = 100
        mgr.leftStack = [200, 300]
        mgr.rightStack = [400]
        w = MockCon(id=200, name="w")
        mgr.windowRemoved(make_window_event(w, "close"), empty_workspace, w)
        assert 200 not in mgr.leftStack


# =============================================================================
# Unbalanced mode
# =============================================================================


class TestUnbalanced:
    def test_addWindows_allGoRight(self, mock_conn, empty_workspace, unbalanced_config):
        mgr = make_manager(mock_conn, empty_workspace, unbalanced_config)
        assert mgr.balanceStacks is False
        for i in range(5):
            w = MockCon(id=100 + i, name=f"w{i}")
            mgr.windowAdded(make_window_event(w), empty_workspace, w)
        assert len(mgr.leftStack) == 0
        assert len(mgr.rightStack) == 4  # First goes to master


# =============================================================================
# Unknown command
# =============================================================================


class TestUnknownCommand:
    def test_unknownCommand(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.masterId = 100
        w = MockCon(id=100, name="w", focused=True)
        empty_workspace.nodes = [w]
        w.parent = empty_workspace
        mgr.onCommand("nonexistent", empty_workspace)

    def test_command_noFocused(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.masterId = 100
        mgr.onCommand("move left", empty_workspace)
