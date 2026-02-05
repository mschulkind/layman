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

import json
import os
import sys

from . import layman, utils, config
from .server import DEFAULT_PIPE_PATH

# Decision #16: Help text
HELP_TEXT = """Layman - Sway/i3 Layout Manager

Usage: layman [command]

Commands:
  layout <name>      Set layout (MasterStack, Autotiling, Grid, none)
  move <dir>         Move focused window (up, down, left, right, to master)
  focus <dir>        Focus window (up, down, master)
  stack toggle       Cycle stack layout
  stackside toggle   Swap stack side
  maximize           Toggle fake fullscreen
  rotate <dir>       Rotate windows (cw, ccw)
  swap master        Swap focused window with master
  reload             Reload configuration
  status             Show current state
  status --json      Show current state as JSON (for waybar/scripts)
  help               Show this message

Without arguments, layman starts the daemon.

Configuration:
  Config file: ~/.config/layman/config.toml
  Named pipe:  /tmp/layman.pipe (configurable via pipePath)

For more information, see: https://github.com/frap129/layman
"""


def get_pipe_path() -> str:
    """Get pipe path from config or use default."""
    try:
        config_path = utils.getConfigPath()
        if os.path.exists(config_path):
            options = config.LaymanConfig(config_path)
            custom_path = options.getDefault(config.KEY_PIPE_PATH)
            if custom_path:
                return str(custom_path)
    except Exception:
        pass
    return DEFAULT_PIPE_PATH


def send_command(command: str, pipe_path: str) -> bool:
    """Send a command to the daemon via named pipe."""
    try:
        with open(pipe_path, "w") as pipe:
            pipe.write(command)
        return True
    except FileNotFoundError:
        # Decision #18: Better error message
        print(f"Error: Layman daemon is not running.", file=sys.stderr)
        print(f"Start the daemon with: layman", file=sys.stderr)
        return False
    except PermissionError:
        print(f"Error: Permission denied accessing {pipe_path}", file=sys.stderr)
        return False


def main():
    """Application entry point."""

    # Handle command-line arguments
    if len(sys.argv) > 1:
        command = " ".join(sys.argv[1:])

        # Decision #16: Handle help command
        if command in ("help", "--help", "-h"):
            print(HELP_TEXT)
            return

        # Decision #15: Handle status command
        if command == "status" or command == "status --json":
            # TODO: Implement proper status query via pipe
            # For now, just pass to daemon
            pass

        pipe_path = get_pipe_path()
        if send_command(command, pipe_path):
            # Decision #14: Show feedback for commands
            if command.startswith("layout "):
                layout_name = command.split(" ", 1)[1]
                print(f"Layout set to {layout_name}")
            elif command == "maximize":
                print("Maximize toggled")
            elif command == "reload":
                print("Configuration reloaded")
            elif command.startswith("move "):
                direction = command.split(" ", 1)[1]
                print(f"Window moved {direction}")
        return

    # Start layman daemon
    daemon = layman.Layman()
    daemon.run()


if __name__ == "__main__":
    main()
