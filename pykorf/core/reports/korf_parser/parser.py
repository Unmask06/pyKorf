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

# Column mapping dicts: param -> (header_name, offset)

_FEED_COL_MAP: dict[str, tuple[str, int]] = {
    "name": ("Number", 0),
    "description": ("Description", 0),
    "pressure": ("Pressure", 9),
    "pipe": ("Pipe", 0),
}

_PRODUCT_COL_MAP: dict[str, tuple[str, int]] = {
    "name": ("Number", 0),
    "description": ("Description", 0),
    "pressure": ("Pressure", 9),
    "pipe": ("Pipe", 0),
}

_ORIFICE_COL_MAP: dict[str, tuple[str, int]] = {
    "name": ("Number", 0),
    "description": ("Description", 0),
    "type": ("Type", 0),
    "bore": ("Bore", 0),
    "beta": ("Beta", 0),
    "dp_flange": ("Pressures", 0),
    "dp_pipe": ("Pressures", 1),
    "pressure_in": ("Pressures", 2),
    "pressure_out": ("Pressures", 3),
    "pipe_inlet": ("Pipe", 0),
    "pipe_outlet": ("Pipe", 1),
}

_VALVE_COL_MAP: dict[str, tuple[str, int]] = {
    "name": ("Number", 0),
    "description": ("Description", 0),
    "type": ("Type", 0),
    "elevation": ("Elevation", 0),
    "cv": ("Cv", 0),
    "dp": ("Pressures", 0),
    "pressure_in": ("Pressures", 1),
    "pressure_out": ("Pressures", 2),
    "pipe_inlet": ("Pipe", 0),
    "pipe_outlet": ("Pipe", 1),
}

_PUMP_COL_MAP: dict[str, tuple[str, int]] = {
    "name": ("Number", 0),
    "description": ("Description", 0),
    "elevation": ("Elevation", 0),
    "efficiency": ("Efficiency (pump*motor)", 0),
    "power": ("Power", 0),
    "flow": ("Flow", 0),
    "density": ("Density", 0),
    "vol_flow": ("Vol Flow", 0),
    "head": ("Head", 0),
    "dp": ("Pressures", 0),
    "pressure_in": ("Pressures", 1),
    "pressure_out": ("Pressures", 2),
    "pipe_inlet": ("Pipe", 0),
    "pipe_outlet": ("Pipe", 1),
}

_NPSH_COL_MAP: dict[str, tuple[str, int]] = {
    "name": ("Number", 0),
    "npsha": ("NPSHA", 0),
    "npshr": ("NPSHR", 0),
    "vapour_pressure": ("Vap Pres Value (Psat)", 0),
}

_SHUTOFF_COL_MAP: dict[str, tuple[str, int]] = {
    "name": ("Number", 0),
    "vessel_pressure": ("Pressure Maximum (top)", 0),
    "vessel_max_level": ("Level Maximum", 0),
    "suction_max_pressure": ("Pressure Maximum", 0),
    "shutoff_dp": ("dP Shutoff", 0),
    "shutoff_pressure": ("Pressure Shutoff", 0),
    "raise_to_shutoff_dp": ("dP Shutoff/dP Calc", 0),
}

_COMPRESSOR_COL_MAP: dict[str, tuple[str, int]] = {
    "name": ("Number", 0),
    "description": ("Description", 0),
    "type": ("Type", 0),
    "dp": ("Pressures", 0),
    "pressure_in": ("Pressures", 1),
    "pressure_out": ("Pressures", 2),
    "flow": ("Flow", 0),
    "power": ("Power", 0),
    "efficiency": ("Efficiency", 0),
    "head": ("Head", 0),
}

_EXCHANGER_COL_MAP: dict[str, tuple[str, int]] = {
    "name": ("Number", 0),
    "description": ("Description", 0),
    "type": ("Type", 0),
    "side": ("Side", 0),
    "duty": ("Duty", 0),
    "dp": ("Pressures", 0),
    "pressure_in": ("Pressures", 2),
    "pressure_out": ("Pressures", 3),
    "pipe_inlet": ("Pipe", 0),
    "pipe_outlet": ("Pipe", 1),
}

_MISC_COL_MAP: dict[str, tuple[str, int]] = {
    "name": ("Number", 0),
    "description": ("Description", 0),
    "dp": ("Pressures", 0),
    "pressure_in": ("Pressures", 2),
    "pressure_out": ("Pressures", 3),
    "pipe_inlet": ("Pipe", 0),
    "pipe_outlet": ("Pipe", 1),
}


