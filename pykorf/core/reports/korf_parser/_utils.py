"""Shared utility functions for KORF Excel parsing."""

from __future__ import annotations

from typing import Any


def _safe_float(val: Any) -> float | None:
    """Convert a cell value to float, returning None if not numeric."""
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _safe_str(val: Any) -> str:
    """Convert a cell value to string, empty string if None."""
    if val is None:
        return ""
    return str(val).strip()
