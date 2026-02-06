"""Tests for the session save/restore feature (Phase 8)."""

import json
import os
import time

import pytest

from layman.session import (
    SessionData,
    SessionManager,
    WindowSlot,
    WorkspaceSession,
)

from tests.mocks.i3ipc_mocks import (
    MockCon,
    MockConnection,
    MockRect,
    create_workspace,
    create_tree_with_workspaces,
)


# =============================================================================
# Data Model Tests
# =============================================================================


class TestWindowSlot:
    def test_defaults(self):
        slot = WindowSlot()
        assert slot.app_id is None
        assert slot.window_class is None
        assert slot.position == "stack"
        assert slot.index == 0
        assert slot.launch_command is None

    def test_withValues(self):
        slot = WindowSlot(app_id="firefox", position="master", launch_command="firefox")
        assert slot.app_id == "firefox"
        assert slot.position == "master"
        assert slot.launch_command == "firefox"


class TestWorkspaceSession:
    def test_defaults(self):
        ws = WorkspaceSession(workspace_name="1", layout_name="MasterStack")
        assert ws.workspace_name == "1"
        assert ws.layout_name == "MasterStack"
        assert ws.windows == []

    def test_withWindows(self):
        ws = WorkspaceSession(
            workspace_name="1",
            layout_name="MasterStack",
            windows=[WindowSlot(app_id="vim"), WindowSlot(app_id="firefox")],
        )
        assert len(ws.windows) == 2


class TestSessionData:
    def test_defaults(self):
        session = SessionData()
        assert session.name == "default"
        assert session.workspaces == []

    def test_withWorkspaces(self):
        session = SessionData(
            name="test",
            workspaces=[
                WorkspaceSession(workspace_name="1", layout_name="MasterStack")
            ],
        )
        assert len(session.workspaces) == 1


# =============================================================================
# SessionManager Tests
# =============================================================================


class TestSessionManager:
    @pytest.fixture
    def session_dir(self, tmp_path):
        return str(tmp_path / "sessions")

    @pytest.fixture
    def mock_conn(self):
        tree = create_tree_with_workspaces(
            [
                {"name": "1", "window_count": 2},
                {"name": "2", "window_count": 1},
            ]
        )
        return MockConnection(tree=tree)

    @pytest.fixture
    def manager(self, mock_conn, session_dir):
        return SessionManager(mock_conn, session_dir)

    def test_init_createsDir(self, mock_conn, session_dir):
        SessionManager(mock_conn, session_dir)
        assert os.path.isdir(session_dir)

    def test_save_createsFile(self, manager, session_dir):
        path = manager.save("test_session")
        assert os.path.exists(path)

    def test_save_validJson(self, manager):
        path = manager.save("test_session")
        with open(path) as f:
            data = json.load(f)
        assert data["name"] == "test_session"
        assert len(data["workspaces"]) == 2

    def test_save_includesWindows(self, manager):
        path = manager.save("test_session")
        with open(path) as f:
            data = json.load(f)
        # First workspace has 2 windows
        ws1 = data["workspaces"][0]
        assert len(ws1["windows"]) == 2

    def test_listSessions_empty(self, manager):
        assert manager.list_sessions() == []

    def test_listSessions_afterSave(self, manager):
        manager.save("session_a")
        manager.save("session_b")
        sessions = manager.list_sessions()
        assert "session_a" in sessions
        assert "session_b" in sessions

    def test_delete_removesFile(self, manager):
        manager.save("to_delete")
        assert manager.delete("to_delete") is True
        assert "to_delete" not in manager.list_sessions()

    def test_delete_nonexistent(self, manager):
        assert manager.delete("nonexistent") is False

    def test_getSessionInfo(self, manager):
        manager.save("info_test")
        info = manager.get_session_info("info_test")
        assert info is not None
        assert info.name == "info_test"
        assert len(info.workspaces) == 2

    def test_getSessionInfo_notFound(self, manager):
        assert manager.get_session_info("nonexistent") is None

    def test_restore_nonexistent(self, manager):
        assert manager.restore("nonexistent") is None


# =============================================================================
# Window Matching Tests
# =============================================================================


class TestWindowMatching:
    @pytest.fixture
    def manager(self, tmp_path):
        conn = MockConnection()
        return SessionManager(conn, str(tmp_path / "sessions"))

    def test_matchByAppId(self, manager):
        window = MockCon(id=1, name="vim", app_id="vim")
        slots = [
            WindowSlot(app_id="firefox"),
            WindowSlot(app_id="vim"),
        ]
        match = manager.match_window(window, slots)
        assert match is not None
        assert match.app_id == "vim"

    def test_matchByWindowClass(self, manager):
        window = MockCon(id=1, name="Firefox", window_class="Firefox")
        slots = [WindowSlot(window_class="Firefox")]
        match = manager.match_window(window, slots)
        assert match is not None
        assert match.window_class == "Firefox"

    def test_noMatch(self, manager):
        window = MockCon(id=1, name="test")
        slots = [WindowSlot(app_id="firefox")]
        match = manager.match_window(window, slots)
        assert match is None

    def test_caseInsensitiveAppId(self, manager):
        window = MockCon(id=1, name="vim", app_id="VIM")
        slots = [WindowSlot(app_id="vim")]
        match = manager.match_window(window, slots)
        assert match is not None


# =============================================================================
# Session Path Sanitization
# =============================================================================


class TestSessionPath:
    def test_normalName(self, tmp_path):
        conn = MockConnection()
        mgr = SessionManager(conn, str(tmp_path / "sessions"))
        path = mgr._session_path("my_session")
        assert path.name == "my_session.json"

    def test_specialChars_sanitized(self, tmp_path):
        conn = MockConnection()
        mgr = SessionManager(conn, str(tmp_path / "sessions"))
        path = mgr._session_path("my/../session")
        # Slashes are stripped, only safe characters remain
        assert "/" not in path.name

    def test_emptyName(self, tmp_path):
        conn = MockConnection()
        mgr = SessionManager(conn, str(tmp_path / "sessions"))
        path = mgr._session_path("")
        assert path.name == ".json"
