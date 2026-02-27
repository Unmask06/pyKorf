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

from typing import TYPE_CHECKING

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

    Raises
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
            raise ConnectivityError(
                f"{other_elem.name} ({et}) has no CON record"
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
        # TEE has 3 slots: combined, main, branch
        placed = False
        for i in range(min(3, len(vals))):
            if str(vals[i]) == "0":
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
        raise ConnectivityError(
            f"Don't know how to connect a PIPE to {et}"
        )


def disconnect(model: Model, name1: str, name2: str) -> None:
    """Disconnect two elements.

    Clears the pipe reference in the equipment/boundary element's
    CON or NOZ/NOZL field.

    Raises
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
            raise ConnectivityError(f"{other_elem.name} ({et}) has no CON record")
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
        for i in range(min(3, len(vals))):
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
    for collection_attr in ("valves", "check_valves", "orifices", "exchangers",
                            "pumps", "compressors", "misc_equipment", "expanders"):
        collection = getattr(model, collection_attr, {})
        for idx, elem in collection.items():
            if idx == 0:
                continue
            rec = elem._get("CON")
            if rec is None:
                continue
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
