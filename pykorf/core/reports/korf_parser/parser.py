"""Parsing logic for KORF Excel reports."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet

from pykorf.core.reports.korf_parser.models import (
    CaseInfo,
    CompressorData,
    ExchangerData,
    FeedData,
    KorfCaseData,
    MiscEquipmentData,
    OrificeData,
    PipeData,
    ProductData,
    PumpData,
    ValidationEntry,
    ValveData,
)

_logger = logging.getLogger(__name__)

_SHEET_PATTERN = re.compile(r"^(Title|Profile|Piping|Equipment)-(\d+)\s+(.+)$")

_SECTION_MARKERS_EQUIPMENT = {
    "FEEDS",
    "PRODUCTS",
    "ORIFICES",
    "VALVES",
    "TEES",
    "PUMPS",
    "COMPRESSORS",
    "EXCHANGERS",
    "MISCELLANEOUS",
}

# Column mapping dicts: param -> explicit column index (1-based)

_FEED_COL_MAP: dict[str, int] = {
    "name": 1,
    "description": 2,
    "pressure": 12,
    "pipe": 13,
}

_PRODUCT_COL_MAP: dict[str, int] = {
    "name": 1,
    "description": 2,
    "pressure": 12,
    "pipe": 13,
}

_ORIFICE_COL_MAP: dict[str, int] = {
    "name": 1,
    "description": 2,
    "type": 3,
    "bore": 6,
    "beta": 7,
    "dp_flange": 10,
    "dp_pipe": 11,
    "pressure_in": 12,
    "pressure_out": 13,
    "pipe_inlet": 14,
    "pipe_outlet": 15,
}

_VALVE_COL_MAP: dict[str, int] = {
    "name": 1,
    "description": 2,
    "type": 3,
    "cv": 6,
    "dp": 13,
    "pressure_in": 14,
    "pressure_out": 15,
    "pipe_inlet": 18,
    "pipe_outlet": 19,
}

_PUMP_COL_MAP: dict[str, int] = {
    "name": 1,
    "description": 2,
    "elevation": 3,
    "efficiency": 4,
    "power": 5,
    "flow": 6,
    "density": 7,
    "vol_flow": 8,
    "head": 9,
    "dp": 10,
    "pressure_in": 11,
    "pressure_out": 12,
    "pipe_inlet": 13,
    "pipe_outlet": 14,
}

_NPSH_COL_MAP: dict[str, int] = {
    "name": 1,
    "npsha": 15,
    "npshr": 18,
    "vapour_pressure": 6,
}

_SHUTOFF_COL_MAP: dict[str, int] = {
    "name": 1,
    "vessel_pressure": 3,
    "vessel_max_level": 6,
    "suction_max_pressure": 9,
    "shutoff_dp": 13,
    "shutoff_pressure": 14,
    "raise_to_shutoff_dp": 12,
}

_COMPRESSOR_COL_MAP: dict[str, int] = {
    "name": 1,
    "description": 2,
    "type": 3,
    "dp": 10,
    "pressure_in": 11,
    "pressure_out": 12,
    "flow": 6,
    "power": 5,
    "efficiency": 4,
    "head": 9,
}

_EXCHANGER_COL_MAP: dict[str, int] = {
    "name": 1,
    "description": 2,
    "type": 3,
    "side": 4,
    "duty": 5,
    "elevation_in": 6,
    "dp": 10,
    "pressure_in": 11,
    "pressure_out": 12,
    "pipe_inlet": 13,
    "pipe_outlet": 14,
}

_MISC_COL_MAP: dict[str, int] = {
    "name": 1,
    "description": 2,
    "dp": 10,
    "pressure_in": 11,
    "pressure_out": 12,
    "pipe_inlet": 13,
    "pipe_outlet": 14,
}


def _find_column(ws: Worksheet, header_row: int, header_name: str, offset: int = 0) -> int:
    """Find column index by searching header row for a header name."""
    for col in range(1, ws.max_column + 1):
        val = ws.cell(row=header_row, column=col).value
        if val and str(val).strip() == header_name:
            return col + offset
    return 0


def _extract_row_data_direct(
    ws: Worksheet,
    data_row: int,
    col_map: dict[str, int],
) -> dict[str, Any]:
    """Extract data from a single row using explicit column indices."""
    result: dict[str, Any] = {}
    for param, col in col_map.items():
        result[param] = ws.cell(row=data_row, column=col).value
    return result


def _parse_cases(ws_names: list[str]) -> dict[tuple[str, str], dict[str, str]]:
    """Parse sheet names to discover cases."""
    cases: dict[tuple[str, str], dict[str, str]] = {}
    for name in ws_names:
        m = _SHEET_PATTERN.match(name)
        if m:
            sheet_type, case_num, case_name = m.groups()
            key = (case_num, case_name)
            cases.setdefault(key, {})[sheet_type] = name
    return cases


def _safe_float(val: Any) -> float | None:
    """Convert a cell value to float, returning None if not numeric."""
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _safe_str(val: Any) -> str:
    """Convert a cell value to string, empty string if None."""
    if val is None:
        return ""
    return str(val).strip()


# ── TITLE SHEET PARSER ──────────────────────────────────────────────


def _parse_title_sheet(ws: Worksheet) -> tuple[list[ValidationEntry], str]:
    """Parse Title sheet to extract validation issues and run message."""
    validations: list[ValidationEntry] = []
    run_message = ""
    in_warnings = False

    for row_idx in range(1, ws.max_row + 1):
        cell_a = ws.cell(row=row_idx, column=1).value
        cell_b = ws.cell(row=row_idx, column=2).value

        if cell_a and "WARNINGS AND ERRORS" in str(cell_a).upper():
            in_warnings = True
            continue

        if in_warnings and cell_a:
            msg = str(cell_a).strip()
            if msg:
                validations.append(ValidationEntry(message=msg))
            continue

        if cell_a and str(cell_a).strip() == "Run Message":
            run_message = str(cell_b).strip() if cell_b else ""

    return validations, run_message


# ── PIPING SHEET PARSER ──────────────────────────────────────────────

_PIPE_ROW_MAP: dict[tuple[str, str, str], str] = {
    ("Total", "Flow", ""): "mass_flow",
    ("", "Pressure", "In"): "pressure_in",
    ("", "Pressure", "Out"): "pressure_out",
    ("", "Temperature", "In"): "temperature_in",
    ("", "Temperature", "Out"): "temperature_out",
    ("", "Density (No slip)", "In"): "density_in",
    ("", "Density (No slip)", "Out"): "density_out",
    ("", "Volumetric Flow", "Avg"): "vol_flow",
    ("Size", "", ""): "size",
    ("Length", "", ""): "length",
    ("Schedule", "", ""): "schedule",
    ("Overall", "", ""): "dp_overall",
    ("Friction", "", ""): "dp_friction",
    ("Elevation", "", ""): "dp_elevation",
    ("dP/Length", "", ""): "dp_length",
    ("Velocity", "", "In"): "velocity_in",
    ("dP/Length", "Target", "Max"): "dp_length_criteria_max",
    ("Velocity", "Target", "Max"): "velocity_criteria_max",
}

_VISCOSITY_SPELLINGS = {"Viscocity (No slip)", "Viscosity (No slip)"}
_RHO_V2_SPELLINGS = {"Rho.V^2", "Rho.V²", "ρV²"}  # noqa: RUF001

_UNIT_STANDARDIZE: dict[str, str] = {
    "kg/m3.(m/s": "Pa",
    "kg/m3.(m/s]": "Pa",
    "kg/m3.(m/s)^2": "Pa",
    "kg/m3(m/s)^2": "Pa",
    "barg": "barg",
    "bar": "bar",
    "bar/100m": "bar/100m",
    "m": "m",
    "m/s": "m/s",
    "kg/h": "kg/h",
    "m3/h": "m³/h",
    "cP": "cP",
    "C": "°C",
    "kg/m3": "kg/m³",
}


def _standardize_unit(raw_unit: str) -> str:
    """Standardize KORF unit strings to clean format."""
    if not raw_unit:
        return ""
    unit = raw_unit.strip()
    if unit in _UNIT_STANDARDIZE:
        return _UNIT_STANDARDIZE[unit]
    return unit


_REPORT_FIELDS: set[str] = {
    "length",
    "dp_length",
    "dp_length_criteria_max",
    "velocity_in",
    "velocity_criteria_max",
    "velocity_criteria_min",
    "rho_v2_in",
    "dp_overall",
    "dp_friction",
    "dp_elevation",
    "pressure_in",
    "pressure_out",
    "temperature_in",
    "temperature_out",
    "density_in",
    "density_out",
    "viscosity",
    "mass_flow",
    "vol_flow",
}

_CONTINUATION_FIELDS: dict[str, str] = {
    "Pressure": "pressure_out",
    "Temperature": "temperature_out",
    "Density (No slip)": "density_out",
}


def _parse_piping_sheet(ws: Worksheet) -> list[PipeData]:
    """Parse a Piping sheet to extract pipe result data using optimized lookup dict."""
    pipe_names: list[str] = []
    pipe_data: dict[str, dict[str, Any]] = {}
    pipe_units: dict[str, dict[str, str]] = {}

    for col in range(5, ws.max_column + 1):
        name = _safe_str(ws.cell(row=2, column=col).value)
        if name:
            pipe_names.append(name)
            pipe_data[name] = {}
            pipe_units[name] = {}

    if not pipe_names:
        return []

    prev_row_key: tuple[str, str, str] = ("", "", "")
    prev_field_name: str = ""

    for row_idx in range(5, ws.max_row + 1):
        col_a = _safe_str(ws.cell(row=row_idx, column=1).value)
        col_b = _safe_str(ws.cell(row=row_idx, column=2).value)
        col_c = _safe_str(ws.cell(row=row_idx, column=3).value)
        col_d_raw = _safe_str(ws.cell(row=row_idx, column=4).value)
        col_d = _standardize_unit(col_d_raw)

        key = (col_a, col_b, col_c)

        if col_b in _VISCOSITY_SPELLINGS:
            for i, pname in enumerate(pipe_names):
                val = _safe_float(ws.cell(row=row_idx, column=5 + i).value)
                pipe_data[pname]["viscosity"] = val
                if "viscosity" in _REPORT_FIELDS:
                    pipe_units[pname]["viscosity"] = col_d
            prev_row_key = key
            prev_field_name = "viscosity"
            continue

        if col_a in _RHO_V2_SPELLINGS and col_c == "In":
            for i, pname in enumerate(pipe_names):
                val = _safe_float(ws.cell(row=row_idx, column=5 + i).value)
                pipe_data[pname]["rho_v2_in"] = val
                if "rho_v2_in" in _REPORT_FIELDS:
                    pipe_units[pname]["rho_v2_in"] = col_d
            prev_row_key = key
            prev_field_name = "rho_v2_in"
            continue

        if key in _PIPE_ROW_MAP:
            field_name = _PIPE_ROW_MAP[key]
            for i, pname in enumerate(pipe_names):
                if field_name in ("size", "schedule"):
                    val = _safe_str(ws.cell(row=row_idx, column=5 + i).value)
                else:
                    val = _safe_float(ws.cell(row=row_idx, column=5 + i).value)
                pipe_data[pname][field_name] = val
                if field_name in _REPORT_FIELDS and field_name not in ("size", "schedule"):
                    pipe_units[pname][field_name] = col_d
            prev_row_key = key
            prev_field_name = col_b if col_b else col_a
            continue

        if key == ("", "", "Min") and prev_row_key == ("Velocity", "Target", "Max"):
            for i, pname in enumerate(pipe_names):
                val = _safe_float(ws.cell(row=row_idx, column=5 + i).value)
                pipe_data[pname]["velocity_criteria_min"] = val
                if "velocity_criteria_min" in _REPORT_FIELDS:
                    pipe_units[pname]["velocity_criteria_min"] = col_d
            continue

        if key == ("", "", "Out") and prev_field_name in _CONTINUATION_FIELDS:
            field_name = _CONTINUATION_FIELDS[prev_field_name]
            for i, pname in enumerate(pipe_names):
                val = _safe_float(ws.cell(row=row_idx, column=5 + i).value)
                pipe_data[pname][field_name] = val
                if field_name in _REPORT_FIELDS:
                    pipe_units[pname][field_name] = col_d
            continue

        prev_row_key = key
        prev_field_name = col_b if col_b else col_a

    results: list[PipeData] = []
    for pname in pipe_names:
        d = pipe_data.get(pname, {})
        u = pipe_units.get(pname, {})
        results.append(
            PipeData(
                name=pname,
                length=d.get("length"),
                size=d.get("size"),
                schedule=d.get("schedule"),
                dp_length=d.get("dp_length"),
                velocity_in=d.get("velocity_in"),
                rho_v2_in=d.get("rho_v2_in"),
                dp_overall=d.get("dp_overall"),
                dp_friction=d.get("dp_friction"),
                dp_elevation=d.get("dp_elevation"),
                pressure_in=d.get("pressure_in"),
                pressure_out=d.get("pressure_out"),
                temperature_in=d.get("temperature_in"),
                temperature_out=d.get("temperature_out"),
                density_in=d.get("density_in"),
                density_out=d.get("density_out"),
                viscosity=d.get("viscosity"),
                mass_flow=d.get("mass_flow"),
                vol_flow=d.get("vol_flow"),
                dp_length_criteria_max=d.get("dp_length_criteria_max"),
                velocity_criteria_max=d.get("velocity_criteria_max"),
                velocity_criteria_min=d.get("velocity_criteria_min"),
                units=u,
            )
        )
    return results


# ── EQUIPMENT SHEET PARSER ───────────────────────────────────────────


def _parse_equipment_sheet(ws: Worksheet) -> dict[str, list]:
    """Parse an Equipment sheet to extract all element data."""
    result: dict[str, list] = {
        "feeds": [],
        "products": [],
        "orifices": [],
        "valves": [],
        "pumps": [],
        "compressors": [],
        "exchangers": [],
        "misc_equipment": [],
    }

    row = 1
    while row <= ws.max_row:
        cell_a = _safe_str(ws.cell(row=row, column=1).value)

        if cell_a == "FEEDS":
            feeds, row = _parse_feeds_section(ws, row)
            result["feeds"] = feeds
            continue
        elif cell_a == "PRODUCTS":
            products, row = _parse_products_section(ws, row)
            result["products"] = products
            continue
        elif cell_a == "ORIFICES":
            orifices, row = _parse_orifices_section(ws, row)
            result["orifices"] = orifices
            continue
        elif cell_a == "VALVES":
            valves, row = _parse_valves_section(ws, row)
            result["valves"] = valves
            continue
        elif cell_a == "PUMPS":
            pumps, row = _parse_pumps_section(ws, row)
            result["pumps"] = pumps
            continue
        elif cell_a == "COMPRESSORS":
            compressors, row = _parse_compressors_section(ws, row)
            result["compressors"] = compressors
            continue
        elif cell_a == "EXCHANGERS":
            exchangers, row = _parse_exchangers_section(ws, row)
            result["exchangers"] = exchangers
            continue
        elif cell_a == "MISCELLANEOUS":
            misc, row = _parse_misc_section(ws, row)
            result["misc_equipment"] = misc
            continue

        row += 1

    return result


def _parse_feeds_section(ws: Worksheet, start_row: int) -> tuple[list[FeedData], int]:
    """Parse FEEDS section from Equipment sheet using explicit column indices."""
    feeds: list[FeedData] = []
    row = start_row + 4

    while row <= ws.max_row:
        cell_a = ws.cell(row=row, column=1).value
        cell_a_str = _safe_str(cell_a)
        if cell_a_str in _SECTION_MARKERS_EQUIPMENT:
            break
        if not cell_a_str:
            row += 1
            continue

        data = _extract_row_data_direct(ws, row, _FEED_COL_MAP)
        feeds.append(
            FeedData(
                name=_safe_str(data.get("name")),
                description=_safe_str(data.get("description")),
                pressure=_safe_float(data.get("pressure")),
            )
        )
        row += 1

    return feeds, row


def _parse_products_section(ws: Worksheet, start_row: int) -> tuple[list[ProductData], int]:
    """Parse PRODUCTS section from Equipment sheet using explicit column indices."""
    products: list[ProductData] = []
    row = start_row + 4

    while row <= ws.max_row:
        cell_a = ws.cell(row=row, column=1).value
        cell_a_str = _safe_str(cell_a)
        if cell_a_str in _SECTION_MARKERS_EQUIPMENT:
            break
        if not cell_a_str:
            row += 1
            continue

        data = _extract_row_data_direct(ws, row, _PRODUCT_COL_MAP)
        products.append(
            ProductData(
                name=_safe_str(data.get("name")),
                description=_safe_str(data.get("description")),
                pressure=_safe_float(data.get("pressure")),
            )
        )
        row += 1

    return products, row


def _parse_orifices_section(ws: Worksheet, start_row: int) -> tuple[list[OrificeData], int]:
    """Parse ORIFICES section from Equipment sheet using explicit column indices."""
    orifices: list[OrificeData] = []
    row = start_row + 4

    while row <= ws.max_row:
        cell_a = ws.cell(row=row, column=1).value
        cell_a_str = _safe_str(cell_a)
        if cell_a_str in _SECTION_MARKERS_EQUIPMENT:
            break
        if not cell_a_str:
            row += 1
            continue

        data = _extract_row_data_direct(ws, row, _ORIFICE_COL_MAP)
        orifices.append(
            OrificeData(
                name=_safe_str(data.get("name")),
                description=_safe_str(data.get("description")),
                type=_safe_str(data.get("type")),
                bore=_safe_float(data.get("bore")),
                beta=_safe_float(data.get("beta")),
                dp_flange_tap=_safe_float(data.get("dp_flange")),
                dp_pipe_tap=_safe_float(data.get("dp_pipe")),
                pressure_in=_safe_float(data.get("pressure_in")),
                pressure_out=_safe_float(data.get("pressure_out")),
                pipe_inlet=_safe_str(data.get("pipe_inlet")),
                pipe_outlet=_safe_str(data.get("pipe_outlet")),
            )
        )
        row += 1

    return orifices, row


def _parse_valves_section(ws: Worksheet, start_row: int) -> tuple[list[ValveData], int]:
    """Parse VALVES section from Equipment sheet using explicit column indices."""
    valves: list[ValveData] = []
    row = start_row + 4

    while row <= ws.max_row:
        cell_a = ws.cell(row=row, column=1).value
        cell_a_str = _safe_str(cell_a)
        if cell_a_str in _SECTION_MARKERS_EQUIPMENT:
            break
        if not cell_a_str:
            row += 1
            continue

        data = _extract_row_data_direct(ws, row, _VALVE_COL_MAP)
        valves.append(
            ValveData(
                name=_safe_str(data.get("name")),
                description=_safe_str(data.get("description")),
                type=_safe_str(data.get("type")),
                cv=_safe_float(data.get("cv")),
                dp=_safe_float(data.get("dp")),
                pressure_in=_safe_float(data.get("pressure_in")),
                pressure_out=_safe_float(data.get("pressure_out")),
                pipe_inlet=_safe_str(data.get("pipe_inlet")),
                pipe_outlet=_safe_str(data.get("pipe_outlet")),
            )
        )
        row += 1

    return valves, row


def _parse_pumps_section(ws: Worksheet, start_row: int) -> tuple[list[PumpData], int]:
    """Parse PUMPS section including NPSH and SHUT OFF PRESSURE subsections."""
    pumps: list[PumpData] = []
    unit_row = start_row + 2
    data_row = start_row + 4

    pump_units: dict[str, str] = {}
    if unit_row <= ws.max_row:
        for field_name, col_idx in _PUMP_COL_MAP.items():
            cell_val = ws.cell(row=unit_row, column=col_idx).value
            if cell_val:
                pump_units[field_name] = _safe_str(cell_val)

    while data_row <= ws.max_row:
        cell_a = ws.cell(row=data_row, column=1).value
        cell_a_str = _safe_str(cell_a)
        if (
            cell_a_str in ("NPSH", "SHUT OFF PRESSURE", "CURVES")
            or cell_a_str in _SECTION_MARKERS_EQUIPMENT
        ):
            break
        if not cell_a_str:
            data_row += 1
            continue

        data = _extract_row_data_direct(ws, data_row, _PUMP_COL_MAP)
        pumps.append(
            PumpData(
                name=_safe_str(data.get("name")),
                description=_safe_str(data.get("description")),
                elevation=_safe_float(data.get("elevation")),
                efficiency=_safe_float(data.get("efficiency")),
                power=_safe_float(data.get("power")),
                flow=_safe_float(data.get("flow")),
                density=_safe_float(data.get("density")),
                vol_flow=_safe_float(data.get("vol_flow")),
                head=_safe_float(data.get("head")),
                dp=_safe_float(data.get("dp")),
                pressure_in=_safe_float(data.get("pressure_in")),
                pressure_out=_safe_float(data.get("pressure_out")),
                pipe_inlet=_safe_str(data.get("pipe_inlet")),
                pipe_outlet=_safe_str(data.get("pipe_outlet")),
                pressure_in_unit=pump_units.get("pressure_in", ""),
                density_unit=pump_units.get("density", ""),
            )
        )
        data_row += 1

    # Parse NPSH subsection
    while data_row <= ws.max_row:
        cell_a = _safe_str(ws.cell(row=data_row, column=1).value)
        if cell_a == "NPSH":
            npsh_unit_row = data_row + 2
            npsh_data_row = data_row + 4
            npsh_units: dict[str, str] = {}
            if npsh_unit_row <= ws.max_row:
                for field_name, col_idx in _NPSH_COL_MAP.items():
                    cell_val = ws.cell(row=npsh_unit_row, column=col_idx).value
                    if cell_val:
                        npsh_units[field_name] = _safe_str(cell_val)
            if npsh_data_row <= ws.max_row:
                for pump in pumps:
                    data = _extract_row_data_direct(ws, npsh_data_row, _NPSH_COL_MAP)
                    if _safe_str(data.get("name")) == pump.name:
                        pump.npsha = _safe_float(data.get("npsha"))
                        pump.npshr = _safe_float(data.get("npshr"))
                        pump.vapour_pressure = _safe_float(data.get("vapour_pressure"))
                        pump.vapour_pressure_unit = npsh_units.get("vapour_pressure", "")
            data_row += 1
            continue
        if cell_a in ("SHUT OFF PRESSURE", "CURVES") or cell_a in _SECTION_MARKERS_EQUIPMENT:
            break
        data_row += 1

    # Parse SHUT OFF PRESSURE subsection
    while data_row <= ws.max_row:
        cell_a = _safe_str(ws.cell(row=data_row, column=1).value)
        if cell_a == "SHUT OFF PRESSURE":
            shutoff_data_row = data_row + 4
            if shutoff_data_row <= ws.max_row:
                for pump in pumps:
                    data = _extract_row_data_direct(ws, shutoff_data_row, _SHUTOFF_COL_MAP)
                    if _safe_str(data.get("name")) == pump.name:
                        pump.vessel_pressure = _safe_float(data.get("vessel_pressure"))
                        pump.vessel_max_level = _safe_float(data.get("vessel_max_level"))
                        pump.suction_max_pressure = _safe_float(data.get("suction_max_pressure"))
                        pump.shutoff_dp = _safe_float(data.get("shutoff_dp"))
                        pump.shutoff_pressure = _safe_float(data.get("shutoff_pressure"))
                        pump.raise_to_shutoff_dp = _safe_float(data.get("raise_to_shutoff_dp"))
            data_row += 1
            continue
        if cell_a in ("CURVES",) or cell_a in _SECTION_MARKERS_EQUIPMENT:
            break
        data_row += 1

    return pumps, data_row


def _parse_compressors_section(ws: Worksheet, start_row: int) -> tuple[list[CompressorData], int]:
    """Parse COMPRESSORS section from Equipment sheet using explicit column indices."""
    compressors: list[CompressorData] = []
    row = start_row + 4

    while row <= ws.max_row:
        cell_a = ws.cell(row=row, column=1).value
        cell_a_str = _safe_str(cell_a)
        if cell_a_str in _SECTION_MARKERS_EQUIPMENT:
            break
        if not cell_a_str:
            row += 1
            continue

        data = _extract_row_data_direct(ws, row, _COMPRESSOR_COL_MAP)
        compressors.append(
            CompressorData(
                name=_safe_str(data.get("name")),
                description=_safe_str(data.get("description")),
                type=_safe_str(data.get("type")),
                dp=_safe_float(data.get("dp")),
                pressure_in=_safe_float(data.get("pressure_in")),
                pressure_out=_safe_float(data.get("pressure_out")),
                flow=_safe_float(data.get("flow")),
                power=_safe_float(data.get("power")),
                efficiency=_safe_float(data.get("efficiency")),
                head=_safe_float(data.get("head")),
            )
        )
        row += 1

    return compressors, row


def _parse_exchangers_section(ws: Worksheet, start_row: int) -> tuple[list[ExchangerData], int]:
    """Parse EXCHANGERS section from Equipment sheet using explicit column indices."""
    exchangers: list[ExchangerData] = []
    row = start_row + 4

    while row <= ws.max_row:
        cell_a = ws.cell(row=row, column=1).value
        cell_a_str = _safe_str(cell_a)
        if cell_a_str in _SECTION_MARKERS_EQUIPMENT:
            break
        if not cell_a_str:
            row += 1
            continue

        data = _extract_row_data_direct(ws, row, _EXCHANGER_COL_MAP)
        exchangers.append(
            ExchangerData(
                name=_safe_str(data.get("name")),
                description=_safe_str(data.get("description")),
                type=_safe_str(data.get("type")),
                side=_safe_str(data.get("side")),
                elevation_in=_safe_float(data.get("elevation_in")),
                duty=_safe_float(data.get("duty")),
                dp=_safe_float(data.get("dp")),
                pressure_in=_safe_float(data.get("pressure_in")),
                pressure_out=_safe_float(data.get("pressure_out")),
                pipe_inlet=_safe_str(data.get("pipe_inlet")),
                pipe_outlet=_safe_str(data.get("pipe_outlet")),
            )
        )
        row += 1

    return exchangers, row


def _parse_misc_section(ws: Worksheet, start_row: int) -> tuple[list[MiscEquipmentData], int]:
    """Parse MISCELLANEOUS section from Equipment sheet using explicit column indices."""
    misc: list[MiscEquipmentData] = []
    row = start_row + 4

    while row <= ws.max_row:
        cell_a = ws.cell(row=row, column=1).value
        cell_a_str = _safe_str(cell_a)
        if cell_a_str in _SECTION_MARKERS_EQUIPMENT:
            break
        if not cell_a_str:
            row += 1
            continue

        data = _extract_row_data_direct(ws, row, _MISC_COL_MAP)
        misc.append(
            MiscEquipmentData(
                name=_safe_str(data.get("name")),
                description=_safe_str(data.get("description")),
                dp=_safe_float(data.get("dp")),
                pressure_in=_safe_float(data.get("pressure_in")),
                pressure_out=_safe_float(data.get("pressure_out")),
                pipe_inlet=_safe_str(data.get("pipe_inlet")),
                pipe_outlet=_safe_str(data.get("pipe_outlet")),
            )
        )
        row += 1

    return misc, row


# ── MAIN PARSER ───────────────────────────────────────────────────────


def parse_korf_excel(excel_path: str | Path) -> dict[CaseInfo, KorfCaseData]:
    """Parse a KORF Excel report file and extract data for all cases.

    Args:
        excel_path: Path to the KORF Excel report file (.xlsx).

    Returns:
        Dict mapping CaseInfo to KorfCaseData for each case found.
    """
    excel_path = Path(excel_path)
    wb = load_workbook(str(excel_path), data_only=True)

    cases = _parse_cases(wb.sheetnames)
    if not cases:
        _logger.warning("No case sheets found in %s", excel_path)
        return {}

    result: dict[CaseInfo, KorfCaseData] = {}

    for (case_num, case_name), sheets in cases.items():
        case_info = CaseInfo(number=case_num, name=case_name)
        case_data = KorfCaseData(case=case_info)

        # Parse Title sheet
        title_sheet_name = sheets.get("Title")
        if title_sheet_name and title_sheet_name in wb.sheetnames:
            ws = wb[title_sheet_name]
            validations, run_message = _parse_title_sheet(ws)
            case_data.validations = validations
            case_data.run_message = run_message

        # Parse Piping sheet
        piping_sheet_name = sheets.get("Piping")
        if piping_sheet_name and piping_sheet_name in wb.sheetnames:
            ws = wb[piping_sheet_name]
            case_data.pipes = _parse_piping_sheet(ws)

        # Parse Equipment sheet
        equip_sheet_name = sheets.get("Equipment")
        if equip_sheet_name and equip_sheet_name in wb.sheetnames:
            ws = wb[equip_sheet_name]
            equip_data = _parse_equipment_sheet(ws)
            case_data.feeds = equip_data.get("feeds", [])
            case_data.products = equip_data.get("products", [])
            case_data.orifices = equip_data.get("orifices", [])
            case_data.valves = equip_data.get("valves", [])
            case_data.pumps = equip_data.get("pumps", [])
            case_data.compressors = equip_data.get("compressors", [])
            case_data.exchangers = equip_data.get("exchangers", [])
            case_data.misc_equipment = equip_data.get("misc_equipment", [])

        result[case_info] = case_data

    wb.close()
    return result
