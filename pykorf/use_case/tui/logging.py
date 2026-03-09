"""Colored logging utilities for TUI screens.

This module provides helper functions for writing colored messages
directly to RichLog widgets, and utilities for checking log files
for warnings and errors.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from rich.text import Text

if TYPE_CHECKING:
    from textual.widgets import RichLog


def has_warnings_or_errors(log_file: str | Path) -> bool:
    """Check if the log file contains any WARNING, ERROR, or CRITICAL entries.

    Args:
        log_file: Path to the log file to check.

    Returns:
        True if any warnings or errors are found, False otherwise.

    Example:
        >>> if has_warnings_or_errors("model.log"):
        ...     print("Warnings detected!")
    """
    log_path = Path(log_file)
    if not log_path.exists():
        return False

    try:
        with open(log_path, encoding="utf-8") as f:
            for line in f:
                # Check for WARNING, ERROR, or CRITICAL in the log line
                # Note: Log format pads levelname to 8 chars, so we check with regex-like approach
                if re.search(r"\|\s*(WARNING|ERROR|CRITICAL)\s*\|", line):
                    return True
        return False
    except Exception:
        return False


def get_log_entries(
    log_file: str | Path,
    levels: set[str] | None = None,
    logger_filter: str | None = None,
) -> list[tuple[str, str, str, str]]:
    """Extract log entries from file filtered by level and/or logger name.

    Parses the log format: timestamp | logger_name | LEVEL | message

    Args:
        log_file: Path to the log file to read.
        levels: Set of log levels to include (e.g., {"WARNING", "ERROR"}).
            Defaults to WARNING and ERROR.
        logger_filter: Substring to match in logger name (e.g., "pykorf.use_case.pms").
            If None, entries from all loggers are included.

    Returns:
        List of tuples (timestamp, logger_name, level, message) matching the filters.

    Example:
        >>> entries = get_log_entries("model.log", levels={"WARNING", "ERROR"})
        >>> for ts, name, level, msg in entries:
        ...     print(f"{level}: {msg}")
    """
    if levels is None:
        levels = {"WARNING", "ERROR", "CRITICAL"}

    log_path = Path(log_file)
    if not log_path.exists():
        return []

    results: list[tuple[str, str, str, str]] = []
    # Pattern: timestamp | logger_name | LEVEL | message
    # logger_name is padded to 20 chars, LEVEL to 8 chars
    pattern = re.compile(r"^(\S+\s+\S+)\s+\|\s*(\S+)\s*\|\s*(\w+)\s*\|\s*(.*)$")

    try:
        with open(log_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                match = pattern.match(line)
                if not match:
                    continue
                timestamp, logger_name, level, message = match.groups()
                level = level.strip()
                if level not in levels:
                    continue
                if logger_filter and logger_filter not in logger_name:
                    continue
                results.append((timestamp, logger_name.strip(), level, message.strip()))
    except Exception:
        pass

    return results


def log_debug(log: RichLog, message: str) -> None:
    """Write a debug message to the log (dim cyan)."""
    log.write(Text(message, style="dim cyan"))


def log_info(log: RichLog, message: str) -> None:
    """Write an info message (cyan) to the log."""
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


__all__ = [
    "get_log_entries",
    "has_warnings_or_errors",
    "log_debug",
    "log_error",
    "log_info",
    "log_success",
    "log_warning",
]
