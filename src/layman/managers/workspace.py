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
import inspect
from typing import ClassVar, Optional

import i3ipc

from layman.config import KEY_DEBUG, LaymanConfig


class WorkspaceLayoutManager:
    # These properties should be overriden to configure your WLM as
    # needed.
    shortName: ClassVar[str] = "none"
    overridesMoveBinds: ClassVar[
        bool
    ] = False  # Should window movement commands be sent as binds
    overridesFocusBinds: ClassVar[
        bool
    ] = False  # Should focus movement commands be sent as binds
    supportsFloating: ClassVar[
        bool
    ] = False  # Should windowFloating be used, or treated as Added/Removed

    con: i3ipc.Connection
    workspaceName: str

    # These are the functions you should override to implement a WLM.
    #
    # Parameters:
    # con (i3ipc.Connection): An i3ipc connection for executing commands.
    # workspace (Optional[i3ipc.Con]):
    #     The i3ipc.Con of the workspace the layout manager is associated with. This includes all
    #     windows on the workspace at the time of initialization. If this is called while the
    #     workspace is empty and not focused, it may not exist in the tree, so this argument may be
    #     None.
    # workspaceName (str): The name of the workspace. This exists in case workspace is None.
    # options (LaymanConfig): The loaded config file used for option defaults.
    def __init__(
        self,
        con: i3ipc.Connection,
        workspace: Optional[i3ipc.Con],
        workspaceName: str,
        options: LaymanConfig,
    ):
        self.con = con
        self.workspaceName = workspaceName
        self.debug = options.getForWorkspace(workspaceName, KEY_DEBUG)

    # windowAdded is called when a new window is added to the workspace,
    # either by being created on the workspace or moved to it from another.
    def windowAdded(
        self, event: i3ipc.WindowEvent, workspace: i3ipc.Con, window: i3ipc.Con
    ):
        pass

    # windowRemoved is called when a window is removed from the workspace,
    # either by being closed or moved to a different workspace. If the workspace
    # is not focused when the last window is removed, the workspace ceases to exist
    # before windowRemoved is called, so the workspace argument can sometimes be None.
    def windowRemoved(
        self,
        event: i3ipc.WindowEvent,
        workspace: Optional[i3ipc.Con],
        window: i3ipc.Con,
    ):
        pass

    # windowFocused is called when a window on the workspace is focused.
    def windowFocused(
        self, event: i3ipc.WindowEvent, workspace: i3ipc.Con, window: i3ipc.Con
    ):
        pass

    # windowMoved is called when a window is moved, but stays on the same
    # workspace.
    def windowMoved(
        self, event: i3ipc.WindowEvent, workspace: i3ipc.Con, window: i3ipc.Con
    ):
        pass

    # windowFloating is called when a window's floating state is toggled.
    def windowFloating(
        self, event: i3ipc.WindowEvent, workspace: i3ipc.Con, window: i3ipc.Con
    ):
        pass

    # onCommand is called when a layman command is executed while the workspace
    # is focused, whether the command was from a key binding or the layman cli.
    def onCommand(self, command: str, workspace: i3ipc.Con):
        pass

    # command is used by the layout manager itself to run commands.
    def command(self, command: str):
        self.logCaller(f"Running command: {command}")
        results = self.con.command(command)
        for result in results:
            if result.success:
                self.logCaller("Command succeeded.")
            else:
                self.logCaller(f"Command failed: {result.error}")

    # This log function includes the class name, workspace number, and the
    # name of the function it is called by. This makes it useful for functions
    # that are called in response to events.
    def log(self, msg):
        if self.debug:
            print(
                (
                    "%s %s: %s: %s"
                    % (self.shortName, self.workspaceName, inspect.stack()[1][3], msg)
                )
            )

    # Same as log(), but prints in non-debug as well.
    def logError(self, msg):
        print(
            (
                "%s %s: %s: %s"
                % (self.shortName, self.workspaceName, inspect.stack()[1][3], msg)
            )
        )

    # This log function includes the class name, workspace number, and the
    # name of the function 2 calls up. This makes it useful for helper
    # functions that get called by event handlers
    def logCaller(self, msg):
        if self.debug:
            print(
                (
                    "%s %s: %s: %s"
                    % (self.shortName, self.workspaceName, inspect.stack()[2][3], msg)
                )
            )
