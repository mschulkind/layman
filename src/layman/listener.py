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

from queue import SimpleQueue
from threading import Thread

from i3ipc import Connection, Event
from i3ipc.events import IpcBaseEvent


class ListenerThread:
    def handleEvent(self, _, event: IpcBaseEvent):
        self.queue.put({"type": "event", "event": event})

    def run(self):
        self.connection.main()

    def __init__(self, queue: SimpleQueue):
        self.queue = queue
        self.connection = Connection()

        for event in [
            Event.BINDING,
            Event.WINDOW_FOCUS,
            Event.WINDOW_NEW,
            Event.WINDOW_CLOSE,
            Event.WINDOW_MOVE,
            Event.WINDOW_FLOATING,
            Event.WORKSPACE_INIT,
        ]:
            self.connection.on(event, self.handleEvent)

        thread = Thread(target=self.run, daemon=True)
        thread.start()
