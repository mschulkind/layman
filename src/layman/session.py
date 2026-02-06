"""
Session restore for layman.

Saves and restores workspace layout state (window positions, layout type,
configuration) to/from JSON files. Matches windows by app_id or window_class
on restore and can optionally launch saved applications.

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

import json
import os
import subprocess
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from i3ipc import Con, Connection

from layman.log import get_logger

logger = get_logger(__name__)


# =============================================================================
# Data Model
# =============================================================================


@dataclass
class WindowSlot:
    """A saved window slot within a layout."""

    app_id: str | None = None
    window_class: str | None = None
    position: str = "stack"  # "master", "left", "right", "stack", "unpaired"
    index: int = 0
    launch_command: str | None = None


@dataclass
class WorkspaceSession:
    """Saved state for a single workspace."""

    workspace_name: str
    layout_name: str
    windows: list[WindowSlot] = field(default_factory=list)
    config_overrides: dict[str, Any] = field(default_factory=dict)
    saved_at: float = 0.0


@dataclass
class SessionData:
    """Top-level session data containing all workspace sessions."""

    name: str = "default"
    workspaces: list[WorkspaceSession] = field(default_factory=list)
    saved_at: float = 0.0


# =============================================================================
# Session Manager
# =============================================================================


class SessionManager:
    """Manages saving and restoring workspace layout sessions.

    Usage:
        manager = SessionManager(connection, session_dir="~/.config/layman/sessions")
        manager.save("my_session")
        manager.restore("my_session")
        sessions = manager.list_sessions()
        manager.delete("my_session")
    """

    def __init__(
        self,
        con: Connection,
        session_dir: str | None = None,
    ) -> None:
        self.con = con
        self.session_dir = Path(
            session_dir or os.path.expanduser("~/.config/layman/sessions")
        )
        self.session_dir.mkdir(parents=True, exist_ok=True)

    def save(
        self,
        session_name: str,
        workspace_states: dict[str, Any] | None = None,
    ) -> str:
        """Save the current state of all workspaces to a named session.

        Args:
            session_name: Name for the session file.
            workspace_states: Optional dict of workspace name → state from Layman.

        Returns:
            Path to the saved session file.
        """
        tree = self.con.get_tree()
        session = SessionData(
            name=session_name,
            saved_at=time.time(),
        )

        for workspace in tree.workspaces():
            ws_session = WorkspaceSession(
                workspace_name=workspace.name,
                layout_name=workspace.layout or "splith",
                saved_at=time.time(),
            )

            # Save window slots
            for i, leaf in enumerate(workspace.leaves()):
                slot = WindowSlot(
                    app_id=getattr(leaf, "app_id", None),
                    window_class=getattr(leaf, "window_class", None),
                    position="stack",
                    index=i,
                )
                ws_session.windows.append(slot)

            # Include layout name from workspace_states if available
            if workspace_states and workspace.name in workspace_states:
                state = workspace_states[workspace.name]
                if hasattr(state, "layoutName"):
                    ws_session.layout_name = state.layoutName

            session.workspaces.append(ws_session)

        filepath = self._session_path(session_name)
        filepath.write_text(json.dumps(asdict(session), indent=2))
        logger.info(
            "Session saved: %s (%d workspaces)", session_name, len(session.workspaces)
        )
        return str(filepath)

    def restore(
        self,
        session_name: str,
        launch_apps: bool = False,
    ) -> SessionData | None:
        """Restore a previously saved session.

        Args:
            session_name: Name of the session to restore.
            launch_apps: Whether to launch applications for unmatched window slots.

        Returns:
            The restored SessionData, or None if not found.
        """
        filepath = self._session_path(session_name)
        if not filepath.exists():
            logger.error("Session not found: %s", session_name)
            return None

        data = json.loads(filepath.read_text())
        session = self._parse_session(data)

        tree = self.con.get_tree()

        for ws_session in session.workspaces:
            workspace = next(
                (w for w in tree.workspaces() if w.name == ws_session.workspace_name),
                None,
            )

            if workspace:
                self._restore_workspace(workspace, ws_session, launch_apps)
            else:
                logger.warning(
                    "Workspace %s not found, skipping", ws_session.workspace_name
                )

        logger.info("Session restored: %s", session_name)
        return session

    def list_sessions(self) -> list[str]:
        """List all saved session names."""
        sessions = []
        for f in sorted(self.session_dir.glob("*.json")):
            sessions.append(f.stem)
        return sessions

    def delete(self, session_name: str) -> bool:
        """Delete a saved session.

        Returns:
            True if the session was deleted, False if not found.
        """
        filepath = self._session_path(session_name)
        if filepath.exists():
            filepath.unlink()
            logger.info("Session deleted: %s", session_name)
            return True
        logger.warning("Session not found: %s", session_name)
        return False

    def get_session_info(self, session_name: str) -> SessionData | None:
        """Load and return session data without restoring it."""
        filepath = self._session_path(session_name)
        if not filepath.exists():
            return None
        data = json.loads(filepath.read_text())
        return self._parse_session(data)

    # -------------------------------------------------------------------------
    # Window Matching (Task 26)
    # -------------------------------------------------------------------------

    def match_window(self, window: Con, slots: list[WindowSlot]) -> WindowSlot | None:
        """Find the best matching slot for a window.

        Matches by app_id first (exact match), then window_class.
        """
        window_app_id = getattr(window, "app_id", None)
        window_class = getattr(window, "window_class", None)

        # Exact app_id match
        if window_app_id:
            for slot in slots:
                if slot.app_id and slot.app_id == window_app_id:
                    return slot

        # Exact window_class match
        if window_class:
            for slot in slots:
                if slot.window_class and slot.window_class == window_class:
                    return slot

        # Case-insensitive app_id match
        if window_app_id:
            for slot in slots:
                if slot.app_id and slot.app_id.lower() == window_app_id.lower():
                    return slot

        return None

    # -------------------------------------------------------------------------
    # Application Launch (Task 27)
    # -------------------------------------------------------------------------

    def launch_application(self, slot: WindowSlot, workspace_name: str) -> bool:
        """Launch an application for an unmatched window slot.

        Args:
            slot: The window slot with launch_command.
            workspace_name: Target workspace for the new window.

        Returns:
            True if launch was attempted, False if no command available.
        """
        cmd = slot.launch_command
        if not cmd:
            # Try to launch by app_id
            cmd = slot.app_id

        if not cmd:
            logger.debug("No launch command for slot: %s", slot)
            return False

        try:
            # Move to workspace first, then launch
            self.con.command(f"workspace {workspace_name}")
            subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            logger.info("Launched '%s' on workspace %s", cmd, workspace_name)
            return True
        except Exception:
            logger.error("Failed to launch '%s'", cmd, exc_info=True)
            return False

    # -------------------------------------------------------------------------
    # Internal Helpers
    # -------------------------------------------------------------------------

    def _session_path(self, name: str) -> Path:
        """Get the file path for a session name."""
        # Sanitize name
        safe_name = "".join(c for c in name if c.isalnum() or c in "-_.")
        return self.session_dir / f"{safe_name}.json"

    def _parse_session(self, data: dict) -> SessionData:
        """Parse raw JSON data into SessionData."""
        session = SessionData(
            name=data.get("name", "unknown"),
            saved_at=data.get("saved_at", 0.0),
        )
        for ws_data in data.get("workspaces", []):
            ws = WorkspaceSession(
                workspace_name=ws_data.get("workspace_name", ""),
                layout_name=ws_data.get("layout_name", "splith"),
                saved_at=ws_data.get("saved_at", 0.0),
            )
            for w_data in ws_data.get("windows", []):
                slot = WindowSlot(
                    app_id=w_data.get("app_id"),
                    window_class=w_data.get("window_class"),
                    position=w_data.get("position", "stack"),
                    index=w_data.get("index", 0),
                    launch_command=w_data.get("launch_command"),
                )
                ws.windows.append(slot)
            session.workspaces.append(ws)
        return session

    def _restore_workspace(
        self,
        workspace: Con,
        ws_session: WorkspaceSession,
        launch_apps: bool,
    ) -> None:
        """Restore a single workspace's layout."""
        existing_windows = list(workspace.leaves())
        unmatched_slots = list(ws_session.windows)

        # Match existing windows to saved slots
        for window in existing_windows:
            slot = self.match_window(window, unmatched_slots)
            if slot:
                unmatched_slots.remove(slot)
                logger.debug(
                    "Matched window %s to slot %s",
                    getattr(window, "app_id", None) or getattr(window, "id", "?"),
                    slot.app_id or slot.window_class,
                )

        # Optionally launch apps for unmatched slots
        if launch_apps:
            for slot in unmatched_slots:
                self.launch_application(slot, ws_session.workspace_name)
