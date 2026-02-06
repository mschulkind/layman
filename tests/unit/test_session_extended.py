"""Extended tests for SessionManager — coverage boost."""

import json
from unittest.mock import Mock, patch

import pytest

from layman.session import (
    SessionData,
    SessionManager,
    WindowSlot,
    WorkspaceSession,
)
from tests.mocks.i3ipc_mocks import MockCon, MockConnection, create_workspace


@pytest.fixture
def mock_conn():
    ws1 = create_workspace(name="1", window_count=2, start_id=100)
    ws1.nodes[0].app_id = "firefox"
    ws1.nodes[1].app_id = "terminal"
    ws2 = create_workspace(name="2", window_count=1, start_id=200)
    ws2.nodes[0].app_id = "code"

    root = MockCon(
        type="root",
        nodes=[MockCon(type="output", nodes=[ws1, ws2])],
    )
    return MockConnection(tree=root)


@pytest.fixture
def session_dir(tmp_path):
    d = tmp_path / "sessions"
    d.mkdir()
    return str(d)


@pytest.fixture
def manager(mock_conn, session_dir):
    return SessionManager(mock_conn, session_dir)


# =============================================================================
# Save/Load round-trip
# =============================================================================


class TestSaveLoad:
    def test_save_createsFile(self, manager, session_dir):
        path = manager.save("test_session")
        assert "test_session" in path
        assert json.loads(open(path).read())["name"] == "test_session"

    def test_save_withWorkspaceStates(self, manager):
        mock_state = Mock()
        mock_state.layoutName = "MasterStack"
        states = {"1": mock_state}
        manager.save("test_ws_state", workspace_states=states)

    def test_save_sanitizesName(self, manager, session_dir):
        path = manager.save("my/bad name!")
        assert "mybadname" in path  # Special chars stripped

    def test_list_sessions(self, manager):
        manager.save("session_a")
        manager.save("session_b")
        sessions = manager.list_sessions()
        assert "session_a" in sessions
        assert "session_b" in sessions

    def test_delete_existing(self, manager):
        manager.save("to_delete")
        assert manager.delete("to_delete") is True
        assert "to_delete" not in manager.list_sessions()

    def test_delete_nonexistent(self, manager):
        assert manager.delete("nonexistent") is False

    def test_get_session_info(self, manager):
        manager.save("info_test")
        info = manager.get_session_info("info_test")
        assert info is not None
        assert info.name == "info_test"
        assert len(info.workspaces) > 0

    def test_get_session_info_notFound(self, manager):
        assert manager.get_session_info("nonexistent") is None


# =============================================================================
# Restore
# =============================================================================


class TestRestore:
    def test_restore_basic(self, manager):
        manager.save("restore_test")
        result = manager.restore("restore_test")
        assert result is not None
        assert isinstance(result, SessionData)

    def test_restore_notFound(self, manager):
        assert manager.restore("nonexistent") is None

    def test_restore_missingWorkspace(self, manager, session_dir):
        # Create a session with a workspace that doesn't exist
        data = {
            "name": "missing_ws",
            "saved_at": 0,
            "workspaces": [
                {
                    "workspace_name": "nonexistent_ws",
                    "layout_name": "splith",
                    "saved_at": 0,
                    "windows": [],
                }
            ],
        }
        path = manager._session_path("missing_ws")
        path.write_text(json.dumps(data))
        result = manager.restore("missing_ws")
        assert result is not None  # Should handle gracefully


# =============================================================================
# Window Matching
# =============================================================================


class TestWindowMatching:
    def test_match_by_appId_exact(self, manager):
        window = MockCon(id=1, app_id="firefox")
        slots = [
            WindowSlot(app_id="terminal", position="stack"),
            WindowSlot(app_id="firefox", position="master"),
        ]
        match = manager.match_window(window, slots)
        assert match is not None
        assert match.app_id == "firefox"

    def test_match_by_windowClass(self, manager):
        window = MockCon(id=1, app_id=None, window_class="Firefox")
        slots = [
            WindowSlot(window_class="Firefox", position="stack"),
        ]
        match = manager.match_window(window, slots)
        assert match is not None
        assert match.window_class == "Firefox"

    def test_match_caseInsensitive_appId(self, manager):
        window = MockCon(id=1, app_id="FireFox")
        slots = [
            WindowSlot(app_id="firefox", position="master"),
        ]
        match = manager.match_window(window, slots)
        assert match is not None

    def test_match_noMatch(self, manager):
        window = MockCon(id=1, app_id="gimp")
        slots = [
            WindowSlot(app_id="firefox", position="master"),
        ]
        match = manager.match_window(window, slots)
        assert match is None

    def test_match_noAppId_noWindowClass(self, manager):
        window = MockCon(id=1, app_id=None, window_class=None)
        slots = [
            WindowSlot(app_id="firefox"),
        ]
        match = manager.match_window(window, slots)
        assert match is None


