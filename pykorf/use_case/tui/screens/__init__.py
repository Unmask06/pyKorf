"""Shared helpers for TUI screens."""

from __future__ import annotations


def real_elements(collection: dict) -> dict:
    """Filter out template (index 0) from an element collection.

    Args:
        collection: Dictionary of elements indexed by ID.

    Returns:
        Dictionary with index 0 (template) removed.
    """
    return {idx: el for idx, el in collection.items() if idx > 0}
