"""Structured logging for pyKorf.

Provides a centralized logging system with support for:
- File-based logging (all logs go to file)
- Dynamic log file switching per model
- Context binding
- Performance timing

Example:
    >>> from pykorf.log import get_logger, bind_context, set_log_file
    >>> set_log_file("model.log")
    >>> logger = get_logger()
    >>> with bind_context(model="Pumpcases.kdf"):
    ...     logger.info("Loading model")
    ...     # ... do work
    ...     logger.info("Model loaded", elements=42)
"""

from __future__ import annotations

import functools
import logging
import time
from collections.abc import Callable
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeVar

from pykorf.config import get_config

# Try to import structlog, fall back to stdlib logging
try:
    import structlog

    HAS_STRUCTLOG = True
except ImportError:
    HAS_STRUCTLOG = False


if TYPE_CHECKING:
    import structlog

# Context variable for request/operation context
_log_context: ContextVar[dict[str, Any]] = ContextVar("log_context", default={})

# Module-level tracking of current log file
_current_log_file: str | None = None
_file_handler: logging.FileHandler | None = None


def configure_logging(log_file: str = "pykorf.log") -> None:
    """Configure logging with file output.

    All logs are written to the specified file. This function sets up
    the root "pykorf" logger with a file handler.

    Args:
        log_file: Path to the log file. Defaults to 'pykorf.log'.
    """
    global _current_log_file, _file_handler

    config = get_config()

    root_logger = logging.getLogger("pykorf")
    root_logger.setLevel(logging.DEBUG)
    root_logger.handlers = []

    _file_handler = logging.FileHandler(log_file, mode="w", encoding="utf-8")
    _file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter("%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s")
    _file_handler.setFormatter(file_formatter)
    root_logger.addHandler(_file_handler)

    _current_log_file = log_file

    if HAS_STRUCTLOG:
        _configure_structlog()
    else:
        import logging as std_logging

        std_logging.getLogger("pykorf").setLevel(getattr(std_logging, config.logging.level))


def set_log_file(log_file: str | Path) -> None:
    """Switch the log file to a new path.

    This closes the current file handler and opens a new one,
    effectively clearing the old log and starting fresh.

    Args:
        log_file: Path to the new log file.

    Example:
        >>> set_log_file("Cooling.log")
        >>> # All subsequent logs go to Cooling.log
    """
    global _current_log_file, _file_handler

    log_file_str = str(log_file)

    root_logger = logging.getLogger("pykorf")

    if _file_handler:
        root_logger.removeHandler(_file_handler)
        _file_handler.close()

    _file_handler = logging.FileHandler(log_file_str, mode="w", encoding="utf-8")
    _file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter("%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s")
    _file_handler.setFormatter(file_formatter)
    root_logger.addHandler(_file_handler)

    _current_log_file = log_file_str

    logger = logging.getLogger("pykorf.log")
    logger.debug(f"Log file switched to: {log_file_str}")


def get_log_file() -> str | None:
    """Get the current log file path.

    Returns:
        Path to the current log file, or None if not configured.
    """
    return _current_log_file


def _configure_structlog() -> None:
    """Configure structlog to use standard library logging."""
    config = get_config()

    shared_processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ]

    if config.logging.format == "structured":
        structlog.configure(
            processors=[*shared_processors, structlog.processors.JSONRenderer()],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    else:
        structlog.configure(
            processors=[*shared_processors, structlog.dev.ConsoleRenderer(colors=True)],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

    import logging as std_logging

    std_logging.getLogger("pykorf").setLevel(getattr(std_logging, config.logging.level))


class SimpleLogger:
    """Simple logger wrapper for when structlog is not available."""

    def __init__(self, name: str) -> None:
        self._logger = logging.getLogger(name)

    def _merge_context(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Merge global context into kwargs."""
        context = _log_context.get()
        if context:
            return {**context, **kwargs}
        return kwargs

    def debug(self, msg: str, **kwargs: Any) -> None:
        if kwargs:
            self._logger.debug(f"{msg} | {kwargs}")
        else:
            self._logger.debug(msg)

    def info(self, msg: str, **kwargs: Any) -> None:
        if kwargs:
            self._logger.info(f"{msg} | {kwargs}")
        else:
            self._logger.info(msg)

    def warning(self, msg: str, **kwargs: Any) -> None:
        if kwargs:
            self._logger.warning(f"{msg} | {kwargs}")
        else:
            self._logger.warning(msg)

    def error(self, msg: str, **kwargs: Any) -> None:
        if kwargs:
            self._logger.error(f"{msg} | {kwargs}")
        else:
            self._logger.error(msg)

    def exception(self, msg: str, **kwargs: Any) -> None:
        if kwargs:
            self._logger.exception(f"{msg} | {kwargs}")
        else:
            self._logger.exception(msg)

    def bind(self, **kwargs: Any) -> SimpleLogger:
        """Create a new logger with additional bound context."""
        new_logger = SimpleLogger(self._logger.name)
        return new_logger


if HAS_STRUCTLOG:

    class BoundContextLogger:
        """A logger wrapper that automatically includes context variables."""

        def __init__(self, logger: structlog.stdlib.BoundLogger) -> None:
            self._logger = logger

        def _merge_context(self, event_dict: dict[str, Any]) -> dict[str, Any]:
            """Merge global context into event dict."""
            context = _log_context.get()
            if context:
                return {**context, **event_dict}
            return event_dict

        def debug(self, msg: str, **kwargs: Any) -> None:
            self._logger.debug(msg, **self._merge_context(kwargs))

        def info(self, msg: str, **kwargs: Any) -> None:
            self._logger.info(msg, **self._merge_context(kwargs))

        def warning(self, msg: str, **kwargs: Any) -> None:
            self._logger.warning(msg, **self._merge_context(kwargs))

        def error(self, msg: str, **kwargs: Any) -> None:
            self._logger.error(msg, **self._merge_context(kwargs))

        def exception(self, msg: str, **kwargs: Any) -> None:
            self._logger.exception(msg, **self._merge_context(kwargs))

        def bind(self, **kwargs: Any) -> BoundContextLogger:
            """Create a new logger with additional bound context."""
            return BoundContextLogger(self._logger.bind(**kwargs))


def get_logger(name: str | None = None) -> BoundContextLogger | SimpleLogger:
    """Get a structured logger.

    Args:
        name: Logger name (defaults to calling module)

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

    if HAS_STRUCTLOG:
        logger = structlog.get_logger(name)
        return BoundContextLogger(logger)
    else:
        return SimpleLogger(name)


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


F = TypeVar("F", bound=Callable[..., Any])


def timed(func: F) -> F:
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


__all__ = [
    "bind_context",
    "configure_logging",
    "get_log_file",
    "get_logger",
    "log_operation",
    "set_log_file",
    "timed",
]

if HAS_STRUCTLOG:
    __all__.append("BoundContextLogger")
