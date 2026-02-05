"""
Unit tests for layman.listener module.

These tests cover the ListenerThread class which handles i3ipc events.
The actual event handling is tested via mocks since it requires IPC.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from queue import SimpleQueue


class TestListenerThread:
    """Tests for ListenerThread class."""

    def test_init_createsQueue(self):
        """ListenerThread should accept a queue."""
        queue = SimpleQueue()

        with patch("layman.listener.Connection") as mock_conn_class:
            mock_conn = MagicMock()
            mock_conn_class.return_value = mock_conn

            from layman.listener import ListenerThread

            listener = ListenerThread(queue)

            assert listener.queue is queue

    def test_init_createsConnection(self):
        """ListenerThread should create a Connection."""
        queue = SimpleQueue()

        with patch("layman.listener.Connection") as mock_conn_class:
            mock_conn = MagicMock()
            mock_conn_class.return_value = mock_conn

            from layman.listener import ListenerThread

            listener = ListenerThread(queue)

            mock_conn_class.assert_called_once()
            assert listener.connection is mock_conn

    def test_init_subscribesToEvents(self):
        """ListenerThread should subscribe to multiple event types."""
        queue = SimpleQueue()

        with patch("layman.listener.Connection") as mock_conn_class:
            mock_conn = MagicMock()
            mock_conn_class.return_value = mock_conn

            from layman.listener import ListenerThread

            listener = ListenerThread(queue)

            # Should have called on() multiple times for different events
            assert mock_conn.on.call_count >= 5  # At least 5 event types

    def test_handleEvent_putsEventInQueue(self):
        """handleEvent should put events in the queue."""
        queue = SimpleQueue()
        mock_event = Mock()
        mock_event.change = "focus"

        with patch("layman.listener.Connection") as mock_conn_class:
            mock_conn = MagicMock()
            mock_conn_class.return_value = mock_conn

            from layman.listener import ListenerThread

            listener = ListenerThread(queue)
            listener.handleEvent(None, mock_event)

            assert not queue.empty()
            message = queue.get()
            assert message["type"] == "event"
            assert message["event"] is mock_event


class TestListenerThreadEventTypes:
    """Tests for event type subscriptions."""

    def test_subscribes_to_binding_event(self):
        """Should subscribe to BINDING events."""
        queue = SimpleQueue()

        with patch("layman.listener.Connection") as mock_conn_class:
            mock_conn = MagicMock()
            mock_conn_class.return_value = mock_conn

            from layman.listener import ListenerThread, Event

            listener = ListenerThread(queue)

            # Check that BINDING was subscribed
            event_types = [call[0][0] for call in mock_conn.on.call_args_list]
            assert Event.BINDING in event_types

    def test_subscribes_to_window_events(self):
        """Should subscribe to WINDOW events."""
        queue = SimpleQueue()

        with patch("layman.listener.Connection") as mock_conn_class:
            mock_conn = MagicMock()
            mock_conn_class.return_value = mock_conn

            from layman.listener import ListenerThread, Event

            listener = ListenerThread(queue)

            event_types = [call[0][0] for call in mock_conn.on.call_args_list]
            assert Event.WINDOW_FOCUS in event_types
            assert Event.WINDOW_NEW in event_types
            assert Event.WINDOW_CLOSE in event_types
            assert Event.WINDOW_MOVE in event_types
            assert Event.WINDOW_FLOATING in event_types

    def test_subscribes_to_workspace_init(self):
        """Should subscribe to WORKSPACE_INIT events."""
        queue = SimpleQueue()

        with patch("layman.listener.Connection") as mock_conn_class:
            mock_conn = MagicMock()
            mock_conn_class.return_value = mock_conn

            from layman.listener import ListenerThread, Event

            listener = ListenerThread(queue)

            event_types = [call[0][0] for call in mock_conn.on.call_args_list]
            assert Event.WORKSPACE_INIT in event_types
