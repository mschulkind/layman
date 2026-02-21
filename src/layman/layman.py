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

import itertools
import logging
import os
import shutil
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
from importlib.machinery import SourceFileLoader
from queue import SimpleQueue
from typing import Any, cast

import yaml
from i3ipc import BindingEvent, Con, Connection, WindowEvent, WorkspaceEvent
from setproctitle import setproctitle

from layman import config, utils
from layman.config import ConfigError
from layman.focus_history import FocusHistory
from layman.listener import ListenerThread
from layman.log import get_logger, setup_logging
from layman.managers import (
    AutotilingLayoutManager,
    GridLayoutManager,
    MasterStackLayoutManager,
    TabbedPairsLayoutManager,
    ThreeColumnLayoutManager,
    WorkspaceLayoutManager,
)
from layman.perf import CommandBatcher, EventDebouncer, TreeCache
from layman.presets import PresetManager
from layman.rules import WindowRuleEngine
from layman.server import MessageServer
from layman.session import SessionManager

logger = get_logger(__name__)


@dataclass
class WorkspaceState:
    layoutManager: WorkspaceLayoutManager | None = None
    layoutName: str = "none"
    # The set of all window IDs on the workspace, including floating windows.
    windowIds: set[int] = field(default_factory=set)
    isExcluded: bool = False
    # Per-workspace focus history
    focusHistory: FocusHistory = field(default_factory=FocusHistory)
    # Fake fullscreen state (global, works with any layout)
    fakeFullscreen: bool = False
    fakeFullscreenWindowId: int | None = None
    savedStackLayout: str | None = None