def _find_column(ws: Worksheet, header_row: int, header_name: str, offset: int = 0) -> int:
    """Find column index by searching header row for a header name."""
    for col in range(1, ws.max_column + 1):
        val = ws.cell(row=header_row, column=col).value
        if val and str(val).strip() == header_name:
            return col + offset
    return 0


def _extract_row_data(
    ws: Worksheet,
    data_row: int,
    header_row: int,
    col_map: dict[str, tuple[str, int]],
) -> dict[str, Any]:
    """Extract data from a single row using a column mapping dict."""
    result: dict[str, Any] = {}
    for param, (header_name, offset) in col_map.items():
        col = _find_column(ws, header_row, header_name, offset)
        if col > 0:
            result[param] = ws.cell(row=data_row, column=col).value
        else:
            result[param] = None
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


def _parse_piping_sheet(ws: Worksheet) -> list[PipeData]:
    """Parse a Piping sheet to extract pipe result data."""
    pipe_names: list[str] = []
    pipe_data: dict[str, dict[str, float | None | str]] = {}

    for col in range(5, ws.max_column + 1):
        name = _safe_str(ws.cell(row=2, column=col).value)
        if name and name != "Number":
            pipe_names.append(name)
            pipe_data[name] = {}

    if not pipe_names:
        return []

    def _set_all_pipes(label: str, row_idx: int, sub_key: str | None = None):
        for i, pname in enumerate(pipe_names):
            col = 5 + i
            val = _safe_float(ws.cell(row=row_idx, column=col).value)
            key = f"{label}" if not sub_key else f"{label}_{sub_key}"
            pipe_data[pname][key] = val

    for row_idx in range(1, ws.max_row + 1):
        col_a = _safe_str(ws.cell(row=row_idx, column=1).value)
        col_b = _safe_str(ws.cell(row=row_idx, column=2).value)
        col_c = _safe_str(ws.cell(row=row_idx, column=3).value)
        col_d = _safe_str(ws.cell(row=row_idx, column=4).value)

        if col_a == "Total" and col_b == "Flow":
            _set_all_pipes("mass_flow", row_idx)
        elif col_b == "Pressure" and col_c == "In":
            _set_all_pipes("pressure_in", row_idx)
        elif col_b == "Pressure" and col_c == "Out":
            _set_all_pipes("pressure_out", row_idx)
        elif col_b == "Temperature" and col_c == "In":
            _set_all_pipes("temperature_in", row_idx)
        elif col_b == "Temperature" and col_c == "Out":
            _set_all_pipes("temperature_out", row_idx)
        elif col_b == "Density (No slip)" and col_c == "In":
            _set_all_pipes("density_in", row_idx)
        elif col_b == "Density (No slip)" and col_c == "Out":
            _set_all_pipes("density_out", row_idx)
        elif col_b == "Viscocity (No slip)" or col_b == "Viscosity (No slip)":
            _set_all_pipes("viscosity", row_idx)
        elif col_b == "Volumetric Flow" and col_c == "Avg":
            _set_all_pipes("vol_flow", row_idx)
        elif col_a == "Size" and col_d == "in":
            for i, pname in enumerate(pipe_names):
                pipe_data[pname]["size"] = _safe_str(ws.cell(row=row_idx, column=5 + i).value)
        elif col_a == "Length" and col_d == "m":
            _set_all_pipes("length", row_idx)
        elif col_a == "Schedule":
            for i, pname in enumerate(pipe_names):
                pipe_data[pname]["schedule"] = _safe_str(ws.cell(row=row_idx, column=5 + i).value)
        elif col_a == "dP/Length" and col_b == "" and col_d == "bar/100m":
            _set_all_pipes("dp_length", row_idx)
        elif col_a == "dP/Length" and col_b == "Target" and col_c == "Max":
            _set_all_pipes("dp_length_criteria_max", row_idx)
        elif col_a == "Velocity" and col_b == "" and col_c == "In":
            _set_all_pipes("velocity_in", row_idx)
        elif col_a == "Rho.V^2" or col_a == "Rho.V²" or col_a == "ρV²":  # noqa: RUF001
            if col_c == "In":
                _set_all_pipes("rho_v2_in", row_idx)
        elif col_a == "Overall" and col_d == "bar":
            _set_all_pipes("dp_overall", row_idx)
        elif col_a == "Friction" and col_d == "bar":
            _set_all_pipes("dp_friction", row_idx)
        elif col_a == "Elevation" and col_d == "bar":
            _set_all_pipes("dp_elevation", row_idx)
        elif col_a == "dP/Length" and col_b == "Target" and col_c == "Max":
            _set_all_pipes("dp_length_criteria_max", row_idx)
        elif col_a == "Velocity" and col_b == "Target" and col_c == "Max":
            _set_all_pipes("velocity_criteria_max", row_idx)
        elif col_a == "" and col_b == "" and col_c == "Min" and col_d == "m/s":
            if row_idx > 1:
                row_above_a = _safe_str(ws.cell(row=row_idx - 1, column=1).value)
                row_above_b = _safe_str(ws.cell(row=row_idx - 1, column=2).value)
                if row_above_a == "Velocity" and row_above_b == "Target":
                    _set_all_pipes("velocity_criteria_min", row_idx)

    results: list[PipeData] = []
    for pname in pipe_names:
        d = pipe_data.get(pname, {})
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
    """Parse FEEDS section from Equipment sheet using header-based column lookup."""
    header_row = start_row + 1
    feeds: list[FeedData] = []
    row = start_row + 4

    while row <= ws.max_row:
        name_col = _find_column(ws, header_row, "Number")
        cell_a = ws.cell(row=row, column=name_col).value if name_col else None
        cell_a_str = _safe_str(cell_a)
        if cell_a_str in _SECTION_MARKERS_EQUIPMENT:
            break
        if not cell_a_str:
            row += 1
            continue

        data = _extract_row_data(ws, row, header_row, _FEED_COL_MAP)
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
    """Parse PRODUCTS section from Equipment sheet using header-based column lookup."""
    header_row = start_row + 1
    products: list[ProductData] = []
    row = start_row + 4

    while row <= ws.max_row:
        name_col = _find_column(ws, header_row, "Number")
        cell_a = ws.cell(row=row, column=name_col).value if name_col else None
        cell_a_str = _safe_str(cell_a)
        if cell_a_str in _SECTION_MARKERS_EQUIPMENT:
            break
        if not cell_a_str:
            row += 1
            continue

        data = _extract_row_data(ws, row, header_row, _PRODUCT_COL_MAP)
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
    """Parse ORIFICES section from Equipment sheet using header-based column lookup."""
    header_row = start_row + 1
    orifices: list[OrificeData] = []
    row = start_row + 4

    while row <= ws.max_row:
        name_col = _find_column(ws, header_row, "Number")
        cell_a = ws.cell(row=row, column=name_col).value if name_col else None
        cell_a_str = _safe_str(cell_a)
        if cell_a_str in _SECTION_MARKERS_EQUIPMENT:
            break
        if not cell_a_str:
            row += 1
            continue

        data = _extract_row_data(ws, row, header_row, _ORIFICE_COL_MAP)
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
    """Parse VALVES section from Equipment sheet using header-based column lookup."""
    header_row = start_row + 1
    valves: list[ValveData] = []
    row = start_row + 4

    while row <= ws.max_row:
        name_col = _find_column(ws, header_row, "Number")
        cell_a = ws.cell(row=row, column=name_col).value if name_col else None
        cell_a_str = _safe_str(cell_a)
        if cell_a_str in _SECTION_MARKERS_EQUIPMENT:
            break
        if not cell_a_str:
            row += 1
            continue

        data = _extract_row_data(ws, row, header_row, _VALVE_COL_MAP)
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
    header_row = start_row + 1
    pumps: list[PumpData] = []

    # Parse main PUMPS data rows
    row = start_row + 4

    while row <= ws.max_row:
        name_col = _find_column(ws, header_row, "Number")
        cell_a = ws.cell(row=row, column=name_col).value if name_col else None
        cell_a_str = _safe_str(cell_a)
        if (
            cell_a_str in ("NPSH", "SHUT OFF PRESSURE", "CURVES")
            or cell_a_str in _SECTION_MARKERS_EQUIPMENT
        ):
            break
        if not cell_a_str:
            row += 1
            continue

        data = _extract_row_data(ws, row, header_row, _PUMP_COL_MAP)
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
            )
        )
        row += 1

    # Parse NPSH subsection
    while row <= ws.max_row:
        cell_a = _safe_str(ws.cell(row=row, column=1).value)
        if cell_a == "NPSH":
            npsh_header_row = row + 2
            npsh_data_row = row + 4
            if npsh_data_row <= ws.max_row:
                for pump in pumps:
                    data = _extract_row_data(ws, npsh_data_row, npsh_header_row, _NPSH_COL_MAP)
                    if _safe_str(data.get("name")) == pump.name:
                        pump.npsha = _safe_float(data.get("npsha"))
                        pump.npshr = _safe_float(data.get("npshr"))
                        pump.vapour_pressure = _safe_float(data.get("vapour_pressure"))
            row += 1
            continue
        if cell_a in ("SHUT OFF PRESSURE", "CURVES") or cell_a in _SECTION_MARKERS_EQUIPMENT:
            break
        row += 1

    # Parse SHUT OFF PRESSURE subsection
    while row <= ws.max_row:
        cell_a = _safe_str(ws.cell(row=row, column=1).value)
        if cell_a == "SHUT OFF PRESSURE":
            shutoff_header_row = row + 2
            shutoff_data_row = row + 4
            if shutoff_data_row <= ws.max_row:
                for pump in pumps:
                    data = _extract_row_data(
                        ws, shutoff_data_row, shutoff_header_row, _SHUTOFF_COL_MAP
                    )
                    if _safe_str(data.get("name")) == pump.name:
                        pump.vessel_pressure = _safe_float(data.get("vessel_pressure"))
                        pump.vessel_max_level = _safe_float(data.get("vessel_max_level"))
                        pump.suction_max_pressure = _safe_float(data.get("suction_max_pressure"))
                        pump.shutoff_dp = _safe_float(data.get("shutoff_dp"))
                        pump.shutoff_pressure = _safe_float(data.get("shutoff_pressure"))
                        pump.raise_to_shutoff_dp = _safe_float(data.get("raise_to_shutoff_dp"))
            row += 1
            continue
        if cell_a in ("CURVES",) or (
            cell_a in _SECTION_MARKERS_EQUIPMENT and cell_a != "SHUT OFF PRESSURE"
        ):
            break
        row += 1

    return pumps, row


