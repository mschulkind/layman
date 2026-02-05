"""
Mock classes for i3ipc objects used in unit testing.

These mocks simulate the behavior of i3ipc.Con, i3ipc.Connection,
and related event objects without requiring a running Sway/i3 instance.
"""

from dataclasses import dataclass, field
from typing import Optional
from unittest.mock import Mock


@dataclass
class MockRect:
    """Mock for i3ipc Rect object."""

    x: int = 0
    y: int = 0
    width: int = 800
    height: int = 600


@dataclass
class MockCommandReply:
    """Mock for i3ipc CommandReply."""

    success: bool = True
    error: str | None = None


class MockCon:
    """
    Flexible mock for i3ipc.Con that supports tree structures.

    This class mimics the essential properties and methods of i3ipc.Con
    for unit testing layout managers and event handlers.
    """

    def __init__(
        self,
        id: int = 1,
        name: str = "window",
        type: str = "con",
        rect: MockRect | None = None,
        floating: str | None = None,
        fullscreen_mode: int = 0,
        layout: str = "splith",
        app_id: str | None = None,
        window_class: str | None = None,
        parent: Optional["MockCon"] = None,
        nodes: list["MockCon"] | None = None,
        floating_nodes: list["MockCon"] | None = None,
        focused: bool = False,
        marks: list[str] | None = None,
    ):
        self.id = id
        self.name = name
        self.type = type
        self.rect = rect or MockRect()
        self.floating = floating
        self.fullscreen_mode = fullscreen_mode
        self.layout = layout
        self.app_id = app_id
        self.window_class = window_class
        self.parent = parent
        self.nodes = nodes or []
        self.floating_nodes = floating_nodes or []
        self.focused = focused
        self.marks = marks or []

        # Set parent references for child nodes
        for node in self.nodes:
            node.parent = self
        for node in self.floating_nodes:
            node.parent = self

    def find_by_id(self, target_id: int) -> Optional["MockCon"]:
        """Find a container by ID in this tree."""
        if self.id == target_id:
            return self

        for node in self.nodes + self.floating_nodes:
            result = node.find_by_id(target_id)
            if result:
                return result

        return None

    def find_focused(self) -> Optional["MockCon"]:
        """Find the focused container in this tree."""
        if self.focused:
            return self

        for node in self.nodes + self.floating_nodes:
            result = node.find_focused()
            if result:
                return result

        return None

    def workspace(self) -> Optional["MockCon"]:
        """Find the workspace containing this container."""
        if self.type == "workspace":
            return self

        if self.parent:
            return self.parent.workspace()

        return None

    def leaves(self) -> list["MockCon"]:
        """Get all leaf (window) containers."""
        if not self.nodes:
            if self.type == "con":
                return [self]
            return []

        result = []
        for node in self.nodes:
            result.extend(node.leaves())
        return result

    def workspaces(self) -> list["MockCon"]:
        """Get all workspace containers in this tree."""
        if self.type == "workspace":
            return [self]

        result = []
        for node in self.nodes:
            result.extend(node.workspaces())
        return result

    def is_floating(self) -> bool:
        """Check if this container is floating."""
        return self.floating is not None and "on" in self.floating


class MockConnection:
    """
    Mock for i3ipc.Connection.

    Records executed commands for test verification and provides
    a controllable tree structure.
    """

    def __init__(self, tree: MockCon | None = None):
        self.tree = tree or MockCon(type="root")
        self.commands_executed: list[str] = []
        self._command_results: list[MockCommandReply] = []

    def command(self, cmd: str) -> list[MockCommandReply]:
        """Execute a command and record it."""
        self.commands_executed.append(cmd)

        if self._command_results:
            return self._command_results

        return [MockCommandReply(success=True)]

    def get_tree(self) -> MockCon:
        """Return the mock tree."""
        return self.tree

    def set_command_result(
        self, success: bool = True, error: str | None = None
    ) -> None:
        """Set the result for the next command."""
        self._command_results = [MockCommandReply(success=success, error=error)]

    def clear_commands(self) -> None:
        """Clear recorded commands."""
        self.commands_executed.clear()


class MockWindowEvent:
    """Mock for i3ipc.WindowEvent."""

    def __init__(
        self,
        change: str = "new",
        container: MockCon | None = None,
    ):
        self.change = change
        self.container = container or MockCon()


class MockWorkspaceEvent:
    """Mock for i3ipc.WorkspaceEvent."""

    def __init__(
        self,
        change: str = "init",
        current: MockCon | None = None,
        old: MockCon | None = None,
    ):
        self.change = change
        self.current = current
        self.old = old


class MockBinding:
    """Mock for i3ipc binding object."""

    def __init__(self, command: str = ""):
        self.command = command


class MockBindingEvent:
    """Mock for i3ipc.BindingEvent."""

    def __init__(self, command: str = ""):
        self.binding = MockBinding(command)


# Factory functions for common scenarios


def create_workspace(
    name: str = "1",
    window_count: int = 0,
    floating_count: int = 0,
    start_id: int = 100,
) -> MockCon:
    """Create a workspace with the specified number of windows."""
    windows = []
    for i in range(window_count):
        windows.append(
            MockCon(
                id=start_id + i,
                name=f"Window{i + 1}",
                rect=MockRect(width=800, height=600),
            )
        )

    floating = []
    for i in range(floating_count):
        floating.append(
            MockCon(
                id=start_id + window_count + i,
                name=f"Floating{i + 1}",
                floating="auto_on",
                type="floating_con",
            )
        )

    ws = MockCon(
        name=name,
        type="workspace",
        nodes=windows,
        floating_nodes=floating,
    )

    return ws


def create_tree_with_workspaces(
    workspace_configs: list[dict],
) -> MockCon:
    """
    Create a root tree with multiple workspaces.

    workspace_configs is a list of dicts with keys:
    - name: str
    - window_count: int
    - floating_count: int (optional)
    """
    workspaces = []
    current_id = 100

    for config in workspace_configs:
        ws = create_workspace(
            name=config.get("name", "1"),
            window_count=config.get("window_count", 0),
            floating_count=config.get("floating_count", 0),
            start_id=current_id,
        )
        workspaces.append(ws)
        current_id += config.get("window_count", 0) + config.get("floating_count", 0)

    # Create output and root structure
    output = MockCon(
        name="output",
        type="output",
        nodes=workspaces,
    )

    root = MockCon(
        type="root",
        nodes=[output],
    )

    return root
