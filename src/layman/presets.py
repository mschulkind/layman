"""
Layout presets for layman.

Allows users to save and load named workspace layout configurations,
including layout type and settings, for quick switching.

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
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from layman.log import get_logger

logger = get_logger(__name__)


@dataclass
class LayoutPreset:
    """A saved layout preset."""

    name: str
    layout_name: str
    options: dict[str, Any] = field(default_factory=dict)


class PresetManager:
    """Manages layout presets (save, load, list, delete).

    Presets are stored as JSON files in a presets directory alongside
    the layman config.

    Usage:
        presets = PresetManager()
        presets.save("coding", "MasterStack", {"masterWidth": 60})
        preset = presets.load("coding")
        names = presets.list_presets()
        presets.delete("coding")
    """

    def __init__(self, presets_dir: str | None = None) -> None:
        self.presets_dir = Path(
            presets_dir or os.path.expanduser("~/.config/layman/presets")
        )
        self.presets_dir.mkdir(parents=True, exist_ok=True)

    def save(
        self, name: str, layout_name: str, options: dict[str, Any] | None = None
    ) -> str:
        """Save a layout preset.

        Args:
            name: Preset name.
            layout_name: The layout manager short name.
            options: Layout-specific options to save.

        Returns:
            Path to the saved preset file.
        """
        preset = LayoutPreset(
            name=name,
            layout_name=layout_name,
            options=options or {},
        )
        filepath = self._preset_path(name)
        filepath.write_text(json.dumps(asdict(preset), indent=2))
        logger.info("Preset saved: %s (layout: %s)", name, layout_name)
        return str(filepath)

    def load(self, name: str) -> LayoutPreset | None:
        """Load a layout preset by name.

        Returns:
            The preset, or None if not found.
        """
        filepath = self._preset_path(name)
        if not filepath.exists():
            logger.warning("Preset not found: %s", name)
            return None

        data = json.loads(filepath.read_text())
        return LayoutPreset(
            name=data.get("name", name),
            layout_name=data.get("layout_name", "none"),
            options=data.get("options", {}),
        )

    def list_presets(self) -> list[str]:
        """List all saved preset names."""
        return sorted(f.stem for f in self.presets_dir.glob("*.json"))

    def delete(self, name: str) -> bool:
        """Delete a preset. Returns True if deleted."""
        filepath = self._preset_path(name)
        if filepath.exists():
            filepath.unlink()
            logger.info("Preset deleted: %s", name)
            return True
        return False

    def _preset_path(self, name: str) -> Path:
        safe_name = "".join(c for c in name if c.isalnum() or c in "-_.")
        return self.presets_dir / f"{safe_name}.json"
