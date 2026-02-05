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

import tomli

CONFIG_PATH = ".config/layman/config.toml"

TABLE_LAYMAN = "layman"
TABLE_WORKSPACE = "workspace"
KEY_DEBUG = "debug"
KEY_EXCLUDED_WORKSPACES = "excludeWorkspaces"
KEY_LAYOUT = "defaultLayout"
KEY_PIPE_PATH = "pipePath"


class ConfigError(Exception):
    """Raised when configuration is invalid."""
    pass


class LaymanConfig:
    def __init__(self, configPath: str | None):
        self.configDict = self.parse(configPath or CONFIG_PATH)

    def parse(self, configPath: str):
        with open(configPath, "rb") as f:
            try:
                return tomli.load(f)
            except Exception as e:
                raise ConfigError(
                    f"Failed to parse config file '{configPath}': {e}"
                ) from e

    def getDefault(self, key):
        try:
            return self.configDict[TABLE_LAYMAN][key]
        except KeyError:
            return None

    def getForWorkspace(self, workspaceName: str, key: str) -> str | int | float | None:
        # Try to get value for the workspace
        try:
            return self.configDict[TABLE_WORKSPACE][workspaceName][key]
        except KeyError:
            pass

        # Fallback to default
        try:
            return self.configDict[TABLE_LAYMAN][key]
        except KeyError:
            pass

        return None
