"""Extended tests for the TabbedPairsLayoutManager — coverage boost."""

import pytest

from layman.managers.tabbed_pairs import (
    TabbedPairsLayoutManager,
    WindowPair,
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
    return temp_config('[layman]\ndefaultLayout = "TabbedPairs"\n')


@pytest.fixture
def rules_config(temp_config):
    return temp_config(
        '[layman]\ndefaultLayout = "TabbedPairs"\n'
        '[layman.pairRules]\nnvim = ["code", "terminal"]\n'
        'firefox = ["slack"]\n'
    )


@pytest.fixture
def mock_conn():
    return MockConnection()


@pytest.fixture
def empty_workspace():
    return create_workspace(name="1", window_count=0)


def make_manager(conn, workspace, config):
    return TabbedPairsLayoutManager(conn, workspace, "1", config)


def make_window_event(window, change="new"):
    return MockWindowEvent(change=change, container=window)


# =============================================================================
# Auto-pairing Tests
# =============================================================================


class TestAutoPairing:
    def test_autoPair_byAppId(self, mock_conn, empty_workspace, rules_config):
        mgr = make_manager(mock_conn, empty_workspace, rules_config)
        # Add "code" window first (the partner)
        w1 = MockCon(id=100, name="code", app_id="code")
        mgr.windowAdded(make_window_event(w1), empty_workspace, w1)
        assert 100 in mgr.unpairedWindows

        # Set up the tree so _findAutoPartner can look up the unpaired "code" window
        mock_conn.tree = MockCon(
            type="root",
            nodes=[
                MockCon(
                    type="output",
                    nodes=[
                        MockCon(
                            type="workspace",
                            name="1",
                            nodes=[w1],
                        )
                    ],
                )
            ],
        )

        # Add nvim window — rule says nvim → ["code", "terminal"],
        # so nvim should auto-pair with the existing "code" window
        w2 = MockCon(id=200, name="nvim", app_id="nvim")
        mgr.windowAdded(make_window_event(w2), empty_workspace, w2)
        assert len(mgr.pairs) == 1
        assert mgr.pairs[0].primary == 100
        assert mgr.pairs[0].secondary == 200
        assert 100 not in mgr.unpairedWindows
        assert 200 not in mgr.unpairedWindows

    def test_autoPair_noMatch(self, mock_conn, empty_workspace, rules_config):
        mgr = make_manager(mock_conn, empty_workspace, rules_config)
        w1 = MockCon(id=100, name="w1", app_id="chrome")
        mgr.windowAdded(make_window_event(w1), empty_workspace, w1)
        w2 = MockCon(id=200, name="w2", app_id="gimp")
        mgr.windowAdded(make_window_event(w2), empty_workspace, w2)
        assert len(mgr.pairs) == 0
        assert len(mgr.unpairedWindows) == 2

    def test_autoPair_noAppId(self, mock_conn, empty_workspace, rules_config):
        mgr = make_manager(mock_conn, empty_workspace, rules_config)
        w = MockCon(id=100, name="w1", app_id=None, window_class=None)
        mgr.windowAdded(make_window_event(w), empty_workspace, w)
        assert 100 in mgr.unpairedWindows


# =============================================================================
# windowFloating Tests
# =============================================================================


class TestWindowFloating:
    def test_tiledToFloating_unpaired(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.unpairedWindows = [100, 200]
        w = MockCon(id=100, floating="auto_on", type="floating_con")
        mgr.windowFloating(make_window_event(w, "floating"), empty_workspace, w)
        assert 100 not in mgr.unpairedWindows
        assert 100 in mgr.floatingWindowIds

    def test_tiledToFloating_paired(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.pairs = [WindowPair(primary=100, secondary=200)]
        w = MockCon(id=200, floating="auto_on", type="floating_con")
        mgr.windowFloating(make_window_event(w, "floating"), empty_workspace, w)
        assert len(mgr.pairs) == 0
        assert 100 in mgr.unpairedWindows
        assert 200 in mgr.floatingWindowIds

    def test_floatingToTiled(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.floatingWindowIds = {100}
        w = MockCon(id=100, floating=None, type="con")
        mgr.windowFloating(make_window_event(w, "floating"), empty_workspace, w)
        assert 100 not in mgr.floatingWindowIds
        assert 100 in mgr.unpairedWindows


# =============================================================================
# windowFocused Tests
# =============================================================================


class TestWindowFocused:
    def test_focusPairedWindow_updatesFocusIndex(
        self, mock_conn, empty_workspace, default_config
    ):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.pairs = [
            WindowPair(primary=100, secondary=101),
            WindowPair(primary=200, secondary=201),
        ]
        mgr.focusedPairIndex = 0
        w = MockCon(id=200, name="w")
        mgr.windowFocused(make_window_event(w, "focus"), empty_workspace, w)
        assert mgr.focusedPairIndex == 1

    def test_focusUnpairedWindow_noChange(
        self, mock_conn, empty_workspace, default_config
    ):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.unpairedWindows = [100]
        mgr.focusedPairIndex = 0
        w = MockCon(id=100, name="w")
        mgr.windowFocused(make_window_event(w, "focus"), empty_workspace, w)
        assert mgr.focusedPairIndex == 0

    def test_focusFloatingWindow_noChange(
        self, mock_conn, empty_workspace, default_config
    ):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.floatingWindowIds = {100}
        w = MockCon(id=100, floating="auto_on", type="floating_con")
        mgr.windowFocused(make_window_event(w, "focus"), empty_workspace, w)


# =============================================================================
# windowRemoved edge cases
# =============================================================================


class TestWindowRemovedEdgeCases:
    def test_removePrimary_breaksPair(
        self, mock_conn, empty_workspace, default_config
    ):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.pairs = [WindowPair(primary=100, secondary=200)]
        w = MockCon(id=100, name="w1")
        mgr.windowRemoved(make_window_event(w, "close"), empty_workspace, w)
        assert len(mgr.pairs) == 0
        assert 200 in mgr.unpairedWindows

    def test_removePendingPairWindow(
        self, mock_conn, empty_workspace, default_config
    ):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.unpairedWindows = [100]
        mgr.pendingManualPair = 100
        w = MockCon(id=100, name="w1")
        mgr.windowRemoved(make_window_event(w, "close"), empty_workspace, w)
        assert mgr.pendingManualPair is None

    def test_removeUnknownWindow_noError(
        self, mock_conn, empty_workspace, default_config
    ):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        w = MockCon(id=999, name="unknown")
        # Should not raise
        mgr.windowRemoved(make_window_event(w, "close"), empty_workspace, w)


# =============================================================================
# Navigation Commands Extended
# =============================================================================


class TestNavigationCommands:
    def test_focusPair_wrapsAround(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.pairs = [
            WindowPair(primary=100, secondary=101),
            WindowPair(primary=200, secondary=201),
        ]
        mgr.focusedPairIndex = 0
        mgr.onCommand("focus left", empty_workspace)
        assert mgr.focusedPairIndex == 1  # wraps from 0 to last

    def test_focusPair_noPairs(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.pairs = []
        mgr.onCommand("focus right", empty_workspace)  # Should not crash

    def test_focusWithinPair_up(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.pairs = [WindowPair(primary=100, secondary=200)]
        w = MockCon(id=200, name="secondary", focused=True)
        empty_workspace.nodes = [w]
        w.parent = empty_workspace
        mgr.onCommand("focus up", empty_workspace)
        assert any("[con_id=100] focus" in c for c in mock_conn.commands_executed)

    def test_focusWithinPair_unpairedWindow(
        self, mock_conn, empty_workspace, default_config
    ):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.unpairedWindows = [100]
        w = MockCon(id=100, name="w", focused=True)
        empty_workspace.nodes = [w]
        w.parent = empty_workspace
        # Should not crash when focused window is not in a pair
        mgr.onCommand("focus down", empty_workspace)

    def test_focusWithinPair_noFocused(
        self, mock_conn, empty_workspace, default_config
    ):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        # No focused window
        mgr.onCommand("focus up", empty_workspace)


# =============================================================================
# Move Commands
# =============================================================================


class TestMoveCommands:
    def test_movePair_right(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.pairs = [
            WindowPair(primary=100, secondary=101),
            WindowPair(primary=200, secondary=201),
        ]
        w = MockCon(id=100, name="w", focused=True)
        empty_workspace.nodes = [w]
        w.parent = empty_workspace
        mgr.onCommand("move right", empty_workspace)
        assert mgr.pairs[0].primary == 200
        assert mgr.pairs[1].primary == 100
        assert mgr.focusedPairIndex == 1

    def test_movePair_noWindow(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.pairs = [WindowPair(primary=100, secondary=101)]
        mgr.onCommand("move right", empty_workspace)

    def test_movePair_singlePair(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.pairs = [WindowPair(primary=100, secondary=101)]
        w = MockCon(id=100, name="w", focused=True)
        empty_workspace.nodes = [w]
        w.parent = empty_workspace
        mgr.onCommand("move right", empty_workspace)
        # With only one pair, wrapping results in same index — should be a no-op


# =============================================================================
# Manual Pair/Unpair Extended
# =============================================================================


class TestManualPairExtended:
    def test_pair_cancelPending(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.unpairedWindows = [100]
        mgr.pendingManualPair = 100
        w = MockCon(id=100, name="w1", focused=True)
        empty_workspace.nodes = [w]
        w.parent = empty_workspace
        mgr.onCommand("pair", empty_workspace)
        assert mgr.pendingManualPair is None  # Cancelled

    def test_pair_alreadyPaired(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.pairs = [WindowPair(primary=100, secondary=200)]
        w = MockCon(id=100, name="w1", focused=True)
        empty_workspace.nodes = [w]
        w.parent = empty_workspace
        mgr.onCommand("pair", empty_workspace)
        assert mgr.pendingManualPair is None  # Should not set pending

    def test_unpair_notPaired(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.unpairedWindows = [100]
        w = MockCon(id=100, name="w1", focused=True)
        empty_workspace.nodes = [w]
        w.parent = empty_workspace
        mgr.onCommand("unpair", empty_workspace)
        # Should log error but not crash

    def test_unpair_noFocused(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.onCommand("unpair", empty_workspace)


# =============================================================================
# Maximize
# =============================================================================


class TestMaximize:
    def test_toggleMaximize(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.pairs = [WindowPair(primary=100, secondary=200)]
        mgr.unpairedWindows = [300]
        mgr.onCommand("maximize", empty_workspace)
        assert any("layout tabbed" in c for c in mock_conn.commands_executed)

    def test_toggleMaximize_noWindows(
        self, mock_conn, empty_workspace, default_config
    ):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.onCommand("maximize", empty_workspace)


# =============================================================================
# _arrangeExisting with auto-pairing
# =============================================================================


class TestArrangeExisting:
    def test_arrangeExisting_withPairRules(self, mock_conn, rules_config):
        ws = MockCon(
            type="workspace",
            name="1",
            nodes=[
                MockCon(id=100, name="nvim", app_id="nvim"),
                MockCon(id=200, name="code", app_id="code"),
                MockCon(id=300, name="chrome", app_id="chrome"),
            ],
        )
        mgr = make_manager(mock_conn, ws, rules_config)
        assert len(mgr.pairs) == 1
        assert mgr.pairs[0].primary == 100
        assert mgr.pairs[0].secondary == 200
        assert 300 in mgr.unpairedWindows

    def test_arrangeExisting_noPairRules(self, mock_conn, default_config):
        ws = create_workspace(name="1", window_count=3)
        mgr = make_manager(mock_conn, ws, default_config)
        assert len(mgr.pairs) == 0
        assert len(mgr.unpairedWindows) == 3

    def test_arrangeExisting_empty(self, mock_conn, default_config):
        ws = create_workspace(name="1", window_count=0)
        mgr = make_manager(mock_conn, ws, default_config)
        assert mgr.pairs == []
        assert mgr.unpairedWindows == []


# =============================================================================
# windowMoved (currently a no-op)
# =============================================================================


class TestWindowMoved:
    def test_windowMoved_noOp(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        w = MockCon(id=100)
        mgr.windowMoved(make_window_event(w, "move"), empty_workspace, w)


# =============================================================================
# _getWindowClass
# =============================================================================


class TestGetWindowClass:
    def test_appIdPreferred(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        w = MockCon(id=100, app_id="myapp", window_class="MyApp")
        assert mgr._getWindowClass(w) == "myapp"

    def test_fallbackToWindowClass(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        w = MockCon(id=100, app_id=None, window_class="MyApp")
        assert mgr._getWindowClass(w) == "MyApp"

    def test_noneIfBothMissing(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        w = MockCon(id=100, app_id=None, window_class=None)
        assert mgr._getWindowClass(w) is None
