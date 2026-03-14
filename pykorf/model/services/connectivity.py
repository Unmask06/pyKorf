"""Connectivity service for KORF models.

Handles connecting and disconnecting elements, and validating
that all connections in a model are consistent.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from pykorf.elements import Element
from pykorf.exceptions import ConnectivityError

if TYPE_CHECKING:
    from pykorf.model import Model

_CON_ELEMENTS = {"PUMP", "VALVE", "CHECK", "HX", "COMP", "MISC", "EXPAND", "FO"}
_NOZ_ELEMENTS = {"FEED", "PROD"}


@dataclass(frozen=True, slots=True)
class ConnectivityService:
    """Service providing connectivity management functionality for KORF models.

    Args:
        model: The Model instance this service operates on.
    """

    model: Model

    # -------------------------------------------------------------------------
    # Public API methods (moved from ConnectivityMixin)
    # -------------------------------------------------------------------------

    def connect_elements(
        self,
        name1_or_pairs: str | list[tuple[str, str] | tuple[str, str, str]],
        name2: str | None = None,
        pipe_name: str | None = None,
    ) -> None:
        """Connect elements in the model.

        Supports both single connections and batch connections via a list.
        When connecting two non-PIPE elements, an intermediate pipe is created.

        Args:
            name1_or_pairs: Either a single element name or a list of connection
                pairs. Each pair can be (name1, name2) or (name1, name2, pipe_name).
            name2: The second element name when using single connection mode.
                Required when name1_or_pairs is a string.
            pipe_name: Optional name for the auto-created pipe when connecting
                two non-PIPE elements. Only valid when connecting two non-PIPEs.

        Raises:
            ValueError: If name2 is not provided in single connection mode,
                or if pipe_name is provided when connecting a PIPE to another element.
            ConnectivityError: If the connection cannot be made.

        Example:
            ```python
            # Single connection (one must be a PIPE)
            service.connect_elements("Pipe1", "Pump1")

            # Connect two non-PIPEs with auto-created pipe
            service.connect_elements("Feed1", "Pump1")

            # Connect with specific pipe name
            service.connect_elements("Feed1", "Pump1", pipe_name="NewPipe")

            # Batch connections
            service.connect_elements([
                ("Pipe1", "Pump1"),
                ("Feed1", "Pump1", "AutoPipe"),
            ])
            ```
        """
        if isinstance(name1_or_pairs, list):
            for pair in name1_or_pairs:
                if len(pair) == 2:
                    n1, n2 = pair
                    p_name = None
                elif len(pair) == 3:
                    n1, n2, p_name = pair
                else:
                    raise ValueError(
                        "Each connection pair must be (name1, name2) or (name1, name2, pipe_name)."
                    )
                self.connect_elements(n1, n2, pipe_name=p_name)
        else:
            if name2 is None:
                raise ValueError("name2 is required when name1 is a string")
            elem1 = self.model.get_element(name1_or_pairs)
            elem2 = self.model.get_element(name2)
            if elem1.etype == Element.PIPE or elem2.etype == Element.PIPE:
                if pipe_name is not None:
                    raise ValueError(
                        "pipe_name can only be provided when connecting two non-PIPE elements."
                    )
                self._connect(name1_or_pairs, name2)
                return

            new_pipe_name = pipe_name or self.model._next_auto_pipe_name()
            self.model._add_element_internal(Element.PIPE, new_pipe_name, auto_position=False)
            self.model._position_pipe_between(new_pipe_name, name1_or_pairs, name2)
            self._connect(new_pipe_name, name1_or_pairs)
            self._connect(new_pipe_name, name2)

    def disconnect_elements(
        self,
        name1_or_pairs: str | list[tuple[str, str]],
        name2: str | None = None,
    ) -> None:
        """Disconnect elements in the model.

        Supports both single disconnection and batch disconnections via a list.
        One of the elements must be a PIPE.

        Args:
            name1_or_pairs: Either a single element name or a list of disconnection
                pairs (name1, name2).
            name2: The second element name when using single disconnection mode.
                Required when name1_or_pairs is a string.

        Raises:
            ValueError: If name2 is not provided in single disconnection mode.
            ConnectivityError: If the disconnection cannot be made.

        Example:
            ```python
            # Single disconnection
            service.disconnect_elements("Pipe1", "Pump1")

            # Batch disconnections
            service.disconnect_elements([
                ("Pipe1", "Pump1"),
                ("Pipe2", "Valve1"),
            ])
            ```
        """
        if isinstance(name1_or_pairs, list):
            for n1, n2 in name1_or_pairs:
                self._disconnect(n1, n2)
        else:
            if name2 is None:
                raise ValueError("name2 is required when name1 is a string")
            self._disconnect(name1_or_pairs, name2)

    def check_connectivity(self) -> list[str]:
        """Check all element connections for consistency.

        Validates that all pipe references in CON and nozzle records
        point to existing pipes.

        Returns:
            List of issue descriptions. Empty list if no issues found.

        Example:
            ```python
            issues = service.check_connectivity()
            if issues:
                print("Connectivity issues found:")
                for issue in issues:
                    print(f"  - {issue}")
            ```
        """
        return self._check_connectivity()

    def get_connections(self, name: str) -> list[str]:
        """Return a list of element names connected to the named element.

        For a PIPE, returns all elements connected to it.
        For other elements, returns the connected PIPE names.

        Args:
            name: Element NAME tag (e.g. ``'L1'``, ``'P1'``).

        Returns:
            Sorted list of connected element names.

        Raises:
            ElementNotFoundError: If the element does not exist.

        Example:
            ```python
            connected = service.get_connections("Pipe1")
            print(f"Pipe1 is connected to: {connected}")
            ```
        """
        return self._get_connections(name)

    def get_unconnected_elements(self) -> list[str]:
        """Return a list of element names that have open connections.

        Checks pipes (need at least 2 connections) and equipment elements
        (CON records with "0" values or missing connections).

        Returns:
            Sorted list of element names with open connections.

        Example:
            ```python
            unconnected = service.get_unconnected_elements()
            if unconnected:
                print(f"Elements with open connections: {unconnected}")
            ```
        """
        unconnected = []

        for pipe in self.model.get_elements_by_type("PIPE"):
            conns = self._get_connections(pipe.name)
            if len(conns) < 2:
                unconnected.append(pipe.name)

        for elem in self.model.elements:
            if elem.etype == "PIPE":
                continue

            et = elem.etype
            if et in _CON_ELEMENTS:
                rec = elem.get_param("CON")
                if rec and (str(rec.values[0]) == "0" or str(rec.values[1]) == "0"):
                    unconnected.append(elem.name)
                elif rec is None:
                    nozzle_recs = self._get_nozzle_records(elem)
                    if nozzle_recs and any(
                        not nozzle_rec.values or str(nozzle_rec.values[0]) == "0"
                        for _, nozzle_rec in nozzle_recs
                    ):
                        unconnected.append(elem.name)
            elif et in _NOZ_ELEMENTS:
                noz_param = self._get_nozzle_param(elem)
                rec = elem.get_param(noz_param)
                if rec and str(rec.values[0]) == "0":
                    unconnected.append(elem.name)
            elif et == "TEE":
                rec = elem.get_param("CON")
                if rec:
                    for i in [0, 3, 5]:
                        if i < len(rec.values) and str(rec.values[i]) == "0":
                            unconnected.append(elem.name)
                            break
            elif et in ("JUNC", "VESSEL"):
                pipe_indices = self._get_element_pipe_indices(elem)
                if not pipe_indices:
                    unconnected.append(elem.name)

        return sorted(list(set(unconnected)))

    # -------------------------------------------------------------------------
    # Private helper methods (moved from module-level functions)
    # -------------------------------------------------------------------------

    def _get_connections(self, name: str) -> list[str]:
        """Get all elements connected to the named element."""
        elem = self.model.get_element(name)
        connected_names = []

        if elem.etype == "PIPE":
            pipe_idx = elem.index
            for other in self.model.elements:
                if other.etype == "PIPE":
                    continue
                if self._is_element_connected_to_pipe(other, pipe_idx):
                    connected_names.append(other.name)
        else:
            pipe_indices = self._get_element_pipe_indices(elem)
            for p_idx in pipe_indices:
                if p_idx in self.model.pipes:
                    connected_names.append(self.model.pipes[p_idx].name)

        return sorted(list(set(connected_names)))

    def _connect(self, name1: str, name2: str) -> None:
        """Connect two elements where one must be a PIPE."""
        elem1 = self.model.get_element(name1)
        elem2 = self.model.get_element(name2)

        if elem1.etype == "PIPE" and elem2.etype == "PIPE":
            raise ConnectivityError(
                f"Cannot directly connect two pipes ({name1} and {name2}). "
                "Use a TEE, JUNC, or equipment element between them."
            )

        if elem1.etype == "PIPE":
            pipe_elem, other_elem = elem1, elem2
        elif elem2.etype == "PIPE":
            pipe_elem, other_elem = elem2, elem1
        else:
            raise ConnectivityError(
                f"At least one element must be a PIPE. "
                f"Got {name1} ({elem1.etype}) and {name2} ({elem2.etype})."
            )

        pipe_idx = pipe_elem.index
        et = other_elem.etype

        if et in _CON_ELEMENTS:
            rec = other_elem.get_param("CON")
            if rec is None:
                if self._set_nozzle_pipe_reference(other_elem, pipe_idx):
                    return
                raise ConnectivityError(f"{other_elem.name} ({et}) has no CON/NOZI/NOZO record")
            vals = list(rec.values)
            if len(vals) >= 2:
                if str(vals[0]) == "0":
                    vals[0] = str(pipe_idx)
                elif str(vals[1]) == "0":
                    vals[1] = str(pipe_idx)
                else:
                    raise ConnectivityError(
                        f"{other_elem.name} ({et}) already has both connections filled: "
                        f"inlet={vals[0]}, outlet={vals[1]}"
                    )
                rec.values = vals
                rec.raw_line = ""
            else:
                raise ConnectivityError(
                    f"{other_elem.name} ({et}) CON record has unexpected format"
                )

        elif et in _NOZ_ELEMENTS:
            noz_param = self._get_nozzle_param(other_elem)
            rec = other_elem.get_param(noz_param)
            if rec is not None:
                rec.values = [str(pipe_idx), *rec.values[1:]]
                rec.raw_line = ""
            else:
                self.model._parser.set_value(et, other_elem.index, noz_param, [str(pipe_idx)])

        elif et == "TEE":
            rec = other_elem.get_param("CON")
            if rec is None:
                raise ConnectivityError(f"{other_elem.name} (TEE) has no CON record")
            vals = list(rec.values)
            placed = False
            for i in [0, 3, 5]:
                if i < len(vals) and str(vals[i]) == "0":
                    vals[i] = str(pipe_idx)
                    placed = True
                    break
            if not placed:
                raise ConnectivityError(
                    f"{other_elem.name} (TEE) all three connections already filled"
                )
            rec.values = vals
            rec.raw_line = ""

        else:
            raise ConnectivityError(f"Don't know how to connect a PIPE to {et}")

    def _disconnect(self, name1: str, name2: str) -> None:
        """Disconnect two elements where one must be a PIPE."""
        elem1 = self.model.get_element(name1)
        elem2 = self.model.get_element(name2)

        if elem1.etype == "PIPE":
            pipe_elem, other_elem = elem1, elem2
        elif elem2.etype == "PIPE":
            pipe_elem, other_elem = elem2, elem1
        else:
            raise ConnectivityError(
                f"At least one element must be a PIPE. "
                f"Got {name1} ({elem1.etype}) and {name2} ({elem2.etype})."
            )

        pipe_idx = str(pipe_elem.index)
        et = other_elem.etype

        if et in _CON_ELEMENTS:
            rec = other_elem.get_param("CON")
            if rec is None:
                if self._clear_nozzle_pipe_reference(other_elem, pipe_idx):
                    return
                raise ConnectivityError(
                    f"{other_elem.name} is not connected to pipe {pipe_elem.name}"
                )
            vals = list(rec.values)
            found = False
            for i in range(min(2, len(vals))):
                if str(vals[i]) == pipe_idx:
                    vals[i] = "0"
                    found = True
                    break
            if not found:
                raise ConnectivityError(
                    f"{other_elem.name} is not connected to pipe {pipe_elem.name}"
                )
            rec.values = vals
            rec.raw_line = ""

        elif et in _NOZ_ELEMENTS:
            noz_param = self._get_nozzle_param(other_elem)
            rec = other_elem.get_param(noz_param)
            if rec is None or str(rec.values[0]) != pipe_idx:
                raise ConnectivityError(
                    f"{other_elem.name} is not connected to pipe {pipe_elem.name}"
                )
            rec.values = ["0", *rec.values[1:]]
            rec.raw_line = ""

        elif et == "TEE":
            rec = other_elem.get_param("CON")
            if rec is None:
                raise ConnectivityError(f"{other_elem.name} (TEE) has no CON record")
            vals = list(rec.values)
            found = False
            for i in [0, 3, 5]:
                if i < len(vals) and str(vals[i]) == pipe_idx:
                    vals[i] = "0"
                    found = True
                    break
            if not found:
                raise ConnectivityError(
                    f"{other_elem.name} is not connected to pipe {pipe_elem.name}"
                )
            rec.values = vals
            rec.raw_line = ""

        else:
            raise ConnectivityError(f"Don't know how to disconnect a PIPE from {et}")

    def _check_connectivity(self) -> list[str]:
        """Check all element connections for consistency."""
        issues: list[str] = []
        pipe_indices = {idx for idx in self.model.pipes if idx >= 1}

        for collection_attr in (
            "valves",
            "check_valves",
            "orifices",
            "exchangers",
            "pumps",
            "compressors",
            "misc_equipment",
            "expanders",
        ):
            collection = getattr(self.model, collection_attr, {})
            for idx, elem in collection.items():
                if idx == 0:
                    continue
                rec = elem.get_param("CON")
                if rec is not None:
                    vals = rec.values
                    for i, label in enumerate(["inlet", "outlet"]):
                        if i >= len(vals):
                            break
                        try:
                            pipe_ref = int(vals[i])
                        except (ValueError, TypeError):
                            issues.append(
                                f"{elem.name} ({elem.etype}): {label} CON value "
                                f"{vals[i]!r} is not a valid integer"
                            )
                            continue
                        if pipe_ref != 0 and pipe_ref not in pipe_indices:
                            issues.append(
                                f"{elem.name} ({elem.etype}): {label} references "
                                f"pipe index {pipe_ref} which does not exist"
                            )
                    continue

                nozzle_recs = self._get_nozzle_records(elem)
                for nozzle_label, nozzle_rec in nozzle_recs:
                    if not nozzle_rec.values:
                        continue
                    try:
                        pipe_ref = int(nozzle_rec.values[0])
                    except (ValueError, TypeError):
                        issues.append(
                            f"{elem.name} ({elem.etype}): {nozzle_label} value "
                            f"{nozzle_rec.values[0]!r} is not a valid integer"
                        )
                        continue
                    if pipe_ref != 0 and pipe_ref not in pipe_indices:
                        issues.append(
                            f"{elem.name} ({elem.etype}): {nozzle_label} references "
                            f"pipe index {pipe_ref} which does not exist"
                        )

        for collection_attr in ("feeds", "products"):
            collection = getattr(self.model, collection_attr, {})
            for idx, elem in collection.items():
                if idx == 0:
                    continue
                noz_param = self._get_nozzle_param(elem)
                rec = elem.get_param(noz_param)
                if rec is None or not rec.values:
                    continue
                try:
                    pipe_ref = int(rec.values[0])
                except (ValueError, TypeError):
                    issues.append(
                        f"{elem.name} ({elem.etype}): {noz_param} value "
                        f"{rec.values[0]!r} is not a valid integer"
                    )
                    continue
                if pipe_ref != 0 and pipe_ref not in pipe_indices:
                    issues.append(
                        f"{elem.name} ({elem.etype}): references pipe index "
                        f"{pipe_ref} which does not exist"
                    )

        for idx, elem in self.model.tees.items():
            if idx == 0:
                continue
            rec = elem.get_param("CON")
            if rec is None:
                continue
            labels = ["combined", "main", "branch"]
            for i, label in enumerate(labels):
                if i >= len(rec.values):
                    break
                try:
                    pipe_ref = int(rec.values[i])
                except (ValueError, TypeError):
                    issues.append(
                        f"{elem.name} (TEE): {label} CON value {rec.values[i]!r} is not a valid integer"
                    )
                    continue
                if pipe_ref != 0 and pipe_ref not in pipe_indices:
                    issues.append(
                        f"{elem.name} (TEE): {label} references pipe index "
                        f"{pipe_ref} which does not exist"
                    )

        return issues

    def _update_pipe_references(self, old_idx: int, new_idx: int) -> None:
        """Update all pipe index references from old_idx to new_idx."""
        old_s = str(old_idx)
        new_s = str(new_idx)

        for elem in self.model.elements:
            if elem.etype == "PIPE":
                continue

            et = elem.etype
            if et in _CON_ELEMENTS:
                rec = elem.get_param("CON")
                if rec:
                    vals = list(rec.values)
                    changed = False
                    for i in range(min(2, len(vals))):
                        if vals[i] == old_s:
                            vals[i] = new_s
                            changed = True
                    if changed:
                        rec.values = vals
                        rec.raw_line = ""
                else:
                    self._update_nozzle_pipe_reference(elem, old_s, new_s)
            elif et in _NOZ_ELEMENTS:
                noz_param = self._get_nozzle_param(elem)
                rec = elem.get_param(noz_param)
                if rec and rec.values and rec.values[0] == old_s:
                    rec.values = [new_s, *rec.values[1:]]
                    rec.raw_line = ""
            elif et == "TEE":
                rec = elem.get_param("CON")
                if rec:
                    vals = list(rec.values)
                    changed = False
                    for i in [0, 1, 2, 3, 4, 5]:
                        if i < len(vals) and vals[i] == old_s:
                            vals[i] = new_s
                            changed = True
                    if changed:
                        rec.values = vals
                        rec.raw_line = ""
            elif et == "JUNC":
                for rec in elem.records():
                    if rec.param in ("NOZI", "NOZO") and len(rec.values) >= 2:
                        if rec.values[1] == old_s:
                            rec.values[1] = new_s
                            rec.raw_line = ""
            elif et == "VESSEL":
                for rec in elem.records():
                    if rec.param in ("NOZLI", "NOZLO") and len(rec.values) >= 2:
                        if rec.values[1] == old_s:
                            rec.values[1] = new_s
                            rec.raw_line = ""

    def _get_nozzle_param(self, elem) -> str:
        """Get the nozzle parameter name (NOZL or NOZ) for an element."""
        if elem.get_param("NOZL") is not None:
            return "NOZL"
        if elem.get_param("NOZ") is not None:
            return "NOZ"
        return "NOZL"

    def _is_valid_idx(self, v: Any) -> bool:
        """Check if a value is a valid positive integer index."""
        try:
            return int(v) > 0
        except (ValueError, TypeError):
            return False

    def _get_nozzle_records(self, elem) -> list[tuple[str, Any]]:
        """Get all nozzle records (NOZI, NOZO) for an element."""
        records: list[tuple[str, Any]] = []
        for nozzle_param in ("NOZI", "NOZO"):
            rec = elem.get_param(nozzle_param)
            if rec is not None:
                records.append((nozzle_param, rec))
        return records

    def _set_nozzle_pipe_reference(self, elem, pipe_idx: int) -> bool:
        """Set the first available nozzle pipe reference to pipe_idx.

        Returns:
            True if a nozzle was updated, False otherwise.
        """
        pipe_idx_s = str(pipe_idx)
        for _, rec in self._get_nozzle_records(elem):
            if rec.values and str(rec.values[0]) == "0":
                rec.values = [pipe_idx_s, *rec.values[1:]]
                rec.raw_line = ""
                return True
        return False

    def _clear_nozzle_pipe_reference(self, elem, pipe_idx: str) -> bool:
        """Clear the nozzle pipe reference matching pipe_idx.

        Returns:
            True if a nozzle was cleared, False otherwise.
        """
        for _, rec in self._get_nozzle_records(elem):
            if rec.values and str(rec.values[0]) == pipe_idx:
                rec.values = ["0", *rec.values[1:]]
                rec.raw_line = ""
                return True
        return False

    def _update_nozzle_pipe_reference(self, elem, old_idx: str, new_idx: str) -> None:
        """Update nozzle pipe references from old_idx to new_idx."""
        for _, rec in self._get_nozzle_records(elem):
            if rec.values and rec.values[0] == old_idx:
                rec.values = [new_idx, *rec.values[1:]]
                rec.raw_line = ""

    def _get_element_pipe_indices(self, elem) -> list[int]:
        """Get all pipe indices connected to an element."""
        indices = []
        et = elem.etype
        if et in _CON_ELEMENTS:
            rec = elem.get_param("CON")
            if rec and len(rec.values) >= 2:
                for v in rec.values[:2]:
                    if self._is_valid_idx(v):
                        indices.append(int(v))
            else:
                for _, nozzle_rec in self._get_nozzle_records(elem):
                    if nozzle_rec.values and self._is_valid_idx(nozzle_rec.values[0]):
                        indices.append(int(nozzle_rec.values[0]))
        elif et in _NOZ_ELEMENTS:
            noz_param = self._get_nozzle_param(elem)
            rec = elem.get_param(noz_param)
            if rec and rec.values:
                if self._is_valid_idx(rec.values[0]):
                    indices.append(int(rec.values[0]))
        elif et == "TEE":
            rec = elem.get_param("CON")
            if rec:
                for i in [0, 3, 5]:
                    if i < len(rec.values) and self._is_valid_idx(rec.values[i]):
                        indices.append(int(rec.values[i]))
        elif et == "JUNC":
            for rec in elem.records():
                if rec.param in ("NOZI", "NOZO") and len(rec.values) >= 2:
                    if self._is_valid_idx(rec.values[1]):
                        indices.append(int(rec.values[1]))
        elif et == "VESSEL":
            for rec in elem.records():
                if rec.param in ("NOZLI", "NOZLO") and len(rec.values) >= 2:
                    if self._is_valid_idx(rec.values[1]):
                        indices.append(int(rec.values[1]))
        return indices

    def _is_element_connected_to_pipe(self, elem, pipe_idx: int) -> bool:
        """Check if an element is connected to a specific pipe index."""
        indices = self._get_element_pipe_indices(elem)
        return pipe_idx in indices
