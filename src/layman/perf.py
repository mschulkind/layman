"""
Performance utilities for layman.

Provides command batching, tree caching, and event debouncing to minimize
IPC calls and reduce redundant layout recalculations.

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

import time
from contextlib import contextmanager

from i3ipc import Connection

from layman.log import get_logger

logger = get_logger(__name__)


# =============================================================================
# Command Batching (Task 22)
# =============================================================================


class CommandBatcher:
    """Collects Sway/i3 commands and sends them as a single semicolon-joined IPC call.

    Usage:
        batcher = CommandBatcher(connection)
        with batcher.batch():
            batcher.command("[con_id=1] move left")
            batcher.command("[con_id=2] focus")
        # Sends: "[con_id=1] move left; [con_id=2] focus" as one IPC call

    When not in a batch context, commands are sent immediately.
    """

    def __init__(self, con: Connection) -> None:
        self.con = con
        self._batching = False
        self._commands: list[str] = []

    @contextmanager
    def batch(self):
        """Context manager to batch commands into a single IPC call."""
        self._batching = True
        self._commands.clear()
        try:
            yield self
        finally:
            self._flush()
            self._batching = False

    def command(self, cmd: str) -> None:
        """Queue a command (if batching) or send immediately."""
        if self._batching:
            self._commands.append(cmd)
            logger.debug("Queued command: %s", cmd)
        else:
            logger.debug("Running command: %s", cmd)
            results = self.con.command(cmd)
            for result in results:
                if hasattr(result, "success") and not result.success:
                    logger.error(
                        "Command failed: %s", getattr(result, "error", "unknown")
                    )

    def _flush(self) -> None:
        """Send all batched commands as a single IPC call."""
        if not self._commands:
            return

        combined = "; ".join(self._commands)
        count = len(self._commands)
        self._commands.clear()

        logger.debug("Flushing %d batched commands: %s", count, combined)
        results = self.con.command(combined)
        for result in results:
            if hasattr(result, "success") and not result.success:
                logger.error(
                    "Batched command failed: %s", getattr(result, "error", "unknown")
                )


# =============================================================================
# Tree Cache (Task 23)
# =============================================================================


class TreeCache:
    """Caches window_id → workspace_name mappings to avoid repeated get_tree() calls.

    The cache is invalidated when:
    - A window is created, closed, or moved (changes the mapping)
    - The cache age exceeds max_age_seconds
    - invalidate() is called explicitly

    Usage:
        cache = TreeCache(connection)
        ws_name = cache.get_workspace_for_window(window_id)
        cache.invalidate()  # After events that change the tree
    """

    def __init__(self, con: Connection, max_age_seconds: float = 1.0) -> None:
        self.con = con
        self.max_age_seconds = max_age_seconds
        self._cache: dict[int, str] = {}
        self._last_refresh: float = 0.0

    def get_workspace_for_window(self, window_id: int) -> str | None:
        """Look up which workspace a window is on, using cache if fresh."""
        if self._is_stale():
            self._refresh()

        return self._cache.get(window_id)

    def invalidate(self) -> None:
        """Mark the cache as stale. Next lookup will refresh."""
        self._cache.clear()
        self._last_refresh = 0.0
        logger.debug("Tree cache invalidated")

    def _is_stale(self) -> bool:
        if not self._cache:
            return True
        return (time.monotonic() - self._last_refresh) > self.max_age_seconds

    def _refresh(self) -> None:
        """Rebuild the cache from the current tree."""
        self._cache.clear()
        try:
            tree = self.con.get_tree()
            for workspace in tree.workspaces():
                for leaf in workspace.leaves():
                    self._cache[leaf.id] = workspace.name
                for floating in workspace.floating_nodes:
                    self._cache[floating.id] = workspace.name
        except Exception:
            logger.warning("Failed to refresh tree cache", exc_info=True)
            return

        self._last_refresh = time.monotonic()
        logger.debug("Tree cache refreshed: %d entries", len(self._cache))


# =============================================================================
# Event Debouncing (Task 24)
# =============================================================================


class EventDebouncer:
    """Deduplicates rapid events within a time window.

    When multiple events arrive for the same key within the debounce window,
    only the last one is processed. This avoids redundant layout recalculations
    during bursts (e.g., closing multiple windows in quick succession).

    Usage:
        debouncer = EventDebouncer(window_ms=10)

        # Returns True if this event should be processed
        if debouncer.should_process("window_close_100"):
            handle_event()
    """

    def __init__(self, window_ms: float = 10.0) -> None:
        self.window_seconds = window_ms / 1000.0
        self._last_seen: dict[str, float] = {}

    def should_process(self, key: str) -> bool:
        """Check if an event with this key should be processed.

        Returns True if enough time has passed since the last event with the
        same key, or if this is the first event with this key.
        """
        now = time.monotonic()
        last = self._last_seen.get(key)

        if last is not None and (now - last) < self.window_seconds:
            logger.debug("Debounced event: %s (%.1fms ago)", key, (now - last) * 1000)
            return False

        self._last_seen[key] = now
        return True

    def clear(self) -> None:
        """Clear all debounce state."""
        self._last_seen.clear()

    def cleanup(self, max_age_seconds: float = 60.0) -> None:
        """Remove entries older than max_age_seconds to prevent memory leaks."""
        now = time.monotonic()
        stale_keys = [
            k for k, v in self._last_seen.items() if (now - v) > max_age_seconds
        ]
        for k in stale_keys:
            del self._last_seen[k]
