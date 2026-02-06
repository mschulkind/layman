"""
Layout manager factory for layman.

Centralizes the creation of layout managers, replacing scattered
if-elif chains with a clean registry pattern.

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

from i3ipc import Con, Connection

from layman.config import LaymanConfig
from layman.log import get_logger
from layman.managers.workspace import WorkspaceLayoutManager

logger = get_logger(__name__)


class LayoutManagerFactory:
    """Factory for creating layout manager instances.

    Maintains a registry of layout short names → layout manager classes.
    Supports both builtin and user-provided layouts.

    Usage:
        factory = LayoutManagerFactory()
        factory.register(MasterStackLayoutManager)
        factory.register_user_layouts(user_layouts_dict)

        manager = factory.create("MasterStack", connection, workspace, "1", config)
        names = factory.available_layouts()
    """

    def __init__(self) -> None:
        self._registry: dict[str, type[WorkspaceLayoutManager]] = {}

    def register(self, layout_class: type[WorkspaceLayoutManager]) -> None:
        """Register a layout manager class by its shortName."""
        name = layout_class.shortName
        self._registry[name] = layout_class
        logger.debug("Registered layout: %s", name)

    def register_many(self, classes: list[type[WorkspaceLayoutManager]]) -> None:
        """Register multiple layout manager classes."""
        for cls in classes:
            self.register(cls)

    def register_user_layouts(
        self, user_layouts: dict[str, type[WorkspaceLayoutManager]]
    ) -> None:
        """Register user-provided layouts (overrides builtins on conflict)."""
        for name, cls in user_layouts.items():
            self._registry[name] = cls
            logger.debug("Registered user layout: %s", name)

    def create(
        self,
        name: str,
        con: Connection,
        workspace: Con | None,
        workspace_name: str,
        options: LaymanConfig,
    ) -> WorkspaceLayoutManager | None:
        """Create a layout manager instance by short name.

        Returns None if the layout name is not registered.
        """
        layout_class = self._registry.get(name)
        if layout_class is None:
            logger.error("Unknown layout: '%s'", name)
            return None

        return layout_class(con, workspace, workspace_name, options)

    def available_layouts(self) -> list[str]:
        """Return a sorted list of all registered layout names."""
        return sorted(self._registry.keys())

    def is_registered(self, name: str) -> bool:
        """Check if a layout name is registered."""
        return name in self._registry

    def get_class(self, name: str) -> type[WorkspaceLayoutManager] | None:
        """Get the class for a layout name without instantiating."""
        return self._registry.get(name)