@contextmanager
def layoutManagerReloader(
    layman: "Layman", workspace: Con | None, workspaceName: str | None = None
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
    builtinLayouts: dict[str, type[WorkspaceLayoutManager]]
    userLayouts: dict[str, type[WorkspaceLayoutManager]]
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
            ThreeColumnLayoutManager,
            TabbedPairsLayoutManager,
        ]:
            self.builtinLayouts[builtin_layout.shortName] = builtin_layout

        self.fetchUserLayouts()

        # Initialize window rule engine from config
        self._loadRules()

    def _loadRules(self) -> None:
        """Load window rules from config (top-level [[rules]] array)."""
        rules_config = self.options.configDict.get("rules", [])
        if isinstance(rules_config, list):
            self.ruleEngine = WindowRuleEngine.from_config(rules_config)
        else:
            self.ruleEngine = WindowRuleEngine()

    """
    Window Events

    The following functions that are called in response to window events, specifically
    window::new, window::focus, window::close, window::move, and window::floating.
    """

    def windowCreated(
        self,
        event: WindowEvent,
        tree: Con,
        workspace: Con | None,
        window: Con | None,
    ):
        if not (workspace and window):
            # Hopefully this was just a window that showed up and disappeared extremely quickly.
            # We'll just ignore it.
            self.log("no window found")
            return

        state = self.workspaceStates[workspace.name]
        state.windowIds.add(window.id)
        self.log(f"Adding window ID {window.id} to workspace {workspace.name}")
        self.log(f"Workspace {workspace.name} window ids: {state.windowIds}")

        # Evaluate window rules before passing to layout manager
        if hasattr(self, "ruleEngine") and self.ruleEngine.rules:
            actions = self.ruleEngine.evaluate(window)
            if actions.get("exclude"):
                self.log(f"Window {window.id} excluded by rule")
                state.windowIds.discard(window.id)
                return
            if actions.get("floating"):
                self.log(f"Window {window.id} floated by rule")
                self.command(f"[con_id={window.id}] floating enable")
                return
            if actions.get("workspace"):
                target_ws = actions["workspace"]
                self.log(f"Window {window.id} moved to workspace {target_ws} by rule")
                self.command(
                    f"[con_id={window.id}] move container to workspace {target_ws}"
                )
                return

        self.handleWindowAdded(event, workspace, window)

    def windowFocused(
        self,
        event: WindowEvent,
        tree: Con,
        workspace: Con | None,
        window: Con | None,
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
            logger.warning(
                "Stale focus event: window %s no longer focused (current: %s), skipping",
                event.container.id,
                focused_workspace_window.id if focused_workspace_window else None,
            )
            return

        # Track focus history
        state.focusHistory.push(window.id)

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
        workspace: Con | None,
        window: Con | None,
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

        state.windowIds.remove(event.container.id)
        self.log(
            f"Removing window ID {event.container.id} from workspace {workspaceName}"
        )
        self.log(f"Workspace {workspaceName} window ids: {state.windowIds}")

        # Remove from focus history
        state.focusHistory.remove(event.container.id)

        # If the fake-fullscreened window was closed, exit fake fullscreen
        if state.fakeFullscreen and state.fakeFullscreenWindowId == event.container.id:
            state.fakeFullscreen = False
            state.fakeFullscreenWindowId = None
            state.savedStackLayout = None
            self.log("Fake fullscreen window closed, exiting fake fullscreen")

        self.handleWindowRemoved(event, workspace, workspaceName, window)

    def windowMoved(
        self,
        event: WindowEvent,
        tree: Con,
        to_workspace: Con | None,
        window: Con | None,
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
            from_state.windowIds.remove(window.id)
            self.handleWindowRemoved(event, from_workspace, None, window)
            to_state.windowIds.add(window.id)
            self.handleWindowAdded(event, to_workspace, window)

    def windowFloating(
        self,
        event: WindowEvent,
        tree: Con,
        workspace: Con | None,
        window: Con | None,
    ):
        # If we can't find a window, hopefully it was just closed very quickly after the floating
        # event. Ignoring.
        if not (workspace and window):
            self.log("Window not found")
            return
        state = self.workspaceStates[workspace.name]

        # Check if we should pass this call to a layout manager
        if state.isExcluded:
            self.log("Workspace excluded")
            return

        # Only send windowFloating event if the layout manager supports it
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
                command = command.strip()
                # Decision #6: Filter empty commands
                if not command:
                    continue
                if command.startswith("nop layman"):
                    command = command.replace("nop layman ", "").strip()
                    self.handleCommand(command)
                else:
                    self.command(command)

    def onCommand(self, command) -> str:
        results = []
        for cmd in command.split(";"):
            cmd = cmd.strip()
            # Decision #6: Filter empty commands
            if not cmd:
                continue
            res = self.handleCommand(cmd)
            if res:
                results.append(res)
        return "\n".join(results) or "OK"

    def handleCommand(self, command: str) -> str | None:
        assert ";" not in command

        # Handle reload (no workspace needed)
        if command == "reload":
            self.options = config.LaymanConfig(utils.getConfigPath())
            setup_logging(self.options)
            self.fetchUserLayouts()
            self._loadRules()
            self.log("Reloaded layman config")
            return "Reloaded config"

        # Handle state dump
        if command == "dump":
            return self._dumpInternalState()

        # Handle session commands (no focused workspace needed)
        if command.startswith("session "):
            return self._handleSessionCommand(command[len("session ") :])

        # Handle preset commands (no focused workspace needed)
        if command.startswith("preset "):
            return self._handlePresetCommand(command[len("preset ") :])
        workspace = utils.findFocusedWorkspace(self.conn)
        if not workspace or self.workspaceStates[workspace.name].isExcluded:
            self.command(command)
            return f"Passed to sway: {command}"

        state = self.workspaceStates[workspace.name]

        # Route "layout set <name>" and "layout maximize"
        if command.startswith("layout "):
            rest = command[len("layout ") :]
            if rest.startswith("set "):
                shortName = rest[len("set ") :]
                self.setWorkspaceLayout(workspace, workspace.name, shortName)
                return f"Layout set to {shortName}"
            elif rest == "maximize":
                self.toggleFakeFullscreen(workspace, state)
                return "Maximize toggled"
            else:
                msg = f"Unknown layout command: '{command}'"
                self.logError(msg)
                return msg

        # Route "window <subcommand>" → strip prefix, pass to manager
        if command.startswith("window "):
            manager_command = command[len("window ") :]
            # Handle 'focus previous' via focus history (works with any layout)
            if manager_command == "focus previous":
                prev_id = state.focusHistory.previous()
                if prev_id:
                    self.command(f"[con_id={prev_id}] focus")
                    self.log(f"Focus previous: window {prev_id}")
                    return f"Focus previous: window {prev_id}"
                else:
                    self.log("No previous window in focus history")
                    return "No previous focus history"
            # Check move/focus overrides
            if (
                manager_command.startswith("move")
                and (
                    not state.layoutManager
                    or not state.layoutManager.overridesMoveBinds
                )
            ) or (
                manager_command.startswith("focus")
                and (
                    not state.layoutManager
                    or not state.layoutManager.overridesFocusBinds
                )
            ):
                self.command(manager_command)
                self.log(
                    'Handling bind "%s" for workspace %s'
                    % (manager_command, workspace.name)
                )
                return

            if state.layoutManager:
                self.log("Calling manager for workspace %s" % workspace.name)
                with layoutManagerReloader(self, workspace):
                    state.layoutManager.onCommand(manager_command, workspace)
                return (
                    f"Processed by {state.layoutManager.shortName}: {manager_command}"
                )
            else:
                self.log("No manager for workspace %s, ignoring" % workspace.name)
                return f"No manager for workspace {workspace.name}"

        # Route "stack <subcommand>" → pass to manager
        if command.startswith("stack "):
            manager_command = command[len("stack ") :]
            if state.layoutManager:
                self.log("Calling manager for workspace %s" % workspace.name)
                with layoutManagerReloader(self, workspace):
                    state.layoutManager.onCommand(manager_command, workspace)
                return (
                    f"Processed by {state.layoutManager.shortName}: {manager_command}"
                )
            else:
                self.log("No manager for workspace %s, ignoring" % workspace.name)
                return f"No manager for workspace {workspace.name}"

        # Route "master <subcommand>" → pass to manager
        if command.startswith("master "):
            manager_command = command  # Pass full command (e.g. "master add")
            if state.layoutManager:
                self.log("Calling manager for workspace %s" % workspace.name)
                with layoutManagerReloader(self, workspace):
                    state.layoutManager.onCommand(manager_command, workspace)
                return (
                    f"Processed by {state.layoutManager.shortName}: {manager_command}"
                )
            else:
                self.log("No manager for workspace %s, ignoring" % workspace.name)
                return f"No manager for workspace {workspace.name}"

        # Backwards compatibility: pass bare move/focus commands to Sway
        # if the layout manager doesn't override them
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

        # Pass remaining commands to the appropriate wlm
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

    def toggleFakeFullscreen(self, workspace: Con, state: WorkspaceState) -> None:
        """Toggle fake fullscreen for the focused workspace.

        Works with any layout (or no layout). Uses tabbed mode to show only
        the focused window while keeping the bar visible.
        """
        if state.fakeFullscreen:
            # Restore from fake fullscreen
            state.fakeFullscreen = False
            state.fakeFullscreenWindowId = None

            if state.layoutManager:
                # Let the layout manager re-arrange everything
                self.log("Restoring layout after fake fullscreen")
                with layoutManagerReloader(self, workspace):
                    state.layoutManager.onCommand("maximize", workspace)
            elif state.savedStackLayout:
                # Restore native layout
                windowIds = list(state.windowIds)
                if windowIds:
                    self.command(
                        f"[con_id={windowIds[0]}] layout {state.savedStackLayout}"
                    )
                state.savedStackLayout = None

            self.log(f"Exited fake fullscreen on workspace {workspace.name}")
        else:
            # Enter fake fullscreen
            focused = utils.findFocusedWindow(self.conn)
            if not focused:
                self.log("No focused window for fake fullscreen")
                return

            state.fakeFullscreenWindowId = focused.id

            if state.layoutManager:
                self.log("Entering fake fullscreen via layout manager")
                with layoutManagerReloader(self, workspace):
                    state.layoutManager.onCommand("maximize", workspace)
            else:
                # Save current layout and switch to tabbed
                windowIds = list(state.windowIds)
                if windowIds:
                    # Find current layout of the parent container
                    tree = self.conn.get_tree()
                    window = tree.find_by_id(focused.id)
                    if window and window.parent:
                        state.savedStackLayout = window.parent.layout
                    self.command(f"[con_id={windowIds[0]}] layout tabbed")

            state.fakeFullscreen = True
            self.log(f"Entered fake fullscreen on workspace {workspace.name}")

    # Runs and logs a command and its result.
    def command(self, command: str):
        logger.debug("Running command: %s", command, stacklevel=2)
        results = self.conn.command(command)
        for result in results:
            if result.success:
                logger.debug("Command succeeded.", stacklevel=2)
            else:
                logger.error("Command failed: %s", result.error, stacklevel=2)

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
                        type[WorkspaceLayoutManager], module
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

        state.windowIds = set(
            w.id for w in itertools.chain(workspace.leaves(), workspace.floating_nodes)
        )
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
        workspace: Con | None,
        workspaceName: str,
        layoutName: str | None = None,
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
                # Decision #3: Raise exception on unknown layout
                available = list(self.builtinLayouts.keys()) + list(
                    self.userLayouts.keys()
                )
                raise ConfigError(
                    f"Unknown layout '{layoutName}' for workspace {workspaceName}. "
                    f"Available layouts: {', '.join(available)}"
                )

        self.log(f"Initialized workspace {workspaceName} with layout {layoutName}")

    def handleWindowAdded(self, event: WindowEvent, workspace: Con, window: Con):
        state = self.workspaceStates[workspace.name]

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
        workspace: Con | None,
        workspaceName: str | None,
        window: Con | None,
    ):
        assert workspace or workspaceName
        if not workspaceName:
            assert workspace
            workspaceName = workspace.name
        assert workspaceName
        state = self.workspaceStates[workspaceName]

        # Check if we should handle layouts on this workspace.
        if state.isExcluded:
            self.log("Workspace excluded")
            return

        if state.layoutManager:
            self.log(
                f"Calling windowRemoved for window id {event.container.id} on workspace {workspaceName}"
            )
            with layoutManagerReloader(self, workspace, workspaceName):
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
                logger.error("Path to user config does not exist: %s", configPath)
                exit()

    def log(self, msg):
        logger.debug(msg, stacklevel=2)

    def logCaller(self, msg):
        logger.debug(msg, stacklevel=3)

    def _handleSessionCommand(self, subcommand: str) -> str:
        """Handle session save/restore/list/delete commands."""
        if not hasattr(self, "sessionManager"):
            session_dir = os.path.join(
                os.path.dirname(utils.getConfigPath()), "sessions"
            )
            self.sessionManager = SessionManager(self.conn, session_dir)

        parts = subcommand.strip().split(maxsplit=1)
        action = parts[0] if parts else ""
        name = parts[1] if len(parts) > 1 else "default"

        if action == "save":
            path = self.sessionManager.save(name, self.workspaceStates)
            msg = f"Session saved to {path}"
            self.log(msg)
            return msg
        elif action == "restore":
            self.sessionManager.restore(name)
            return f"Session {name} restored"
        elif action == "list":
            sessions = self.sessionManager.list_sessions()
            msg = f"Sessions: {', '.join(sessions) if sessions else '(none)'}"
            self.log(msg)
            return msg
        elif action == "delete":
            self.sessionManager.delete(name)
            return f"Session {name} deleted"
        else:
            msg = f"Unknown session command: '{subcommand}'"
            self.logError(msg)
            return msg
            self.logError(f"Unknown session command: '{subcommand}'")

    def _dumpInternalState(self) -> str:
        """Dump all internal state to logs for debugging."""
        state_dump = {
            "config": self.options.configDict,
            "workspaces": {},
        }

        for name, state in self.workspaceStates.items():
            ws_state = {
                "layoutName": state.layoutName,
                "windowIds": list(state.windowIds),
                "isExcluded": state.isExcluded,
                "fakeFullscreen": state.fakeFullscreen,
                "fakeFullscreenWindowId": state.fakeFullscreenWindowId,
            }
            if state.layoutManager:
                try:
                    ws_state["manager"] = state.layoutManager.dumpState()
                except Exception as e:
                    ws_state["manager_error"] = str(e)

            state_dump["workspaces"][name] = ws_state

        if hasattr(self, "ruleEngine"):
            state_dump["rules"] = [
                {
                    "app_id": r.match_app_id,
                    "class": r.match_window_class,
                    "floating": r.floating,
                    "exclude": r.exclude,
                    "workspace": r.workspace,
                }
                for r in self.ruleEngine.rules
            ]

        yaml_dump = yaml.dump(state_dump, default_flow_style=False, sort_keys=False)
        self.log(f"Dumping internal state:\n{yaml_dump}")
        return yaml_dump

    def _handlePresetCommand(self, subcommand: str) -> str:
        """Handle preset save/load/list/delete commands.

        Presets save the current workspace's layout name and options so you
        can quickly switch between named configurations.
        """
        if not hasattr(self, "presetManager"):
            presets_dir = os.path.join(
                os.path.dirname(utils.getConfigPath()), "presets"
            )
            self.presetManager = PresetManager(presets_dir)

        parts = subcommand.strip().split(maxsplit=1)
        action = parts[0] if parts else ""
        name = parts[1] if len(parts) > 1 else ""

        if action == "save" and name:
            workspace = utils.findFocusedWorkspace(self.conn)
            if workspace and workspace.name in self.workspaceStates:
                state = self.workspaceStates[workspace.name]
                self.presetManager.save(name, state.layoutName)
                msg = f"Preset saved: {name}"
                self.log(msg)
                return msg
            else:
                msg = "No focused workspace for preset save"
                self.logError(msg)
                return msg
        elif action == "load" and name:
            preset = self.presetManager.load(name)
            if preset:
                workspace = utils.findFocusedWorkspace(self.conn)
                if workspace:
                    self.setWorkspaceLayout(
                        workspace, workspace.name, preset.layout_name
                    )
                    msg = f"Preset loaded: {name} ({preset.layout_name})"
                    self.log(msg)
                    return msg
                else:
                    msg = "No focused workspace for preset load"
                    self.logError(msg)
                    return msg
            else:
                msg = f"Preset not found: {name}"
                self.logError(msg)
                return msg
        elif action == "list":
            presets = self.presetManager.list_presets()
            msg = f"Presets: {', '.join(presets) if presets else '(none)'}"
            self.log(msg)
            return msg
        elif action == "delete" and name:
            self.presetManager.delete(name)
            return f"Preset {name} deleted"
        else:
            msg = f"Unknown preset command: '{subcommand}'"
            self.logError(msg)
            return msg

    def logError(self, msg):
        logger.error(msg, stacklevel=2)

    def run(self):
        # Set up structured logging from config
        setup_logging(self.options)

        self.conn = Connection()
        notificationQueue = SimpleQueue()

        # Initialize performance utilities
        self.commandBatcher = CommandBatcher(self.conn)
        self.treeCache = TreeCache(self.conn)
        self.eventDebouncer = EventDebouncer(window_ms=10.0)

        # Get pipe path from config (Decision #17)
        pipe_path = self.options.getDefault(config.KEY_PIPE_PATH)

        # In order to shrink the window for race conditions as much as possible, we get the full
        # current container tree, and then immediately set up all listeners before continuing on
        # with any further initialization. The subscriptions are not actually created inside i3ipc
        # until calling Connection#main(), so we do that here, while delaying any callbacks, so that
        # we don't miss any notifications.
        tree = self.conn.get_tree()
        ListenerThread(notificationQueue)
        MessageServer(notificationQueue, pipe_path)

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
                        Callable[[WindowEvent, Con, Con | None, Con | None], None],
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
                        try:
                            handlers[event.change](event, tree, workspace, window)
                        except Exception:
                            logger.error(
                                "Error handling '%s' event for window %s",
                                event.change,
                                event.container.id,
                                exc_info=True,
                            )
                    else:
                        raise RuntimeError(
                            f"Unexpected window event type {event.change}"
                        )
                else:
                    raise RuntimeError(f"Invalid event received: {event}")

            elif notification["type"] == "command":
                try:
                    result = self.onCommand(notification["command"])
                    if "response_queue" in notification:
                        notification["response_queue"].put(result)
                except Exception:
                    logger.error(
                        "Error handling command: %s",
                        notification["command"],
                        exc_info=True,
                    )
                    if "response_queue" in notification:
                        notification["response_queue"].put(
                            "Error: Command execution failed."
                        )
            else:
                raise RuntimeError(f"Notification with invalid type: {notification}")
