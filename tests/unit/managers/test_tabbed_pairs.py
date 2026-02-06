"""Tests for the TabbedPairsLayoutManager."""

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


# =============================================================================
# Fixtures
# =============================================================================


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
# Initialization Tests
# =============================================================================


class TestTabbedPairsInit:
    def test_shortName(self):
        assert TabbedPairsLayoutManager.shortName == "TabbedPairs"

    def test_overrides(self):
        assert TabbedPairsLayoutManager.overridesMoveBinds is True
        assert TabbedPairsLayoutManager.overridesFocusBinds is True

    def test_init_empty(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        assert mgr.pairs == []
        assert mgr.unpairedWindows == []
        assert mgr.floatingWindowIds == set()

    def test_init_withWindows(self, mock_conn, default_config):
        ws = create_workspace(name="1", window_count=3)
        mgr = make_manager(mock_conn, ws, default_config)
        # All should be unpaired (no rules)
        assert len(mgr.unpairedWindows) == 3
        assert mgr.pairs == []

    def test_init_withPairRules(self, mock_conn, empty_workspace, temp_config):
        config = temp_config(
            '[layman]\ndefaultLayout = "TabbedPairs"\n'
            '[layman.pairRules]\nnvim = ["code", "vscode"]\n'
        )
        mgr = make_manager(mock_conn, empty_workspace, config)
        assert "nvim" in mgr.pairRules
        assert "code" in mgr.pairRules["nvim"]


# =============================================================================
# WindowPair Tests
# =============================================================================


class TestWindowPair:
    def test_create(self):
        pair = WindowPair(primary=1, secondary=2)
        assert pair.primary == 1
        assert pair.secondary == 2


# =============================================================================
# Window Addition Tests
# =============================================================================


class TestTabbedPairsWindowAdded:
    def test_firstWindow_unpaired(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        w = MockCon(id=100, name="w1")
        mgr.windowAdded(make_window_event(w), empty_workspace, w)
        assert 100 in mgr.unpairedWindows

    def test_manualPair_createdOnAdd(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.unpairedWindows = [100]
        mgr.pendingManualPair = 100

        w = MockCon(id=200, name="w2")
        mgr.windowAdded(make_window_event(w), empty_workspace, w)
        assert mgr.pendingManualPair is None
        assert len(mgr.pairs) == 1
        assert mgr.pairs[0].primary == 100
        assert mgr.pairs[0].secondary == 200

    def test_floatingWindow_notPaired(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        w = MockCon(id=100, floating="auto_on", type="floating_con")
        mgr.windowAdded(make_window_event(w), empty_workspace, w)
        assert 100 in mgr.floatingWindowIds
        assert mgr.unpairedWindows == []


# =============================================================================
# Window Removal Tests
# =============================================================================


class TestTabbedPairsWindowRemoved:
    def test_removeUnpaired(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.unpairedWindows = [100, 200]

        w = MockCon(id=100, name="w1")
        mgr.windowRemoved(make_window_event(w, "close"), empty_workspace, w)
        assert 100 not in mgr.unpairedWindows
        assert 200 in mgr.unpairedWindows

    def test_removePaired_breaksPair(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.pairs = [WindowPair(primary=100, secondary=200)]

        w = MockCon(id=200, name="w2")
        mgr.windowRemoved(make_window_event(w, "close"), empty_workspace, w)
        assert len(mgr.pairs) == 0
        assert 100 in mgr.unpairedWindows

    def test_removeFloating(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.floatingWindowIds = {100}
        w = MockCon(id=100, floating="auto_on", type="floating_con")
        mgr.windowRemoved(make_window_event(w, "close"), empty_workspace, w)
        assert 100 not in mgr.floatingWindowIds


# =============================================================================
# Command Tests
# =============================================================================


class TestTabbedPairsCommands:
    def test_pair_setPending(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.unpairedWindows = [100]
        w = MockCon(id=100, name="w1", focused=True)
        empty_workspace.nodes = [w]
        w.parent = empty_workspace
        mgr.onCommand("pair", empty_workspace)
        assert mgr.pendingManualPair == 100

    def test_unpair_breaksPair(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.pairs = [WindowPair(primary=100, secondary=200)]
        w = MockCon(id=100, name="w1", focused=True)
        empty_workspace.nodes = [w]
        w.parent = empty_workspace
        mgr.onCommand("unpair", empty_workspace)
        assert len(mgr.pairs) == 0
        assert 100 in mgr.unpairedWindows
        assert 200 in mgr.unpairedWindows

    def test_focusPair(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.pairs = [
            WindowPair(primary=100, secondary=101),
            WindowPair(primary=200, secondary=201),
        ]
        mgr.focusedPairIndex = 0
        mgr.onCommand("focus right", empty_workspace)
        assert mgr.focusedPairIndex == 1
        assert any("[con_id=200] focus" in c for c in mock_conn.commands_executed)

    def test_focusWithinPair(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.pairs = [WindowPair(primary=100, secondary=200)]
        w = MockCon(id=100, name="w1", focused=True)
        empty_workspace.nodes = [w]
        w.parent = empty_workspace
        mgr.onCommand("focus down", empty_workspace)
        assert any("[con_id=200] focus" in c for c in mock_conn.commands_executed)

    def test_unknownCommand(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        # Should not crash
        mgr.onCommand("unknown", empty_workspace)


# =============================================================================
# Pair Helpers
# =============================================================================


class TestTabbedPairsHelpers:
    def test_getPairForWindow_found(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        pair = WindowPair(primary=100, secondary=200)
        mgr.pairs = [pair]
        assert mgr._getPairForWindow(100) == pair
        assert mgr._getPairForWindow(200) == pair

    def test_getPairForWindow_notFound(
        self, mock_conn, empty_workspace, default_config
    ):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        assert mgr._getPairForWindow(999) is None

    def test_isFloating(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        w = MockCon(id=100, floating="auto_on", type="floating_con")
        assert mgr._isFloating(w) is True

    def test_isNotFloating(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        w = MockCon(id=100, type="con")
        assert mgr._isFloating(w) is False
