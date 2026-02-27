"""
BaseElement – abstract foundation for all KORF element objects.

Every element holds a live reference to the :class:`KdfParser` so that
get/set operations immediately affect the underlying record list that will
be serialised on save.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from pykorf.definitions import Common

if TYPE_CHECKING:
    from pykorf.parser import KdfParser, KdfRecord


class BaseElement:
    """
    Base class wrapping a single KORF element instance.

    Args:
        parser: The :class:`KdfParser` that owns this file's records.
        etype: KDF element-type keyword string (e.g. ``Element.PIPE`` which is ``"PIPE"``).
        index: Instance index (>= 1 for real instances; 0 = default template).
    """

    #: KDF element-type keyword (override in subclasses)
    ETYPE: str = ""

    def __init__(self, parser: "KdfParser", etype: str, index: int):
        self._parser = parser
        self._etype = etype.upper()
        self._index = index

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def index(self) -> int:
        return self._index

    @property
    def etype(self) -> str:
        return self._etype

    @property
    def name(self) -> str:
        """Element name tag (e.g. ``'L1'``, ``'P1'``)."""
        rec = self._get(Common.NAME)
        return rec.values[0] if rec and rec.values else ""

    @property
    def description(self) -> str:
        """Optional description (second value of the NAME record)."""
        rec = self._get(Common.NAME)
        return rec.values[1] if rec and len(rec.values) > 1 else ""

    @description.setter
    def description(self, value: str) -> None:
        rec = self._get(Common.NAME)
        if rec:
            if len(rec.values) > 1:
                rec.values[1] = value
            else:
                rec.values.append(value)
            rec.raw_line = ""

    @property
    def notes(self) -> str:
        rec = self._get(Common.NOTES)
        return rec.values[0] if rec and rec.values else ""

    @notes.setter
    def notes(self, value: str) -> None:
        self._set(Common.NOTES, [value])

    # ------------------------------------------------------------------
    # Internal record access
    # ------------------------------------------------------------------

    def _get(self, param: str) -> Optional["KdfRecord"]:
        return self._parser.get(self._etype, self._index, param)

    def get_param(self, param: str) -> Optional["KdfRecord"]:
        """Return the record for a given parameter, or *None* if missing.

        Example:
            >>> from pykorf.definitions import Feed
            >>> rec = model.feeds[1].get_param(Feed.NAME)
            >>> rec.update(["EXP DRUM", "FEED"])
        """
        return self._get(param)

    def _values(self, param: str) -> list:
        rec = self._get(param)
        return rec.values if rec else []

    def _set(self, param: str, values: list) -> None:
        """Update an existing record's values list in-place."""
        self._parser.set_value(self._etype, self._index, param, values)

    def set_param(self, param: str, values: list) -> bool:
        """Set values for a given parameter.

        Returns:
            ``True`` if parameter exists and was updated, otherwise ``False``.
        """
        return self._parser.set_value(self._etype, self._index, param, values)

    def _scalar(self, param: str, pos: int = 0, default: Any = None) -> Any:
        """Return a single value from a record's value list."""
        v = self._values(param)
        return v[pos] if len(v) > pos else default

    # ------------------------------------------------------------------
    # Raw record list
    # ------------------------------------------------------------------

    def records(self) -> list["KdfRecord"]:
        """All KDF records belonging to this element instance."""
        return self._parser.get_all(self._etype, self._index)

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(index={self._index}, name={self.name!r})"
