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
from enum import Enum
from typing import Optional, Type, TypeVar

from i3ipc import Con
from layman.config import LaymanConfig
from layman.managers.workspace import WorkspaceLayoutManager

KEY_MASTER_WIDTH = "masterWidth"
KEY_STACK_LAYOUT = "stackLayout"
KEY_STACK_SIDE = "stackSide"
KEY_DEPTH_LIMIT = "depthLimit"


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

    windowIds: list[int]

    masterWidth: int
    stackLayout: StackLayout
    stackSide: Side
    depthLimit: int
    substackExists: bool
    lastFocusedWindowId: Optional[int]

    E = TypeVar("E", bound=Enum)

    def getEnumOption(
        self, workspace: Con, options: LaymanConfig, enum_class: Type[E], key: str
    ) -> Optional[E]:
        value = options.getForWorkspace(workspace, key)
        try:
            if value is not None:
                if not isinstance(value, str):
                    raise KeyError()

                return enum_class[value.upper()]
        except KeyError:
            self.logError(
                f"Invalid {key} '{value}'. Must be in {[l.name.lower() for l in enum_class]}."
            )
        return None

    def __init__(self, con, workspace, options):
        super().__init__(con, workspace, options)
        # A list of all window IDs in the workspace, with the first ID being the master and the
        # rest being the stack.
        self.windowIds = []
        self.masterWidth = 50
        masterWidth = options.getForWorkspace(workspace, KEY_MASTER_WIDTH)
        if isinstance(masterWidth, int) and masterWidth > 0 and masterWidth < 100:
            self.masterWidth = masterWidth
        elif masterWidth is not None:
            self.logError(
                f"Invalid masterWidth of '{masterWidth}'. Must be an integer between 0 and 100 exclusive."
            )
        self.substackExists = False
        self.lastFocusedWindowId = None

        self.stackSide = (
            self.getEnumOption(workspace, options, Side, KEY_STACK_SIDE) or Side.RIGHT
        )
        self.stackLayout = (
            self.getEnumOption(workspace, options, StackLayout, KEY_STACK_LAYOUT)
            or StackLayout.SPLITV
        )

        depthLimit = options.getForWorkspace(workspace, KEY_DEPTH_LIMIT) or 0
        if not isinstance(depthLimit, int) or depthLimit < 0 or depthLimit == 1:
            self.logError(
                f"Invalid depthLimit '{depthLimit}'. Must be an integer greater than 1."
            )
            self.depthLimit = 0
        else:
            self.depthLimit = depthLimit

        # If windows exist, fit them into MasterStack
        self.arrangeWindows(workspace)

    def windowAdded(self, event, workspace, window):
        # Ignore excluded windows
        if self.isExcluded(window):
            return

        self.pushWindow(workspace, window)

        self.log("Added window id: %d" % window.id)

    def windowRemoved(self, event, workspace, window):
        # Ignore excluded windows
        if self.isExcluded(window):
            return

        self.popWindow(workspace, window)

    def windowFocused(self, event, workspace, window):
        # Ignore excluded windows
        if self.isExcluded(window):
            return

        self.lastFocusedWindowId = window.id

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
            self.log(f"Usage: move to index <i>")
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

    def isExcluded(self, window):
        if window.floating is not None and "on" in window.floating:
            return True

        return False

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
        master = self.con.get_tree().find_by_id(self.windowIds[0])
        if not master:
            self.log("Something probably went wrong in arrangeWindows")
            return
        masterParent = master.parent
        assert masterParent
        if masterParent.id != workspace.id:
            self.command(f"[con_id={masterParent.id}] split none")

    def arrangeWindows(self, workspace):
        windows = workspace.leaves()
        if not windows:
            return

        self.log("Arranging windows")
        self.windowIds.clear()
        previousWindow = None
        for window in windows:
            self.pushWindow(workspace, window, previousWindow)
            previousWindow = window

        self.removeExtraNesting(workspace)

    def pushWindow(
        self, workspace: Con, window: Con, positionAfter: Optional[Con] = None
    ):
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
                self.substackExists and positionAtIndex == self.depthLimit
            ):
                # New first stack or first substack
                self.moveWindowCommand(window.id, self.windowIds[positionAtIndex])
                self.swapWindowsCommand(window.id, self.windowIds[positionAtIndex])

            else:
                self.moveWindowCommand(window.id, self.windowIds[positionAtIndex - 1])

        # If it was a new visible stack window and we have a substack, we need to demote a window
        # into the substack.
        if self.substackExists and positionAtIndex < self.depthLimit:
            lastVisibleStack = self.windowIds[self.depthLimit - 1]
            firstSubstack = self.windowIds[self.depthLimit]
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

    def popWindow(self, workspace: Con, window: Con):
        self.log(f"Removing window id: {window.id}")
        sourceIndex = self.getWindowListIndex(window)
        if sourceIndex is None:
            self.log("Window not found in window list. This is probably a bug.")
            return

        self.windowIds.remove(window.id)
        self.log(f"window ids: {self.windowIds}")

        if sourceIndex == 0:
            # Master was removed.
            self.command(
                f"[con_id={self.windowIds[0]}] move {self.stackSide.opposite()}"
            )

            # If the master was removed, that means the stack resized itself to full-width before we
            # added a master back, and now that master is at default 50% width, so we need to resize
            # it to the width of the previous master.
            if len(self.windowIds) > 1:
                self.command(
                    f"[con_id={self.windowIds[0]}] resize set width {window.rect.width} px"
                )

        if self.substackExists:
            # We need to rebalance the visible stack and the substack if a window was removed from
            # the visible stack or master.
            if sourceIndex < self.depthLimit:
                # A visible stack window is being removed, so we need to promote a window from the
                # substack.
                lastVisibleStack = self.windowIds[self.depthLimit - 2]
                firstSubstack = self.windowIds[self.depthLimit - 1]
                self.moveWindowCommand(firstSubstack, lastVisibleStack)

            if not self.shouldSubstackExist():
                self.destroySubstackIfExists()

    def shouldSubstackExist(self):
        return (
            self.stackLayout == StackLayout.SPLITV
            and self.depthLimit > 0
            and len(self.windowIds) > (self.depthLimit + 1)
        )

    def setStackLayout(self):
        if len(self.windowIds) > 1:
            self.command(
                f"[con_id={self.windowIds[1]}] layout {self.stackLayout.name.lower()}"
            )
            self.log(f"Changed stackLayout to {self.stackLayout.name.lower()}")

    def createSubstackIfNeeded(self):
        if self.shouldSubstackExist() and not self.substackExists:
            firstSubstack = self.windowIds[self.depthLimit]
            self.command(f"[con_id={firstSubstack}] splitv, layout stacking")
            for windowId in reversed(self.windowIds[self.depthLimit + 1 :]):
                self.moveWindowCommand(windowId, firstSubstack)

            self.substackExists = True

    def destroySubstackIfExists(self):
        if self.substackExists:
            lastVisibleStack = self.windowIds[self.depthLimit - 1]
            for windowId in reversed(self.windowIds[self.depthLimit :]):
                self.moveWindowCommand(windowId, lastVisibleStack)

            self.substackExists = False

    def toggleStackLayout(self):
        self.destroySubstackIfExists()

        self.stackLayout = self.stackLayout.nextChoice()
        self.setStackLayout()

        self.createSubstackIfNeeded()

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

    def getWindowListIndex(self, window: Con) -> Optional[int]:
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
        if (sourceIndex == 0 and targetIndex == 1) or (
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
            and targetIndex == self.depthLimit
            and sourceIndex > self.depthLimit
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
            if sourceIndex >= self.depthLimit and targetIndex < self.depthLimit:
                # A substack window is being moved out of the substack, so we need to demote a
                # window to refill the substack.
                lastVisibleStack = self.windowIds[self.depthLimit - 1]
                firstSubstack = self.windowIds[self.depthLimit]
                if firstSubstack == window.id:
                    firstSubstack = self.windowIds[self.depthLimit + 1]
                self.moveWindowCommand(lastVisibleStack, firstSubstack)
                self.swapWindowsCommand(lastVisibleStack, firstSubstack)

            if sourceIndex < self.depthLimit and targetIndex >= self.depthLimit:
                # A non-substack-window was added to the substack, so we need to promote a window
                # from the substack to refill the visible stack.
                lastVisibleStack = self.windowIds[self.depthLimit - 1]
                firstSubstack = self.windowIds[self.depthLimit]
                self.moveWindowCommand(firstSubstack, lastVisibleStack)

        self.windowIds.remove(window.id)
        self.windowIds.insert(targetIndex, window.id)
        self.log(f"window ids: {self.windowIds}")

    def moveWindowRelative(self, window: Con, delta: int):
        sourceIndex = self.getWindowListIndex(window)
        if sourceIndex is None:
            return
        targetIndex = sourceIndex + delta
        if (targetIndex < 0) or (targetIndex >= len(self.windowIds)):
            # Out of range
            self.log("Move out of range")
            return
        else:
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
