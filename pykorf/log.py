"""Structured logging for pyKorf.

Provides a centralized logging system with support for:
- Console-based logging with colored output (stderr)
- Context binding via contextvars
- Performance timing
- Structured key=value output
- Flask flash message integration for web UI

Example:
    >>> from pykorf.log import get_logger, bind_context
    >>> logger = get_logger()
    >>> with bind_context(model="Pumpcases.kdf"):
    ...     logger.info("Loading model")
    ...     # ... do work
    ...     logger.info("Model loaded", elements=42)
"""

from __future__ import annotations

import functools
import logging
import os
import sys
import time
from collections.abc import Callable
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

# ANSI color codes for log levels
COLORS = {
    "DEBUG": "\033[36m",  # Cyan
    "INFO": "\033[32m",  # Green
    "WARNING": "\033[33m",  # Yellow
    "ERROR": "\033[31m",  # Red
    "CRITICAL": "\033[35m",  # Magenta
    "RESET": "\033[0m",  # Reset
}

# Context variable for request/operation context
_log_context: ContextVar[dict[str, Any]] = ContextVar("log_context", default={})

# Context variable for FlashLogHandler to capture messages for Flask
_flash_log_context: ContextVar[list[tuple[str, str]] | None] = ContextVar(
    "flash_log_context", default=None
)


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colored output for console logging."""

    def __init__(self, use_colors: bool = True) -> None:
        super().__init__()
        self.use_colors = use_colors and sys.stderr.isatty()

    def format(self, record: logging.LogRecord) -> str:
        # Build the base message
        levelname = record.levelname
        name = record.name
        msg = record.getMessage()

        # Extract structured data from extra kwargs
        structured = {}
        for key, value in record.__dict__.items():
            if key not in {
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "exc_info",
                "exc_text",
                "thread",
                "threadName",
                "message",
                "asctime",
            }:
                structured[key] = value

        # Add context from contextvars
        context = _log_context.get()
        if context:
            structured = {**context, **structured}

        # Format timestamp
        asctime = self.formatTime(record, self.datefmt)

        # Build structured data string
        if structured:
            structured_str = " | " + " ".join(f"{k}={v}" for k, v in structured.items())
        else:
            structured_str = ""

        # Apply colors
        if self.use_colors:
            color = COLORS.get(levelname, COLORS["RESET"])
            reset = COLORS["RESET"]
            levelname_colored = f"{color}{levelname}{reset}"
        else:
            levelname_colored = levelname

        # Format: TIMESTAMP LEVEL NAME - MESSAGE | key=value ...
        return f"{asctime} {levelname_colored} {name} - {msg}{structured_str}"


class FlashLogHandler(logging.Handler):
    """Logging handler that captures messages for Flask flash display.

    This handler captures INFO, WARNING, and ERROR level messages during a request
    and makes them available via get_captured_logs() for conversion to flash messages.
    """

    def emit(self, record: logging.LogRecord) -> None:
        # Only capture INFO and above (skip DEBUG)
        if record.levelno < logging.INFO:
            return

        # Check if we're in a flash capture context
        capture_list = _flash_log_context.get()
        if capture_list is None:
            return

        # Format the message
        msg = record.getMessage()

        # Add structured data if present
        structured = {}
        for key, value in record.__dict__.items():
            if key not in {
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "exc_info",
                "exc_text",
                "thread",
                "threadName",
                "message",
                "asctime",
            }:
                structured[key] = value

        if structured:
            msg = f"{msg} | " + " ".join(f"{k}={v}" for k, v in structured.items())

        # Map log level to Bootstrap alert type
        level_map = {
            logging.DEBUG: "info",
            logging.INFO: "info",
            logging.WARNING: "warning",
            logging.ERROR: "danger",
            logging.CRITICAL: "danger",
        }
        alert_type = level_map.get(record.levelno, "info")

        capture_list.append((alert_type, msg))


def get_captured_logs() -> list[tuple[str, str]] | None:
    """Get logs captured during the current request context.

    Returns:
        List of (alert_type, message) tuples, or None if not in capture context.
        alert_type is one of: 'info', 'warning', 'danger'
    """
    return _flash_log_context.get()


class BoundContextLogger:
    """A logger wrapper that automatically includes context variables and supports structured logging."""

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    def _merge_context(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Merge global context into kwargs."""
        context = _log_context.get()
        if context:
            return {**context, **kwargs}
        return kwargs

    def _log(self, level: int, msg: str, kwargs: dict[str, Any]) -> None:
        """Log a message with structured data."""
        merged = self._merge_context(kwargs)
        if merged:
            # Pass structured data via extra parameter
            self._logger.log(level, msg, extra=merged)
        else:
            self._logger.log(level, msg)

    def debug(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.DEBUG, msg, kwargs)

    def info(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.INFO, msg, kwargs)

    def warning(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.WARNING, msg, kwargs)

    def error(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.ERROR, msg, kwargs)

    def exception(self, msg: str, **kwargs: Any) -> None:
        """Log with exception info."""
        merged = self._merge_context(kwargs)
        if merged:
            self._logger.exception(msg, extra=merged)
        else:
            self._logger.exception(msg)

    def bind(self, **kwargs: Any) -> BoundContextLogger:
        """Create a new logger with additional bound context."""
        # For stdlib logging, we just return self since context is managed via contextvars
        # The bind() call is kept for API compatibility but doesn't create a new logger
        return self


