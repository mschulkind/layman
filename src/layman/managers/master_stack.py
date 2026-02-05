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

import pprint
from enum import Enum
from typing import TypeVar

from i3ipc import Con

from layman.config import LaymanConfig, ConfigError
from layman.managers.workspace import WorkspaceLayoutManager

KEY_MASTER_WIDTH = "masterWidth"
KEY_STACK_LAYOUT = "stackLayout"
KEY_STACK_SIDE = "stackSide"
KEY_VISIBLE_STACK_LIMIT = "visibleStackLimit"


class StackLayout(Enum):
    SPLITV = 1
    SPLITH = 2
    STACKING = 3
    TABBED = 4

    def nextChoice(self):
        if self == StackLayout.SPLITV:
            return StackLayout.SPLITH
        elif self == StackLayout.SPLITH:
            return StackLayout.STACKING
        elif self == StackLayout.STACKING:
            return StackLayout.TABBED
        else:  # self == StackLayout.TABBED
            return StackLayout.SPLITV


class Side(Enum):
    RIGHT = 1
    LEFT = 2

    def opposite(self):
        if self == Side.LEFT:
            return Side.RIGHT
        else:
            return Side.LEFT

    def __str__(self):
        if self == self.RIGHT:
            return "right"
        else:
            return "left"


