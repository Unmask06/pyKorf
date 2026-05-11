"""Column mapping constants and helpers for KORF Excel report parsing."""

from __future__ import annotations

from openpyxl.worksheet.worksheet import Worksheet

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
    "raise_to_shutoff_dp": 11,
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
    "dp": 11,
    "pressure_in": 13,
    "pressure_out": 14,
    "pipe_inlet": 15,
    "pipe_outlet": 16,
}

_MISC_COL_MAP: dict[str, int] = {
    "name": 1,
    "description": 2,
    "dp": 12,
    "pressure_in": 14,
    "pressure_out": 15,
    "pipe_inlet": 16,
    "pipe_outlet": 17,
}


def _find_column(ws: Worksheet, header_row: int, header_name: str, offset: int = 0) -> int:
    """Find column index by searching header row for a header name."""
    for col in range(1, ws.max_column + 1):
        val = ws.cell(row=header_row, column=col).value
        if val and str(val).strip() == header_name:
            return col + offset
    return -1
