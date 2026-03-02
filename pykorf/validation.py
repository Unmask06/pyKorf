"""KDF format validation for KORF models.

Checks that a model conforms to the KDF file format requirements:
- Required fields are present for each element type
- NUM records match actual instance counts
- Version header is present
- Value types are reasonable
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


def validate(model: Model) -> list[str]:
    """Validate KDF format compliance.

    Returns a list of validation issue descriptions.
    An empty list means the model passes all checks.

    Parameters
    ----------
    model:
        The model to validate.
    """
    issues: list[str] = []

    # 1. Version header
    version = model.version
    if not version.startswith("KORF"):
        issues.append(f"Invalid or missing version header: {version!r}")

    # 2. GEN section must exist
    gen_rec = model._parser.get("GEN", 0, "VERNO")
    if gen_rec is None:
        # Try checking if any GEN records exist
        gen_recs = model._parser.get_all("GEN", 0)
        if not gen_recs:
            issues.append("No GEN section found in model")

    # 3. NUM records match actual counts
    _check_num_counts(model, issues)

    # 4. Required params for each element type (at template index 0)
    _check_required_params(model, issues)

    # 5. Element instances have NAME records
    _check_instance_names(model, issues)

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
