"""Structured logging for pyKorf.

Provides a centralized logging system with support for:
- Console-based logging (stderr)
- Context binding
- Performance timing

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
import time
from collections.abc import Callable
from contextlib import contextmanager
from contextvars import ContextVar
from typing import TYPE_CHECKING, Any

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


def _configure_structlog() -> None:
    """Configure structlog to use standard library logging."""
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

    log_format = os.getenv("PYKORF_LOG_FORMAT", "structured").lower()
    if log_format == "structured":
        structlog.configure(
            processors=[*shared_processors, structlog.processors.JSONRenderer()],  # type: ignore[list-item]
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    else:
        structlog.configure(
            processors=[*shared_processors, structlog.dev.ConsoleRenderer(colors=True)],  # type: ignore[list-item]
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

    log_level = os.getenv("PYKORF_LOG_LEVEL", "INFO").upper()
    logging.getLogger("pykorf").setLevel(getattr(logging, log_level))


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
    _configure_structlog()

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


__all__ = [
    "bind_context",
    "get_logger",
    "log_operation",
    "timed",
]

if HAS_STRUCTLOG:
    __all__.append("BoundContextLogger")
