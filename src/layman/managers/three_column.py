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

import i3ipc
from i3ipc import Con, WindowEvent

from layman.config import ConfigError, LaymanConfig
from layman.managers.workspace import WorkspaceLayoutManager

KEY_MASTER_WIDTH = "masterWidth"
KEY_STACK_LAYOUT = "stackLayout"
KEY_BALANCE_STACKS = "balanceStacks"


class StackLayout(Enum):
    SPLITV = 1
    SPLITH = 2
    STACKING = 3
    TABBED = 4

    def nextChoice(self) -> "StackLayout":
        cycle = {
            StackLayout.SPLITV: StackLayout.SPLITH,
            StackLayout.SPLITH: StackLayout.STACKING,
            StackLayout.STACKING: StackLayout.TABBED,
            StackLayout.TABBED: StackLayout.SPLITV,
        }
        return cycle[self]


class ThreeColumnLayoutManager(WorkspaceLayoutManager):
    """Three-column layout with master in center, stacks on left and right.

    Inspired by XMonad's ThreeColMid layout. The master window occupies
    the center column, with stack windows distributed between left and
    right side columns.

    Window distribution (with balanceStacks=True):
        Window 1 → Center (master)
        Window 2 → Right stack
        Window 3 → Left stack
        Window 4 → Right stack (2nd)
        Window 5 → Left stack (2nd)
        ...
    """

    shortName = "ThreeColumn"
    overridesMoveBinds = True
    overridesFocusBinds = True
    supportsFloating = True

    # Window tracking
    masterId: int | None
    leftStack: list[int]
    rightStack: list[int]
    floatingWindowIds: set[int]

    # Configuration
    masterWidth: int
    stackLayout: StackLayout
    balanceStacks: bool

    # State
    lastFocusedWindowId: int | None
    maximized: bool
    masterWidthBeforeMaximize: int

    def __init__(
        self,
        con: "i3ipc.Connection",
        workspace: Con | None,
        workspaceName: str,
        options: LaymanConfig,
    ) -> None:
        super().__init__(con, workspace, workspaceName, options)
        self.masterId = None
        self.leftStack = []
        self.rightStack = []
        self.floatingWindowIds = set()
        self.lastFocusedWindowId = None
        self.maximized = False
        self.masterWidthBeforeMaximize = 0

        # Parse masterWidth
        self.masterWidth = 50
        masterWidth = options.getForWorkspace(workspaceName, KEY_MASTER_WIDTH)
        if masterWidth is not None:
            if isinstance(masterWidth, (int, float)) and 0 < masterWidth < 100:
                self.masterWidth = (
                    int(masterWidth) if isinstance(masterWidth, float) else masterWidth
                )
            else:
                raise ConfigError(
                    f"Invalid masterWidth '{masterWidth}'. "
                    "Must be a number between 0 and 100 exclusive."
                )

        # Parse stackLayout
        self.stackLayout = StackLayout.SPLITV
        stackLayoutValue = options.getForWorkspace(workspaceName, KEY_STACK_LAYOUT)
        if stackLayoutValue is not None:
            try:
                if not isinstance(stackLayoutValue, str):
                    raise KeyError()
                self.stackLayout = StackLayout[stackLayoutValue.upper()]
            except KeyError:
                valid = [e.name.lower() for e in StackLayout]
                raise ConfigError(
                    f"Invalid stackLayout '{stackLayoutValue}'. "
                    f"Valid options: {', '.join(valid)}"
                ) from None

        # Parse balanceStacks
        self.balanceStacks = True
        balanceValue = options.getForWorkspace(workspaceName, KEY_BALANCE_STACKS)
        if balanceValue is not None:
            if isinstance(balanceValue, bool):
                self.balanceStacks = balanceValue
            else:
                raise ConfigError(
                    f"Invalid balanceStacks '{balanceValue}'. Must be true or false."
                )

        # If windows exist, arrange them
        if workspace:
            self._arrangeExisting(workspace)
            self.floatingWindowIds = set(w.id for w in workspace.floating_nodes)
            self.log(f"floating window ids: {self.floatingWindowIds}")

    # -------------------------------------------------------------------------
    # Window event handlers
    # -------------------------------------------------------------------------

    def windowAdded(self, event: WindowEvent, workspace: Con, window: Con) -> None:
        if self._isFloating(window):
            self.floatingWindowIds.add(window.id)
            self.log(f"floating window ids: {self.floatingWindowIds}")
            return

        self._addWindow(workspace, window)

    def windowRemoved(
        self, event: WindowEvent, workspace: Con | None, window: Con
    ) -> None:
        if self._isFloating(window):
            if window.id in self.floatingWindowIds:
                self.floatingWindowIds.remove(window.id)
                self.log(f"floating window ids: {self.floatingWindowIds}")
            else:
                self.logError(f"Floating window ID {window.id} not found")
            return

        self._removeWindow(workspace, window)

    def windowFocused(self, event: WindowEvent, workspace: Con, window: Con) -> None:
        if self._isFloating(window):
            return
        self.lastFocusedWindowId = window.id

    def windowMoved(self, event: WindowEvent, workspace: Con, window: Con) -> None:
        if self._isFloating(window):
            return

    def windowFloating(self, event: WindowEvent, workspace: Con, window: Con) -> None:
        i3Floating = window.floating is not None and "on" in window.floating
        swayFloating = window.type == "floating_con"
        isNowFloating = swayFloating or i3Floating

        if isNowFloating:
            # Tiled → floating: remove from layout, add to floating set
            self._removeWindow(workspace, window)
            self.floatingWindowIds.add(window.id)
        else:
            # Floating → tiled: remove from floating set, add to layout
            self.floatingWindowIds.discard(window.id)
            self._addWindow(workspace, window)

    # -------------------------------------------------------------------------
    # Command handling
    # -------------------------------------------------------------------------

    def onCommand(self, command: str, workspace: Con) -> None:
        focused = workspace.find_focused()
        if not focused and command not in ("balance",):
            self.logError("No focused window found")
            return

        dispatch = {
            "move left": lambda: self._moveToColumn(workspace, focused, "left"),
            "move right": lambda: self._moveToColumn(workspace, focused, "right"),
            "move to master": lambda: self._moveToColumn(workspace, focused, "master"),
            "move up": lambda: self._moveWithinColumn(workspace, focused, -1),
            "move down": lambda: self._moveWithinColumn(workspace, focused, 1),
            "focus left": lambda: self._focusColumn(workspace, "left"),
            "focus right": lambda: self._focusColumn(workspace, "right"),
            "focus up": lambda: self._focusWithinColumn(workspace, focused, -1),
            "focus down": lambda: self._focusWithinColumn(workspace, focused, 1),
            "focus master": lambda: self._focusMaster(),
            "swap master": lambda: self._swapWithMaster(workspace, focused),
            "rotate cw": lambda: self._rotate(workspace, 1),
            "rotate ccw": lambda: self._rotate(workspace, -1),
            "toggle": lambda: self._toggleStackLayout(),
            "maximize": lambda: self._toggleMaximize(workspace),
            "balance": lambda: self._balance(workspace),
        }

        handler = dispatch.get(command)
        if handler:
            handler()
        else:
            self.logError(f"Unknown command: '{command}'")

    # -------------------------------------------------------------------------
    # Window management
    # -------------------------------------------------------------------------

    def _getAllWindowIds(self) -> list[int]:
        """Get all window IDs in order: left stack, master, right stack."""
        result = list(self.leftStack)
        if self.masterId is not None:
            result.append(self.masterId)
        result.extend(self.rightStack)
        return result

    def _getWindowColumn(self, windowId: int) -> str | None:
        """Return which column a window is in: 'left', 'master', or 'right'."""
        if windowId == self.masterId:
            return "master"
        if windowId in self.leftStack:
            return "left"
        if windowId in self.rightStack:
            return "right"
        return None

    def _isFloating(self, window: Con) -> bool:
        i3Floating = window.floating is not None and "on" in window.floating
        swayFloating = window.type == "floating_con"
        return swayFloating or i3Floating

    def _addWindow(self, workspace: Con, window: Con) -> None:
        """Add a tiled window to the layout."""
        if self.masterId is None:
            # First window becomes master
            self.masterId = window.id
            self.log(f"Window {window.id} → master")
            return

        # Determine target stack
        if self.balanceStacks:
            if len(self.rightStack) <= len(self.leftStack):
                self.rightStack.append(window.id)
                self.log(f"Window {window.id} → right stack")
            else:
                self.leftStack.append(window.id)
                self.log(f"Window {window.id} → left stack")
        else:
            self.rightStack.append(window.id)
            self.log(f"Window {window.id} → right stack")

        self._arrange(workspace)

    def _removeWindow(self, workspace: Con | None, window: Con) -> None:
        """Remove a tiled window from the layout."""
        column = self._getWindowColumn(window.id)
        if column is None:
            self.logError(f"Window {window.id} not found in any column")
            return

        if column == "master":
            # Promote from right stack first, then left
            if self.rightStack:
                self.masterId = self.rightStack.pop(0)
                self.log(f"Promoted {self.masterId} from right stack to master")
            elif self.leftStack:
                self.masterId = self.leftStack.pop(0)
                self.log(f"Promoted {self.masterId} from left stack to master")
            else:
                self.masterId = None
                self.log("No windows left to promote to master")
        elif column == "left":
            self.leftStack.remove(window.id)
        elif column == "right":
            self.rightStack.remove(window.id)

        if workspace and (self.masterId is not None):
            self._arrange(workspace)

    def _arrangeExisting(self, workspace: Con) -> None:
        """Arrange existing windows when layout is first activated."""
        windows = [w for w in workspace.leaves() if not self._isFloating(w)]
        if not windows:
            return

        # First window (focused if possible) becomes master
        focused = workspace.find_focused()
        if focused and focused in windows:
            self.masterId = focused.id
            windows.remove(focused)
        else:
            self.masterId = windows[0].id
            windows = windows[1:]

        # Distribute remaining to stacks
        for w in windows:
            if self.balanceStacks:
                if len(self.rightStack) <= len(self.leftStack):
                    self.rightStack.append(w.id)
                else:
                    self.leftStack.append(w.id)
            else:
                self.rightStack.append(w.id)

        self._arrange(workspace)

    def _arrange(self, workspace: Con) -> None:
        """Arrange all windows into the three-column structure."""
        if self.masterId is None:
            return

        allIds = self._getAllWindowIds()
        totalWindows = len(allIds)

        if totalWindows == 1:
            # Single window fills workspace
            return

        if totalWindows == 2:
            # Master + one stack column
            otherId = (
                self.leftStack[0]
                if self.leftStack
                else self.rightStack[0]
                if self.rightStack
                else None
            )
            if otherId is None:
                return

            # Ensure master is on the correct side
            self.command(f"[con_id={self.masterId}] split none")
            self.command(f"[con_id={self.masterId}] splith")
            self.moveWindowCommand(otherId, self.masterId)

            # Set master width
            self.command(
                f"[con_id={self.masterId}] resize set width {self.masterWidth} ppt"
            )
            return

        # Three or more windows: full three-column layout
        # 1. Build the structure: left | master | right
        self.command(f"[con_id={self.masterId}] split none")
        self.command(f"[con_id={self.masterId}] splith")

        # Place all right stack windows
        for wId in self.rightStack:
            self.moveWindowCommand(wId, self.masterId)

        # Place all left stack windows
        for wId in self.leftStack:
            self.moveWindowCommand(wId, self.masterId)
            self.command(f"[con_id={wId}] move left")

        # Set stack layouts
        if self.leftStack:
            self.command(
                f"[con_id={self.leftStack[0]}] layout {self.stackLayout.name.lower()}"
            )
        if self.rightStack:
            self.command(
                f"[con_id={self.rightStack[0]}] layout {self.stackLayout.name.lower()}"
            )

        # Set column widths
        self.command(
            f"[con_id={self.masterId}] resize set width {self.masterWidth} ppt"
        )

        # Focus master
        self.command(f"[con_id={self.masterId}] focus")

    # -------------------------------------------------------------------------
    # Movement commands
    # -------------------------------------------------------------------------

    def _moveToColumn(self, workspace: Con, window: Con | None, target: str) -> None:
        """Move a window to a different column."""
        if window is None:
            return

        current = self._getWindowColumn(window.id)
        if current is None or current == target:
            return

        # Remove from current column
        if current == "master":
            pass  # Will be handled below
        elif current == "left":
            self.leftStack.remove(window.id)
        elif current == "right":
            self.rightStack.remove(window.id)

        # Add to target column
        if target == "master":
            oldMaster = self.masterId
            self.masterId = window.id
            # Push old master to the opposite side of where the window came from
            if oldMaster is not None:
                if current == "left":
                    self.rightStack.insert(0, oldMaster)
                else:
                    self.leftStack.insert(0, oldMaster)
        elif target == "left":
            if current == "master":
                # Promote from right stack (or left) to master
                if self.rightStack:
                    self.masterId = self.rightStack.pop(0)
                elif self.leftStack:
                    self.masterId = self.leftStack.pop(0)
                else:
                    self.masterId = None
            self.leftStack.append(window.id)
        elif target == "right":
            if current == "master":
                if self.leftStack:
                    self.masterId = self.leftStack.pop(0)
                elif self.rightStack:
                    self.masterId = self.rightStack.pop(0)
                else:
                    self.masterId = None
            self.rightStack.append(window.id)

        self._arrange(workspace)

    def _moveWithinColumn(
        self, workspace: Con, window: Con | None, direction: int
    ) -> None:
        """Move a window up or down within its column."""
        if window is None:
            return

        column = self._getWindowColumn(window.id)
        if column == "master":
            # Master can't move within its column (it's the only one)
            return

        stack = self.leftStack if column == "left" else self.rightStack
        try:
            idx = stack.index(window.id)
        except ValueError:
            return

        newIdx = (idx + direction) % len(stack)
        if newIdx == idx:
            return

        # Swap positions
        stack[idx], stack[newIdx] = stack[newIdx], stack[idx]
        self.swapWindowsCommand(stack[idx], stack[newIdx])

    def _swapWithMaster(self, workspace: Con, window: Con | None) -> None:
        """Swap the focused window with the master window."""
        if window is None or self.masterId is None:
            return
        if window.id == self.masterId:
            return

        column = self._getWindowColumn(window.id)
        if column is None:
            return

        oldMaster = self.masterId
        self.masterId = window.id

        if column == "left":
            idx = self.leftStack.index(window.id)
            self.leftStack[idx] = oldMaster
        elif column == "right":
            idx = self.rightStack.index(window.id)
            self.rightStack[idx] = oldMaster

        self.swapWindowsCommand(window.id, oldMaster)

    def _rotate(self, workspace: Con, direction: int) -> None:
        """Rotate all windows clockwise (1) or counter-clockwise (-1)."""
        allIds = self._getAllWindowIds()
        if len(allIds) <= 1:
            return

        if direction > 0:
            # Clockwise: last becomes first
            rotated = [allIds[-1], *allIds[:-1]]
        else:
            # Counter-clockwise: first becomes last
            rotated = [*allIds[1:], allIds[0]]

        # Redistribute into columns
        self._redistributeFromList(rotated)
        self._arrange(workspace)

    # -------------------------------------------------------------------------
    # Focus commands
    # -------------------------------------------------------------------------

    def _focusColumn(self, workspace: Con, direction: str) -> None:
        """Focus the first window in the column to the left or right."""
        focused = workspace.find_focused()
        if not focused:
            return

        current = self._getWindowColumn(focused.id)
        columns = ["left", "master", "right"]

        if current not in columns:
            return

        currentIdx = columns.index(current)

        if direction == "left":
            targetIdx = (currentIdx - 1) % 3
        else:
            targetIdx = (currentIdx + 1) % 3

        targetColumn = columns[targetIdx]
        targetId = self._getFirstInColumn(targetColumn)
        if targetId is not None:
            self.command(f"[con_id={targetId}] focus")

    def _focusWithinColumn(
        self, workspace: Con, window: Con | None, direction: int
    ) -> None:
        """Focus next/previous window within the current column."""
        if window is None:
            return

        column = self._getWindowColumn(window.id)
        if column == "master":
            return

        stack = self.leftStack if column == "left" else self.rightStack
        try:
            idx = stack.index(window.id)
        except ValueError:
            return

        newIdx = (idx + direction) % len(stack)
        self.command(f"[con_id={stack[newIdx]}] focus")

    def _focusMaster(self) -> None:
        """Focus the master window."""
        if self.masterId is not None:
            self.command(f"[con_id={self.masterId}] focus")

    def _getFirstInColumn(self, column: str) -> int | None:
        """Get the first window ID in a column."""
        if column == "master":
            return self.masterId
        elif column == "left":
            return self.leftStack[0] if self.leftStack else None
        elif column == "right":
            return self.rightStack[0] if self.rightStack else None
        return None

    # -------------------------------------------------------------------------
    # Layout toggles
    # -------------------------------------------------------------------------

    def _toggleStackLayout(self) -> None:
        """Cycle through stack layout options."""
        self.stackLayout = self.stackLayout.nextChoice()
        if self.leftStack:
            self.command(
                f"[con_id={self.leftStack[0]}] layout {self.stackLayout.name.lower()}"
            )
        if self.rightStack:
            self.command(
                f"[con_id={self.rightStack[0]}] layout {self.stackLayout.name.lower()}"
            )
        self.log(f"Stack layout set to {self.stackLayout.name.lower()}")

    def _toggleMaximize(self, workspace: Con) -> None:
        """Toggle fake fullscreen (tabbed mode)."""
        allIds = self._getAllWindowIds()
        if not allIds:
            return

        if self.maximized:
            # Restore
            self._arrange(workspace)
            self.maximized = False
            self.log("Unmaximized")
        else:
            # Maximize: tabbed layout across all
            self.command(f"[con_id={allIds[0]}] layout tabbed")
            self.maximized = True
            self.log("Maximized")

    def _balance(self, workspace: Con) -> None:
        """Rebalance windows between left and right stacks."""
        allStackIds = list(self.leftStack) + list(self.rightStack)
        self.leftStack.clear()
        self.rightStack.clear()

        for i, wId in enumerate(allStackIds):
            if i % 2 == 0:
                self.rightStack.append(wId)
            else:
                self.leftStack.append(wId)

        self._arrange(workspace)
        self.log("Rebalanced stacks")

    # -------------------------------------------------------------------------
    # Helper commands
    # -------------------------------------------------------------------------

    def moveWindowCommand(self, moveId: int, targetId: int) -> None:
        """Move a window to be adjacent to another using marks."""
        self.command(f"[con_id={targetId}] mark --add _layman_target")
        self.command(f"[con_id={moveId}] move to mark _layman_target")
        self.command("unmark _layman_target")

    def swapWindowsCommand(self, id1: int, id2: int) -> None:
        """Swap two windows' positions."""
        self.command(f"[con_id={id1}] swap container with con_id {id2}")

    def _redistributeFromList(self, ids: list[int]) -> None:
        """Redistribute a flat list of IDs into master/left/right."""
        if not ids:
            self.masterId = None
            self.leftStack.clear()
            self.rightStack.clear()
            return

        # Determine how many were in each column before
        leftCount = len(self.leftStack)

        self.leftStack.clear()
        self.rightStack.clear()

        # Master is still the element at the same position
        # Find where master was in the original ordering
        # left stack, then master, then right stack
        self.masterId = ids[leftCount] if leftCount < len(ids) else ids[0]
        self.leftStack = ids[:leftCount]
        self.rightStack = ids[leftCount + 1 :]
