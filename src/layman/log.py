"""
Structured logging for layman.

Provides:
- get_logger(name): Factory for named loggers under the 'layman' hierarchy
- setup_logging(options, cli_log_level): Configure levels from config and CLI

Log levels:
- DEBUG:   Per-event detail (window IDs, rect sizes, command strings)
- INFO:    High-level actions (layout set, window added/removed, config loaded)
- WARNING: Recoverable issues (window not found, stale event skipped)
- ERROR:   Failures (command failed, config error)

Config example:
    [layman]
    logLevel = "info"

    [logging]
    "layman.managers.master_stack" = "debug"
    "layman.listener" = "warning"

CLI override:
    layman --log-level debug
"""

import logging
import sys

from layman.config import KEY_DEBUG, LaymanConfig

KEY_LOG_LEVEL = "logLevel"
TABLE_LOGGING = "logging"

LOG_FORMAT = "%(asctime)s.%(msecs)03d %(name)s %(funcName)s: %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_LEVEL_MAP = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}


def get_logger(name: str) -> logging.Logger:
    """Get a named logger under the layman hierarchy.

    Args:
        name: Logger name (e.g., 'layman.managers.master_stack')

    Returns:
        A logging.Logger instance.
    """
    return logging.getLogger(name)


def setup_logging(options: LaymanConfig, cli_log_level: str | None = None) -> None:
    """Configure logging from config and optional CLI override.

    Args:
        options: Parsed layman config.
        cli_log_level: Optional CLI override (e.g., 'debug').
    """
    root_logger = logging.getLogger("layman")

    # Remove existing handlers to avoid duplicates on reload
    root_logger.handlers.clear()

    # Add stderr handler with format
    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Determine root level: CLI > config logLevel > config debug > INFO
    if cli_log_level:
        level = _LEVEL_MAP.get(cli_log_level.lower(), logging.INFO)
    else:
        configured_level = options.getDefault(KEY_LOG_LEVEL)
        if configured_level and isinstance(configured_level, str):
            level = _LEVEL_MAP.get(configured_level.lower(), logging.INFO)
        elif options.getDefault(KEY_DEBUG):
            # Backwards compat: debug=true means DEBUG level
            level = logging.DEBUG
        else:
            level = logging.INFO

    root_logger.setLevel(level)

    # Per-module overrides from [logging] section
    try:
        logging_section = options.configDict.get(TABLE_LOGGING, {})
        if isinstance(logging_section, dict):
            for module_name, module_level in logging_section.items():
                if isinstance(module_level, str):
                    parsed_level = _LEVEL_MAP.get(module_level.lower())
                    if parsed_level is not None:
                        logging.getLogger(module_name).setLevel(parsed_level)
    except (AttributeError, TypeError):
        pass

    # Don't propagate to root Python logger
    root_logger.propagate = False
