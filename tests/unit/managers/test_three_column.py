"""Tests for the ThreeColumnLayoutManager."""

import pytest

from layman.managers.three_column import ThreeColumnLayoutManager, StackLayout

from tests.mocks.i3ipc_mocks import (
    MockCon,
    MockConnection,
    MockRect,
    MockWindowEvent,
    create_workspace,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_config(tmp_path):
    """Factory fixture for creating temporary config files."""
    from layman.config import LaymanConfig

    def _create_config(content: str) -> LaymanConfig:
        config_path = tmp_path / "config.toml"
        config_path.write_text(content)
        return LaymanConfig(str(config_path))

    return _create_config


@pytest.fixture
def default_config(temp_config):
    """Default config with ThreeColumn defaults."""
    return temp_config('[layman]\ndefaultLayout = "ThreeColumn"\n')


@pytest.fixture
def mock_conn():
    """Mock i3ipc connection."""
    return MockConnection()


@pytest.fixture
def empty_workspace():
    return create_workspace(name="1", window_count=0)


@pytest.fixture
def single_window_workspace():
    return create_workspace(name="1", window_count=1)


@pytest.fixture
def two_window_workspace():
    return create_workspace(name="1", window_count=2)


@pytest.fixture
def three_window_workspace():
    return create_workspace(name="1", window_count=3)


@pytest.fixture
def five_window_workspace():
    return create_workspace(name="1", window_count=5)


def make_manager(conn, workspace, config):
    """Create a ThreeColumnLayoutManager with the given config."""
    return ThreeColumnLayoutManager(conn, workspace, "1", config)


def make_window_event(window, change="new"):
    """Create a mock window event."""
    return MockWindowEvent(change=change, container=window)


# =============================================================================
# Initialization Tests
# =============================================================================


class TestThreeColumnInit:
    """Tests for ThreeColumnLayoutManager initialization."""

    def test_shortName(self):
        assert ThreeColumnLayoutManager.shortName == "ThreeColumn"

    def test_overrides(self):
        assert ThreeColumnLayoutManager.overridesMoveBinds is True
        assert ThreeColumnLayoutManager.overridesFocusBinds is True
        assert ThreeColumnLayoutManager.supportsFloating is True

    def test_init_emptyWorkspace(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        assert mgr.masterId is None
        assert mgr.leftStack == []
        assert mgr.rightStack == []

    def test_init_singleWindow(
        self, mock_conn, single_window_workspace, default_config
    ):
        mgr = make_manager(mock_conn, single_window_workspace, default_config)
        assert mgr.masterId == 100
        assert mgr.leftStack == []
        assert mgr.rightStack == []

    def test_init_twoWindows(self, mock_conn, two_window_workspace, default_config):
        mgr = make_manager(mock_conn, two_window_workspace, default_config)
        assert mgr.masterId is not None
        # One window should be in a stack
        assert len(mgr.leftStack) + len(mgr.rightStack) == 1

    def test_init_threeWindows(
        self, mock_conn, three_window_workspace, default_config
    ):
        mgr = make_manager(mock_conn, three_window_workspace, default_config)
        assert mgr.masterId is not None
        assert len(mgr.leftStack) + len(mgr.rightStack) == 2

    def test_init_fiveWindows_balanced(
        self, mock_conn, five_window_workspace, default_config
    ):
        mgr = make_manager(mock_conn, five_window_workspace, default_config)
        assert mgr.masterId is not None
        # 4 stack windows: balanced means right gets 2, left gets 2
        assert len(mgr.leftStack) == 2
        assert len(mgr.rightStack) == 2

    def test_init_defaultConfig(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        assert mgr.masterWidth == 50
        assert mgr.stackLayout == StackLayout.SPLITV
        assert mgr.balanceStacks is True


class TestThreeColumnConfig:
    """Tests for configuration parsing."""

    def test_customMasterWidth(self, mock_conn, empty_workspace, temp_config):
        config = temp_config(
            '[layman]\ndefaultLayout = "ThreeColumn"\nmasterWidth = 60\n'
        )
        mgr = make_manager(mock_conn, empty_workspace, config)
        assert mgr.masterWidth == 60

    def test_invalidMasterWidth_zero(self, mock_conn, empty_workspace, temp_config):
        config = temp_config(
            '[layman]\ndefaultLayout = "ThreeColumn"\nmasterWidth = 0\n'
        )
        with pytest.raises(Exception):
            make_manager(mock_conn, empty_workspace, config)

    def test_invalidMasterWidth_100(self, mock_conn, empty_workspace, temp_config):
        config = temp_config(
            '[layman]\ndefaultLayout = "ThreeColumn"\nmasterWidth = 100\n'
        )
        with pytest.raises(Exception):
            make_manager(mock_conn, empty_workspace, config)

    def test_stackLayout_tabbed(self, mock_conn, empty_workspace, temp_config):
        config = temp_config(
            '[layman]\ndefaultLayout = "ThreeColumn"\nstackLayout = "tabbed"\n'
        )
        mgr = make_manager(mock_conn, empty_workspace, config)
        assert mgr.stackLayout == StackLayout.TABBED

    def test_balanceStacks_false(self, mock_conn, empty_workspace, temp_config):
        config = temp_config(
            '[layman]\ndefaultLayout = "ThreeColumn"\nbalanceStacks = false\n'
        )
        mgr = make_manager(mock_conn, empty_workspace, config)
        assert mgr.balanceStacks is False


# =============================================================================
# Window Addition Tests
# =============================================================================


class TestThreeColumnWindowAdded:
    """Tests for window addition."""

    def test_firstWindow_becomesMaster(
        self, mock_conn, empty_workspace, default_config
    ):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        window = MockCon(id=100, name="w1")
        event = make_window_event(window)
        mgr.windowAdded(event, empty_workspace, window)
        assert mgr.masterId == 100

    def test_secondWindow_goesToRightStack(
        self, mock_conn, empty_workspace, default_config
    ):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.masterId = 100

        window = MockCon(id=200, name="w2")
        event = make_window_event(window)
        mgr.windowAdded(event, empty_workspace, window)
        assert 200 in mgr.rightStack

    def test_thirdWindow_goesToLeftStack(
        self, mock_conn, empty_workspace, default_config
    ):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.masterId = 100
        mgr.rightStack = [200]

        window = MockCon(id=300, name="w3")
        event = make_window_event(window)
        mgr.windowAdded(event, empty_workspace, window)
        assert 300 in mgr.leftStack

    def test_unbalanced_allGoToRight(
        self, mock_conn, empty_workspace, temp_config
    ):
        config = temp_config(
            '[layman]\ndefaultLayout = "ThreeColumn"\nbalanceStacks = false\n'
        )
        mgr = make_manager(mock_conn, empty_workspace, config)
        mgr.masterId = 100

        for i in range(200, 500, 100):
            w = MockCon(id=i, name=f"w{i}")
            mgr.windowAdded(make_window_event(w), empty_workspace, w)

        assert len(mgr.rightStack) == 3
        assert len(mgr.leftStack) == 0

    def test_floatingWindow_notAddedToLayout(
        self, mock_conn, empty_workspace, default_config
    ):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        window = MockCon(id=100, name="float", floating="auto_on", type="floating_con")
        event = make_window_event(window)
        mgr.windowAdded(event, empty_workspace, window)
        assert mgr.masterId is None
        assert 100 in mgr.floatingWindowIds


# =============================================================================
# Window Removal Tests
# =============================================================================


class TestThreeColumnWindowRemoved:
    """Tests for window removal."""

    def test_removeMaster_promotesFromRight(
        self, mock_conn, empty_workspace, default_config
    ):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.masterId = 100
        mgr.rightStack = [200, 300]
        mgr.leftStack = [400]

        master = MockCon(id=100, name="master")
        mgr.windowRemoved(make_window_event(master, "close"), empty_workspace, master)
        assert mgr.masterId == 200
        assert mgr.rightStack == [300]

    def test_removeMaster_promotesFromLeft_ifRightEmpty(
        self, mock_conn, empty_workspace, default_config
    ):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.masterId = 100
        mgr.leftStack = [200]
        mgr.rightStack = []

        master = MockCon(id=100, name="master")
        mgr.windowRemoved(make_window_event(master, "close"), empty_workspace, master)
        assert mgr.masterId == 200

    def test_removeMaster_lastWindow(
        self, mock_conn, empty_workspace, default_config
    ):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.masterId = 100

        master = MockCon(id=100, name="master")
        mgr.windowRemoved(make_window_event(master, "close"), empty_workspace, master)
        assert mgr.masterId is None

    def test_removeFromLeftStack(
        self, mock_conn, empty_workspace, default_config
    ):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.masterId = 100
        mgr.leftStack = [200, 300]

        window = MockCon(id=200, name="w")
        mgr.windowRemoved(make_window_event(window, "close"), empty_workspace, window)
        assert mgr.leftStack == [300]

    def test_removeFromRightStack(
        self, mock_conn, empty_workspace, default_config
    ):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.masterId = 100
        mgr.rightStack = [200, 300]

        window = MockCon(id=200, name="w")
        mgr.windowRemoved(make_window_event(window, "close"), empty_workspace, window)
        assert mgr.rightStack == [300]


# =============================================================================
# Command Tests
# =============================================================================


class TestThreeColumnCommands:
    """Tests for command handling."""

    def test_swapMaster(self, mock_conn, default_config):
        ws = create_workspace(name="1", window_count=3)
        ws.nodes[0].focused = True
        mgr = make_manager(mock_conn, ws, default_config)

        # Master should be ws.nodes[0] (focused), find a stack window
        stack_windows = mgr.leftStack + mgr.rightStack
        assert len(stack_windows) >= 1

        # Focus a stack window and swap
        stackId = stack_windows[0]
        stackWindow = ws.find_by_id(stackId)
        if stackWindow:
            ws.nodes[0].focused = False
            stackWindow.focused = True
            mgr.onCommand("swap master", ws)
            assert mgr.masterId == stackId

    def test_moveToMaster(self, mock_conn, default_config):
        ws = create_workspace(name="1", window_count=3)
        ws.nodes[0].focused = True
        mgr = make_manager(mock_conn, ws, default_config)

        stackId = (mgr.leftStack + mgr.rightStack)[0]
        stackWindow = ws.find_by_id(stackId)
        if stackWindow:
            ws.nodes[0].focused = False
            stackWindow.focused = True
            origMaster = mgr.masterId
            mgr.onCommand("move to master", ws)
            assert mgr.masterId == stackId
            # Old master should be in a stack
            assert origMaster in mgr.leftStack or origMaster in mgr.rightStack

    def test_focusMaster(self, mock_conn, default_config):
        ws = create_workspace(name="1", window_count=2)
        ws.nodes[0].focused = True
        mgr = make_manager(mock_conn, ws, default_config)
        mgr.onCommand("focus master", ws)
        assert any(
            f"[con_id={mgr.masterId}] focus" in cmd
            for cmd in mock_conn.commands_executed
        )

    def test_toggleStackLayout(self, mock_conn, default_config):
        ws = create_workspace(name="1", window_count=3)
        ws.nodes[0].focused = True
        mgr = make_manager(mock_conn, ws, default_config)
        assert mgr.stackLayout == StackLayout.SPLITV
        mgr.onCommand("toggle", ws)
        assert mgr.stackLayout == StackLayout.SPLITH

    def test_maximize(self, mock_conn, default_config):
        ws = create_workspace(name="1", window_count=3)
        ws.nodes[0].focused = True
        mgr = make_manager(mock_conn, ws, default_config)
        assert mgr.maximized is False
        mgr.onCommand("maximize", ws)
        assert mgr.maximized is True
        mgr.onCommand("maximize", ws)
        assert mgr.maximized is False

    def test_balance(self, mock_conn, default_config):
        ws = create_workspace(name="1", window_count=5)
        ws.nodes[0].focused = True
        mgr = make_manager(mock_conn, ws, default_config)
        # Force unbalanced state
        mgr.rightStack = list(mgr.rightStack) + list(mgr.leftStack)
        mgr.leftStack = []
        mgr.onCommand("balance", ws)
        # Should be balanced now
        assert abs(len(mgr.leftStack) - len(mgr.rightStack)) <= 1

    def test_unknownCommand(self, mock_conn, default_config):
        ws = create_workspace(name="1", window_count=1)
        ws.nodes[0].focused = True
        mgr = make_manager(mock_conn, ws, default_config)
        # Should not raise
        mgr.onCommand("unknown_command", ws)


# =============================================================================
# Column Identification Tests
# =============================================================================


class TestThreeColumnHelpers:
    """Tests for helper methods."""

    def test_getWindowColumn_master(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.masterId = 100
        assert mgr._getWindowColumn(100) == "master"

    def test_getWindowColumn_left(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.leftStack = [200]
        assert mgr._getWindowColumn(200) == "left"

    def test_getWindowColumn_right(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.rightStack = [300]
        assert mgr._getWindowColumn(300) == "right"

    def test_getWindowColumn_unknown(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        assert mgr._getWindowColumn(999) is None

    def test_getAllWindowIds(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.masterId = 100
        mgr.leftStack = [200, 300]
        mgr.rightStack = [400, 500]
        assert mgr._getAllWindowIds() == [200, 300, 100, 400, 500]

    def test_getFirstInColumn(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.masterId = 100
        mgr.leftStack = [200]
        mgr.rightStack = [300]
        assert mgr._getFirstInColumn("master") == 100
        assert mgr._getFirstInColumn("left") == 200
        assert mgr._getFirstInColumn("right") == 300

    def test_getFirstInColumn_empty(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        assert mgr._getFirstInColumn("left") is None
        assert mgr._getFirstInColumn("right") is None


# =============================================================================
# Floating Window Tests
# =============================================================================


class TestThreeColumnFloating:
    """Tests for floating window handling."""

    def test_floatingWindow_tracked(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        window = MockCon(id=100, floating="auto_on", type="floating_con")
        mgr.windowAdded(make_window_event(window), empty_workspace, window)
        assert 100 in mgr.floatingWindowIds
        assert mgr.masterId is None

    def test_floatingRemoved(self, mock_conn, empty_workspace, default_config):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.floatingWindowIds = {100}
        window = MockCon(id=100, floating="auto_on", type="floating_con")
        mgr.windowRemoved(make_window_event(window, "close"), empty_workspace, window)
        assert 100 not in mgr.floatingWindowIds

    def test_windowFloating_tiledToFloat(
        self, mock_conn, empty_workspace, default_config
    ):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.masterId = 100
        window = MockCon(id=100, floating="auto_on", type="floating_con")
        mgr.windowFloating(make_window_event(window), empty_workspace, window)
        assert mgr.masterId != 100
        assert 100 in mgr.floatingWindowIds

    def test_windowFloating_floatToTiled(
        self, mock_conn, empty_workspace, default_config
    ):
        mgr = make_manager(mock_conn, empty_workspace, default_config)
        mgr.floatingWindowIds = {100}
        window = MockCon(id=100, floating=None, type="con")
        mgr.windowFloating(make_window_event(window), empty_workspace, window)
        assert 100 not in mgr.floatingWindowIds
        assert mgr.masterId == 100
