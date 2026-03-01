"""
Structured logging for pyKorf.

Provides a centralized logging system with support for:
- Structured JSON logging
- Console output with colors
- Context binding
- Performance timing

Example:
    >>> from pykorf.log import get_logger, bind_context
    >>> logger = get_logger()
    >>> 
    >>> with bind_context(model="Pumpcases.kdf"):
    ...     logger.info("Loading model")
    ...     # ... do work
    ...     logger.info("Model loaded", elements=42)
"""

from __future__ import annotations

import functools
import logging
import time
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Callable, TypeVar

from pykorf.config import get_config

# Try to import structlog, fall back to stdlib logging
try:
    import structlog
    HAS_STRUCTLOG = True
except ImportError:
    HAS_STRUCTLOG = False

# Context variable for request/operation context
_log_context: ContextVar[dict[str, Any]] = ContextVar("log_context", default={})


def configure_logging() -> None:
    """Configure logging with pyKorf settings."""
    if not HAS_STRUCTLOG:
        # Use standard logging configuration
        config = get_config()
        level = getattr(logging, config.logging.level, logging.INFO)
        logging.basicConfig(
            level=level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        return
    
    config = get_config()
    
    shared_processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    if config.logging.format == "structured":
        # JSON output for production
        structlog.configure(
            processors=shared_processors + [structlog.processors.JSONRenderer()],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    else:
        # Console output for development
        structlog.configure(
            processors=shared_processors + [
                structlog.dev.ConsoleRenderer(colors=True)
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    
    # Set log level
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
    """Bind context variables for the duration of the context.
    
    Example:
        >>> with bind_context(model="Pumpcases.kdf", operation="load"):
        ...     logger.info("Starting")  # Includes model and operation
    """
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
    """Log an operation with timing.
    
    Example:
        >>> with log_operation("load_model", path="model.kdf"):
        ...     model = Model("model.kdf")
    """
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
    """Decorator to time function execution.
    
    Example:
        >>> @timed
        ... def heavy_operation():
        ...     pass
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        logger = get_logger(func.__module__)
        start = time.time()
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start
            logger.debug(
                f"{func.__name__}_completed",
                duration_ms=elapsed * 1000,
            )
            return result
        except Exception as e:
            elapsed = time.time() - start
            logger.error(
                f"{func.__name__}_failed",
                error=str(e),
                duration_ms=elapsed * 1000,
            )
            raise
    return wrapper  # type: ignore[return-value]


__all__ = [
    "configure_logging",
    "get_logger",
    "bind_context",
    "log_operation",
    "timed",
]

if HAS_STRUCTLOG:
    __all__.append("BoundContextLogger")
