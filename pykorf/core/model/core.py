"""Core utilities for the KORF model package.

Provides the :class:`ElementCollection` dict subclass and the default
template path constant used by :class:`~pykorf.core.model.Model`.
"""

from __future__ import annotations

from pathlib import Path
from typing import TypeVar

T = TypeVar("T")

_DEFAULT_TEMPLATE = Path(__file__).resolve().parent.parent.parent / "library" / "New.kdf"


class ElementCollection(dict[int, T]):
    """Dict subclass for element collections where __len__ excludes index 0.

    KORF models use index 0 as the template record, with real instances
    starting at index 1. This collection makes len() return the count of
    real instances only.
    """

    def __len__(self) -> int:
        """Return count of real instances (excluding index 0 template)."""
        count = super().__len__()
        return count - 1 if 0 in self else count
