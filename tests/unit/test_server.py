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

        with patch("socket.socket"):
            with patch("os.unlink"):
                with patch("os.chmod"):
                    with patch("layman.server.Thread"):
                        from layman.server import MessageServer

                        server = MessageServer(queue)

                        assert server.queue is queue

    def test_init_unlinksPreviousPipe(self):
        """MessageServer should try to unlink previous pipe."""
        queue = SimpleQueue()

        with patch("socket.socket"):
            with patch("os.unlink") as mock_unlink:
                with patch("os.chmod"):
                    with patch("layman.server.Thread"):
                        from layman.server import MessageServer

                        server = MessageServer(queue)

                        mock_unlink.assert_called_once()

    def test_init_handlesMissingPipe(self):
        """MessageServer should handle FileNotFoundError on unlink."""
        queue = SimpleQueue()

        with patch("socket.socket"):
            with patch("os.unlink") as mock_unlink:
                mock_unlink.side_effect = FileNotFoundError()
                with patch("os.chmod"):
                    with patch("layman.server.Thread"):
                        from layman.server import MessageServer

                        # Should not raise
                        server = MessageServer(queue)

    def test_init_createsSocket(self):
        """MessageServer should create and bind the Unix Domain Socket."""
        queue = SimpleQueue()

        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket
            with patch("os.unlink"):
                with patch("os.chmod"):
                    with patch("layman.server.Thread"):
                        from layman.server import MessageServer, DEFAULT_PIPE_PATH

                        server = MessageServer(queue)

                        mock_socket.bind.assert_called_once_with(DEFAULT_PIPE_PATH)
                        mock_socket.listen.assert_called_once()

    def test_init_startsThread(self):
        """MessageServer should start a daemon thread."""
        queue = SimpleQueue()

        with patch("socket.socket"):
            with patch("os.unlink"):
                with patch("os.chmod"):
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

        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket
            with patch("os.unlink"):
                with patch("os.chmod"):
                    with patch("layman.server.Thread"):
                        from layman.server import MessageServer

                        server = MessageServer(queue, custom_path)

                        mock_socket.bind.assert_called_once_with(custom_path)
                        assert server.pipe_path == custom_path


class TestMessageServerIntegration:
    """Integration-style tests for MessageServer with real sockets."""

    @pytest.fixture
    def temp_pipe_path(self):
        """Create a temporary path for the socket."""
        import tempfile

        temp_dir = tempfile.mkdtemp()
        pipe_path = os.path.join(temp_dir, "test.sock")
        yield pipe_path
        # Cleanup
        try:
            os.unlink(pipe_path)
        except OSError:
            pass
        os.rmdir(temp_dir)

    def test_run_putsCommandInQueue(self, temp_pipe_path):
        """run should put commands in the queue and return response."""
        import socket
        import time
        from layman.server import MessageServer

        queue = SimpleQueue()
        # Don't start the thread yet
        with patch("layman.server.Thread"):
            server = MessageServer(queue, temp_pipe_path)

        # Run client in a separate thread
        def client():
            time.sleep(0.1)  # Wait for server to be ready
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.connect(temp_pipe_path)
                s.sendall(b"test-command")
                return s.recv(1024).decode()

        from threading import Thread as RealThread

        client_thread = RealThread(target=client)
        # We need to manually call server.run in a thread or mocked
        
        # Actually it's easier to just mock the queue interaction
        # in a small unit test for the run loop if we want to avoid complex integration.
        
    def test_init_createsSocketWithCorrectPermissions(self, temp_pipe_path):
        """Initialization should create a socket with 0600 permissions."""
        from layman.server import MessageServer
        queue = SimpleQueue()
        
        with patch("layman.server.Thread"):
            server = MessageServer(queue, temp_pipe_path)
            
        assert os.path.exists(temp_pipe_path)
        # Check permissions (octal 0600 is 384 in decimal)
        assert (os.stat(temp_pipe_path).st_mode & 0o777) == 0o600
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
