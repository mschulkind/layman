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

from __future__ import annotations

from dataclasses import dataclass

import i3ipc
from i3ipc import Con, WindowEvent

from layman.config import LaymanConfig
from layman.managers.workspace import WorkspaceLayoutManager

KEY_PAIR_RULES = "pairRules"


@dataclass
class WindowPair:
    """A pair of related windows displayed in a tabbed container."""

    primary: int
    secondary: int


class TabbedPairsLayoutManager(WorkspaceLayoutManager):
    """Layout manager that groups related windows into tabbed pairs.

    Windows are auto-paired by app_id matching rules, or manually via
    the pair/unpair commands. Pairs appear as tabbed containers; navigation
    between pairs is left/right, within pairs is up/down.

    Configuration example:
        [workspace.coding]
        defaultLayout = "TabbedPairs"

        [workspace.coding.pairRules]
        nvim = ["code", "vscode"]
        emacs = ["code", "vscode"]
    """

    shortName = "TabbedPairs"
    overridesMoveBinds = True
    overridesFocusBinds = True
    supportsFloating = True

    # State
    pairs: list[WindowPair]
    unpairedWindows: list[int]
    floatingWindowIds: set[int]
    focusedPairIndex: int
    pendingManualPair: int | None  # Window ID awaiting a partner

    # Configuration
    pairRules: dict[str, list[str]]

    def __init__(
        self,
        con: i3ipc.Connection,
        workspace: Con | None,
        workspaceName: str,
        options: LaymanConfig,
    ) -> None:
        super().__init__(con, workspace, workspaceName, options)
        self.pairs = []
        self.unpairedWindows = []
        self.floatingWindowIds = set()
        self.focusedPairIndex = 0
        self.pendingManualPair = None

        # Parse pair rules from config
        self.pairRules = {}
        rules = options.getForWorkspace(workspaceName, KEY_PAIR_RULES)
        if rules and isinstance(rules, dict):
            for key, partners in rules.items():
                if isinstance(partners, list):
                    self.pairRules[str(key)] = [str(p) for p in partners]

        # Arrange existing windows
        if workspace:
            self._arrangeExisting(workspace)
            self.floatingWindowIds = set(w.id for w in workspace.floating_nodes)

    # -------------------------------------------------------------------------
    # Window event handlers
    # -------------------------------------------------------------------------

    def windowAdded(self, event: WindowEvent, workspace: Con, window: Con) -> None:
        if self._isFloating(window):
            self.floatingWindowIds.add(window.id)
            return

        # Check for pending manual pair
        if self.pendingManualPair is not None:
            self._createPair(workspace, self.pendingManualPair, window.id)
            self.pendingManualPair = None
            return

        # Try auto-pairing
        partner = self._findAutoPartner(window)
        if partner is not None:
            self._createPair(workspace, partner, window.id)
        else:
            self.unpairedWindows.append(window.id)
            self._arrange(workspace)

    def windowRemoved(
        self, event: WindowEvent, workspace: Con | None, window: Con
    ) -> None:
        if self._isFloating(window):
            self.floatingWindowIds.discard(window.id)
            return

        # Check if the window is part of a pair
        pair = self._getPairForWindow(window.id)
        if pair is not None:
            self.pairs.remove(pair)
            # The remaining window becomes unpaired
            remaining = pair.primary if pair.secondary == window.id else pair.secondary
            self.unpairedWindows.append(remaining)
            self.log(
                f"Pair broken by removal: {window.id}, {remaining} is now unpaired"
            )
        elif window.id in self.unpairedWindows:
            self.unpairedWindows.remove(window.id)

        if self.pendingManualPair == window.id:
            self.pendingManualPair = None

        if workspace:
            self._arrange(workspace)

    def windowFocused(self, event: WindowEvent, workspace: Con, window: Con) -> None:
        if self._isFloating(window):
            return

        # Update focused pair index
        pair = self._getPairForWindow(window.id)
        if pair is not None:
            try:
                self.focusedPairIndex = self.pairs.index(pair)
            except ValueError:
                pass

    def windowMoved(self, event: WindowEvent, workspace: Con, window: Con) -> None:
        pass

    def windowFloating(self, event: WindowEvent, workspace: Con, window: Con) -> None:
        i3Floating = window.floating is not None and "on" in window.floating
        swayFloating = window.type == "floating_con"

        if swayFloating or i3Floating:
            # Remove from layout, add to floating set
            pair = self._getPairForWindow(window.id)
            if pair is not None:
                self.pairs.remove(pair)
                remaining = (
                    pair.primary if pair.secondary == window.id else pair.secondary
                )
                self.unpairedWindows.append(remaining)
            elif window.id in self.unpairedWindows:
                self.unpairedWindows.remove(window.id)
            self.floatingWindowIds.add(window.id)
        else:
            # Add back to layout
            self.floatingWindowIds.discard(window.id)
            self.unpairedWindows.append(window.id)
            self._arrange(workspace)

    # -------------------------------------------------------------------------
    # Command handling
    # -------------------------------------------------------------------------

    def onCommand(self, command: str, workspace: Con) -> None:
        focused = workspace.find_focused()

        dispatch = {
            "focus left": lambda: self._focusPair(-1),
            "focus right": lambda: self._focusPair(1),
            "focus up": lambda: self._focusWithinPair(focused, True),
            "focus down": lambda: self._focusWithinPair(focused, False),
            "move left": lambda: self._movePair(workspace, focused, -1),
            "move right": lambda: self._movePair(workspace, focused, 1),
            "pair": lambda: self._startManualPair(focused),
            "unpair": lambda: self._unpair(workspace, focused),
            "maximize": lambda: self._toggleMaximize(workspace),
        }

        handler = dispatch.get(command)
        if handler:
            handler()
        else:
            self.logError(f"Unknown command: '{command}'")

    # -------------------------------------------------------------------------
    # Pairing logic
    # -------------------------------------------------------------------------

    def _findAutoPartner(self, window: Con) -> int | None:
        """Find an unpaired window that matches the pair rules for this window."""
        windowClass = self._getWindowClass(window)
        if not windowClass:
            return None

        # Find matching rules
        matchingPartnerClasses: list[str] = []
        for ruleClass, partners in self.pairRules.items():
            if ruleClass.lower() in windowClass.lower():
                matchingPartnerClasses.extend(partners)

        if not matchingPartnerClasses:
            return None

        # Search unpaired windows for a match
        for unpairedId in self.unpairedWindows:
            # We need the window's app_id, but we only have the ID.
            # During arrange, we might have workspace context, but for now
            # we'll use marks or stored class info.
            # For simplicity, we'll check the tree.
            tree = self.con.get_tree()
            unpairedWindow = tree.find_by_id(unpairedId)
            if unpairedWindow:
                unpairedClass = self._getWindowClass(unpairedWindow)
                if unpairedClass and any(
                    p.lower() in unpairedClass.lower() for p in matchingPartnerClasses
                ):
                    return unpairedId

        return None

    def _createPair(self, workspace: Con, id1: int, id2: int) -> None:
        """Create a tabbed pair from two windows."""
        # Remove from unpaired if present
        if id1 in self.unpairedWindows:
            self.unpairedWindows.remove(id1)
        if id2 in self.unpairedWindows:
            self.unpairedWindows.remove(id2)

        pair = WindowPair(primary=id1, secondary=id2)
        self.pairs.append(pair)

        # Create tabbed container: move secondary to primary, set tabbed
        self.command(f"[con_id={id1}] split none")
        self.command(f"[con_id={id1}] layout tabbed")
        self.moveWindowCommand(id2, id1)

        self.log(f"Created pair: {id1} + {id2}")

    def _getPairForWindow(self, windowId: int) -> WindowPair | None:
        """Find the pair containing a given window ID."""
        for pair in self.pairs:
            if pair.primary == windowId or pair.secondary == windowId:
                return pair
        return None

    def _getWindowClass(self, window: Con) -> str | None:
        """Get the app_id or window_class for matching."""
        return window.app_id or window.window_class

    # -------------------------------------------------------------------------
    # Navigation
    # -------------------------------------------------------------------------

    def _focusPair(self, direction: int) -> None:
        """Focus the next/previous pair."""
        if not self.pairs:
            return

        self.focusedPairIndex = (self.focusedPairIndex + direction) % len(self.pairs)
        pair = self.pairs[self.focusedPairIndex]
        self.command(f"[con_id={pair.primary}] focus")

    def _focusWithinPair(self, window: Con | None, up: bool) -> None:
        """Switch focus between windows within a pair."""
        if window is None:
            return

        pair = self._getPairForWindow(window.id)
        if pair is None:
            return

        # Toggle between primary and secondary
        if window.id == pair.primary:
            target = pair.secondary
        else:
            target = pair.primary

        self.command(f"[con_id={target}] focus")

    def _movePair(self, workspace: Con, window: Con | None, direction: int) -> None:
        """Swap pair ordering."""
        if window is None or not self.pairs:
            return

        pair = self._getPairForWindow(window.id)
        if pair is None:
            return

        idx = self.pairs.index(pair)
        newIdx = (idx + direction) % len(self.pairs)
        if idx == newIdx:
            return

        self.pairs[idx], self.pairs[newIdx] = self.pairs[newIdx], self.pairs[idx]
        self.focusedPairIndex = newIdx
        self._arrange(workspace)

    # -------------------------------------------------------------------------
    # Manual pair/unpair
    # -------------------------------------------------------------------------

    def _startManualPair(self, window: Con | None) -> None:
        """Start manual pairing: the next created window will be paired with this one."""
        if window is None:
            return

        if self.pendingManualPair == window.id:
            # Cancel pending pair
            self.pendingManualPair = None
            self.log("Manual pair cancelled")
            return

        # Check if already paired
        if self._getPairForWindow(window.id) is not None:
            self.logError("Window is already paired. Unpair first.")
            return

        self.pendingManualPair = window.id
        self.log(f"Waiting for partner window to pair with {window.id}")

    def _unpair(self, workspace: Con, window: Con | None) -> None:
        """Break the pair containing the focused window."""
        if window is None:
            return

        pair = self._getPairForWindow(window.id)
        if pair is None:
            self.logError("Window is not paired")
            return

        self.pairs.remove(pair)
        self.unpairedWindows.append(pair.primary)
        self.unpairedWindows.append(pair.secondary)
        self.log(f"Unpaired: {pair.primary} and {pair.secondary}")
        self._arrange(workspace)

    # -------------------------------------------------------------------------
    # Layout
    # -------------------------------------------------------------------------

    def _arrange(self, workspace: Con) -> None:
        """Arrange all windows: pairs as tabbed containers, unpaired as splits."""
        allIds = []
        for pair in self.pairs:
            allIds.extend([pair.primary, pair.secondary])
        allIds.extend(self.unpairedWindows)

        if not allIds:
            return

        # Set up the horizontal split structure
        firstId = allIds[0]
        self.command(f"[con_id={firstId}] split none")
        self.command(f"[con_id={firstId}] splith")

        # Move all other windows next to first
        for wId in allIds[1:]:
            self.moveWindowCommand(wId, firstId)

        # Now group pairs into tabbed containers
        for pair in self.pairs:
            self.command(f"[con_id={pair.primary}] split none")
            self.command(f"[con_id={pair.primary}] layout tabbed")
            self.moveWindowCommand(pair.secondary, pair.primary)

    def _arrangeExisting(self, workspace: Con) -> None:
        """Arrange existing windows when layout is activated."""
        windows = [w for w in workspace.leaves() if not self._isFloating(w)]
        for w in windows:
            self.unpairedWindows.append(w.id)

        # Try to auto-pair existing windows
        paired: set[int] = set()
        for w in windows:
            if w.id in paired:
                continue
            windowClass = self._getWindowClass(w)
            if not windowClass:
                continue

            matchingPartnerClasses: list[str] = []
            for ruleClass, partners in self.pairRules.items():
                if ruleClass.lower() in windowClass.lower():
                    matchingPartnerClasses.extend(partners)

            if not matchingPartnerClasses:
                continue

            for other in windows:
                if other.id == w.id or other.id in paired:
                    continue
                otherClass = self._getWindowClass(other)
                if otherClass and any(
                    p.lower() in otherClass.lower() for p in matchingPartnerClasses
                ):
                    # Found a match
                    if w.id in self.unpairedWindows:
                        self.unpairedWindows.remove(w.id)
                    if other.id in self.unpairedWindows:
                        self.unpairedWindows.remove(other.id)
                    self.pairs.append(WindowPair(primary=w.id, secondary=other.id))
                    paired.add(w.id)
                    paired.add(other.id)
                    break

        if self.pairs or self.unpairedWindows:
            self._arrange(workspace)

    def _toggleMaximize(self, workspace: Con) -> None:
        """Toggle tabbed maximize across all windows."""
        allIds = []
        for pair in self.pairs:
            allIds.extend([pair.primary, pair.secondary])
        allIds.extend(self.unpairedWindows)
        if allIds:
            self.command(f"[con_id={allIds[0]}] layout tabbed")

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _isFloating(self, window: Con) -> bool:
        i3Floating = window.floating is not None and "on" in window.floating
        swayFloating = window.type == "floating_con"
        return swayFloating or i3Floating

    def moveWindowCommand(self, moveId: int, targetId: int) -> None:
        """Move a window to be adjacent to another using marks."""
        self.command(f"[con_id={targetId}] mark --add _layman_target")
        self.command(f"[con_id={moveId}] move to mark _layman_target")
        self.command("unmark _layman_target")
