"""
Window rules for layman.

Provides per-window behavior overrides based on app_id or window_class
matching. Rules can float windows, exclude them from layout management,
assign them to specific workspaces, or set properties.

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

import re
from dataclasses import dataclass
from typing import Any

from i3ipc import Con

from layman.log import get_logger

logger = get_logger(__name__)


@dataclass
class WindowRule:
    """A rule that matches windows and applies actions.

    Attributes:
        match_app_id: Regex pattern to match window app_id.
        match_window_class: Regex pattern to match window_class.
        exclude: If True, exclude matched windows from layout management.
        floating: If True, float matched windows.
        workspace: Move matched windows to this workspace.
        position: Preferred position in layout ("master", "stack").
    """

    match_app_id: str | None = None
    match_window_class: str | None = None
    exclude: bool = False
    floating: bool = False
    workspace: str | None = None
    position: str | None = None


class WindowRuleEngine:
    """Evaluates window rules against windows.

    Rules are loaded from the ``[rules]`` section of the layman config.

    Config format:
        [rules]
        [[rules.float]]
        match_app_id = "pavucontrol"
        floating = true

        [[rules.exclude]]
        match_app_id = "waybar"
        exclude = true

    Usage:
        engine = WindowRuleEngine(rules)
        actions = engine.evaluate(window)
        if actions.get("exclude"):
            # Skip this window
    """

    def __init__(self, rules: list[WindowRule] | None = None) -> None:
        self.rules: list[WindowRule] = rules or []

    @classmethod
    def from_config(cls, rules_config: list[dict[str, Any]]) -> WindowRuleEngine:
        """Create an engine from parsed config data.

        Args:
            rules_config: List of rule dicts from the config file.

        Returns:
            A configured WindowRuleEngine.
        """
        rules: list[WindowRule] = []
        for rule_data in rules_config:
            rule = WindowRule(
                match_app_id=rule_data.get("match_app_id"),
                match_window_class=rule_data.get("match_window_class"),
                exclude=rule_data.get("exclude", False),
                floating=rule_data.get("floating", False),
                workspace=rule_data.get("workspace"),
                position=rule_data.get("position"),
            )
            rules.append(rule)
        return cls(rules)

    def evaluate(self, window: Con) -> dict[str, Any]:
        """Evaluate all rules against a window.

        Returns a dict of actions to apply. Later rules override earlier ones.

        Args:
            window: The window to evaluate.

        Returns:
            Dict of action name → value for all matching rules.
        """
        actions: dict[str, Any] = {}

        for rule in self.rules:
            if self._matches(rule, window):
                if rule.exclude:
                    actions["exclude"] = True
                if rule.floating:
                    actions["floating"] = True
                if rule.workspace:
                    actions["workspace"] = rule.workspace
                if rule.position:
                    actions["position"] = rule.position

        return actions

    def _matches(self, rule: WindowRule, window: Con) -> bool:
        """Check if a rule matches a window."""
        if rule.match_app_id:
            app_id = getattr(window, "app_id", None) or ""
            if not re.search(rule.match_app_id, app_id, re.IGNORECASE):
                return False

        if rule.match_window_class:
            window_class = getattr(window, "window_class", None) or ""
            if not re.search(rule.match_window_class, window_class, re.IGNORECASE):
                return False

        # At least one match field must be specified
        if not rule.match_app_id and not rule.match_window_class:
            return False

        return True

    def add_rule(self, rule: WindowRule) -> None:
        """Add a rule dynamically."""
        self.rules.append(rule)

    def clear(self) -> None:
        """Remove all rules."""
        self.rules.clear()