def _configure_logging() -> None:
    """Configure stdlib logging with colored console output."""
    root_logger = logging.getLogger("pykorf")

    # Avoid adding handlers multiple times
    if root_logger.handlers:
        return

    log_level = os.getenv("PYKORF_LOG_LEVEL", "INFO").upper()
    numeric_level = getattr(logging, log_level, logging.INFO)
    root_logger.setLevel(numeric_level)

    # Console handler with colored formatter
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(numeric_level)

    # Check if colors should be disabled (e.g., CI/CD, non-TTY)
    use_colors = os.getenv("PYKORF_LOG_COLORS", "auto").lower()
    if use_colors == "auto":
        use_colors = sys.stderr.isatty()
    elif use_colors in ("1", "true", "yes"):
        use_colors = True
    else:
        use_colors = False

    formatter = ColoredFormatter(use_colors=use_colors)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Flash handler for web UI (always added, but only captures in flash_logs context)
    flash_handler = FlashLogHandler()
    flash_handler.setLevel(logging.INFO)
    root_logger.addHandler(flash_handler)

    root_logger.propagate = False


def get_logger(name: str | None = None) -> BoundContextLogger:
    """Get a structured logger.

    Args:
        name: Logger name (defaults to calling module).  Short names like
            ``"IOService"`` are automatically prefixed with ``"pykorf."`` so
            they inherit the root ``pykorf`` log-level configuration.

    Returns:
        A logger instance
    """
    if name is None:
        import inspect

        frame = inspect.currentframe()
        if frame and frame.f_back:
            module = inspect.getmodule(frame.f_back)
            name = module.__name__ if module else "pykorf"
        else:
            name = "pykorf"

    # Ensure the name sits under the pykorf hierarchy so it inherits the
    # configured log level.  Module-style names (containing ".") are left
    # as-is; short labels like "IOService" are prefixed.
    if "." not in name and not name.startswith("pykorf"):
        name = f"pykorf.{name}"

    logger = logging.getLogger(name)
    return BoundContextLogger(logger)


@contextmanager
def bind_context(**kwargs: Any):
    """Bind context variables for the duration of the context."""
    token = None
    try:
        current = _log_context.get()
        new_context = {**current, **kwargs}
        token = _log_context.set(new_context)
        yield
    finally:
        if token is not None:
            _log_context.reset(token)


@contextmanager
def flash_logs():
    """Context manager to capture log messages for Flask flash display.

    Use this in Flask routes to automatically capture INFO/WARNING/ERROR logs
    and display them as flash messages in the UI.

    Example:
        >>> from pykorf.log import get_logger, flash_logs
        >>> from flask import flash
        >>>
        >>> @bp.route("/operation")
        >>> def operation():
        ...     logger = get_logger(__name__)
        ...     with flash_logs() as logs:
        ...         logger.info("Starting operation")
        ...         # ... do work
        ...         logger.info("Operation complete", items=42)
        ...     # Convert captured logs to flash messages
        ...     for alert_type, message in logs:
        ...         flash(message, alert_type)

    Yields:
        A list that will be populated with (alert_type, message) tuples
    """
    capture_list: list[tuple[str, str]] = []
    token = None
    try:
        token = _flash_log_context.set(capture_list)
        yield capture_list
    finally:
        if token is not None:
            _flash_log_context.reset(token)


@contextmanager
def log_operation(operation: str, **context: Any):
    """Log an operation with timing."""
    logger = get_logger()
    start_time = time.time()
    with bind_context(operation=operation, **context):
        logger.info(f"{operation}_started")
        try:
            yield
            elapsed = time.time() - start_time
            logger.info(f"{operation}_completed", duration_ms=elapsed * 1000)
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(
                f"{operation}_failed",
                error=str(e),
                error_type=type(e).__name__,
                duration_ms=elapsed * 1000,
            )
            raise


def timed[F: Callable[..., Any]](func: F) -> F:
    """Decorator to time function execution."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        logger = get_logger(func.__module__)
        start = time.time()
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start
            logger.debug(f"{func.__name__}_completed", duration_ms=elapsed * 1000)
            return result
        except Exception as e:
            elapsed = time.time() - start
            logger.error(f"{func.__name__}_failed", error=str(e), duration_ms=elapsed * 1000)
            raise

    return wrapper  # type: ignore[return-value]


# Initialize logging on module import
_configure_logging()


__all__ = [
    "BoundContextLogger",
    "bind_context",
    "flash_logs",
    "get_captured_logs",
    "get_logger",
    "log_operation",
    "timed",
]
