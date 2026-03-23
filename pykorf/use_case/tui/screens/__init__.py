"""Shared helpers for TUI screens."""

from __future__ import annotations


def normalize_path_input(raw: str) -> str:
    """Strip newlines (pasted content) and surrounding quotes from a user-entered path."""
    return raw.replace("\n", "").strip().strip('"').strip("'")


def real_elements(collection: dict) -> dict:
    """Filter out template (index 0) from an element collection.

    Args:
        collection: Dictionary of elements indexed by ID.

    Returns:
        Dictionary with index 0 (template) removed.
    """
    return {idx: el for idx, el in collection.items() if idx > 0}