class MasterStackLayoutManager(WorkspaceLayoutManager):
    shortName = "MasterStack"
    overridesMoveBinds = True
    overridesFocusBinds = True
    supportsFloating = True

    # A list of all window IDs, excluding floating windows, in the workspace, with the first ID
    # being the master and the rest being the stack.
    windowIds: list[int]
    # A set of all window ID of floating windows in the workspace.
    floatingWindowIds: set[int]

    masterWidth: int
    stackLayout: StackLayout
    stackSide: Side
    visibleStackLimit: int
    substackExists: bool
    lastFocusedWindowId: int | None
    maximized: bool
    masterWidthBeforeMaximize: int

    E = TypeVar("E", bound=Enum)

    def getEnumOption(
        self, workspaceName: str, options: LaymanConfig, enum_class: type[E], key: str
    ) -> E | None:
        value = options.getForWorkspace(workspaceName, key)
        try:
            if value is not None:
                if not isinstance(value, str):
                    raise KeyError()

                return enum_class[value.upper()]
        except KeyError:
            valid_options = [e.name.lower() for e in enum_class]
            raise ConfigError(
                f"Invalid {key} '{value}'. Valid options: {', '.join(valid_options)}"
            )
        return None

    def __init__(self, con, workspace, workspaceName, options):
        super().__init__(con, workspace, workspaceName, options)
        self.windowIds = []
        self.floatingWindowIds = set()
        self.substackExists = False
        self.lastFocusedWindowId = None
        self.maximized = False
        self.masterWidthBeforeMaximize = 0

        # Decision #10: Accept int or float, reject 0 and 100
        self.masterWidth = 50
        masterWidth = options.getForWorkspace(workspaceName, KEY_MASTER_WIDTH)
        if masterWidth is not None:
            if isinstance(masterWidth, (int, float)) and 0 < masterWidth < 100:
                self.masterWidth = int(masterWidth) if isinstance(masterWidth, float) else masterWidth
            else:
                raise ConfigError(
                    f"Invalid masterWidth '{masterWidth}'. Must be a number between 0 and 100 exclusive."
                )

        self.stackSide = (
            self.getEnumOption(workspaceName, options, Side, KEY_STACK_SIDE)
            or Side.RIGHT
        )
        self.stackLayout = (
            self.getEnumOption(workspaceName, options, StackLayout, KEY_STACK_LAYOUT)
            or StackLayout.SPLITV
        )

        # Decision update: name change to visibleStackLimit (default 3)
        stack_limit = options.getForWorkspace(workspaceName, KEY_VISIBLE_STACK_LIMIT)
        if stack_limit is None:
            stack_limit = 3
        if isinstance(stack_limit, int) and stack_limit >= 0:
            self.visibleStackLimit = stack_limit
        else:
            raise ConfigError(
                f"Invalid {KEY_VISIBLE_STACK_LIMIT} '{stack_limit}'. Must be a non-negative integer."
            )

        # If windows exist, fit them into MasterStack
        if workspace:
            self.arrangeWindows(workspace)
            self.floatingWindowIds = set(w.id for w in workspace.floating_nodes)
            self.log(f"floating window ids: {self.floatingWindowIds}")

    def windowAdded(self, event, workspace, window):
        if self.isFloating(window):
            # We do nothing other than track floating windows.
            self.floatingWindowIds.add(window.id)
            self.log(f"floating window ids: {self.floatingWindowIds}")
            return

        self.pushWindow(workspace, window)
        self.log(f"Added window id: {window.id}")

    def windowRemoved(self, event, workspace, window):
        if self.isFloating(window):
            if window.id in self.floatingWindowIds:
                # We do nothing other than track floating windows.
                self.floatingWindowIds.remove(window.id)
                self.log(f"floating window ids: {self.floatingWindowIds}")
            else:
                self.logError(f"Floating window ID {window.id} not found")
            return

        self.popWindow(window)
        self.log(f"Removed window id: {window.id}")

    def windowFocused(self, event, workspace, window):
        if self.isFloating(window):
            return

        self.lastFocusedWindowId = window.id

    def windowFloating(self, event, workspace, window):
        if self.isFloating(window):
            self.log(f"Transitioning window id {window.id} to floating.")
            self.popWindow(window)
            self.floatingWindowIds.add(window.id)
            self.log(f"floating window ids: {self.floatingWindowIds}")
        else:
            self.log(f"Transitioning window id {window.id} to not floating.")
            self.floatingWindowIds.remove(window.id)
            self.log(f"floating window ids: {self.floatingWindowIds}")
            self.pushWindow(workspace, window)

    def onCommand(self, command, workspace):
        self.log(f"received command '{command}' with window ids {self.windowIds}")

        focused = workspace.find_focused()
        if not focused:
            self.log("no focused window, ignoring")
            return
        assert focused.id in self.windowIds

        if command == "move up":
            self.moveWindowRelative(focused, -1)
        elif command == "move down":
            self.moveWindowRelative(focused, 1)
        elif command == "move right":
            self.moveWindowHorizontally(workspace, focused, Side.RIGHT)
        elif command == "move left":
            self.moveWindowHorizontally(workspace, focused, Side.LEFT)
        elif command == "move to master":
            self.moveWindowToIndex(focused, 0)
        elif command.startswith("move to index"):
            split = command.split(" ")
            if len(split) == 4:
                try:
                    index = int(command.split(" ")[3])
                    if index >= 0 and index < len(self.windowIds):
                        self.moveWindowToIndex(focused, index)
                    else:
                        self.log(f"index {index} out of range.")
                    return
                except ValueError:
                    pass
            self.log("Usage: move to index <i>")
        elif command == "focus up":
            self.focusWindowRelative(workspace, -1)
        elif command == "focus down":
            self.focusWindowRelative(workspace, 1)
        elif command == "rotate ccw":
            self.rotateWindows(workspace, "ccw")
        elif command == "rotate cw":
            self.rotateWindows(workspace, "cw")
        elif command == "swap master":
            master = workspace.find_by_id(self.windowIds[0])
            assert master
            self.swapWindows(focused, master)
        elif command == "stack toggle":
            self.toggleStackLayout()
        elif command == "stackside toggle":
            self.toggleStackSide(workspace)
        elif command == "focus master":
            self.command(f"[con_id={self.windowIds[0]}] focus")
        elif command == "maximize":
            self.toggleMaximize(workspace)
        else:
            # Decision #4: Log unknown commands
            self.logError(f"Unknown command: '{command}'")

    def isFloating(self, window: Con) -> bool:
        i3Floating = window.floating is not None and "on" in window.floating
        swayFloating = window.type == "floating_con"
        return swayFloating or i3Floating

    def setMasterWidth(self):
        if self.masterWidth is not None and self.windowIds:
            masterId = self.windowIds[0]
            self.command(f"[con_id={masterId}] resize set width {self.masterWidth} ppt")
            self.logCaller(f"Set window {masterId} width to {self.masterWidth} ppt")

    def moveWindowCommand(self, moveId: int, targetId: int):
        self.command(f"[con_id={targetId}] mark --add move_target")
        self.command(f"[con_id={moveId}] move window to mark move_target")
        self.command(f"[con_id={targetId}] unmark move_target")
        self.logCaller(f"Moved window {moveId} to mark on window {targetId}")

    def swapWindowsCommand(self, firstWindowId: int, secondWindowId: int):
        self.command(
            f"[con_id={firstWindowId}] swap container with con_id {secondWindowId}"
        )

    def removeExtraNesting(self, workspace: Con):
        # We need to refresh our view of the tree here because master's parent may not have even
        # existed when we started handling this init/event, it is created as we arrange the first
        # stack window.
        master = self.con.get_tree().find_by_id(self.windowIds[0])
        if not master:
            self.log("Something probably went wrong in arrangeWindows")
            return
        masterParent = master.parent
        assert masterParent
        if masterParent.id != workspace.id:
            self.command(f"[con_id={masterParent.id}] split none")

    def arrangeWindows(self, workspace: Con):
        windows = workspace.leaves()
        if not windows:
            return

        # Decision #7: Focused window becomes master
        focused = workspace.find_focused()
        if focused and focused in windows:
            # Move focused window to front of list
            windows.remove(focused)
            windows.insert(0, focused)

        self.log(f"Arranging {len(windows)} windows")
        self.windowIds.clear()
        previousWindow = None
        for window in windows:
            self.pushWindow(workspace, window, previousWindow)
            previousWindow = window

        # Decision #13: Add debug logging when fewer windows than expected
        actual_leaves = len(workspace.leaves())
        if len(self.windowIds) != actual_leaves:
            self.logError(
                f"Window count mismatch: arranged {len(self.windowIds)} but workspace has {actual_leaves} leaves"
            )

        self.removeExtraNesting(workspace)

    def pushWindow(self, workspace: Con, window: Con, positionAfter: Con | None = None):
        positionAtIndex: int = 0
        if positionAfter:
            positionAfterIndex = self.getWindowListIndex(positionAfter)
            if positionAfterIndex is None:
                self.log(
                    f"Window {positionAfter.id} to positionAfter not found in windowIds."
                )
            else:
                positionAtIndex = positionAfterIndex + 1
        else:
            if self.lastFocusedWindowId:
                lastFocusedWindow = workspace.find_by_id(self.lastFocusedWindowId)
                if lastFocusedWindow is None:
                    self.log(
                        f"Last focused window {self.lastFocusedWindowId} not found."
                    )
                else:
                    lastFocusedIndex = self.getWindowListIndex(lastFocusedWindow)
                    if lastFocusedIndex is None:
                        self.log(
                            f"Last focused window {self.lastFocusedWindowId} not found in windowIds."
                        )
                    else:
                        positionAtIndex = lastFocusedIndex

        if len(self.windowIds) == 0:
            self.log("Too few windows to arrange")
        elif len(self.windowIds) == 1:
            # We have 2 windows now, so we create the master and the stack.

            if positionAtIndex == 0:
                masterId = window.id
                firstStackId = self.windowIds[0]
            else:
                masterId = self.windowIds[0]
                firstStackId = window.id

            if self.stackSide == Side.LEFT:
                self.command(f"[con_id={firstStackId}] splith")
                self.moveWindowCommand(masterId, firstStackId)
            else:
                self.command(f"[con_id={masterId}] splith")
                self.moveWindowCommand(firstStackId, masterId)

            self.command(f"[con_id={firstStackId}] splitv")
        else:
            if positionAtIndex == 0:  # New master
                self.swapWindowsCommand(window.id, self.windowIds[0])
                self.moveWindowCommand(self.windowIds[0], self.windowIds[1])
                self.swapWindowsCommand(self.windowIds[0], self.windowIds[1])
            elif positionAtIndex == 1 or (
                self.substackExists and positionAtIndex == self.visibleStackLimit
            ):
                # New first stack or first substack
                self.moveWindowCommand(window.id, self.windowIds[positionAtIndex])
                self.swapWindowsCommand(window.id, self.windowIds[positionAtIndex])
            else:
                self.moveWindowCommand(window.id, self.windowIds[positionAtIndex - 1])

        # If it was a new visible stack window and we have a substack, we need to demote a window
        # into the substack.
        if self.substackExists and positionAtIndex < self.visibleStackLimit:
            lastVisibleStack = self.windowIds[self.visibleStackLimit - 1]
            firstSubstack = self.windowIds[self.visibleStackLimit]
            self.moveWindowCommand(lastVisibleStack, firstSubstack)
            self.swapWindowsCommand(lastVisibleStack, firstSubstack)

        self.windowIds.insert(positionAtIndex, window.id)
        self.log(f"window ids: {self.windowIds}")
        self.createSubstackIfNeeded()
        if len(self.windowIds) == 2:
            # If we now have two window IDs, then we just created the master and stack and need to
            # adjust them.
            self.setStackLayout()
            self.setMasterWidth()
            self.removeExtraNesting(workspace)

    def popWindow(self, window: Con):
        self.log(f"Removing window id: {window.id}")
        sourceIndex = self.getWindowListIndex(window)
        if sourceIndex is None:
            self.log("Window not found in window list. This is probably a bug.")
            return

        self.windowIds.remove(window.id)
        self.log(f"window ids: {self.windowIds}")

        if sourceIndex == 0 and len(self.windowIds) >= 2:
            # Master was removed.
            self.command(
                f"[con_id={self.windowIds[0]}] move {self.stackSide.opposite()}"
            )

            # If the master was removed, that means the stack resized itself to full-width before we
            # added a master back, and now that master is at default 50% width, so we need to resize
            # it to the width of the previous master.
            if len(self.windowIds) > 1:
                if window.rect.width == 0:
                    # Not sure why width would ever be 0, but I've seen this. Smells a lot like a
                    # bug somewhere.
                    self.log("window with width 0 popped. likely a bug.")
                    self.log(pprint.pformat(window.__dict__))
                else:
                    self.command(
                        f"[con_id={self.windowIds[0]}] resize set width {window.rect.width} px"
                    )

        if self.substackExists:
            # We need to rebalance the visible stack and the substack if a window was removed from
            # the visible stack or master.
            if sourceIndex < self.visibleStackLimit:
                # A visible stack window is being removed, so we need to promote a window from the
                # substack.
                lastVisibleStack = self.windowIds[self.visibleStackLimit - 2]
                firstSubstack = self.windowIds[self.visibleStackLimit - 1]
                self.moveWindowCommand(firstSubstack, lastVisibleStack)

            if not self.shouldSubstackExist():
                self.destroySubstackIfExists()

    def shouldSubstackExist(self):
        return (
            self.stackLayout == StackLayout.SPLITV
            and self.visibleStackLimit > 0
            and len(self.windowIds) > self.visibleStackLimit
        )

    def setStackLayout(self):
        if len(self.windowIds) > 1:
            self.command(
                f"[con_id={self.windowIds[1]}] layout {self.stackLayout.name.lower()}"
            )

    def createSubstackIfNeeded(self):
        if self.shouldSubstackExist() and not self.substackExists:
            firstSubstack = self.windowIds[self.visibleStackLimit]
            self.command(f"[con_id={firstSubstack}] splitv, layout stacking")
            for windowId in reversed(self.windowIds[self.visibleStackLimit + 1 :]):
                self.moveWindowCommand(windowId, firstSubstack)

            self.substackExists = True

    def destroySubstackIfExists(self):
        if self.substackExists:
            lastVisibleStack = self.windowIds[self.visibleStackLimit - 1]
            for windowId in reversed(self.windowIds[self.visibleStackLimit :]):
                self.moveWindowCommand(windowId, lastVisibleStack)

            self.substackExists = False

    def toggleStackLayout(self):
        self.stackLayout = self.stackLayout.nextChoice()

        if not self.maximized:
            self.destroySubstackIfExists()
            self.setStackLayout()
            self.createSubstackIfNeeded()

        self.log(f"Changed stackLayout to {self.stackLayout.name.lower()}")

    def toggleStackSide(self, workspace: Con):
        if len(self.windowIds) >= 2:
            firstStack = workspace.find_by_id(self.windowIds[1])
            if not firstStack:
                self.log("Couldn't find the first stack window. Probably a bug.")
                return
            stackParent = firstStack.parent
            assert stackParent
            self.swapWindowsCommand(self.windowIds[0], stackParent.id)

            # When we move the stack from side to side, we just swap the stack and master
            # containers, so the widths get swapped too. This means we need to resize the master
            # back to the correct size.
            master = workspace.find_by_id(self.windowIds[0])
            assert master
            self.command(
                f"[con_id={master.id}] resize set width {master.rect.width} px"
            )
        self.stackSide = Side.opposite(self.stackSide)

    def getWindowListIndex(self, window: Con) -> int | None:
        try:
            return self.windowIds.index(window.id)
        except ValueError:
            self.logCaller(f"window id {window.id} not in window list")
            return None

    def moveWindowToIndex(self, window: Con, targetIndex: int):
        assert targetIndex >= 0 and targetIndex < len(self.windowIds)

        if len(self.windowIds) <= 1:
            self.log("not enough windows to move any")
            return

        sourceIndex = self.getWindowListIndex(window)
        if sourceIndex is None:
            return
        if sourceIndex == targetIndex:
            self.log("noop move. likely a bug.")
            return

        masterId = self.windowIds[0]
        topOfStackId = self.windowIds[1]
        substackRebalanced = False
        if self.maximized:
            if targetIndex == 0:
                self.moveWindowCommand(window.id, self.windowIds[0])
                self.swapWindowsCommand(window.id, self.windowIds[0])
            else:
                if targetIndex < sourceIndex:
                    moveTarget = targetIndex - 1
                else:
                    moveTarget = targetIndex
                self.moveWindowCommand(window.id, self.windowIds[moveTarget])
        elif (sourceIndex == 0 and targetIndex == 1) or (
            sourceIndex == 1 and targetIndex == 0
        ):
            self.swapWindowsCommand(masterId, topOfStackId)
        elif sourceIndex == 0:  # Master is source
            self.swapWindowsCommand(topOfStackId, masterId)
            self.moveWindowCommand(masterId, self.windowIds[targetIndex])
        elif targetIndex == 0:  # Master is target
            self.swapWindowsCommand(masterId, self.windowIds[sourceIndex])
            self.moveWindowCommand(masterId, self.windowIds[1])
            self.swapWindowsCommand(masterId, self.windowIds[1])
        elif sourceIndex - targetIndex in {-1, 1}:  # Neighbors
            # Moving 1 position in either direction
            self.swapWindowsCommand(
                self.windowIds[sourceIndex], self.windowIds[targetIndex]
            )
            # Because we just swapped the windows, the substack remains balanced, and we can skip
            # rebalancing below.
            substackRebalanced = True
        elif targetIndex == 1:  # Top of stack from in the stack
            self.moveWindowCommand(self.windowIds[sourceIndex], topOfStackId)
            self.swapWindowsCommand(self.windowIds[sourceIndex], topOfStackId)
        elif (
            self.substackExists
            and targetIndex == self.visibleStackLimit
            and sourceIndex > self.visibleStackLimit
        ):
            # Top of substack from within the substack
            self.moveWindowCommand(
                window.id,
                self.windowIds[targetIndex],
            )
            self.swapWindowsCommand(
                window.id,
                self.windowIds[targetIndex],
            )
        else:
            self.moveWindowCommand(
                window.id,
                self.windowIds[
                    targetIndex if sourceIndex < targetIndex else targetIndex - 1
                ],
            )

        if self.substackExists and not substackRebalanced:
            if sourceIndex >= self.visibleStackLimit and targetIndex < self.visibleStackLimit:
                # A substack window is being moved out of the substack, so we need to demote a
                # window to refill the substack.
                lastVisibleStack = self.windowIds[self.visibleStackLimit - 1]
                firstSubstack = self.windowIds[self.visibleStackLimit]
                if firstSubstack == window.id:
                    firstSubstack = self.windowIds[self.visibleStackLimit + 1]
                self.moveWindowCommand(lastVisibleStack, firstSubstack)
                self.swapWindowsCommand(lastVisibleStack, firstSubstack)

            if sourceIndex < self.visibleStackLimit and targetIndex >= self.visibleStackLimit:
                # A non-substack-window was added to the substack, so we need to promote a window
                # from the substack to refill the visible stack.
                lastVisibleStack = self.windowIds[self.visibleStackLimit - 1]
                firstSubstack = self.windowIds[self.visibleStackLimit]
                self.moveWindowCommand(firstSubstack, lastVisibleStack)

        self.windowIds.remove(window.id)
        self.windowIds.insert(targetIndex, window.id)
        self.log(f"window ids: {self.windowIds}")

    def moveWindowRelative(self, window: Con, delta: int):
        sourceIndex = self.getWindowListIndex(window)
        if sourceIndex is None:
            return
        targetIndex = (sourceIndex + delta) % len(self.windowIds)
        self.moveWindowToIndex(window, targetIndex)

    def rotateWindows(self, workspace: Con, direction: str):
        assert direction == "cw" or direction == "ccw"
        if len(self.windowIds) <= 1:
            return
        if (self.stackSide == Side.LEFT and direction == "cw") or (
            self.stackSide == Side.RIGHT and direction == "ccw"
        ):
            master = workspace.find_by_id(self.windowIds[0])
            assert master
            self.moveWindowToIndex(master, len(self.windowIds) - 1)
        else:
            last = workspace.find_by_id(self.windowIds[-1])
            assert last
            self.moveWindowToIndex(last, 0)

    def swapWindows(self, source: Con, target: Con):
        if not self.windowIds or source.id == target.id:
            return

        sourceIndex = self.getWindowListIndex(source)
        if sourceIndex is None:
            return

        targetIndex = self.getWindowListIndex(target)
        if targetIndex is None:
            return

        self.swapWindowsCommand(source.id, target.id)

        self.windowIds[sourceIndex], self.windowIds[targetIndex] = (
            self.windowIds[targetIndex],
            self.windowIds[sourceIndex],
        )
        self.log(f"window ids: {self.windowIds}")

    def moveWindowHorizontally(self, workspace: Con, window: Con, toSide: Side):
        if len(self.windowIds) < 2:
            return

        sourceIndex = self.getWindowListIndex(window)
        assert sourceIndex is not None
        isMaster = window.id == self.windowIds[0]

        if self.maximized:
            if toSide == Side.RIGHT:
                targetIndex = sourceIndex + 1
            else:
                targetIndex = sourceIndex - 1
            targetIndex %= len(self.windowIds)
            self.moveWindowToIndex(window, targetIndex)
            return

        if self.stackLayout in (StackLayout.TABBED, StackLayout.SPLITH):
            if self.stackSide == Side.LEFT:
                # Master towards the stack, or bottom of stack away from the stack
                if (self.stackSide == toSide and isMaster) or (
                    self.stackSide != toSide
                    and (sourceIndex + 1) == len(self.windowIds)
                ):
                    master = workspace.find_by_id(self.windowIds[0])
                    bottomOfStack = workspace.find_by_id(self.windowIds[-1])
                    assert master and bottomOfStack
                    self.swapWindows(master, bottomOfStack)
                    return

                # Master away from the stack, or top of stack away from the stack
                if (isMaster and self.stackSide != toSide) or (
                    sourceIndex == 1 and self.stackSide == toSide
                ):
                    return

            self.moveWindowRelative(window, -1 if toSide == Side.LEFT else 1)
            return

        if self.stackSide == toSide and isMaster:
            self.moveWindowToIndex(window, 1)
        elif self.stackSide != toSide and not isMaster:
            self.moveWindowToIndex(window, 0)

    def focusWindowRelative(self, workspace: Con, delta: int):
        assert self.lastFocusedWindowId
        lastFocusedWindow = workspace.find_by_id(self.lastFocusedWindowId)
        assert lastFocusedWindow
        sourceIndex = self.getWindowListIndex(lastFocusedWindow)
        assert sourceIndex is not None
        targetIndex = (sourceIndex + delta) % len(self.windowIds)
        self.command(f"[con_id={self.windowIds[targetIndex]}] focus")

    def toggleMaximize(self, workspace):
        if len(self.windowIds) >= 2:
            if not self.maximized:
                # Once we maximize, we'll lose the original master width, so we need to store it now so we
                # can restore it later when unmaximizing.
                master = workspace.find_by_id(self.windowIds[0])
                assert master
                self.masterWidthBeforeMaximize = master.rect.width

                self.destroySubstackIfExists()

                self.moveWindowCommand(self.windowIds[0], self.windowIds[1])
                self.swapWindowsCommand(self.windowIds[0], self.windowIds[1])
                self.command(f"[con_id={self.windowIds[0]}] layout tabbed")
            else:
                # Turn the stack back vertical.
                self.command(f"[con_id={self.windowIds[0]}] layout splitv")
                self.createSubstackIfNeeded()
                # Move the first window horizontally to create the master again.
                self.command(
                    f"[con_id={self.windowIds[0]}] move {self.stackSide.opposite()}"
                )
                # Restore the master's previous width.
                self.command(
                    f"[con_id={self.windowIds[0]}] resize set width {self.masterWidthBeforeMaximize} px"
                )
                self.setStackLayout()

        self.maximized = not self.maximized
        if self.maximized:
            self.log("Maximized")
        else:
            self.log("Unmaximized")
