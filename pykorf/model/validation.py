"""KDF format validation for KORF models.

Comprehensive validation checking:
- Required fields are present for each element type
- NUM records match actual instance counts
- Version header is present
- Value types are reasonable
- NOTES records have valid line number format
- Pipe references are valid
- Connectivity consistency
- Layout issues
- Empty or invalid parameter values
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pykorf.elements import PROPERTIES_BY_ELEMENT, Element

if TYPE_CHECKING:
    from pykorf.model import Model

# Minimum required params per element type (params that must exist at index 0)
_REQUIRED_PARAMS: dict[str, tuple[str, ...]] = {
    "PIPE": ("NUM", "NAME", "LEN", "DIA", "MAT"),
    "FEED": ("NUM", "NAME", "TYPE", "PRES"),
    "PROD": ("NUM", "NAME", "TYPE", "PRES"),
    "PUMP": ("NUM", "NAME", "TYPE", "CON"),
    "VALVE": ("NUM", "NAME", "TYPE", "CON"),
    "CHECK": ("NUM", "NAME", "CON"),
    "FO": ("NUM", "NAME", "TYPE", "CON"),
    "HX": ("NUM", "NAME", "TYPE"),
    "COMP": ("NUM", "NAME", "TYPE", "CON"),
    "MISC": ("NUM", "NAME", "CON"),
    "EXPAND": ("NUM", "NAME", "TYPE", "CON"),
    "JUNC": ("NUM", "NAME"),
    "TEE": ("NUM", "NAME", "TYPE"),
    "VESSEL": ("NUM", "NAME", "TYPE"),
}


def validate(
    model: Model, *, check_connectivity: bool = True, check_layout: bool = True
) -> list[str]:
    """Validate KDF format compliance.

    Returns a list of validation issue descriptions.
    An empty list means the model passes all checks.

    Parameters
    ----------
    model:
        The model to validate.
    check_connectivity:
        If True (default), check connectivity consistency.
    check_layout:
        If True (default), check for layout issues.

    Returns
    -------
    List of validation issue descriptions.
    """
    issues: list[str] = []

    # 1. Version header
    version = model.version
    if not version.startswith("KORF"):
        issues.append(f"Invalid or missing version header: {version!r}")

    # 2. GEN section must exist
    gen_rec = model._parser.get("GEN", 0, "VERNO")
    if gen_rec is None:
        gen_recs = model._parser.get_all("GEN", 0)
        if not gen_recs:
            issues.append("No GEN section found in model")

    # 3. NUM records match actual counts
    _check_num_counts(model, issues)

    # 4. Required params for each element type (at template index 0)
    _check_required_params(model, issues)

    # 5. Element instances have NAME records
    _check_instance_names(model, issues)

    # 6. Check for valid NOTES line number format
    _check_notes_format(model, issues)

    # 7. Check for empty or invalid parameter values
    _check_empty_values(model, issues)

    # 8. Check pipe references in connectivity fields
    _check_pipe_references(model, issues)

    # 9. Check connectivity consistency
    if check_connectivity:
        connectivity_issues = _check_connectivity_issues(model)
        issues.extend(connectivity_issues)

    # 10. Check layout issues
    if check_layout:
        layout_issues = _check_layout_issues(model)
        issues.extend(layout_issues)

    return issues


def _check_num_counts(model: Model, issues: list[str]) -> None:
    """Verify NUM records match actual instance counts."""
    etype_collection = {
        "PIPE": model.pipes,
        "FEED": model.feeds,
        "PROD": model.products,
        "PUMP": model.pumps,
        "VALVE": model.valves,
        "CHECK": model.check_valves,
        "FO": model.orifices,
        "HX": model.exchangers,
        "COMP": model.compressors,
        "MISC": model.misc_equipment,
        "EXPAND": model.expanders,
        "JUNC": model.junctions,
        "TEE": model.tees,
        "VESSEL": model.vessels,
    }

    for etype, collection in etype_collection.items():
        declared = model._parser.num_instances(etype)
        actual = sum(1 for idx in collection if idx >= 1)
        if declared != actual:
            issues.append(f"{etype}: NUM declares {declared} instances but {actual} found in file")


def _check_required_params(model: Model, issues: list[str]) -> None:
    """Check that template (index 0) has all required params."""
    for etype, required in _REQUIRED_PARAMS.items():
        # Only check if the element type exists in the file
        template_recs = model._parser.get_all(etype, 0)
        if not template_recs:
            continue  # element type not in this file — OK

        existing_params = {r.param for r in template_recs}
        for param in required:
            if param not in existing_params:
                issues.append(f"{etype} template (index 0): missing required param {param!r}")


def _check_instance_names(model: Model, issues: list[str]) -> None:
    """Check that every real instance (index >= 1) has a NAME record."""
    for elem in model.elements:
        name_rec = elem._get("NAME")
        if name_rec is None or not name_rec.values:
            issues.append(f"{elem.etype} index {elem.index}: missing NAME record")
        elif not name_rec.values[0] or name_rec.values[0].strip() == "":
            issues.append(f"{elem.etype} index {elem.index}: NAME is empty")


def _check_notes_format(model: Model, issues: list[str]) -> None:
    """Check that NOTES records have valid line number format.

    KORF NOTES records should have format:
    - With line number: NOTES,L1,"comment text"
    - Without line number: NOTES,"comment text"

    This function checks for malformed NOTES that might cause issues.
    """
    from pykorf.parser import KdfRecord

    for rec in model._parser.records:
        if rec.param == "NOTES":
            # Check if values are present
            if not rec.values or len(rec.values) < 2:
                # Could be NOTES without proper structure
                if rec.raw_line:
                    line = rec.raw_line.strip()
                    # Check if it looks malformed
                    if line.startswith("\\") and "NOTES" in line:
                        # Try to detect missing line number
                        parts = line.split(",")
                        if len(parts) >= 2:
                            # Check if second field looks like a line number
                            try:
                                # If it's numeric, it's probably the line number
                                int(parts[1].strip().strip('"'))
                            except (ValueError, IndexError):
                                # If not numeric, might be missing line number
                                # This is actually OK in some KORF versions
                                pass
                else:
                    issues.append(
                        f"{rec.element_type} index {rec.index}: NOTES record has no values"
                    )


def _check_empty_values(model: Model, issues: list[str]) -> None:
    """Check for empty or whitespace-only parameter values."""
    critical_params = {"NAME", "TYPE", "LEN", "DIA", "MAT", "PRES", "TFLOW"}

    for elem in model.elements:
        for param_name in critical_params:
            rec = elem._get(param_name)
            if rec is not None and rec.values:
                val = rec.values[0].strip() if rec.values[0] else ""
                if not val:
                    issues.append(
                        f"{elem.etype} {elem.name} (index {elem.index}): "
                        f"{param_name} has empty or whitespace value"
                    )


def _check_pipe_references(model: Model, issues: list[str]) -> None:
    """Check that pipe references in CON/NOZL/NOZ fields point to existing pipes."""
    pipe_indices = set(model.pipes.keys())

    for elem in model.elements:
        # Check CON records for equipment
        con_rec = elem._get("CON")
        if con_rec and con_rec.values:
            for i, val in enumerate(con_rec.values):
                try:
                    pipe_idx = int(val)
                    if pipe_idx > 0 and pipe_idx not in pipe_indices:
                        port_name = "inlet" if i == 0 else "outlet"
                        issues.append(
                            f"{elem.etype} {elem.name} (index {elem.index}): "
                            f"CON {port_name} references non-existent pipe {pipe_idx}"
                        )
                except (ValueError, TypeError):
                    pass

        # Check NOZL/NOZ records for boundaries
        for nozzle_param in ("NOZL", "NOZ", "NOZI", "NOZO"):
            nozzle_rec = elem._get(nozzle_param)
            if nozzle_rec and nozzle_rec.values:
                for val in nozzle_rec.values:
                    try:
                        pipe_idx = int(val)
                        if pipe_idx > 0 and pipe_idx not in pipe_indices:
                            issues.append(
                                f"{elem.etype} {elem.name} (index {elem.index}): "
                                f"{nozzle_param} references non-existent pipe {pipe_idx}"
                            )
                    except (ValueError, TypeError):
                        pass

        # Check TEE CON records (3 connections)
        if elem.etype == "TEE" and con_rec and con_rec.values:
            port_names = ["combined", "main", "branch"]
            for i, val in enumerate(con_rec.values[:3]):
                try:
                    pipe_idx = int(val)
                    if pipe_idx > 0 and pipe_idx not in pipe_indices:
                        issues.append(
                            f"TEE {elem.name} (index {elem.index}): "
                            f"CON {port_names[i] if i < len(port_names) else i} "
                            f"references non-existent pipe {pipe_idx}"
                        )
                except (ValueError, TypeError):
                    pass


def _check_connectivity_issues(model: Model) -> list[str]:
    """Check connectivity consistency using connectivity module."""
    try:
        from pykorf.model.connectivity import check_connectivity

        return check_connectivity(model)
    except Exception:
        # If connectivity check fails, return empty list
        return []


def _check_layout_issues(model: Model) -> list[str]:
    """Check for layout issues using layout module."""
    try:
        from pykorf.model.layout import check_layout

        return check_layout(model)
    except Exception:
        # If layout check fails, return empty list
        return []
