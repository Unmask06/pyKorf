"""PMS (Piping Material Specification) reader and pipe parameter builder.

This module is the single entry point for PMS-based pipe processing.
It loads PMS data from JSON (or Excel), reads pipe NOTES to extract
line numbers, looks up schedule/material, and returns parameter dicts
suitable for ``model.set_params()``.

Main function:
    ``apply_pms(pms_source, model)`` → ``{pipe_name: {PARAM: value}}``

Lower-level functions:
    ``load_pms(source)`` → ``(material, {pms_code: {nps: schedule}})``
    ``lookup_schedule(pms_data, pms_code, nps)`` → schedule string
    ``convert_pms_excel(excel_path)`` → json_path

Example:
    ```python
    from pykorf import Model
    from pykorf.use_case.pms import apply_pms

    model = Model("model.kdf")
    updates = apply_pms("Consolidated PMS.json", model)
    for ename, params in updates.items():
        model.set_params(ename, params)
    model.save()
    ```
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pykorf.elements import Pipe
from pykorf.use_case.exceptions import (
    ExcelConversionError,
    LineNumberParseError,
    PmsLookupError,
)
from pykorf.use_case.line_number import LineNumber

if TYPE_CHECKING:
    from pykorf.model import Model

logger = logging.getLogger(__name__)

DEFAULT_MATERIAL = "Steel"
DEFAULT_ROUGHNESS_MM = 0.046

# Type alias for the loaded PMS data structure:
# {pms_code: {nominal_size_inches: {"schedule": str} | {"wall_mm": float}}}
PmsData = dict[str, dict[float, dict[str, Any]]]

# Type alias for OD data: {nominal_size_inches: od_mm}
OdData = dict[float, float]

# Type alias for PMS lookup result: (OD_mm, "ID" or "SCH", value, material)
# Value is float for ID (inches), str for SCH (schedule number/name)
PmsLookupResult = tuple[float, str, float | str, str]


def convert_pms_excel(
    excel_path: Path | str,
    json_path: Path | str | None = None,
) -> Path:
    """Convert a PMS Excel file to JSON format.

    Reads all sheets from the Excel file and converts them directly
    to JSON without any data manipulation. Each sheet becomes a material,
    with PMS codes as keys and schedule values as nested objects.

    Output format:
        {material: {specifications: {PMS_code: {nominal_size: value}}}}

    Args:
        excel_path: Path to the PMS Excel file.
        json_path: Output path. Defaults to *excel_path* with ``.json`` suffix.

    Returns:
        Path to the created JSON file.

    Raises:
        ExcelConversionError: If pandas is not installed or conversion fails.
    """
    try:
        import pandas as pd
    except ImportError:
        raise ExcelConversionError("pandas is required for Excel conversion")

    from pykorf.utils import read_excel_safe

    excel_path = Path(excel_path)
    if json_path is None:
        json_path = excel_path.with_suffix(".json")
    else:
        json_path = Path(json_path)

    sheets = read_excel_safe(excel_path, sheet_name=None, header=None)
    all_materials_data: dict[str, Any] = {}

    for sheet_name, df in sheets.items():
        material = str(sheet_name).strip()
        specifications: dict[str, dict[str, Any]] = {}
        nominal_sizes: list[str] = []

        for _idx, row in df.iterrows():
            first_cell = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
            if not first_cell:
                continue

            if first_cell.upper() == "PMS":
                nominal_sizes = []
                for col_idx in range(1, len(row)):
                    val = row.iloc[col_idx]
                    if pd.notna(val):
                        nominal_sizes.append(str(val).strip())
            else:
                pms_code = first_cell
                specs: dict[str, Any] = {}

                for col_idx in range(1, len(nominal_sizes) + 1):
                    if col_idx < len(row):
                        nominal_size = nominal_sizes[col_idx - 1]
                        val = row.iloc[col_idx]
                        if pd.notna(val):
                            specs[nominal_size] = str(val).strip()

                specifications[pms_code] = specs

        all_materials_data[material] = {"specifications": specifications}

    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_materials_data, f, indent=2)

    return json_path


def load_pms(source: Path | str, material: str | None = None) -> tuple[str, PmsData, OdData]:
    """Load PMS data from a JSON file (or Excel, auto-converting first).

    Args:
        source: Path to PMS ``.json`` or ``.xlsx`` file.
        material: Material name to load. If None, uses the first material found.

    Returns:
        ``(material, pms_data, od_data)`` where *pms_data* maps
        ``pms_code → {nominal_size_inches → {"schedule": str} | {"wall_mm": float}}``
        and *od_data* maps ``nominal_size_inches → od_mm``.
    """
    source = Path(source)

    if source.suffix.lower() == ".xlsx":
        json_path = source.with_suffix(".json")
        if not json_path.exists():
            convert_pms_excel(source, json_path)
        source = json_path

    with open(source, encoding="utf-8") as f:
        data = json.load(f)

    # Handle new format: {material: {"specifications": {...}, "od": {...}}}
    if (
        "specifications" not in data
        and len(data) > 0
        and isinstance(list(data.values())[0], dict)
        and "specifications" in list(data.values())[0]
    ):
        available_materials = list(data.keys())
        if not available_materials:
            return DEFAULT_MATERIAL, {}, {}

        selected_material = material if material else available_materials[0]
        if selected_material not in data:
            selected_material = available_materials[0]

        material_entry = data[selected_material]
        specifications = material_entry.get("specifications", {})
        od_data = {float(k): v for k, v in material_entry.get("od", {}).items()}
    elif "specifications" in data:
        # Legacy format: {"material": "...", "specifications": {...}}
        selected_material = data.get("material", DEFAULT_MATERIAL)
        specifications = data.get("specifications", {})
        od_data = {}
    else:
        # Old new format without od
        available_materials = list(data.keys())
        if not available_materials:
            return DEFAULT_MATERIAL, {}, {}

        selected_material = material if material else available_materials[0]
        if selected_material not in data:
            selected_material = available_materials[0]

        specifications = data[selected_material]
        od_data = {}

    pms_data: PmsData = {}
    for pms_code, size_specs in specifications.items():
        pms_data[pms_code] = {}
        for size_str, spec_info in size_specs.items():
            try:
                size = float(size_str)
            except (ValueError, TypeError):
                continue
            # Handle both old format (dict) and new format (string)
            if isinstance(spec_info, dict):
                pms_data[pms_code][size] = spec_info
            else:
                # New format: store string value directly
                pms_data[pms_code][size] = {"value": str(spec_info)}

    return selected_material, pms_data, od_data


def load_all_pms(source: Path | str) -> dict[str, tuple[str, PmsData, OdData]]:
    """Load PMS data for all materials from a JSON file.

    Args:
        source: Path to PMS ``.json`` or ``.xlsx`` file.

    Returns:
        Dictionary mapping material names to ``(material, pms_data, od_data)`` tuples.
    """
    source = Path(source)

    if source.suffix.lower() == ".xlsx":
        json_path = source.with_suffix(".json")
        if not json_path.exists():
            convert_pms_excel(source, json_path)
        source = json_path

    with open(source, encoding="utf-8") as f:
        data = json.load(f)

    all_materials: dict[str, tuple[str, PmsData, OdData]] = {}

    # Handle new format: {material: {"specifications": {...}}}
    if (
        "specifications" not in data
        and len(data) > 0
        and isinstance(list(data.values())[0], dict)
        and "specifications" in list(data.values())[0]
    ):
        for material_name in data.keys():
            material, pms_data, od_data = load_pms(source, material_name)
            all_materials[material_name] = (material, pms_data, od_data)
    else:
        # Legacy format - load as single material
        material, pms_data, od_data = load_pms(source)
        all_materials[material] = (material, pms_data, od_data)

    return all_materials


def lookup_pms_across_materials(
    all_materials: dict[str, tuple[str, PmsData, OdData]],
    pms_code: str,
    nominal_size: float,
) -> tuple[str, dict[str, Any], float]:
    """Look up PMS code across all materials.

    Args:
        all_materials: Dictionary from load_all_pms().
        pms_code: PMS class code to look up.
        nominal_size: Nominal pipe size in inches.

    Returns:
        Tuple of (material, spec, od_mm).

    Raises:
        PmsLookupError: If PMS code not found in any material.
    """
    for material_name, (material, pms_data, _) in all_materials.items():
        if pms_code in pms_data:
            spec = lookup_schedule(pms_data, pms_code, nominal_size)
            # Get OD from the "OD" entry
            if "OD" in pms_data:
                od_spec = lookup_schedule(pms_data, "OD", nominal_size)
                od_mm = float(od_spec.get("value", 0))
            else:
                od_mm = 0.0
            return material, spec, od_mm

    raise PmsLookupError(f"PMS class not found: {pms_code}")


def _calc_id(od_mm: float, wall_mm: float) -> float:
    """Calculate inner diameter from outer diameter and wall thickness.

    Args:
        od_mm: Outer diameter in mm.
        wall_mm: Wall thickness in mm.

    Returns:
        Inner diameter in mm.
    """
    id_mm = od_mm - 2 * wall_mm
    return id_mm


def get_pms_data(
    od_mm: float,
    pms_value: str,
    material: str = DEFAULT_MATERIAL,
) -> PmsLookupResult:
    """Get PMS data with calculated ID or schedule value.

    Parses the PMS value and returns the appropriate data format.
    If value contains "mm", calculates ID from OD and wall thickness.
    If value contains "SCH", extracts the schedule number.

    Args:
        od_mm: Outer diameter in mm.
        pms_value: Raw PMS value from JSON (e.g., "5 mm", "SCH 80", "STD").
        material: Material name (default: "Steel").

    Returns:
        Tuple of (OD_mm, "ID" or "SCH", value, material).
        Value is ID in mm if "mm" was found, or schedule number if "SCH" was found.
    """
    val = pms_value.strip()

    # Check for wall thickness in mm
    if "mm" in val.lower():
        # Extract numeric wall thickness
        wall_str = val.lower().replace("mm", "").strip()
        try:
            wall_mm = float(wall_str)
            id_mm = _calc_id(od_mm, wall_mm)
            return (od_mm, "ID", id_mm, material)
        except (ValueError, TypeError):
            pass

    # Check for SCH prefix
    if val.upper().startswith("SCH"):
        schedule = val[3:].strip()
        return (od_mm, "SCH", schedule, material)

    # Default: treat as schedule value directly
    return (od_mm, "SCH", val, material)


def lookup_schedule(
    pms_data: PmsData,
    pms_code: str,
    nominal_size: float,
) -> dict[str, Any]:
    """Look up pipe schedule/wall thickness by PMS code and nominal pipe size.

    Falls back to the closest available size when an exact match is
    not found.

    Args:
        pms_data: Loaded PMS data (from :func:`load_pms`).
        pms_code: PMS class code (e.g. ``"BC1A1B-FDA"``).
        nominal_size: Nominal pipe size in inches.

    Returns:
        Dict with either {"schedule": str} or {"wall_mm": float}.

    Raises:
        PmsLookupError: If the PMS class is not found or has no sizes.
    """
    if pms_code not in pms_data:
        raise PmsLookupError(f"PMS class not found: {pms_code}")

    sizes = pms_data[pms_code]
    if not sizes:
        raise PmsLookupError(f"No sizes defined for PMS class: {pms_code}")

    if nominal_size in sizes:
        return sizes[nominal_size]

    closest = min(sizes.keys(), key=lambda x: abs(x - nominal_size))
    return sizes[closest]


def apply_pms(
    pms_source: Path | str,
    model: Model,
    *,
    delimiter: str = ";",
    roughness_mm: float = DEFAULT_ROUGHNESS_MM,
    save: bool = True,
) -> list[str]:
    """Apply PMS specifications to all pipes in *model*.

    For each pipe whose ``NOTES`` field contains a valid line number,
    this function parses the line number, looks up the PMS specification,
    and applies the parameters directly to the pipe using ``model.set_params()``.

    Pipes with empty NOTES are silently skipped.

    Args:
        pms_source: Path to PMS JSON (or Excel) file.
        model: Loaded :class:`~pykorf.model.Model`.
        delimiter: NOTES field delimiter (default ``";"``).
        roughness_mm: Default pipe roughness in mm.
        save: Whether to save the model after applying changes (default ``True``).

    Returns:
        List of pipe names that were updated.

    Raises:
        LineNumberParseError: If NOTES contains an unparseable line number.
        PmsLookupError: If the PMS class from the line number is not found.

    Example:
        ```python
        from pykorf import Model
        from pykorf.use_case.pms import apply_pms

        model = Model("model.kdf")
        updated_pipes = apply_pms("Consolidated PMS.json", model)
        print(f"Updated {len(updated_pipes)} pipes with PMS specifications")
        ```
    """
    all_materials = load_all_pms(pms_source)
    roughness_m = roughness_mm / 1000.0
    updated_pipes: list[str] = []

    for idx in range(1, model.num_pipes + 1):
        pipe = model.pipes[idx]
        notes = pipe.notes

        if not notes or not notes.strip():
            logger.debug("Pipe %s: empty NOTES, skipping PMS", pipe.name)
            continue

        try:
            line_num = LineNumber.parse(notes, delimiter)

            if line_num is None:
                logger.warning(
                    "Pipe %s: cannot parse line number from NOTES: %r, skipping",
                    pipe.name,
                    notes,
                )
                continue

            nps = line_num.nominal_pipe_size
            pms_code = line_num.pms_code

            # Look up PMS code across all materials
            material, spec, od_mm = lookup_pms_across_materials(all_materials, pms_code, float(nps))

            # Get the raw PMS value from the spec
            pms_value = spec.get("value", "")

            # Use get_pms_data to process the value
            _, id_or_sch, value, _ = get_pms_data(od_mm, pms_value, material)

            nps_str = str(nps)

            if id_or_sch == "ID":
                # Wall thickness in mm - use calculated ID (convert mm to meters)
                id_meters = float(value) / 1000.0
                params: dict[str, Any] = {
                    Pipe.MAT: material,
                    Pipe.ROUGHNESS: [str(roughness_m), str(roughness_m), "m"],
                    Pipe.SCH: "ID",
                    Pipe.ID: [str(id_meters), str(id_meters), "m"],
                }
                logger.info(
                    "Pipe %s: NPS=%d, PMS=%s -> ID=%.6f m, MAT=%s",
                    pipe.name,
                    nps,
                    pms_code,
                    id_meters,
                    material,
                )
            else:
                # Standard schedule
                params: dict[str, Any] = {
                    Pipe.DIA: [nps_str, nps_str, "inch"],
                    Pipe.MAT: material,
                    Pipe.ROUGHNESS: [str(roughness_m), str(roughness_m), "m"],
                    Pipe.SCH: value,
                }
                logger.info(
                    "Pipe %s: NPS=%d, PMS=%s -> SCH=%s, MAT=%s",
                    pipe.name,
                    nps,
                    pms_code,
                    value,
                    material,
                )

            # Apply params directly to the pipe
            model.set_params(pipe.name, params)
            updated_pipes.append(pipe.name)

        except (LineNumberParseError, PmsLookupError) as exc:
            logger.warning("Pipe %s: %s, skipping", pipe.name, exc)
            continue
        except Exception as exc:
            logger.error("Pipe %s: unexpected error: %s, skipping", pipe.name, exc)
            continue

    if save and updated_pipes:
        model.save()

    return updated_pipes
