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
from logging import exception
from typing import Optional

import i3ipc
import tomli

CONFIG_PATH = ".config/layman/config.toml"

TABLE_LAYMAN = "layman"
TABLE_WORKSPACE = "workspace"
TABLE_OUTPUT = "output"
KEY_DEBUG = "debug"
KEY_EXCLUDED_WORKSPACES = "excludeWorkspaces"
KEY_EXCLUDED_OUTPUTS = "excludeOutputs"
KEY_LAYOUT = "defaultLayout"


class LaymanConfig:
    def __init__(self, configPath: Optional[str]):
        self.configDict = self.parse(configPath or CONFIG_PATH)

    def parse(self, configPath: str):
        with open(configPath, "rb") as f:
            try:
                return tomli.load(f)
            except Exception as e:
                exception(e)
                return {}

    def getDefault(self, key):
        try:
            return self.configDict[TABLE_LAYMAN][key]
        except KeyError:
            return None

    def getForWorkspace(self, workspace: i3ipc.Con, key: str):
        # Try to get value for the workspace
        try:
            return self.configDict[TABLE_WORKSPACE][workspace.name][key]
        except KeyError:
            pass

        # TODO(mschulkind): Remove? Disabled because I'm not sure it makes sense.
        # If workspace config doesn't have the key, try output
        #  output = workspace.ipc_data["output"]
        #  if output:
        #  try:
        #  return self.configDict[TABLE_OUTPUT][output][key]
        #  except KeyError:
        #  pass

        # If output config doesn't have the key, fallback to default
        try:
            return self.configDict[TABLE_LAYMAN][key]
        except KeyError:
            pass

        return None
