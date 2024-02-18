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
from datetime import datetime
from importlib.machinery import SourceFileLoader
from queue import SimpleQueue
from typing import Any, Optional, Type, cast

from i3ipc import BindingEvent, Con, Connection, WindowEvent, WorkspaceEvent
from setproctitle import setproctitle

from layman import config, utils
from layman.listener import ListenerThread
from layman.managers import (AutotilingLayoutManager, GridLayoutManager,
                             MasterStackLayoutManager, WorkspaceLayoutManager)
from layman.server import MessageServer


@dataclass
class WorkspaceState:
    layoutManager: Optional[WorkspaceLayoutManager] = None
    layoutName: str = "none"
    windowIds: set[int] = field(default_factory=set)
    isExcluded: bool = False


@contextmanager
def layoutManagerReloader(
    layman: "Layman", workspace: Optional[Con], workspaceName: Optional[str] = None
):
    if not workspaceName:
        assert workspace
        workspaceName = workspace.name
    assert workspaceName

    try:
        yield None
    except BaseException as e:
        logging.exception(e)
        layman.log(
            f"Reloading layout manager for workspace {workspaceName} after exception"
        )
        layman.setWorkspaceLayout(workspace, workspaceName)


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
            WorkspaceLayoutManager,
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

        self.handleWindowAdded(event, workspace, window)

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
        if state.isExcluded:
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
            self.log(
                f"focused window {event.container.id} not found,"
                + f" found {focused_workspace_window.id if focused_workspace_window else None} instead"
            )
            return

        # Pass command to the appropriate manager
        if state.layoutManager:
            self.log(
                f"Calling windowFocused for window id {window.id} on workspace {workspace.name}"
            )
            with layoutManagerReloader(self, workspace):
                state.layoutManager.windowFocused(event, workspace, window)

    def windowClosed(
        self,
        event: WindowEvent,
        tree: Con,
        workspace: Optional[Con],
        window: Optional[Con],
    ):
        state = None
        workspaceName = None
        # Try to find workspace by locating where the window is recorded
        for n, s in self.workspaceStates.items():
            if event.container.id in s.windowIds:
                state = s
                workspaceName = n
                try:
                    workspace = next(
                        w for w in tree.workspaces() if w.name == workspaceName
                    )
                except StopIteration:
                    # This can happen if the last window is closed while the workspace is not
                    # focused.
                    self.log(
                        f"found workspace {n} state for window id {event.container.id}, but not container"
                    )

                break

        if not state:
            # This is hopefully a window that appeared and then
            # disappered quickly enough that we missed recording it in windowCreated.
            self.log("workspace not found")
            return

        self.handleWindowRemoved(event, workspace, workspaceName, window)

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
            if from_state.layoutManager:
                self.log(
                    f"Calling windowMoved for window id {window.id} on workspace {from_workspace.name}"
                )
                with layoutManagerReloader(self, from_workspace):
                    from_state.layoutManager.windowMoved(
                        event, from_workspace, event.container
                    )
        else:
            # Window moving between two workspaces.
            self.handleWindowRemoved(event, from_workspace, None, window)
            self.handleWindowAdded(event, to_workspace, window)

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
        if state.isExcluded:
            self.log("Workspace excluded")
            return

        # Only send windowFloating event if wlm supports it
        if state.layoutManager and state.layoutManager.supportsFloating:
            self.log(
                f"Calling windowFloating for window id {window.id} on workspace {workspace.name}"
            )
            with layoutManagerReloader(self, workspace):
                state.layoutManager.windowFloating(event, workspace, window)
            return

        # Determine if window is floating
        i3Floating = window.floating is not None and "on" in window.floating
        swayFloating = window.type == "floating_con"

        if swayFloating or i3Floating:
            # Window floating, treat like it's removed.
            self.handleWindowRemoved(event, workspace, None, window)
        else:
            # Window is not floating, treat like a new window
            self.handleWindowAdded(event, workspace, window)

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
        command: str = event.binding.command.strip()
        # We only want to handle this binding if the first command is a "nop layman" command. If it
        # is, then we split all commands by ';' and either handle them ourselves if it is a layman
        # command or pass it on to i3/Sway if it is not.
        if command.startswith("nop layman"):
            for command in command.split(";"):
                if command.startswith("nop layman"):
                    command = command.replace("nop layman ", "").strip()
                    self.handleCommand(command)
                else:
                    self.command(command)

    def onCommand(self, command):
        for command in command.split(";"):
            command = command.strip()
            self.handleCommand(command)

    def handleCommand(self, command: str):
        assert ";" not in command

        workspace = utils.findFocusedWorkspace(self.conn)
        if not workspace or self.workspaceStates[workspace.name].isExcluded:
            self.command(command)
            return

        state = self.workspaceStates[workspace.name]

        # Handle movement and focus commands
        if (
            command.startswith("move")
            and (not state.layoutManager or not state.layoutManager.overridesMoveBinds)
        ) or (
            command.startswith("focus")
            and (not state.layoutManager or not state.layoutManager.overridesFocusBinds)
        ):
            self.command(command)
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
            self.setWorkspaceLayout(workspace, workspace.name, shortName)
            return

        # Pass unknown command to the appropriate wlm
        if not state.layoutManager:
            self.log("No manager for workspace %s, ignoring" % workspace.name)
            return

        self.log("Calling manager for workspace %s" % workspace.name)
        with layoutManagerReloader(self, workspace):
            state.layoutManager.onCommand(command, workspace)

    """
    Misc functions

    The following section of code handles miscellaneous tasks needed by the event
    handlers above.
    """

    # Runs and logs a command and its result.
    def command(self, command: str):
        self.logCaller(f"Running command: {command}")
        results = self.conn.command(command)
        for result in results:
            if result.success:
                self.logCaller("Command succeeded.")
            else:
                self.logCaller(f"Command failed: {result.error}")

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

        state.isExcluded = workspace.name in (
            self.options.getDefault(config.KEY_EXCLUDED_WORKSPACES) or []
        )

        state.windowIds = set(w.id for w in workspace.leaves())
        self.log(f"Workspace {workspace.name} window ids: {state.windowIds}")

        defaultLayout = str(
            self.options.getForWorkspace(workspace.name, config.KEY_LAYOUT)
        )
        if defaultLayout and not state.isExcluded:
            self.setWorkspaceLayout(workspace, workspace.name, defaultLayout)

    def getLayoutByShortName(self, shortName):
        if shortName in self.builtinLayouts:
            return self.builtinLayouts[shortName]

        if shortName in self.userLayouts:
            return self.userLayouts[shortName]

        return None

    def setWorkspaceLayoutCommand(self, workspace: Con):
        state = self.workspaceStates[workspace.name]
        if len(state.windowIds) != 1:
            # Can't reliably set the layout with more than one leaf, so ignore it.
            self.log(
                f"workspace {workspace.name} has {len(state.windowIds)} windows. ignoring."
            )
            return
        if state.layoutName and not state.layoutManager:
            self.command(f"[con_id={list(state.windowIds)[0]}] split none")
            self.command(
                f"[con_id={list(state.windowIds)[0]}] layout {state.layoutName}"
            )
        else:
            assert state.layoutName
            self.log(
                f"workspace {workspace.name} has layout {state.layoutName}. ignoring."
            )

    def setWorkspaceLayout(
        self,
        workspace: Optional[Con],
        workspaceName: str,
        layoutName: Optional[str] = None,
    ):
        state = self.workspaceStates[workspaceName]

        # If no layoutName is passed, we replace any current layout manager with a new copy of
        # that same layout manager, if any.
        if not layoutName:
            assert state.layoutName
            layoutName = state.layoutName
        else:
            state.layoutName = layoutName

        if state.isExcluded:
            self.logError(
                f"Attempting to set layout for excluded workspace {workspaceName}"
            )
            return
        #
        # Pass any built-in layouts to i3/Sway.

        if layoutName in ("splitv", "splith", "tabbed", "stacking"):
            state.layoutManager = None
            if workspace:
                self.setWorkspaceLayoutCommand(workspace)
        else:
            layout_manager_class = self.getLayoutByShortName(layoutName)
            if layout_manager_class:
                state.layoutManager = layout_manager_class(
                    self.conn, workspace, workspaceName, self.options
                )
            else:
                self.log(
                    f"Can't find layout manager named {layoutName} for workspace {workspaceName}"
                )
                return

        self.log(f"Initialized workspace {workspaceName} with layout {layoutName}")

    def handleWindowAdded(self, event: WindowEvent, workspace: Con, window: Con):
        state = self.workspaceStates[workspace.name]

        state.windowIds.add(window.id)
        self.log(f"Adding window ID {window.id} to workspace {workspace.name}")
        self.log(f"Workspace {workspace.name} window ids: {state.windowIds}")

        # Check if we should handle layouts on this workspace.
        if state.isExcluded:
            self.log("Workspace excluded")
            return

        if state.layoutManager:
            self.log(
                f"Calling windowAdded for window id {window.id} on workspace {workspace.name}"
            )
            with layoutManagerReloader(self, workspace):
                state.layoutManager.windowAdded(event, workspace, window)
        else:
            self.setWorkspaceLayoutCommand(workspace)

    def handleWindowRemoved(
        self,
        event: WindowEvent,
        workspace: Optional[Con],
        workspaceName: Optional[str],
        window: Optional[Con],
    ):
        assert workspace or workspaceName
        if not workspaceName:
            assert workspace
            workspaceName = workspace.name
        assert workspaceName
        state = self.workspaceStates[workspaceName]

        state.windowIds.remove(event.container.id)
        self.log(
            f"Removing window ID {event.container.id} from workspace {workspaceName}"
        )
        self.log(f"Workspace {workspaceName} window ids: {state.windowIds}")

        # Check if we should handle layouts on this workspace.
        if state.isExcluded:
            self.log("Workspace excluded")
            return

        if state.layoutManager:
            self.log(
                f"Calling windowRemoved for window id {event.container.id} on workspace {workspaceName}"
            )
            with layoutManagerReloader(self, workspace):
                state.layoutManager.windowRemoved(event, workspace, event.container)
        else:
            if workspace:
                self.setWorkspaceLayoutCommand(workspace)

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

    def getCurrentTimestamp(self) -> str:
        current_time = datetime.now()
        return current_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    def log(self, msg):
        if self.options.getDefault(config.KEY_DEBUG):
            print(f"[{self.getCurrentTimestamp()}] {inspect.stack()[1][3]}: {msg}")

    def logCaller(self, msg):
        if self.options.getDefault(config.KEY_DEBUG):
            print(f"[{self.getCurrentTimestamp()}] {inspect.stack()[2][3]}: {msg}")

    def logError(self, msg):
        print(
            f"[{self.getCurrentTimestamp()}] {inspect.stack()[1][3]}: {msg}",
            file=sys.stderr,
        )

    def run(self):
        self.conn = Connection()
        notificationQueue = SimpleQueue()

        # In order to shrink the window for race conditions as much as possible, we get the full
        # current container tree, and then immediately set up all listeners before continuing on
        # with any further initialization. The subscriptions are not actually created inside i3ipc
        # until calling Connection#main(), so we do that here, while delaying any callbacks, so that
        # we don't miss any notifications.
        tree = self.conn.get_tree()
        ListenerThread(notificationQueue)
        MessageServer(notificationQueue)

        # Set default layout mangers for existing workspaces
        for workspace in tree.workspaces():
            self.initWorkspace(workspace)

        # Start handling events
        self.log("layman started")
        while True:
            notification: dict[str, Any] = notificationQueue.get()
            if notification["type"] == "event":
                event = notification["event"]
                if isinstance(event, WorkspaceEvent):
                    event = cast(WorkspaceEvent, event)
                    if event.change == "init":
                        assert event.current is not None
                        self.log(
                            f"Handling workspace 'init' event for workspace {event.current.name}"
                        )
                        self.onWorkspaceInit(event)
                    else:
                        raise RuntimeError(
                            f"Unexpected workspace event type {event.change}"
                        )
                elif isinstance(event, BindingEvent):
                    event = cast(BindingEvent, event)
                    self.log(
                        f"Handling binding event for command '{event.binding.command}'"
                    )
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
                        self.log(
                            f"Handling window '{event.change}' event for window id {event.container.id}"
                        )
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
