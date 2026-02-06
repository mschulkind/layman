"""Tests for multi-master support in MasterStack (Phase 9)."""

import pytest

from layman.managers.master_stack import MasterStackLayoutManager

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
def mock_conn():
    return MockConnection()


# =============================================================================
# Config Tests
# =============================================================================


class TestMultiMasterConfig:
    def test_defaultMasterCount_is1(self, mock_conn, temp_config):
        config = temp_config('[layman]\ndefaultLayout = "MasterStack"\n')
        ws = create_workspace(name="1", window_count=0)
        mgr = MasterStackLayoutManager(mock_conn, ws, "1", config)
        assert mgr.masterCount == 1

    def test_masterCount_fromConfig(self, mock_conn, temp_config):
        config = temp_config(
            '[layman]\ndefaultLayout = "MasterStack"\nmasterCount = 2\n'
        )
        ws = create_workspace(name="1", window_count=0)
        mgr = MasterStackLayoutManager(mock_conn, ws, "1", config)
        assert mgr.masterCount == 2

    def test_invalidMasterCount_raisesError(self, mock_conn, temp_config):
        from layman.config import ConfigError

        config = temp_config(
            '[layman]\ndefaultLayout = "MasterStack"\nmasterCount = 0\n'
        )
        ws = create_workspace(name="1", window_count=0)
        with pytest.raises(ConfigError):
            MasterStackLayoutManager(mock_conn, ws, "1", config)

    def test_negativeMasterCount_raisesError(self, mock_conn, temp_config):
        from layman.config import ConfigError

        config = temp_config(
            '[layman]\ndefaultLayout = "MasterStack"\nmasterCount = -1\n'
        )
        ws = create_workspace(name="1", window_count=0)
        with pytest.raises(ConfigError):
            MasterStackLayoutManager(mock_conn, ws, "1", config)


# =============================================================================
# Master/Stack ID Helpers
# =============================================================================


class TestGetMasterStackIds:
    def test_getMasterIds_single(self, mock_conn, temp_config):
        config = temp_config('[layman]\ndefaultLayout = "MasterStack"\n')
        ws = create_workspace(name="1", window_count=0)
        mgr = MasterStackLayoutManager(mock_conn, ws, "1", config)
        mgr.windowIds = [100, 200, 300]
        assert mgr.getMasterIds() == [100]

    def test_getMasterIds_multi(self, mock_conn, temp_config):
        config = temp_config(
            '[layman]\ndefaultLayout = "MasterStack"\nmasterCount = 2\n'
        )
        ws = create_workspace(name="1", window_count=0)
        mgr = MasterStackLayoutManager(mock_conn, ws, "1", config)
        mgr.windowIds = [100, 200, 300]
        assert mgr.getMasterIds() == [100, 200]

    def test_getStackIds_single(self, mock_conn, temp_config):
        config = temp_config('[layman]\ndefaultLayout = "MasterStack"\n')
        ws = create_workspace(name="1", window_count=0)
        mgr = MasterStackLayoutManager(mock_conn, ws, "1", config)
        mgr.windowIds = [100, 200, 300]
        assert mgr.getStackIds() == [200, 300]

    def test_getStackIds_multi(self, mock_conn, temp_config):
        config = temp_config(
            '[layman]\ndefaultLayout = "MasterStack"\nmasterCount = 2\n'
        )
        ws = create_workspace(name="1", window_count=0)
        mgr = MasterStackLayoutManager(mock_conn, ws, "1", config)
        mgr.windowIds = [100, 200, 300]
        assert mgr.getStackIds() == [300]

    def test_getStackIds_allMasters(self, mock_conn, temp_config):
        config = temp_config(
            '[layman]\ndefaultLayout = "MasterStack"\nmasterCount = 3\n'
        )
        ws = create_workspace(name="1", window_count=0)
        mgr = MasterStackLayoutManager(mock_conn, ws, "1", config)
        mgr.windowIds = [100, 200, 300]
        assert mgr.getStackIds() == []


# =============================================================================
# Add/Remove Master Commands
# =============================================================================


class TestAddRemoveMaster:
    def test_addMaster_incrementsCount(self, mock_conn, temp_config):
        config = temp_config('[layman]\ndefaultLayout = "MasterStack"\n')
        ws = create_workspace(name="1", window_count=3)
        mgr = MasterStackLayoutManager(mock_conn, ws, "1", config)
        assert mgr.masterCount == 1
        mgr._addMaster(ws)
        assert mgr.masterCount == 2

    def test_removeMaster_decrementsCount(self, mock_conn, temp_config):
        config = temp_config(
            '[layman]\ndefaultLayout = "MasterStack"\nmasterCount = 2\n'
        )
        ws = create_workspace(name="1", window_count=3)
        mgr = MasterStackLayoutManager(mock_conn, ws, "1", config)
        assert mgr.masterCount == 2
        mgr._removeMaster(ws)
        assert mgr.masterCount == 1

    def test_removeMaster_cannotGoBelowOne(self, mock_conn, temp_config):
        config = temp_config('[layman]\ndefaultLayout = "MasterStack"\n')
        ws = create_workspace(name="1", window_count=3)
        mgr = MasterStackLayoutManager(mock_conn, ws, "1", config)
        mgr._removeMaster(ws)
        assert mgr.masterCount == 1  # Stays at 1

    def test_addMaster_cannotExceedWindowCount(self, mock_conn, temp_config):
        config = temp_config(
            '[layman]\ndefaultLayout = "MasterStack"\nmasterCount = 3\n'
        )
        ws = create_workspace(name="1", window_count=3)
        mgr = MasterStackLayoutManager(mock_conn, ws, "1", config)
        mgr._addMaster(ws)
        assert mgr.masterCount == 3  # Can't go higher


# =============================================================================
# Command Dispatch Tests
# =============================================================================


class TestMultiMasterCommands:
    def test_masterAddCommand(self, mock_conn, temp_config):
        config = temp_config('[layman]\ndefaultLayout = "MasterStack"\n')
        ws = create_workspace(name="1", window_count=3)
        mgr = MasterStackLayoutManager(mock_conn, ws, "1", config)
        focused = ws.nodes[0]
        focused.focused = True
        mgr.onCommand("master add", ws)
        assert mgr.masterCount == 2

    def test_masterRemoveCommand(self, mock_conn, temp_config):
        config = temp_config(
            '[layman]\ndefaultLayout = "MasterStack"\nmasterCount = 2\n'
        )
        ws = create_workspace(name="1", window_count=3)
        mgr = MasterStackLayoutManager(mock_conn, ws, "1", config)
        focused = ws.nodes[0]
        focused.focused = True
        mgr.onCommand("master remove", ws)
        assert mgr.masterCount == 1
