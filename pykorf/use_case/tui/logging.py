"""Colored logging utilities for TUI screens."""

from __future__ import annotations

from rich.text import Text
from textual.widgets import RichLog


def log_info(log: RichLog, message: str) -> None:
    """Write an info message (blue) to the log."""
    log.write(Text(message, style="cyan"))


def log_success(log: RichLog, message: str) -> None:
    """Write a success message (green) to the log."""
    log.write(Text(message, style="green"))


def log_warning(log: RichLog, message: str) -> None:
    """Write a warning message (yellow) to the log."""
    log.write(Text(message, style="yellow"))


def log_error(log: RichLog, message: str) -> None:
    """Write an error message (red) to the log."""
    log.write(Text(message, style="bold red"))
