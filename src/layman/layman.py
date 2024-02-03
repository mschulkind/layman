#!/usr/bin/env python3
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
import logging
import os
import shutil
import sys
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
from importlib.machinery import SourceFileLoader
from queue import SimpleQueue
from typing import Any, Optional, Type, cast

from i3ipc import BindingEvent, Con, Connection, Event, WindowEvent, WorkspaceEvent
from i3ipc.events import IpcBaseEvent
from setproctitle import setproctitle

from layman import config, utils
from layman.listener import ListenerThread
from layman.managers import (
    AutotilingLayoutManager,
    GridLayoutManager,
    MasterStackLayoutManager,
    WorkspaceLayoutManager,
)
from layman.server import MessageServer


@dataclass
class WorkspaceState:
    layout_manager: Optional[WorkspaceLayoutManager] = None
    windowIds: set[int] = field(default_factory=set)
    is_excluded: bool = False


@contextmanager
def layoutManagerReloader(layman: "Layman", workspace: Con):
    try:
        yield None
    except BaseException as e:
        logging.exception(e)
        layman.setWorkspaceLayoutManager(workspace)


class Layman:
    builtinLayouts: dict[str, Type[WorkspaceLayoutManager]]
    userLayouts: dict[str, Type[WorkspaceLayoutManager]]
    workspaceStates: dict[str, WorkspaceState]

    def __init__(self):
        self.workspaceStates = {}
        setproctitle("layman")

        # Get user config options
        self.options = config.LaymanConfig(utils.getConfigPath())

        # Get builtin layouts
        self.builtinLayouts = {}
        for builtin_layout in [
            AutotilingLayoutManager,
            MasterStackLayoutManager,
            GridLayoutManager,
        ]:
            self.builtinLayouts[builtin_layout.shortName] = builtin_layout

        self.fetchUserLayouts()

    """
    Window Events

    The following functions that are called in response to window events, specifically
    window::new, window::focus, window::close, window::move, and window::floating.
    """

    def windowCreated(
        self,
        event: WindowEvent,
        tree: Con,
        workspace: Optional[Con],
        window: Optional[Con],
    ):
        if not (workspace and window):
            # Hopefully this was just a window that showed up and disappeared extremely quickly.
            # We'll just ignore it.
            self.log("no window found")
            return

        state = self.workspaceStates[workspace.name]
        state.windowIds.add(window.id)
        self.log(f"Adding window ID {window.id} to workspace named {workspace.name}")

        # Check if we should pass this call to a manager
        if state.is_excluded:
            self.log("Workspace excluded")
            return

        if state.layout_manager:
            self.log("Calling windowAdded for workspace %s" % workspace.name)
            with layoutManagerReloader(self, workspace):
                state.layout_manager.windowAdded(event, workspace, window)

    def windowFocused(
        self,
        event: WindowEvent,
        tree: Con,
        workspace: Optional[Con],
        window: Optional[Con],
    ):
        if not workspace:
            self.log("no workspace found")
            return
        assert window
        state = self.workspaceStates[workspace.name]

        # Check if we should pass this call to a manager
        if state.is_excluded:
            self.log("Workspace excluded")
            return

        focused_workspace_window = workspace.find_focused()
        if (
            not focused_workspace_window
            or event.container.id != focused_workspace_window.id
        ):
            # If we're processing a windowFocused event, but the tree either doesn't contain a
            # focused window, or the focused window doesn't match the one in the event, we just
            # assume that the focused changed again and quickly after this event was fired, so we
            # ignore it.
            self.log("focused window not found")
            return

        # Pass command to the appropriate manager
        if state.layout_manager:
            self.log("Calling windowFocused for workspace %s" % workspace.name)
            with layoutManagerReloader(self, workspace):
                state.layout_manager.windowFocused(event, workspace, window)

    def windowClosed(
        self,
        event: WindowEvent,
        tree: Con,
        workspace: Optional[Con],
        window: Optional[Con],
    ):
        state = None
        # Try to find workspace by locating where the window is recorded
        for workspaceName, workspaceState in self.workspaceStates.items():
            if event.container.id in workspaceState.windowIds:
                workspace = next(
                    w for w in tree.workspaces() if w.name == workspaceName
                )
                state = workspaceState

        if not state:
            # This is hopefully a window that appeared and then
            # disappered quickly enough that we missed recording it in windowCreated.
            self.log("workspace not found")
            return

        assert workspace
        self.log(f"window ID {event.container.id} from workspace {workspace.name}")

        state.windowIds.remove(event.container.id)

        if state.is_excluded:
            self.log("Workspace excluded")
            return

        # Pass command to the appropriate manager
        if state.layout_manager:
            self.log("Calling windowRemoved for workspace %s" % workspace.name)
            with layoutManagerReloader(self, workspace):
                state.layout_manager.windowRemoved(event, workspace, event.container)

    def windowMoved(
        self,
        event: WindowEvent,
        tree: Con,
        to_workspace: Optional[Con],
        window: Optional[Con],
    ):
        if not to_workspace:
            # If we didn't find a workspace, hopefully the window was just closed very quickly after
            # moving. We'll ignore it.
            self.log("Window not found")
            return
        assert window

        to_state = self.workspaceStates[to_workspace.name]

        if to_state.is_excluded:
            self.log("Workspace excluded")
            return

        from_workspace_name, from_state = next(
            (name, state)
            for name, state in self.workspaceStates.items()
            if window.id in state.windowIds
        )
        from_workspace = next(
            w for w in tree.workspaces() if w.name == from_workspace_name
        )

        # Pass command to the appropriate managers
        if from_workspace.name == to_workspace.name:
            # Window moving within the same workspace.
            if from_state.layout_manager:
                self.log("Calling windowMoved for workspace %s" % from_workspace.name)
                with layoutManagerReloader(self, from_workspace):
                    from_state.layout_manager.windowMoved(
                        event, from_workspace, event.container
                    )
        else:
            # Window moving between two workspaces.
            if from_state.layout_manager:
                from_state.windowIds.remove(window.id)
                self.log("Calling windowRemoved for workspace %s" % from_workspace.name)
                with layoutManagerReloader(self, from_workspace):
                    from_state.layout_manager.windowRemoved(
                        event, from_workspace, event.container
                    )

            if to_state.layout_manager:
                to_state.windowIds.add(window.id)
                self.log("Calling windowAdded for workspace %s" % to_workspace.name)
                with layoutManagerReloader(self, to_workspace):
                    to_state.layout_manager.windowAdded(event, to_workspace, window)

    def windowFloating(
        self,
        event: WindowEvent,
        tree: Con,
        workspace: Optional[Con],
        window: Optional[Con],
    ):
        # If we can't find a window, hopefully it was just closed very quickly after the floating
        # event. Ignoring.
        if not (workspace and window):
            self.log("Window not found")
            return
        state = self.workspaceStates[workspace.name]

        # Check if we should pass this call to a manager
        if state.is_excluded:
            self.log("Workspace excluded")
            return

        if not state.layout_manager:
            return

        # Only send windowFloating event if wlm supports it
        if state.layout_manager.supportsFloating:
            self.log("Calling windowFloating for workspace %s" % workspace.name)
            with layoutManagerReloader(self, workspace):
                state.layout_manager.windowFloating(event, workspace, window)
            return

        # Determine if window is floating
        i3Floating = window.floating is not None and "on" in window.floating
        swayFloating = any(window.id == node.id for node in workspace.floating_nodes)

        if swayFloating or i3Floating:
            # Window floating, treat like it's removed.
            self.log("Calling windowRemoved for workspace %s" % workspace.name)
            with layoutManagerReloader(self, workspace):
                state.layout_manager.windowRemoved(event, workspace, window)
            return
        else:
            # Window is not floating, treat like a new window
            self.log("Calling windowAdded for workspace %s" % workspace.name)
            with layoutManagerReloader(self, workspace):
                state.layout_manager.windowAdded(event, workspace, window)
            return

    """
    Workspace Events

    The following functions are called in response to workspace events, specifically
    workspace::init and workspace::focus.
    """

    def onWorkspaceInit(self, event: WorkspaceEvent):
        assert event.current is not None
        self.initWorkspace(event.current)

    """
    Binding Events

    The following functions are called in response to any binding event or message and handles
    interpreting the binding command or passing it to the intended workspace layout manager.
    """

    def onBinding(self, event: BindingEvent):
        # Handle chained commands one at a time
        command: str = event.ipc_data["binding"]["command"].strip()
        if command.startswith("nop layman"):
            for command in command.split(";"):
                command = command.replace("nop layman ", "").strip()
                self.handleCommand(command)

    def onCommand(self, command):
        for command in command.split(";"):
            command = command.strip()
            self.handleCommand(command)

    def handleCommand(self, command: str):
        assert ";" not in command

        workspace = utils.findFocusedWorkspace(self.conn)
        if not workspace or self.workspaceStates[workspace.name].is_excluded:
            self.conn.command(command)
            return

        state = self.workspaceStates[workspace.name]

        # Handle movement commands
        if command.startswith("move") and (
            not state.layout_manager or not state.layout_manager.overridesMoveBinds
        ):
            self.conn.command(command)
            self.log('Handling bind "%s" for workspace %s' % (command, workspace.name))
            return

        # Handle reload command
        if command == "reload":
            # Get user config options
            self.options = config.LaymanConfig(utils.getConfigPath())
            self.fetchUserLayouts()
            self.log("Reloaded layman config")
            return

        # Handle wlm creation commands
        if "layout" in command:
            shortName = command.split(" ")[1]
            self.setWorkspaceLayoutManager(workspace, shortName)
            return

        # Pass unknown command to the appropriate wlm
        if not state.layout_manager:
            self.log("No manager for workspace %s, ignoring" % workspace.name)
            return

        self.log("Calling manager for workspace %s" % workspace.name)
        with layoutManagerReloader(self, workspace):
            state.layout_manager.onCommand(command, workspace)

    """
    Misc functions

    The following section of code handles miscellaneous tasks needed by the event
    handlers above.
    """

    def fetchUserLayouts(self):
        self.userLayouts = {}

        # Get user provided layouts
        layoutPath = os.path.dirname(utils.getConfigPath())
        for file in os.listdir(layoutPath):
            if file.endswith(".py"):
                # Assume all python files in the config path are layouts, load them
                className = os.path.splitext(file)[0]
                try:
                    module = SourceFileLoader(
                        className, layoutPath + "/" + file
                    ).load_module()
                    self.userLayouts[module.shortName] = cast(
                        Type[WorkspaceLayoutManager], module
                    )
                    self.log("Loaded user layout %s" % module.shortName)
                except ImportError:
                    self.log("Layout not found: " + className)

    def initWorkspace(self, workspace: Con):
        if workspace.name in self.workspaceStates:
            return

        state = WorkspaceState()
        self.workspaceStates[workspace.name] = state

        state.is_excluded = workspace.name in (
            self.options.getDefault(config.KEY_EXCLUDED_WORKSPACES) or []
        )

        state.windowIds |= set(w.id for w in workspace.leaves())

        default_layout = self.options.getForWorkspace(workspace, config.KEY_LAYOUT)
        if default_layout and not state.is_excluded:
            self.setWorkspaceLayoutManager(workspace, default_layout)

    def getLayoutByShortName(self, shortName):
        if shortName in self.builtinLayouts:
            return self.builtinLayouts[shortName]

        if shortName in self.userLayouts:
            return self.userLayouts[shortName]

        return None

    def setWorkspaceLayoutManager(
        self, workspace: Con, layoutShortName: Optional[str] = None
    ):
        state = self.workspaceStates[workspace.name]

        # If no layoutShortName is passed, we replace any current layout manager with a new copy of
        # that same layout manager, if any.
        if not layoutShortName:
            if state.layout_manager:
                layoutShortName = state.layout_manager.shortName
            else:
                layoutShortName = "none"

        if state.is_excluded:
            self.logError(
                f"Attempting to set layout for excluded workspace {workspace.name}"
            )
            return

        layout_manager_class = None
        if layoutShortName == "none":
            state.layout_manager = None
        else:
            layout_manager_class = self.getLayoutByShortName(layoutShortName)
            if layout_manager_class:
                state.layout_manager = layout_manager_class(
                    self.conn, workspace, self.options
                )
        if layout_manager_class or layoutShortName == "none":
            self.log(
                "Initialized workspace %s with layout %s"
                % (workspace.name, layoutShortName)
            )
        else:
            self.log("Can't find layout manager named %s" % layoutShortName)

    def createConfig(self):
        configPath = utils.getConfigPath()
        if not os.path.exists(configPath):
            if os.path.exists(os.path.dirname(configPath)):
                shutil.copyfile(
                    os.path.join(os.path.dirname(__file__), "config.toml"), configPath
                )
            else:
                self.logCaller("Path to user config does not exist: %s" % configPath)
                exit()

    def log(self, msg):
        if self.options.getDefault(config.KEY_DEBUG):
            print("%s: %s" % (inspect.stack()[1][3], msg))

    def logCaller(self, msg):
        if self.options.getDefault(config.KEY_DEBUG):
            print("%s: %s" % (inspect.stack()[2][3], msg))

    def logError(self, msg):
        print("%s: %s" % (inspect.stack()[1][3], msg), file=sys.stderr)

    def run(self):
        self.conn = Connection()
        self.notificationQueue = SimpleQueue()

        # In order to shrink the window for race conditions as much as possible, we get the full
        # current container tree, and then immediately set up all listeners before continuing on
        # with any further initialization. The subscriptions are not actually created inside i3ipc
        # until calling Connection#main(), so we do that here, while delaying any callbacks, so that
        # we don't miss any notifications.
        tree = self.conn.get_tree()
        self.listenerThread = ListenerThread(self.notificationQueue)
        self.messageServer = MessageServer(self.notificationQueue)

        # Set default layout mangers for existing workspaces
        for workspace in tree.workspaces():
            self.initWorkspace(workspace)

        # Start handling events
        self.log("layman started")
        while True:
            notification: dict[str, Any] = self.notificationQueue.get()
            if notification["type"] == "event":
                event = notification["event"]
                if isinstance(event, WorkspaceEvent):
                    event = cast(WorkspaceEvent, event)
                    if event.change == "init":
                        self.onWorkspaceInit(event)
                    else:
                        raise RuntimeError(
                            f"Unexpected workspace event type {event.change}"
                        )
                elif isinstance(event, BindingEvent):
                    event = cast(BindingEvent, event)
                    self.onBinding(event)
                elif isinstance(event, WindowEvent):
                    # Because the i3ipc.Con that comes with a WindowEvent does not contain the
                    # parents of the window the event is for, we need to make an IPC request to
                    # determine what workspace the window is associated with so we can send the
                    # event to the correct layout manager.
                    #
                    # One obvious way to determine the correct workspace would be to just find the
                    # focused window and its associated workspace, but this isn't quite correct. At
                    # least on Sway, and probably i3 as well, windows are created on the workspace
                    # that was focused at the time the process was created NOT when the window
                    # appears. This means that if you have a process that creates a window 5 seconds
                    # after it starts, and within those 5 seconds you change workspaces, the window
                    # will still be created on the previous workspace, but finding the currently
                    # focused workspace will give you the wrong workspace, and hence the event would
                    # be sent to the wrong layout manager.
                    #
                    # Instead, we get the full tree and find the window by ID, if it still exists.
                    # There's still a potential for race conditions here since something could have
                    # changed between receving the notification and completing the IPC request to
                    # get the full tree, but there's not much we can do about this. To alleviate
                    # this issue as much as possible, we pass the full workspace tree through to the
                    # event handler so that it uses the same view of the state of the workspace
                    # throughout its event handling.
                    event = cast(WindowEvent, event)
                    tree = self.conn.get_tree()
                    window = tree.find_by_id(event.container.id)
                    workspace = window and window.workspace()
                    handlers: dict[
                        str,
                        Callable[
                            [WindowEvent, Con, Optional[Con], Optional[Con]], None
                        ],
                    ] = {
                        "new": self.windowCreated,
                        "close": self.windowClosed,
                        "floating": self.windowFloating,
                        "focus": self.windowFocused,
                        "move": self.windowMoved,
                    }
                    if event.change in handlers:
                        handlers[event.change](event, tree, workspace, window)
                    else:
                        raise RuntimeError(
                            f"Unexpected window event type {event.change}"
                        )
                else:
                    raise RuntimeError(f"Invalid event received: {event}")

            elif notification["type"] == "command":
                self.onCommand(notification["command"])
            else:
                raise RuntimeError(f"Notification with invalid type: {notification}")
