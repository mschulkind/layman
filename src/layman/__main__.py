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

import os
import shutil
import subprocess
import sys
from pathlib import Path

from . import config, layman, utils
from .server import DEFAULT_PIPE_PATH

DEFAULT_CONFIG_PATH = Path("~/.config/layman/config.toml").expanduser()

# Decision #16: Help text
HELP_TEXT = """Layman - Sway/i3 Layout Manager

Usage: layman [command]

Window Commands:
  window move <dir>          Move focused window (up, down, left, right)
  window move to master      Move focused window to master position
  window move to index <n>   Move focused window to position <n>
  window focus <dir>         Focus window (up, down, master)
  window swap master         Swap focused window with master
  window rotate <dir>        Rotate windows (cw, ccw)

Stack Commands:
  stack toggle               Cycle stack layout
  stack side toggle           Swap stack side

Layout Commands:
  layout set <name>          Set layout (MasterStack, Autotiling, Grid, none)
  layout maximize            Toggle fake fullscreen

General Commands:
  reload                     Reload configuration
  status                     Show current state
  status --json              Show current state as JSON (for waybar/scripts)
  help                       Show this message

Service Commands:
  install-service            Install layman as a systemd user service
  init-config                Create example config at ~/.config/layman/config.toml

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
        print("Error: Layman daemon is not running.", file=sys.stderr)
        print("Start the daemon with: layman", file=sys.stderr)
        return False
    except PermissionError:
        print(f"Error: Permission denied accessing {pipe_path}", file=sys.stderr)
        return False


def create_example_config(path: Path | None = None) -> Path:
    """Create an example configuration file."""
    path = path or DEFAULT_CONFIG_PATH
    path = Path(path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    example_content = """\
# Layman Configuration
#
# See https://github.com/frap129/layman/tree/master/docs for full documentation.

[layman]
defaultLayout = "none"        # Default layout: none, MasterStack, Autotiling, Grid
# excludedWorkspaces = []     # Workspace numbers to ignore
# debug = false               # Enable debug logging
# pipePath = "/tmp/layman.pipe"

# MasterStack options
# stackLayout = "splitv"      # splitv, splith, stacking, tabbed
# stackSide = "right"         # left, right
# masterWidth = 50            # Master width percentage (1-99)
# visibleStackLimit = 3       # Max visible stack windows (0 = unlimited)

# Autotiling options
# depthLimit = 0              # 0 = unlimited

# Per-workspace overrides
# [workspace.1]
# defaultLayout = "MasterStack"
# masterWidth = 70
# stackSide = "left"
"""
    with open(path, "w") as f:
        f.write(example_content)
    return path


def install_service() -> None:
    """Install layman as a systemd user service."""
    service_dir = Path("~/.config/systemd/user").expanduser()
    service_dir.mkdir(parents=True, exist_ok=True)
    service_file = service_dir / "layman.service"

    # Find the layman executable
    layman_path = shutil.which("layman")
    if not layman_path:
        try:
            result = subprocess.run(
                ["uv", "tool", "run", "--from", "layman", "which", "layman"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                layman_path = result.stdout.strip()
        except FileNotFoundError:
            pass

    if not layman_path:
        print("Could not find layman executable.", file=sys.stderr)
        print("Install it first with: uv tool install layman", file=sys.stderr)
        sys.exit(1)

    service_content = f"""\
[Unit]
Description=Layman - Sway/i3 Layout Manager
After=graphical-session.target
PartOf=graphical-session.target

[Service]
Type=simple
ExecStart={layman_path}
Restart=on-failure
RestartSec=3

[Install]
WantedBy=graphical-session.target
"""

    with open(service_file, "w") as f:
        f.write(service_content)

    print(f"Created systemd service: {service_file}")
    print()
    print("To enable and start the service:")
    print("  systemctl --user daemon-reload")
    print("  systemctl --user enable layman")
    print("  systemctl --user start layman")
    print()
    print("Then remove 'exec layman' from your sway config and reload sway.")
    print()
    print("To check status:")
    print("  systemctl --user status layman")
    print("  journalctl --user -u layman -f")


def init_config(force: bool = False) -> None:
    """Create an example configuration file."""
    if DEFAULT_CONFIG_PATH.exists() and not force:
        print(f"Config file already exists: {DEFAULT_CONFIG_PATH}", file=sys.stderr)
        print("Use 'layman init-config --force' to overwrite", file=sys.stderr)
        sys.exit(1)

    created_path = create_example_config()
    print(f"Created example config: {created_path}")
    print()
    print("Edit this file to configure your layouts, then restart layman.")


def main():
    """Application entry point."""

    # Handle command-line arguments
    if len(sys.argv) > 1:
        command = " ".join(sys.argv[1:])

        # Decision #16: Handle help command
        if command in ("help", "--help", "-h"):
            print(HELP_TEXT)
            return

        # Handle service management commands
        if command == "install-service":
            install_service()
            return

        if command == "init-config" or command == "init-config --force":
            init_config(force="--force" in command)
            return

        # Decision #15: Handle status command
        if command == "status" or command == "status --json":
            # TODO: Implement proper status query via pipe
            # For now, just pass to daemon
            pass

        pipe_path = get_pipe_path()
        if send_command(command, pipe_path):
            # Decision #14: Show feedback for commands
            if command.startswith("layout set "):
                layout_name = command.split(" ", 2)[2]
                print(f"Layout set to {layout_name}")
            elif command == "layout maximize":
                print("Maximize toggled")
            elif command == "reload":
                print("Configuration reloaded")
            elif command.startswith("window move "):
                direction = command.split(" ", 2)[2]
                print(f"Window moved {direction}")
            elif command.startswith("stack "):
                action = command[len("stack ") :]
                print(f"Stack {action}")
        return

    # Start layman daemon
    daemon = layman.Layman()
    daemon.run()


if __name__ == "__main__":
    main()
