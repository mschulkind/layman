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

import logging
import os
import socket
from queue import SimpleQueue
from threading import Thread

logger = logging.getLogger(__name__)
DEFAULT_PIPE_PATH = "/tmp/layman.pipe"


class MessageServer:
    def __init__(self, queue: SimpleQueue, pipe_path: str | None = None):
        self.queue = queue
        self.pipe_path = pipe_path or DEFAULT_PIPE_PATH

        try:
            os.unlink(self.pipe_path)
        except FileNotFoundError:
            pass

        # We keep the .pipe extension for compatibility but use a Unix Domain Socket
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.bind(self.pipe_path)
        os.chmod(self.pipe_path, 0o600)
        self.sock.listen(5)

        thread = Thread(target=self.run, daemon=True)
        thread.start()

    def run(self):
        while True:
            try:
                conn, _ = self.sock.accept()
                with conn:
                    data = conn.recv(4096)
                    if not data:
                        continue
                    command = data.decode("utf-8").strip()
                    if command:
                        # We use a response queue to get the result back from the main thread
                        response_queue = SimpleQueue()
                        self.queue.put(
                            {
                                "type": "command",
                                "command": command,
                                "response_queue": response_queue,
                            }
                        )
                        # Wait for response with a timeout
                        try:
                            response = response_queue.get(timeout=10)
                            conn.sendall(response.encode("utf-8"))
                        except Exception:
                            conn.sendall(b"Error: Command timed out or failed.")
            except Exception as e:
                logger.error(f"Error in MessageServer: {e}")

    def readPipe(self):
        # Deprecated: kept for reference or until fully replaced
        pass
