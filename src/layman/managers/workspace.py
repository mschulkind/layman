"""
Copyright 2022 Joe Maples <joe@maples.dev>

This file is part of layman.

layman is free software: you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

layman is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
layman. If not, see <https://www.gnu.org/licenses/>.
"""

import logging
from typing import Any, ClassVar

import i3ipc

from layman.config import LaymanConfig
from layman.log import get_logger


class WorkspaceLayoutManager:
    """Base class for all workspace layout managers.

    Layout managers control how windows are arranged on a workspace. Each
    workspace can have at most one active layout manager. Managers receive
    window events (add, remove, focus, move, float) and commands from
    keybindings or the CLI.

    To implement a custom layout manager, subclass this and override:
        - ``shortName``: Unique identifier for the layout.
        - ``windowAdded()``, ``windowRemoved()``, etc.: Event handlers.
        - ``onCommand()``: Handles user commands.

    Class Attributes:
        shortName: Unique short name used in config and CLI (e.g., "MasterStack").
        overridesMoveBinds: If True, move commands are routed to this manager
            instead of being passed to Sway/i3 natively.
        overridesFocusBinds: If True, focus commands are routed to this manager.
        supportsFloating: If True, ``windowFloating()`` is called. If False,
            floating toggles are treated as add/remove events.

    Instance Attributes:
        con: The i3ipc connection for executing IPC commands.
        workspaceName: Name of the workspace this manager controls.
        logger: Per-instance logger (named ``module.workspaceName``).
    """

    shortName: ClassVar[str] = "none"
    overridesMoveBinds: ClassVar[bool] = False
    overridesFocusBinds: ClassVar[bool] = False
    supportsFloating: ClassVar[bool] = False

    con: i3ipc.Connection
    workspaceName: str
    logger: logging.Logger

    def __init__(
        self,
        con: i3ipc.Connection,
        workspace: i3ipc.Con | None,
        workspaceName: str,
        options: LaymanConfig,
    ):
        """Initialize the layout manager.

        Args:
            con: An i3ipc connection for executing Sway/i3 IPC commands.
            workspace: The workspace container, or None if the workspace is
                empty and not focused (doesn't exist in the tree yet).
            workspaceName: The name of the workspace (always available even
                when workspace is None).
            options: The loaded layman configuration.
        """
        self.con = con
        self.workspaceName = workspaceName
        module = type(self).__module__ or "layman.managers"
        self.logger = get_logger(f"{module}.{workspaceName}")

    def windowAdded(
        self, event: i3ipc.WindowEvent, workspace: i3ipc.Con, window: i3ipc.Con
    ) -> None:
        """Called when a new window is added to the workspace.

        Triggered when a window is created on this workspace or moved here
        from another workspace.

        Args:
            event: The i3ipc window event.
            workspace: The workspace container.
            window: The newly added window container.
        """

    def windowRemoved(
        self,
        event: i3ipc.WindowEvent,
        workspace: i3ipc.Con | None,
        window: i3ipc.Con,
    ) -> None:
        """Called when a window is removed from the workspace.

        Triggered when a window is closed or moved to a different workspace.
        If the workspace is not focused when the last window is removed, the
        workspace ceases to exist before this is called, so ``workspace``
        may be None.

        Args:
            event: The i3ipc window event.
            workspace: The workspace container, or None if it no longer exists.
            window: The removed window container.
        """

    def windowFocused(
        self, event: i3ipc.WindowEvent, workspace: i3ipc.Con, window: i3ipc.Con
    ) -> None:
        """Called when a window on the workspace receives focus.

        Args:
            event: The i3ipc window event.
            workspace: The workspace container.
            window: The focused window container.
        """

    def windowMoved(
        self, event: i3ipc.WindowEvent, workspace: i3ipc.Con, window: i3ipc.Con
    ) -> None:
        """Called when a window is moved but stays on the same workspace.

        Args:
            event: The i3ipc window event.
            workspace: The workspace container.
            window: The moved window container.
        """

    def windowFloating(
        self, event: i3ipc.WindowEvent, workspace: i3ipc.Con, window: i3ipc.Con
    ) -> None:
        """Called when a window's floating state is toggled.

        Only called if ``supportsFloating`` is True. Otherwise, floating
        toggles are treated as windowAdded/windowRemoved events.

        Args:
            event: The i3ipc window event.
            workspace: The workspace container.
            window: The window whose floating state changed.
        """

    def onCommand(self, command: str, workspace: i3ipc.Con) -> None:
        """Called when a layman command is executed while this workspace is focused.

        Commands come from keybindings or the layman CLI. Examples:
        "move up", "focus master", "toggle", "maximize".

        Args:
            command: The command string (already stripped of workspace prefix).
            workspace: The workspace container.
        """

    def dumpState(self) -> dict[str, Any]:
        """Return a dictionary of the manager's internal state for debugging.

        Subclasses should override this to include their own specific state.
        """
        return {
            "layout": self.shortName,
            "workspaceName": self.workspaceName,
        }

    def isExcluded(self, window: i3ipc.Con | None) -> bool:
        """Check if a window should be skipped by layout logic.

        Returns True for None windows, non-con types, floating, fullscreen,
        and windows in stacked/tabbed containers.

        Args:
            window: The window to check, or None.

        Returns:
            True if the window should be excluded from layout management.
        """
        if window is None:
            return True

        if window.type != "con":
            return True

        if window.workspace() is None:
            return True

        if window.floating is not None and "on" in window.floating:
            return True

        if window.fullscreen_mode == 1:
            return True

        if window.parent.layout == "stacked":
            return True

        if window.parent.layout == "tabbed":
            return True

        return False

    def command(self, command: str) -> None:
        """Execute a Sway/i3 IPC command.

        Logs the command and its result. Used internally by layout managers
        to manipulate the window tree.

        Args:
            command: The IPC command string (e.g., "[con_id=42] focus").
        """
        self.logger.debug("Running command: %s", command, stacklevel=2)
        results = self.con.command(command)
        for result in results:
            if result.success:
                self.logger.debug("Command succeeded.", stacklevel=2)
            else:
                self.logger.error("Command failed: %s", result.error, stacklevel=2)

    def log(self, msg: str) -> None:
        """Log a debug message. Includes caller function name via logging format."""
        self.logger.debug(msg, stacklevel=2)

    def logError(self, msg: str) -> None:
        """Log an error message (always visible)."""
        self.logger.error(msg, stacklevel=2)

    def logCaller(self, msg: str) -> None:
        """Log a debug message from a helper (shows grandparent caller)."""
        self.logger.debug(msg, stacklevel=3)
