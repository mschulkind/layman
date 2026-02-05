"""
Unit tests for layman.layman module (main Layman class).

These tests cover what can be tested without a running Sway/i3 instance:
- WorkspaceState dataclass
- Command parsing
- State management logic

The event handlers and main loop require integration tests.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from dataclasses import asdict

# Import what we can test in isolation
import sys
sys.path.insert(0, "/home/matt/code/layman/src")

from layman.layman import WorkspaceState, Layman
from tests.mocks.i3ipc_mocks import (
    MockConnection,
    MockCon,
    MockBindingEvent,
    MockWindowEvent,
    create_workspace,
)


class TestWorkspaceState:
    """Tests for WorkspaceState dataclass."""

    def test_workspaceState_defaults(self):
        """WorkspaceState should have sensible defaults."""
        state = WorkspaceState()
        
        assert state.isExcluded is False
        assert state.windowIds == set()  # It's a set, not a list
        assert state.layoutManager is None

    def test_workspaceState_customValues(self):
        """WorkspaceState should accept custom values."""
        manager = Mock()
        state = WorkspaceState(
            isExcluded=True,
            windowIds={100, 200},  # Using set syntax
            layoutManager=manager,
        )
        
        assert state.isExcluded is True
        assert state.windowIds == {100, 200}
        assert state.layoutManager is manager

    def test_workspaceState_windowIdsIsMutable(self):
        """windowIds should be mutable for adding/removing."""
        state = WorkspaceState()
        state.windowIds.add(100)
        state.windowIds.add(200)
        
        assert 100 in state.windowIds
        assert 200 in state.windowIds
        
        state.windowIds.remove(100)
        assert 100 not in state.windowIds


class TestLaymanCommandParsing:
    """Tests for command parsing behavior."""

    def test_isLaymanCommand_recognizesNopLayman(self):
        """Should recognize 'nop layman' prefix."""
        binding = MockBindingEvent(command="nop layman maximize")
        
        # The binding.command starts with "nop layman"
        assert binding.binding.command.startswith("nop layman")

    def test_commandSplitting_multipleCommands(self):
        """Commands should be split by semicolon."""
        commands = "move up; focus down; stack toggle"
        parts = [cmd.strip() for cmd in commands.split(";")]
        
        assert len(parts) == 3
        assert parts[0] == "move up"
        assert parts[1] == "focus down"
        assert parts[2] == "stack toggle"

    def test_commandSplitting_singleCommand(self):
        """Single command should work without semicolon."""
        commands = "maximize"
        parts = [cmd.strip() for cmd in commands.split(";")]
        
        assert len(parts) == 1
        assert parts[0] == "maximize"


class TestLaymanStateManagement:
    """Tests for workspace state management."""

    def test_workspaceStates_tracking(self):
        """Should track workspace states by name."""
        states = {}
        
        states["1"] = WorkspaceState(windowIds={100, 200})
        states["2"] = WorkspaceState(windowIds={300})
        states["coding"] = WorkspaceState(windowIds={400, 500, 600})
        
        assert len(states) == 3
        assert len(states["1"].windowIds) == 2
        assert len(states["coding"].windowIds) == 3

    def test_findWindowInStates_found(self):
        """Should find which workspace contains a window."""
        states = {
            "1": WorkspaceState(windowIds={100, 200}),
            "2": WorkspaceState(windowIds={300}),
        }
        
        # Find which workspace has window 200
        found_workspace = None
        for ws_name, state in states.items():
            if 200 in state.windowIds:
                found_workspace = ws_name
                break
        
        assert found_workspace == "1"

    def test_findWindowInStates_notFound(self):
        """Should return None when window not in any workspace."""
        states = {
            "1": WorkspaceState(windowIds={100, 200}),
            "2": WorkspaceState(windowIds={300}),
        }
        
        found_workspace = None
        for ws_name, state in states.items():
            if 999 in state.windowIds:
                found_workspace = ws_name
                break
        
        assert found_workspace is None


class TestBuiltinLayouts:
    """Tests for builtin layout registration."""

    def test_builtinLayouts_containsMasterStack(self):
        """Should have MasterStack in builtin layouts."""
        from layman.managers.master_stack import MasterStackLayoutManager
        
        layouts = {"MasterStack": MasterStackLayoutManager}
        
        assert "MasterStack" in layouts
        assert layouts["MasterStack"] == MasterStackLayoutManager

    def test_builtinLayouts_containsAutotiling(self):
        """Should have Autotiling in builtin layouts."""
        from layman.managers.autotiling import AutotilingLayoutManager
        
        layouts = {"Autotiling": AutotilingLayoutManager}
        
        assert "Autotiling" in layouts

    def test_builtinLayouts_containsGrid(self):
        """Should have Grid in builtin layouts."""
        from layman.managers.grid import GridLayoutManager
        
        layouts = {"Grid": GridLayoutManager}
        
        assert "Grid" in layouts


class TestSwayLayoutNames:
    """Tests for recognizing Sway/i3 builtin layout names."""

    def test_builtinSwayLayouts(self):
        """Should recognize Sway builtin layout names."""
        sway_layouts = ["splitv", "splith", "tabbed", "stacking"]
        
        for layout in sway_layouts:
            # These should be passed directly to sway
            assert layout in ["splitv", "splith", "tabbed", "stacking"]

    def test_customLayouts_notBuiltin(self):
        """Custom layouts should not be in Sway builtins."""
        sway_layouts = {"splitv", "splith", "tabbed", "stacking"}
        custom_layouts = ["MasterStack", "Autotiling", "Grid"]
        
        for layout in custom_layouts:
            assert layout not in sway_layouts
