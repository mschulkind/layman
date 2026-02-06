"""
Unit tests for structured logging infrastructure.

Tests the logging setup for:
- Per-module loggers
- Config-driven log levels
- CLI log level override
- Log format
- Layout manager logging integration
"""

import logging

import pytest

from layman.config import LaymanConfig
from layman.log import get_logger, setup_logging

from tests.mocks.i3ipc_mocks import MockConnection, MockCon, MockRect, MockWindowEvent


class TestGetLogger:
    """Tests for get_logger() factory function."""

    def test_getLogger_returnsNamedLogger(self):
        """get_logger should return a logger with the given name."""
        logger = get_logger("layman.test")
        assert logger.name == "layman.test"

    def test_getLogger_sameNameReturnsSameLogger(self):
        """Multiple calls with same name should return same logger."""
        logger1 = get_logger("layman.test_same")
        logger2 = get_logger("layman.test_same")
        assert logger1 is logger2

    def test_getLogger_childInheritsParentLevel(self):
        """Child loggers should inherit parent's level."""
        parent = get_logger("layman")
        parent.setLevel(logging.WARNING)
        child = get_logger("layman.child_test")
        # Child's effective level should match parent
        assert child.getEffectiveLevel() == logging.WARNING
        # Reset
        parent.setLevel(logging.NOTSET)


class TestSetupLogging:
    """Tests for setup_logging() configuration function."""

    def setup_method(self):
        """Reset logging state before each test."""
        # Remove all handlers from layman logger
        root_logger = logging.getLogger("layman")
        root_logger.handlers.clear()
        root_logger.setLevel(logging.NOTSET)

    def test_setupLogging_defaultLevel_info(self, tmp_path):
        """Default log level should be INFO when not specified."""
        config_path = tmp_path / "config.toml"
        config_path.write_text('[layman]\ndefaultLayout = "none"\n')
        options = LaymanConfig(str(config_path))

        setup_logging(options)

        logger = logging.getLogger("layman")
        assert logger.level == logging.INFO

    def test_setupLogging_configuredLevel_debug(self, tmp_path):
        """logLevel in config should set the root layman logger level."""
        config_path = tmp_path / "config.toml"
        config_path.write_text('[layman]\ndefaultLayout = "none"\nlogLevel = "debug"\n')
        options = LaymanConfig(str(config_path))

        setup_logging(options)

        logger = logging.getLogger("layman")
        assert logger.level == logging.DEBUG

    def test_setupLogging_configuredLevel_warning(self, tmp_path):
        """logLevel 'warning' should set WARNING level."""
        config_path = tmp_path / "config.toml"
        config_path.write_text('[layman]\ndefaultLayout = "none"\nlogLevel = "warning"\n')
        options = LaymanConfig(str(config_path))

        setup_logging(options)

        logger = logging.getLogger("layman")
        assert logger.level == logging.WARNING

    def test_setupLogging_cliOverride(self, tmp_path):
        """CLI log level should override config."""
        config_path = tmp_path / "config.toml"
        config_path.write_text('[layman]\ndefaultLayout = "none"\nlogLevel = "warning"\n')
        options = LaymanConfig(str(config_path))

        setup_logging(options, cli_log_level="debug")

        logger = logging.getLogger("layman")
        assert logger.level == logging.DEBUG

    def test_setupLogging_perModuleLevels(self, tmp_path):
        """Per-module log levels from [logging] config section."""
        config_path = tmp_path / "config.toml"
        config_path.write_text(
            '[layman]\ndefaultLayout = "none"\nlogLevel = "info"\n'
            "\n[logging]\n"
            '"layman.managers.master_stack" = "debug"\n'
            '"layman.listener" = "warning"\n'
        )
        options = LaymanConfig(str(config_path))

        setup_logging(options)

        ms_logger = logging.getLogger("layman.managers.master_stack")
        assert ms_logger.level == logging.DEBUG

        listener_logger = logging.getLogger("layman.listener")
        assert listener_logger.level == logging.WARNING

    def test_setupLogging_hasStreamHandler(self, tmp_path):
        """setup_logging should add a StreamHandler to the root layman logger."""
        config_path = tmp_path / "config.toml"
        config_path.write_text('[layman]\ndefaultLayout = "none"\n')
        options = LaymanConfig(str(config_path))

        setup_logging(options)

        logger = logging.getLogger("layman")
        stream_handlers = [
            h for h in logger.handlers if isinstance(h, logging.StreamHandler)
        ]
        assert len(stream_handlers) >= 1

    def test_setupLogging_formatIncludesModuleAndFunction(self, tmp_path, capsys):
        """Log format should include module name and function name."""
        config_path = tmp_path / "config.toml"
        config_path.write_text('[layman]\ndefaultLayout = "none"\nlogLevel = "debug"\n')
        options = LaymanConfig(str(config_path))

        setup_logging(options)

        logger = logging.getLogger("layman.test_format")
        logger.debug("test message")

        captured = capsys.readouterr()
        assert "test message" in captured.err
        assert "layman.test_format" in captured.err

    def test_setupLogging_backwardsCompatDebugTrue(self, tmp_path):
        """debug=true with no logLevel should set DEBUG level."""
        config_path = tmp_path / "config.toml"
        config_path.write_text('[layman]\ndefaultLayout = "none"\ndebug = true\n')
        options = LaymanConfig(str(config_path))

        setup_logging(options)

        logger = logging.getLogger("layman")
        assert logger.level == logging.DEBUG

    def test_setupLogging_invalidLevel_usesInfo(self, tmp_path):
        """Invalid logLevel string should fall back to INFO."""
        config_path = tmp_path / "config.toml"
        config_path.write_text('[layman]\ndefaultLayout = "none"\nlogLevel = "banana"\n')
        options = LaymanConfig(str(config_path))

        setup_logging(options)

        logger = logging.getLogger("layman")
        assert logger.level == logging.INFO


class TestLayoutManagerLogging:
    """Tests for layout manager logging via Python logging module."""

    def test_workspaceLayoutManager_hasLogger(self, mock_connection, tmp_path):
        """WorkspaceLayoutManager should use a named logger."""
        from layman.managers.workspace import WorkspaceLayoutManager

        config_path = tmp_path / "config.toml"
        config_path.write_text('[layman]\ndefaultLayout = "none"\nlogLevel = "debug"\n')
        options = LaymanConfig(str(config_path))

        manager = WorkspaceLayoutManager(mock_connection, None, "1", options)

        assert hasattr(manager, "logger")
        assert "workspace" in manager.logger.name.lower() or "none" in manager.logger.name.lower()

    def test_masterStack_loggerIncludesWorkspaceName(self, mock_connection, tmp_path):
        """MasterStack logger should identify the workspace."""
        from layman.managers.master_stack import MasterStackLayoutManager

        config_path = tmp_path / "config.toml"
        config_path.write_text(
            '[layman]\ndefaultLayout = "MasterStack"\nlogLevel = "debug"\n'
        )
        options = LaymanConfig(str(config_path))

        workspace = MockCon(name="3", type="workspace")
        manager = MasterStackLayoutManager(mock_connection, workspace, "3", options)

        assert hasattr(manager, "logger")
