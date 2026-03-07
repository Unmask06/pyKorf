"""Element CRUD (Create, Read, Update, Delete) operations for KORF models.

This module provides the :class:`ElementCRUDMixin` which adds element CRUD
capabilities to a model class. It assumes the following attributes/methods exist
in the class that uses this mixin:

- ``self._parser``: A KdfParser instance
- ``self._name_map``: A dict mapping element names to elements
- ``self._build_collections()``: Method to rebuild element collections
- ``self._ensure_unique_name(name, current_name)``: Method to ensure unique names
- ``self.get_element(name)``: Method to get an element by name
- ``self.elements``: Property returning all elements
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pykorf.elements import (
    ELEMENT_REGISTRY,
    BaseElement,
    Common,
    Element,
    PipeData,
)
from pykorf.exceptions import ParameterError

if TYPE_CHECKING:
    pass


class ElementCRUDMixin:
    """Mixin providing element CRUD (Create, Read, Update, Delete) operations.

    This mixin assumes the host class provides:
    - ``_parser``: KdfParser instance
    - ``_name_map``: Dict mapping element names to elements
    - ``_build_collections()``: Method to rebuild element collections
    - ``_ensure_unique_name(name, current_name)``: Method to ensure unique names
    - ``get_element(name)``: Method to get an element by name
    - ``elements``: Property returning all elements
    """

    def update_element(self, name: str, params: dict[str, Any]) -> None:
        """Update parameters of the named element.

        Args:
            name: Element NAME tag (e.g. ``'L1'``, ``'P1'``).
            params: Dict of ``{KDF_PARAM: value}``. Values are set as the first
                token of the record's value list. Special key ``'X'`` and
                ``'Y'`` update the XY record.

        Example:
            ```python
            model.update_element("L1", {"LEN": 200, "TFLOW": "80;90;60"})
            ```
        """
        elem = self.get_element(name)
        valid_params = type(elem).ALL
        rebuild_collections = False
        if Common.NAME in {key.upper() for key in params}:
            name_key = next(k for k in params if k.upper() == Common.NAME)
            new_name = str(params[name_key])
            new_name = self._ensure_unique_name(new_name, current_name=elem.name)
            params[name_key] = new_name
            rebuild_collections = True
        xy_update: dict[str, float] = {}
        for param, value in params.items():
            key = param.upper()
            if key in (Common.X, Common.Y):
                xy_update[key] = float(value)
                continue
            if key not in valid_params:
                raise ParameterError(
                    f"Parameter '{key}' is not valid for {elem.etype} elements. "
                    f"Valid parameters: {valid_params}"
                )
            rec = elem._get(key)
            if rec is not None:
                rec.values[0] = str(value)
                rec.raw_line = ""
            else:
                self._parser.set_value(elem.etype, elem.index, key, [str(value)])

        if xy_update:
            self._update_xy(elem, xy_update)

        if rebuild_collections:
            self._build_collections()

    def update_elements(self, updates: dict[str, dict[str, Any]]) -> None:
        """Batch-update multiple elements.

        Args:
            updates: ``{element_name: {param: value, ...}, ...}``

        Example:
            ```python
            model.update_elements(
                {
                    "L1": {"LEN": 200},
                    "P1": {"EFFP": 0.75},
                }
            )
            ```
        """
        for name, params in updates.items():
            self.update_element(name, params)

    def _update_xy(self, elem: BaseElement, xy: dict[str, float]) -> None:
        """Update the XY record of an element with X and/or Y values."""
        rec = elem._get(Common.XY)
        if rec is None:
            return
        vals = list(rec.values)
        if Common.X in xy and len(vals) > 0:
            vals[0] = str(xy[Common.X])
        if Common.Y in xy and len(vals) > 1:
            vals[1] = str(xy[Common.Y])
        rec.values = vals
        rec.raw_line = ""

    def add_element(
        self,
        etype: str,
        name: str,
        params: dict[str, Any] | None = None,
    ) -> BaseElement:
        """Add a new element instance cloned from the template (index 0).

        Parameters
        ----------
        etype:
            KDF element type keyword (e.g. ``'PIPE'``, ``'PUMP'``).
        name:
            Name for the new element (e.g. ``'L10'``, ``'P2'``).
        params:
            Optional parameter overrides applied after creation.

        Returns:
        -------
        The newly created element.
        """
        et = etype.upper()
        if et == Element.PIPE:
            raise ValueError(
                "PIPE cannot be created with add_element(); use "
                "connect_elements(..., pipe_name=...) so the pipe is created "
                "with connectivity."
            )
        if et == Element.PIPEDATA:
            return self._add_pipedata_internal(name, params)
        return self._add_element_internal(et, name, params)

    def _add_element_internal(
        self,
        etype: str,
        name: str,
        params: dict[str, Any] | None = None,
        *,
        auto_position: bool = True,
    ) -> BaseElement:
        """Internal element creation path used by model operations.

        Parameters
        ----------
        etype:
            Element type (e.g., 'PIPE', 'PUMP').
        name:
            Element name.
        params:
            Optional parameter overrides.
        auto_position:
            If True (default), automatically place the element at a
            non-overlapping position. Set to False when positioning
            will be handled separately (e.g., pipes in connect_elements).
        """
        et = etype.upper()
        if et not in ELEMENT_REGISTRY:
            raise ValueError(f"Unknown element type: {etype!r}")
        name = self._ensure_unique_name(name)

        new_idx = self._parser.next_index(et)
        self._parser.clone_records(et, 0, new_idx)

        current_count = self._parser.num_instances(et)
        self._parser.set_num_instances(et, current_count + 1)

        name_rec = self._parser.get(et, new_idx, Common.NAME)
        if name_rec:
            name_rec.values[0] = name
            name_rec.raw_line = ""

        self._build_collections()

        if params:
            self.update_element(name, params)

        if auto_position:
            x_or_y_provided = bool(params) and any(
                key.upper() in {Common.X, Common.Y} for key in params
            )
            if not x_or_y_provided:
                from pykorf.model.layout import auto_place

                auto_place(self, self.get_element(name))

        return self.get_element(name)

    def _add_pipedata_internal(
        self,
        name: str,
        params: dict[str, Any] | None = None,
    ) -> PipeData:
        """Add a new PIPEDATA entry.

        PIPEDATA elements don't have a NAME parameter in KORF, so we need
        to handle them specially - they can't be looked up by name.
        """
        et = Element.PIPEDATA
        new_idx = self._parser.next_index(et)

        src_idx = 1 if self._parser.num_instances(et) > 0 else 0
        self._parser.clone_records(et, src_idx, new_idx)

        current_count = self._parser.num_instances(et)
        self._parser.set_num_instances(et, current_count + 1)

        if params:
            for param, value in params.items():
                key = param.upper()
                if isinstance(value, (list, tuple)):
                    val_list = [str(v) for v in value]
                else:
                    val_list = [str(value)]
                self._parser.set_value(et, new_idx, key, val_list)

        self._build_collections()

        return self.pipedata[new_idx]

    def _next_auto_pipe_name(self) -> str:
        """Return the next available auto-generated pipe name."""
        i = 1
        while True:
            candidate = f"L_AUTO_{i}"
            if candidate not in self._name_map:
                return candidate
            i += 1

    def _position_pipe_between(self, pipe_name: str, elem1_name: str, elem2_name: str) -> None:
        """Position a pipe between two elements with proper spacing.

        Places the pipe at a position that visually connects elem1 and elem2,
        ensuring proper layout spacing and bounds. The pipe is aligned on the
        same Y-level as the equipment for a clean flow layout.
        """
        from pykorf.model.layout import auto_place, get_position, set_position

        elem1 = self.get_element(elem1_name)
        elem2 = self.get_element(elem2_name)
        pipe = self.get_element(pipe_name)

        pos1 = get_position(elem1)
        pos2 = get_position(elem2)

        if pos1 is None or pos2 is None or pos1 == (0.0, 0.0) or pos2 == (0.0, 0.0):
            auto_place(self, pipe)
            return

        mid_x = (pos1[0] + pos2[0]) / 2

        pipe_y = pos1[1]

        from pykorf.model.layout import MIN_SPACING, X_MAX, X_MIN, Y_MAX, Y_MIN

        mid_x = max(X_MIN, min(X_MAX, mid_x))
        pipe_y = max(Y_MIN, min(Y_MAX, pipe_y))

        candidate = (mid_x, pipe_y)
        offset = MIN_SPACING / 2
        max_attempts = 5

        for _ in range(max_attempts):
            clash = False
            for elem in self.elements:
                if elem.name == pipe_name:
                    continue
                other_pos = get_position(elem)
                if other_pos is None or other_pos == (0.0, 0.0):
                    continue
                dx = candidate[0] - other_pos[0]
                dy = candidate[1] - other_pos[1]
                dist = (dx * dx + dy * dy) ** 0.5
                if dist < offset:
                    clash = True
                    candidate = (candidate[0], candidate[1] + offset)
                    candidate = (
                        max(X_MIN, min(X_MAX, candidate[0])),
                        max(Y_MIN, min(Y_MAX, candidate[1])),
                    )
                    break
            if not clash:
                break

        mid_x, pipe_y = candidate

        set_position(self, pipe_name, mid_x, pipe_y)

    def add_elements(
        self,
        specs: list[tuple[str, str, dict[str, Any] | None]],
    ) -> list[BaseElement]:
        """Add multiple elements at once.

        Parameters
        ----------
        specs:
            List of ``(etype, name, params)`` tuples.  ``params`` may be
            *None* for default values.

        Returns:
        -------
        List of newly created elements.
        """
        results = []
        for spec in specs:
            etype, name = spec[0], spec[1]
            params = spec[2] if len(spec) > 2 else None
            results.append(self.add_element(etype, name, params))
        return results

    def delete_element(self, name: str) -> None:
        """Delete the named element from the model.

        Removes all records and reindexes remaining elements to be continuous.
        """
        elem = self.get_element(name)
        et = elem.etype
        idx = elem.index

        if et == Element.PIPE:
            from pykorf.model.connectivity import update_pipe_references

            update_pipe_references(self, idx, 0)

        self._parser.delete_records(et, idx)
        self.compact_indices(et)

    def delete_elements(self, names: list[str]) -> None:
        """Delete multiple elements by name."""
        for name in names:
            self.delete_element(name)

    def copy_element(self, src_name: str, dst_name: str) -> BaseElement:
        """Copy an existing element to a new element with a different name.

        Connectivity (CON, NOZI, NOZO, NOZL) is cleared on the copy.

        Parameters
        ----------
        src_name:
            Name of the element to copy.
        dst_name:
            Name for the new copy.

        Returns:
        -------
        The newly created copy.
        """
        dst_name = self._ensure_unique_name(dst_name)
        src = self.get_element(src_name)
        et = src.etype
        new_idx = self._parser.next_index(et)

        self._parser.clone_records(et, src.index, new_idx)

        current_count = self._parser.num_instances(et)
        self._parser.set_num_instances(et, current_count + 1)

        name_rec = self._parser.get(et, new_idx, Common.NAME)
        if name_rec:
            name_rec.values[0] = dst_name
            name_rec.raw_line = ""

        for con_param in (
            Common.CON,
            Common.NOZI,
            Common.NOZO,
            Common.NOZL,
            Common.NOZ,
        ):
            rec = self._parser.get(et, new_idx, con_param)
            if rec is not None:
                rec.values = ["0"] * len(rec.values)
                rec.raw_line = ""

        self._build_collections()
        return self.get_element(dst_name)

    def copy_elements(
        self,
        pairs: list[tuple[str, str]],
    ) -> list[BaseElement]:
        """Copy multiple elements.

        Parameters
        ----------
        pairs:
            List of ``(src_name, dst_name)`` tuples.
        """
        return [self.copy_element(src, dst) for src, dst in pairs]

    def move_element(self, name: str, target_index: int) -> None:
        """Change the index of an element within its type group.

        This swaps the element to a new index, useful for reordering.
        If *target_index* is already in use, the occupant is swapped to
        the source index.

        Parameters
        ----------
        name:
            Element NAME tag.
        target_index:
            Desired new index (must be >= 1).
        """
        elem = self.get_element(name)
        et = elem.etype
        src_idx = elem.index

        if target_index < 1:
            raise ValueError("Target index must be >= 1")
        if target_index == src_idx:
            return

        target_recs = self._parser.get_all(et, target_index)
        if target_recs:
            temp_idx = self._parser.next_index(et) + 1000
            self.reindex_element(et, target_index, temp_idx)
            self.reindex_element(et, src_idx, target_index)
            self.reindex_element(et, temp_idx, src_idx)
        else:
            self.reindex_element(et, src_idx, target_index)

        self._build_collections()

    def reindex_element(self, etype: str, old_index: int, new_index: int) -> None:
        """Update the index of an element and all its external references.

        This is a low-level operation. Use with caution.
        """
        et = etype.upper()
        if old_index == new_index:
            return

        self._parser.reindex(et, old_index, new_index)

        if et == Element.PIPE:
            from pykorf.model.connectivity import update_pipe_references

            update_pipe_references(self, old_index, new_index)

    def compact_indices(self, etype: str | None = None) -> None:
        """Reorder element indices to be continuous (1..N) and update NUM.

        If *etype* is None, compacts all element types.
        """
        etypes = [etype.upper()] if etype else Element.ALL
        for et in etypes:
            if et in (Element.GEN, Element.SYMBOL, Element.TOOLS, Element.PSEUDO):
                continue

            indices = sorted(
                {
                    r.index
                    for r in self._parser.records
                    if r.element_type == et and r.index and r.index >= 1
                }
            )
            if not indices:
                self._parser.set_num_instances(et, 0)
                continue

            for i, old_idx in enumerate(indices, 1):
                if old_idx != i:
                    self.reindex_element(et, old_idx, i)

            self._parser.set_num_instances(et, len(indices))

        self._build_collections()

    def move_elements(self, moves: list[tuple[str, int]]) -> None:
        """Move multiple elements to new indices.

        Parameters
        ----------
        moves:
            List of ``(name, target_index)`` tuples.
        """
        for name, target in moves:
            self.move_element(name, target)
