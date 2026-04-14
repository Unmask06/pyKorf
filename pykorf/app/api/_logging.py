"""Console logging setup for the FastAPI web server."""

from __future__ import annotations

import logging
import sys


def setup_console_logging(debug: bool = True) -> None:
    """Add a stderr StreamHandler to the pykorf logger if none exists yet.

    Args:
        debug: When True, log at DEBUG level; otherwise WARNING.
    """
    from pykorf.core.log import set_log_level

    level = "DEBUG" if debug else "WARNING"
    set_log_level(level)

    pykorf_logger = logging.getLogger("pykorf")
    if not any(isinstance(h, logging.StreamHandler) for h in pykorf_logger.handlers):
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(logging.DEBUG if debug else logging.WARNING)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        pykorf_logger.addHandler(handler)
    pykorf_logger.propagate = False
