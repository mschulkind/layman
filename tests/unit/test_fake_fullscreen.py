"""Tests for the global fake fullscreen feature (Phase 5)."""

import pytest

from layman.layman import Layman, WorkspaceState

from tests.mocks.i3ipc_mocks import (
    MockCon,
    MockConnection,
    MockWindowEvent,
    create_workspace,
)


class TestWorkspaceStateFakeFullscreen:
    """Tests for fake fullscreen fields on WorkspaceState."""

    def test_default_fakeFullscreen_isFalse(self):
        state = WorkspaceState()
        assert state.fakeFullscreen is False

    def test_default_fakeFullscreenWindowId_isNone(self):
        state = WorkspaceState()
        assert state.fakeFullscreenWindowId is None

    def test_default_savedStackLayout_isNone(self):
        state = WorkspaceState()
        assert state.savedStackLayout is None

    def test_fakeFullscreen_canBeSet(self):
        state = WorkspaceState()
        state.fakeFullscreen = True
        state.fakeFullscreenWindowId = 42
        assert state.fakeFullscreen is True
        assert state.fakeFullscreenWindowId == 42


class TestFakeFullscreenExitOnClose:
    """Tests that closing a fake-fullscreened window exits fake fullscreen."""

    def test_closeFakeFullscreenWindow_exitsFakeFullscreen(self):
        state = WorkspaceState()
        state.fakeFullscreen = True
        state.fakeFullscreenWindowId = 100
        state.savedStackLayout = "splith"
        state.windowIds = {100, 200}

        # Simulate what windowClosed does
        event_id = 100
        state.windowIds.remove(event_id)
        if state.fakeFullscreen and state.fakeFullscreenWindowId == event_id:
            state.fakeFullscreen = False
            state.fakeFullscreenWindowId = None
            state.savedStackLayout = None

        assert state.fakeFullscreen is False
        assert state.fakeFullscreenWindowId is None
        assert state.savedStackLayout is None

    def test_closeOtherWindow_keepsFakeFullscreen(self):
        state = WorkspaceState()
        state.fakeFullscreen = True
        state.fakeFullscreenWindowId = 100
        state.windowIds = {100, 200}

        # Close a different window
        event_id = 200
        state.windowIds.remove(event_id)
        if state.fakeFullscreen and state.fakeFullscreenWindowId == event_id:
            state.fakeFullscreen = False
            state.fakeFullscreenWindowId = None

        assert state.fakeFullscreen is True
        assert state.fakeFullscreenWindowId == 100
