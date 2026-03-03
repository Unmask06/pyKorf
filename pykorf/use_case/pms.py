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
# {pms_code: {nominal_size_inches: schedule_string}}
PmsData = dict[str, dict[float, str]]


def convert_pms_excel(
    excel_path: Path | str,
    json_path: Path | str | None = None,
    sheet_name: str = "Steel",
    material: str = DEFAULT_MATERIAL,
) -> Path:
    """Convert a PMS Excel file to JSON format.

    Args:
        excel_path: Path to the PMS Excel file.
        json_path: Output path.  Defaults to *excel_path* with ``.json`` suffix.
        sheet_name: Worksheet name to read.
        material: Material label to embed in the JSON.

    Returns:
        Path to the created JSON file.

    Raises:
        ExcelConversionError: If pandas is not installed or conversion fails.
    """
    try:
        import pandas as pd
    except ImportError:
        raise ExcelConversionError("pandas is required for Excel conversion")

    excel_path = Path(excel_path)
    if json_path is None:
        json_path = excel_path.with_suffix(".json")
    else:
        json_path = Path(json_path)

    df = pd.read_excel(excel_path, sheet_name=sheet_name, header=None)

    pms_json: dict[str, Any] = {"material": material, "specifications": {}}
    nominal_sizes: list[float] = []

    for _idx, row in df.iterrows():
        first_cell = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
        if not first_cell:
            continue

        if first_cell.upper() == "PMS":
            nominal_sizes = []
            for col_idx in range(1, len(row)):
                val = row.iloc[col_idx]
                if pd.notna(val):
                    try:
                        nominal_sizes.append(float(val))
                    except (ValueError, TypeError):
                        pass
        else:
            pms_code = first_cell
            specs: dict[float, dict[str, Any]] = {}

            for col_idx in range(1, len(nominal_sizes) + 1):
                if col_idx < len(row):
                    nominal_size = nominal_sizes[col_idx - 1]
                    val = row.iloc[col_idx]
                    if pd.notna(val):
                        val_str = str(val).strip()
                        if val_str.upper().startswith("SCH"):
                            schedule = val_str.replace("SCH", "").strip()
                            specs[nominal_size] = {"schedule": schedule}

            pms_json["specifications"][pms_code] = specs

    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(pms_json, f, indent=2)

    return json_path


def load_pms(source: Path | str) -> tuple[str, PmsData]:
    """Load PMS data from a JSON file (or Excel, auto-converting first).

    Args:
        source: Path to PMS ``.json`` or ``.xlsx`` file.

    Returns:
        ``(material, pms_data)`` where *pms_data* maps
        ``pms_code → {nominal_size_inches → schedule_string}``.
    """
    source = Path(source)

    if source.suffix.lower() == ".xlsx":
        json_path = source.with_suffix(".json")
        if not json_path.exists():
            convert_pms_excel(source, json_path)
        source = json_path

    with open(source, encoding="utf-8") as f:
        data = json.load(f)

    material: str = data.get("material", DEFAULT_MATERIAL)
    pms_data: PmsData = {}

    for pms_code, size_specs in data.get("specifications", {}).items():
        pms_data[pms_code] = {}
        for size_str, spec_info in size_specs.items():
            try:
                size = float(size_str)
            except (ValueError, TypeError):
                continue
            pms_data[pms_code][size] = spec_info.get("schedule", "STD")

    return material, pms_data


def lookup_schedule(
    pms_data: PmsData,
    pms_code: str,
    nominal_size: float,
) -> str:
    """Look up pipe schedule by PMS code and nominal pipe size.

    Falls back to the closest available size when an exact match is
    not found.

    Args:
        pms_data: Loaded PMS data (from :func:`load_pms`).
        pms_code: PMS class code (e.g. ``"BC1A1B-FDA"``).
        nominal_size: Nominal pipe size in inches.

    Returns:
        Schedule string (e.g. ``"40"``, ``"STD"``, ``"80"``).

    Raises:
        PmsLookupError: If the PMS code is not found or has no sizes.
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
    material, pms_data = load_pms(pms_source)
    roughness_m = roughness_mm / 1000.0
    updated_pipes: list[str] = []

    for idx in range(1, model.num_pipes + 1):
        pipe = model.pipes[idx]
        notes = pipe.notes

        if not notes or not notes.strip():
            logger.debug("Pipe %s: empty NOTES, skipping PMS", pipe.name)
            continue

        line_num = LineNumber.parse(notes, delimiter)
        if line_num is None:
            raise LineNumberParseError(
                f"Pipe {pipe.name}: cannot parse line number from NOTES: {notes!r}"
            )

        nps = line_num.nominal_pipe_size
        pms_code = line_num.pms_code
        schedule = lookup_schedule(pms_data, pms_code, float(nps))

        logger.info(
            "Pipe %s: NPS=%d, PMS=%s -> SCH=%s, MAT=%s",
            pipe.name,
            nps,
            pms_code,
            schedule,
            material,
        )

        nps_str = str(nps)
        params = {
            Pipe.DIA: [nps_str, nps_str, "inch"],
            Pipe.SCH: schedule,
            Pipe.MAT: material,
            Pipe.ROUGHNESS: [str(roughness_m), str(roughness_m), "m"],
            Pipe.DP_DES_FAC: 1.25,
        }

        # Apply params directly to the pipe
        model.set_params(pipe.name, params)
        updated_pipes.append(pipe.name)

    if save and updated_pipes:
        model.save()

    return updated_pipes