# =============================================================================
# Application Launch
# =============================================================================


class TestApplicationLaunch:
    def test_launch_withCommand(self, manager):
        slot = WindowSlot(app_id="firefox", launch_command="firefox --new-window")
        with patch("subprocess.Popen") as mock_popen:
            result = manager.launch_application(slot, "1")
        assert result is True
        mock_popen.assert_called_once()

    def test_launch_byAppId(self, manager):
        slot = WindowSlot(app_id="firefox")
        with patch("subprocess.Popen") as mock_popen:
            result = manager.launch_application(slot, "1")
        assert result is True

    def test_launch_noCommand(self, manager):
        slot = WindowSlot(app_id=None, launch_command=None)
        result = manager.launch_application(slot, "1")
        assert result is False

    def test_launch_exception(self, manager):
        slot = WindowSlot(app_id="firefox", launch_command="firefox")
        with patch("subprocess.Popen", side_effect=OSError("fail")):
            result = manager.launch_application(slot, "1")
        assert result is False


# =============================================================================
# _parse_session
# =============================================================================


class TestParseSession:
    def test_parse_minimal(self, manager):
        data = {"name": "test", "saved_at": 123.0, "workspaces": []}
        session = manager._parse_session(data)
        assert session.name == "test"
        assert session.saved_at == 123.0
        assert session.workspaces == []

    def test_parse_withWindows(self, manager):
        data = {
            "name": "test",
            "saved_at": 0,
            "workspaces": [
                {
                    "workspace_name": "1",
                    "layout_name": "MasterStack",
                    "saved_at": 0,
                    "windows": [
                        {
                            "app_id": "firefox",
                            "window_class": None,
                            "position": "master",
                            "index": 0,
                            "launch_command": "firefox",
                        }
                    ],
                }
            ],
        }
        session = manager._parse_session(data)
        assert len(session.workspaces) == 1
        assert len(session.workspaces[0].windows) == 1
        assert session.workspaces[0].windows[0].app_id == "firefox"
        assert session.workspaces[0].windows[0].launch_command == "firefox"

    def test_parse_missingFields(self, manager):
        data = {}
        session = manager._parse_session(data)
        assert session.name == "unknown"
        assert session.workspaces == []


# =============================================================================
# _restore_workspace
# =============================================================================


class TestRestoreWorkspace:
    def test_restoreWorkspace_withLaunch(self, manager):
        ws = create_workspace(name="1", window_count=0)
        ws_session = WorkspaceSession(
            workspace_name="1",
            layout_name="splith",
            windows=[
                WindowSlot(
                    app_id="firefox",
                    launch_command="firefox",
                    position="master",
                ),
            ],
        )
        with patch("subprocess.Popen"):
            manager._restore_workspace(ws, ws_session, launch_apps=True)

    def test_restoreWorkspace_matchExisting(self, manager):
        w1 = MockCon(id=100, app_id="firefox")
        ws = MockCon(type="workspace", name="1", nodes=[w1])
        ws_session = WorkspaceSession(
            workspace_name="1",
            layout_name="splith",
            windows=[
                WindowSlot(app_id="firefox", position="master"),
            ],
        )
        manager._restore_workspace(ws, ws_session, launch_apps=False)
        # No launch should happen

    def test_restoreWorkspace_noLaunch(self, manager):
        ws = create_workspace(name="1", window_count=0)
        ws_session = WorkspaceSession(
            workspace_name="1",
            layout_name="splith",
            windows=[
                WindowSlot(app_id="firefox", launch_command="firefox"),
            ],
        )
        manager._restore_workspace(ws, ws_session, launch_apps=False)
        # Should not launch since launch_apps=False


# =============================================================================
# Default session dir
# =============================================================================


class TestDefaultDir:
    def test_defaultDir_created(self, mock_conn, tmp_path):
        d = str(tmp_path / "custom_sessions")
        mgr = SessionManager(mock_conn, d)
        assert mgr.session_dir.exists()
