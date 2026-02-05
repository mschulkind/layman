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

from os import mkfifo, unlink
from queue import SimpleQueue
from threading import Thread

DEFAULT_PIPE_PATH = "/tmp/layman.pipe"


class MessageServer:
    def __init__(self, queue: SimpleQueue, pipe_path: str | None = None):
        self.queue = queue
        self.pipe_path = pipe_path or DEFAULT_PIPE_PATH

        try:
            unlink(self.pipe_path)
        except FileNotFoundError:
            pass

        mkfifo(self.pipe_path)
        thread = Thread(target=self.readPipe, daemon=True)
        thread.start()

    def readPipe(self):
        while True:
            with open(self.pipe_path) as fifo:
                command = fifo.read().strip()
                # Decision #6: Filter empty commands
                if command:
                    self.queue.put({"type": "command", "command": command})
