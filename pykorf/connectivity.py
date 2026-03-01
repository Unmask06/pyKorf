"""Connectivity management for KORF models.

Handles connecting and disconnecting elements, and validating
that all connections in a model are consistent.

Connection Model
----------------
In KORF, pipes are the "edges" and equipment/boundaries are "nodes":

- **Equipment** (PUMP, VALVE, CHECK, HX, COMP, MISC, EXPAND, FO):
  Have a ``CON`` record with ``[inlet_pipe_index, outlet_pipe_index]``.
- **Boundaries** (FEED, PROD):
  Have ``NOZL`` (v3.6) or ``NOZ`` (v2.0/3.0) pointing to a pipe index.
- **TEE**: Three connections (combined, main, branch) each referencing
  a pipe index via CON with ``[C_pipe, M_pipe, B_pipe]``.
- **VESSEL**: Multiple nozzle connections via ``NOZLI``/``NOZLO`` records.
- **JUNC**: Multiple pipe connections.
- **PIPE**: Does not have a CON field itself — other elements reference
  pipe indices.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pykorf.exceptions import ConnectivityError

if TYPE_CHECKING:
    from pykorf.model import Model

# Element types that use CON = [inlet_pipe, outlet_pipe]
_CON_ELEMENTS = {"PUMP", "VALVE", "CHECK", "HX", "COMP", "MISC", "EXPAND", "FO"}

# Element types that use NOZL/NOZ = pipe_index (single nozzle)
_NOZ_ELEMENTS = {"FEED", "PROD"}


def _get_nozzle_param(elem) -> str:
    """Return the nozzle param name for a FEED/PROD element."""
    # v3.6 uses NOZL, older versions use NOZ
    if elem._get("NOZL") is not None:
        return "NOZL"
    if elem._get("NOZ") is not None:
        return "NOZ"
    return "NOZL"


def _is_valid_idx(v: Any) -> bool:
    """Return True if v is a non-zero integer string/int."""
    try:
        return int(v) > 0
    except (ValueError, TypeError):
        return False


def _get_nozzle_records(elem) -> list[tuple[str, Any]]:
    """Return existing nozzle records that store pipe indices."""
    records: list[tuple[str, Any]] = []
    for nozzle_param in ("NOZI", "NOZO"):
        rec = elem._get(nozzle_param)
        if rec is not None:
            records.append((nozzle_param, rec))
    return records


def _set_nozzle_pipe_reference(elem, pipe_idx: int) -> bool:
    """Set first free NOZI/NOZO slot to a pipe index."""
    pipe_idx_s = str(pipe_idx)
    for _, rec in _get_nozzle_records(elem):
        if rec.values and str(rec.values[0]) == "0":
            rec.values = [pipe_idx_s] + rec.values[1:]
            rec.raw_line = ""
            return True
    return False


def _clear_nozzle_pipe_reference(elem, pipe_idx: str) -> bool:
    """Clear matching NOZI/NOZO slot for a pipe index."""
    for _, rec in _get_nozzle_records(elem):
        if rec.values and str(rec.values[0]) == pipe_idx:
            rec.values = ["0"] + rec.values[1:]
            rec.raw_line = ""
            return True
    return False


def _update_nozzle_pipe_reference(elem, old_idx: str, new_idx: str) -> None:
    """Update NOZI/NOZO references from old to new pipe index."""
    for _, rec in _get_nozzle_records(elem):
        if rec.values and rec.values[0] == old_idx:
            rec.values = [new_idx] + rec.values[1:]
            rec.raw_line = ""


def get_connections(model: Model, name: str) -> list[str]:
    """Return a list of element names connected to the given element."""
    elem = model.get_element(name)
    connected_names = []

    if elem.etype == "PIPE":
        pipe_idx = elem.index
        # Iterate all other elements to find ones referencing this pipe index
        for other in model.elements:
            if other.etype == "PIPE":
                continue
            if _is_element_connected_to_pipe(other, pipe_idx):
                connected_names.append(other.name)
    else:
        # Get pipe indices connected to this element
        pipe_indices = _get_element_pipe_indices(elem)
        for p_idx in pipe_indices:
            if p_idx in model.pipes:
                connected_names.append(model.pipes[p_idx].name)

    return sorted(list(set(connected_names)))


def get_unconnected_elements(model: Model) -> list[str]:
    """Return names of elements that have at least one open connection.

    - For pipes: connected to < 2 nodes.
    - For equipment/TEEs/Junctions: have at least one '0' in their connection slots.
    """
    unconnected = []

    # Pipes need two connections
    for pipe in model.get_elements_by_type("PIPE"):
        conns = get_connections(model, pipe.name)
        if len(conns) < 2:
            unconnected.append(pipe.name)

    # Nodes with open slots
    for elem in model.elements:
        if elem.etype == "PIPE":
            continue

        et = elem.etype
        if et in _CON_ELEMENTS:
            rec = elem._get("CON")
            if rec and (str(rec.values[0]) == "0" or str(rec.values[1]) == "0"):
                unconnected.append(elem.name)
            elif rec is None:
                nozzle_recs = _get_nozzle_records(elem)
                if nozzle_recs and any(
                    not nozzle_rec.values or str(nozzle_rec.values[0]) == "0"
                    for _, nozzle_rec in nozzle_recs
                ):
                    unconnected.append(elem.name)
        elif et in _NOZ_ELEMENTS:
            noz_param = _get_nozzle_param(elem)
            rec = elem._get(noz_param)
            if rec and str(rec.values[0]) == "0":
                unconnected.append(elem.name)
        elif et == "TEE":
            rec = elem._get("CON")
            if rec:
                # TEE slots 0, 3, 5
                for i in [0, 3, 5]:
                    if i < len(rec.values) and str(rec.values[i]) == "0":
                        unconnected.append(elem.name)
                        break
        # JUNC and VESSEL can have arbitrary number of nozzles, so they are
        # "unconnected" if they have 0 connections? Or if they have defined nozzles
        # that are 0.
        elif et in ("JUNC", "VESSEL"):
            pipe_indices = _get_element_pipe_indices(elem)
            if not pipe_indices:
                unconnected.append(elem.name)

    return sorted(list(set(unconnected)))


def _get_element_pipe_indices(elem) -> list[int]:
    """Extract all non-zero pipe indices referenced by an element."""
    indices = []
    et = elem.etype
    if et in _CON_ELEMENTS:
        rec = elem._get("CON")
        if rec and len(rec.values) >= 2:
            for v in rec.values[:2]:
                if _is_valid_idx(v):
                    indices.append(int(v))
        else:
            # Some KDF files store HX/MISC nozzle links as NOZI/NOZO
            # instead of CON. Keep extraction tolerant to both formats.
            for _, nozzle_rec in _get_nozzle_records(elem):
                if nozzle_rec.values and _is_valid_idx(nozzle_rec.values[0]):
                    indices.append(int(nozzle_rec.values[0]))
    elif et in _NOZ_ELEMENTS:
        noz_param = _get_nozzle_param(elem)
        rec = elem._get(noz_param)
        if rec and rec.values:
            if _is_valid_idx(rec.values[0]):
                indices.append(int(rec.values[0]))
    elif et == "TEE":
        rec = elem._get("CON")
        if rec:
            # Check slots 0, 3, 5 based on KDF analysis
            for i in [0, 3, 5]:
                if i < len(rec.values) and _is_valid_idx(rec.values[i]):
                    indices.append(int(rec.values[i]))
    elif et == "JUNC":
        for rec in elem.records():
            if rec.param in ("NOZI", "NOZO") and len(rec.values) >= 2:
                if _is_valid_idx(rec.values[1]):
                    indices.append(int(rec.values[1]))
    elif et == "VESSEL":
        for rec in elem.records():
            if rec.param in ("NOZLI", "NOZLO") and len(rec.values) >= 2:
                if _is_valid_idx(rec.values[1]):
                    indices.append(int(rec.values[1]))
    return indices


def _is_element_connected_to_pipe(elem, pipe_idx: int) -> bool:
    """Return True if the element references the given pipe index."""
    indices = _get_element_pipe_indices(elem)
    return pipe_idx in indices


def update_pipe_references(model: Model, old_idx: int, new_idx: int) -> None:
    """Find all elements referencing old_idx and update them to new_idx."""
    old_s = str(old_idx)
    new_s = str(new_idx)

    for elem in model.elements:
        if elem.etype == "PIPE":
            continue

        et = elem.etype
        if et in _CON_ELEMENTS:
            rec = elem._get("CON")
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
                _update_nozzle_pipe_reference(elem, old_s, new_s)
        elif et in _NOZ_ELEMENTS:
            noz_param = _get_nozzle_param(elem)
            rec = elem._get(noz_param)
            if rec and rec.values and rec.values[0] == old_s:
                rec.values = [new_s] + rec.values[1:]
                rec.raw_line = ""
        elif et == "TEE":
            rec = elem._get("CON")
            if rec:
                vals = list(rec.values)
                changed = False
                for i in [0, 1, 2, 3, 4, 5]:  # Check all 6 slots in TEE CON
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


def connect(model: Model, name1: str, name2: str) -> None:
    """Connect two elements in the model.

    One of the elements must be a PIPE.  The other element's CON or
    NOZ/NOZL field is updated to reference the pipe's index.

    Parameters
    ----------
    model:
        The model containing both elements.
    name1, name2:
        Element names.  At least one must be a PIPE.

    Raises:
    ------
    ConnectivityError
        If neither element is a PIPE, or the connection is invalid.
    """
    elem1 = model.get_element(name1)
    elem2 = model.get_element(name2)

    # Determine which is the pipe and which is the equipment/boundary
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
        rec = other_elem._get("CON")
        if rec is None:
            if _set_nozzle_pipe_reference(other_elem, pipe_idx):
                return
            raise ConnectivityError(
                f"{other_elem.name} ({et}) has no CON/NOZI/NOZO record"
            )
        vals = list(rec.values)
        # Find first empty slot (0 means unconnected)
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
        noz_param = _get_nozzle_param(other_elem)
        rec = other_elem._get(noz_param)
        if rec is not None:
            rec.values = [str(pipe_idx)] + rec.values[1:]
            rec.raw_line = ""
        else:
            model._parser.set_value(et, other_elem.index, noz_param, [str(pipe_idx)])

    elif et == "TEE":
        rec = other_elem._get("CON")
        if rec is None:
            raise ConnectivityError(f"{other_elem.name} (TEE) has no CON record")
        vals = list(rec.values)
        # TEE has 3 slots for pipe indices: Combined(0), Main(3), Branch(5)
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


def disconnect(model: Model, name1: str, name2: str) -> None:
    """Disconnect two elements.

    Clears the pipe reference in the equipment/boundary element's
    CON or NOZ/NOZL field.

    Raises:
    ------
    ConnectivityError
        If the elements are not currently connected.
    """
    elem1 = model.get_element(name1)
    elem2 = model.get_element(name2)

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
        rec = other_elem._get("CON")
        if rec is None:
            if _clear_nozzle_pipe_reference(other_elem, pipe_idx):
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
        noz_param = _get_nozzle_param(other_elem)
        rec = other_elem._get(noz_param)
        if rec is None or str(rec.values[0]) != pipe_idx:
            raise ConnectivityError(
                f"{other_elem.name} is not connected to pipe {pipe_elem.name}"
            )
        rec.values = ["0"] + rec.values[1:]
        rec.raw_line = ""

    elif et == "TEE":
        rec = other_elem._get("CON")
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


def check_connectivity(model: Model) -> list[str]:
    """Check all element connections for consistency.

    Returns a list of issue descriptions.  An empty list means all
    connections are valid.
    """
    issues: list[str] = []
    pipe_indices = {idx for idx in model.pipes if idx >= 1}

    # Check equipment CON references
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
        collection = getattr(model, collection_attr, {})
        for idx, elem in collection.items():
            if idx == 0:
                continue
            rec = elem._get("CON")
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

            nozzle_recs = _get_nozzle_records(elem)
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

    # Check FEED/PROD nozzle references
    for collection_attr in ("feeds", "products"):
        collection = getattr(model, collection_attr, {})
        for idx, elem in collection.items():
            if idx == 0:
                continue
            noz_param = _get_nozzle_param(elem)
            rec = elem._get(noz_param)
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

    # Check TEE connections
    for idx, elem in model.tees.items():
        if idx == 0:
            continue
        rec = elem._get("CON")
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
                    f"{elem.name} (TEE): {label} CON value "
                    f"{rec.values[i]!r} is not a valid integer"
                )
                continue
            if pipe_ref != 0 and pipe_ref not in pipe_indices:
                issues.append(
                    f"{elem.name} (TEE): {label} references pipe index "
                    f"{pipe_ref} which does not exist"
                )

    return issues