def _parse_compressors_section(ws: Worksheet, start_row: int) -> tuple[list[CompressorData], int]:
    """Parse COMPRESSORS section from Equipment sheet."""
    header_row = start_row + 1
    compressors: list[CompressorData] = []
    row = start_row + 4

    while row <= ws.max_row:
        name_col = _find_column(ws, header_row, "Number")
        cell_a = ws.cell(row=row, column=name_col).value if name_col else None
        cell_a_str = _safe_str(cell_a)
        if cell_a_str in _SECTION_MARKERS_EQUIPMENT:
            break
        if not cell_a_str:
            row += 1
            continue

        data = _extract_row_data(ws, row, header_row, _COMPRESSOR_COL_MAP)
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
    """Parse EXCHANGERS section from Equipment sheet."""
    header_row = start_row + 1
    exchangers: list[ExchangerData] = []
    row = start_row + 4

    while row <= ws.max_row:
        name_col = _find_column(ws, header_row, "Number")
        cell_a = ws.cell(row=row, column=name_col).value if name_col else None
        cell_a_str = _safe_str(cell_a)
        if cell_a_str in _SECTION_MARKERS_EQUIPMENT:
            break
        if not cell_a_str:
            row += 1
            continue

        data = _extract_row_data(ws, row, header_row, _EXCHANGER_COL_MAP)
        exchangers.append(
            ExchangerData(
                name=_safe_str(data.get("name")),
                description=_safe_str(data.get("description")),
                type=_safe_str(data.get("type")),
                side=_safe_str(data.get("side")),
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
    """Parse MISCELLANEOUS section from Equipment sheet."""
    header_row = start_row + 1
    misc: list[MiscEquipmentData] = []
    row = start_row + 4

    while row <= ws.max_row:
        name_col = _find_column(ws, header_row, "Number")
        cell_a = ws.cell(row=row, column=name_col).value if name_col else None
        cell_a_str = _safe_str(cell_a)
        if cell_a_str in _SECTION_MARKERS_EQUIPMENT:
            break
        if not cell_a_str:
            row += 1
            continue

        data = _extract_row_data(ws, row, header_row, _MISC_COL_MAP)
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
