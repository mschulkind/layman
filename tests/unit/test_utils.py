"""
Unit tests for layman.utils module.

Tests utility functions for:
- Finding focused window
- Finding focused workspace
- Config path resolution
"""

import pytest
from unittest.mock import Mock, patch

from layman.utils import findFocusedWindow, findFocusedWorkspace, getConfigPath
from tests.mocks.i3ipc_mocks import MockConnection, MockCon


class TestFindFocusedWindow:
    """Tests for findFocusedWindow() function."""

    def test_findFocusedWindow_focusedExists_returnsWindow(self):
        """Should return the focused window when one exists."""
        focused = MockCon(id=100, name="Focused", focused=True)
        workspace = MockCon(name="1", type="workspace", nodes=[focused])
        root = MockCon(type="root", nodes=[workspace])
        connection = MockConnection(tree=root)

        result = findFocusedWindow(connection)

        assert result is not None
        assert result.id == 100

    def test_findFocusedWindow_noFocused_returnsNone(self):
        """Should return None when no window is focused."""
        window = MockCon(id=100, focused=False)
        workspace = MockCon(name="1", type="workspace", nodes=[window])
        root = MockCon(type="root", nodes=[workspace])
        connection = MockConnection(tree=root)

        result = findFocusedWindow(connection)

        assert result is None

    def test_findFocusedWindow_emptyTree_returnsNone(self):
        """Should return None for empty tree."""
        connection = MockConnection(tree=MockCon(type="root"))

        result = findFocusedWindow(connection)

        assert result is None


class TestFindFocusedWorkspace:
    """Tests for findFocusedWorkspace() function."""

    def test_findFocusedWorkspace_focusedExists_returnsWorkspace(self):
        """Should return the workspace of the focused window."""
        focused = MockCon(id=100, focused=True)
        workspace = MockCon(name="1", type="workspace", nodes=[focused])
        focused.parent = workspace
        root = MockCon(type="root", nodes=[workspace])
        connection = MockConnection(tree=root)

        result = findFocusedWorkspace(connection)

        assert result is not None
        assert result.name == "1"
        assert result.type == "workspace"

    def test_findFocusedWorkspace_noFocused_returnsNone(self):
        """Should return None when no window is focused."""
        window = MockCon(id=100, focused=False)
        workspace = MockCon(name="1", type="workspace", nodes=[window])
        root = MockCon(type="root", nodes=[workspace])
        connection = MockConnection(tree=root)

        result = findFocusedWorkspace(connection)

        assert result is None


class TestGetConfigPath:
    """Tests for getConfigPath() function."""

    def test_getConfigPath_withConfigArg_returnsArgPath(self):
        """Should return path from -c/--config argument."""
        with patch("sys.argv", ["layman", "-c", "/custom/config.toml"]):
            result = getConfigPath()
            assert result == "/custom/config.toml"

    def test_getConfigPath_noArg_returnsDefault(self):
        """Should return default path when no argument given."""
        with patch("sys.argv", ["layman"]):
            result = getConfigPath()
            assert result is None or "config.toml" in result

    def test_getConfigPath_longForm_works(self):
        """Should work with --config long form."""
        with patch("sys.argv", ["layman", "--config", "/another/path.toml"]):
            result = getConfigPath()
            assert result == "/another/path.toml"
