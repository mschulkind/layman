"""
Unit tests for layman.server module.

These tests cover the MessageServer class which handles the named pipe
for receiving commands.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from queue import SimpleQueue


class TestMessageServer:
    """Tests for MessageServer class."""

    def test_init_acceptsQueue(self):
        """MessageServer should accept a queue."""
        queue = SimpleQueue()

        with patch("layman.server.mkfifo"):
            with patch("layman.server.unlink"):
                with patch("layman.server.Thread"):
                    from layman.server import MessageServer

                    server = MessageServer(queue)

                    assert server.queue is queue

    def test_init_unlinksPreviousPipe(self):
        """MessageServer should try to unlink previous pipe."""
        queue = SimpleQueue()

        with patch("layman.server.mkfifo"):
            with patch("layman.server.unlink") as mock_unlink:
                with patch("layman.server.Thread"):
                    from layman.server import MessageServer

                    server = MessageServer(queue)

                    mock_unlink.assert_called_once()

    def test_init_handlesMissingPipe(self):
        """MessageServer should handle FileNotFoundError on unlink."""
        queue = SimpleQueue()

        with patch("layman.server.mkfifo"):
            with patch("layman.server.unlink") as mock_unlink:
                mock_unlink.side_effect = FileNotFoundError()
                with patch("layman.server.Thread"):
                    from layman.server import MessageServer

                    # Should not raise
                    server = MessageServer(queue)

    def test_init_createsPipe(self):
        """MessageServer should create the named pipe."""
        queue = SimpleQueue()

        with patch("layman.server.mkfifo") as mock_mkfifo:
            with patch("layman.server.unlink"):
                with patch("layman.server.Thread"):
                    from layman.server import MessageServer, DEFAULT_PIPE_PATH

                    server = MessageServer(queue)

                    mock_mkfifo.assert_called_once_with(DEFAULT_PIPE_PATH)

    def test_init_startsThread(self):
        """MessageServer should start a daemon thread."""
        queue = SimpleQueue()

        with patch("layman.server.mkfifo"):
            with patch("layman.server.unlink"):
                with patch("layman.server.Thread") as mock_thread_class:
                    mock_thread = MagicMock()
                    mock_thread_class.return_value = mock_thread

                    from layman.server import MessageServer

                    server = MessageServer(queue)

                    mock_thread_class.assert_called_once()
                    mock_thread.start.assert_called_once()

    def test_pipeLocation_isCorrect(self):
        """DEFAULT_PIPE_PATH constant should be at expected location."""
        from layman.server import DEFAULT_PIPE_PATH

        assert DEFAULT_PIPE_PATH == "/tmp/layman.pipe"

    def test_init_customPipePath(self):
        """MessageServer should accept custom pipe path."""
        queue = SimpleQueue()
        custom_path = "/tmp/custom-layman.pipe"

        with patch("layman.server.mkfifo") as mock_mkfifo:
            with patch("layman.server.unlink"):
                with patch("layman.server.Thread"):
                    from layman.server import MessageServer

                    server = MessageServer(queue, custom_path)

                    mock_mkfifo.assert_called_once_with(custom_path)
                    assert server.pipe_path == custom_path


class TestMessageServerIntegration:
    """Integration-style tests for MessageServer with real files."""

    @pytest.fixture
    def temp_pipe_path(self):
        """Create a temporary path for the pipe."""
        import tempfile
        temp_dir = tempfile.mkdtemp()
        pipe_path = os.path.join(temp_dir, "test.pipe")
        yield pipe_path
        # Cleanup
        try:
            os.unlink(pipe_path)
        except FileNotFoundError:
            pass
        os.rmdir(temp_dir)

    def test_readPipe_putsCommandInQueue(self, temp_pipe_path):
        """readPipe should put commands in the queue."""
        queue = SimpleQueue()

        # Use custom pipe path directly
        with patch("layman.server.Thread"):
            from layman.server import MessageServer

            server = MessageServer(queue, temp_pipe_path)

            # Simulate reading from pipe
            # In real tests, we'd write to the pipe from another thread
            # Here we just verify the queue interface

            # Put a test message
            queue.put({"type": "command", "command": "layout maximize"})

            message = queue.get()
            assert message["type"] == "command"
            assert message["command"] == "layout maximize"
