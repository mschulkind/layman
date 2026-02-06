"""
Focus history tracking for layman.

Maintains an ordered history of focused window IDs per workspace,
enabling "focus previous" and other history-based navigation.

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

from collections import deque

from layman.log import get_logger

logger = get_logger(__name__)


class FocusHistory:
    """Tracks window focus history for a workspace.

    Maintains a bounded deque of recently focused window IDs. The most
    recently focused window is at index 0.

    Usage:
        history = FocusHistory(max_size=20)
        history.push(window_id)
        prev = history.previous()  # Go back in history
        history.remove(window_id)  # When window is closed
    """

    def __init__(self, max_size: int = 20) -> None:
        self.max_size = max_size
        self._history: deque[int] = deque(maxlen=max_size)
        self._current_index: int = 0

    def push(self, window_id: int) -> None:
        """Record a new focus event. Deduplicates consecutive focuses."""
        if self._history and self._history[0] == window_id:
            return  # Already the most recent
        # Remove if already in history (moves to front)
        if window_id in self._history:
            self._history.remove(window_id)
        self._history.appendleft(window_id)
        self._current_index = 0

    def previous(self) -> int | None:
        """Get the previously focused window ID.

        Each call moves further back in history. Returns None if at the end.
        """
        target = self._current_index + 1
        if target >= len(self._history):
            return None
        self._current_index = target
        return self._history[target]

    def current(self) -> int | None:
        """Get the currently tracked focused window ID."""
        if not self._history:
            return None
        return self._history[self._current_index]

    def remove(self, window_id: int) -> None:
        """Remove a window from history (e.g., when closed)."""
        if window_id in self._history:
            self._history.remove(window_id)
            if self._current_index >= len(self._history):
                self._current_index = max(0, len(self._history) - 1)

    def reset_navigation(self) -> None:
        """Reset the navigation index to the most recent entry."""
        self._current_index = 0

    def clear(self) -> None:
        """Clear all history."""
        self._history.clear()
        self._current_index = 0

    def __len__(self) -> int:
        return len(self._history)

    def __contains__(self, window_id: int) -> bool:
        return window_id in self._history

    @property
    def entries(self) -> list[int]:
        """Return history as a list (most recent first)."""
        return list(self._history)
