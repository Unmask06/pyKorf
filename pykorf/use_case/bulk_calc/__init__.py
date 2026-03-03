"""Bulk calculation tools for copying/pasting properties across pipes.

This module provides utilities for bulk operations on KDF models,
such as copying fluid properties from one pipe to many others.

Example::
    >>> from pykorf import Model
    >>> from pykorf.use_case.bulk_calc import copy_fluids
    >>>
    >>> model = Model("model.kdf")
    >>> # Copy fluid from L1 to all other pipes
    >>> updated = copy_fluids(model, ref_line="L1")
    >>> print(f"Updated {len(updated)} pipes")
    >>>
    >>> # Copy to specific pipes only
    >>> updated = copy_fluids(model, ref_line="L1", target_lines=["L2", "L3", "L4"])
    >>>
    >>> # Copy to all pipes EXCEPT these
    >>> updated = copy_fluids(model, ref_line="L1", target_lines=["L1", "L10"], exclude=True)
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykorf.model import Model

from pykorf.exceptions import ElementNotFound


def copy_fluids(
    model: Model,
    ref_line: str,
    target_lines: list[str] | None = None,
    exclude: bool = False,
) -> list[str]:
    """Copy fluid properties from reference pipe to target pipes.

    This function extracts all fluid properties from a reference pipe
    and applies them to target pipes. Uses the Fluid class for
    consistent property handling.

    Args:
        model: KORF Model instance containing the pipes.
        ref_line: Name of the pipe to copy fluid properties FROM.
        target_lines: List of pipe names to copy TO. If None, copies
            to ALL pipes in the model (except ref_line).
        exclude: If True, copy to ALL pipes EXCEPT those in target_lines.
            target_lines must be provided when exclude=True.

    Returns:
        List of pipe names that were successfully updated.

    Raises:
        ElementNotFound: If the reference pipe (ref_line) doesn't exist.
        ValueError: If exclude=True but target_lines is None.

    Example::
        >>> # Copy to all pipes
        >>> updated = copy_fluids(model, "L1")
        >>>
        >>> # Copy to specific pipes
        >>> updated = copy_fluids(model, "L1", ["L2", "L3"])
        >>>
        >>> # Copy to all except L1 and L10
        >>> updated = copy_fluids(model, "L1", ["L1", "L10"], exclude=True)
    """
    # Validate inputs
    if exclude and target_lines is None:
        raise ValueError("target_lines must be provided when exclude=True")

    # Get reference pipe and extract fluid
    try:
        ref_pipe = model.get_element(ref_line)
    except ElementNotFound as e:
        raise ElementNotFound(f"Reference pipe '{ref_line}' not found in model") from e

    fluid = ref_pipe.get_fluid()

    # Determine target pipes
    all_pipe_names = set()
    for idx, pipe in model.pipes.items():
        if idx == 0:
            continue  # Skip template (index 0)
        if pipe.name:
            all_pipe_names.add(pipe.name)

    if target_lines is None:
        # Copy to all pipes except ref_line
        targets = all_pipe_names - {ref_line}
    elif exclude:
        # Copy to all pipes EXCEPT those in target_lines
        targets = all_pipe_names - set(target_lines)
    else:
        # Copy only to specified pipes
        targets = set(target_lines)

    # Apply fluid to each target pipe
    updated: list[str] = []
    for target_name in sorted(targets):
        # Skip self-copy
        if target_name == ref_line:
            continue

        try:
            target_pipe = model.get_element(target_name)
            target_pipe.set_fluid(fluid)
            updated.append(target_name)
        except ElementNotFound:
            warnings.warn(
                f"Target pipe '{target_name}' not found in model, skipping",
                UserWarning,
                stacklevel=2,
            )

    return updated
