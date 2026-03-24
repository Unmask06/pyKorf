"""HMB (Heat and Material Balance) Excel to JSON converter and reader.

This module handles reading HMB data from Excel files, converting them to JSON
for faster subsequent reads, and providing lookup functionality.

The main entry point is :func:`apply_hmb` which takes an HMB JSON file and a
Model, extracts stream numbers from pipe NOTES, looks up fluid properties,
and returns ``{pipe_name: {PARAM: value_list}}`` for ``model.set_params()``.

Excel Format Expected:
    Column 0: Property names (TEMP, PRES, LF, LIQDEN, LIQVISC, etc.)
    Column 1: Unit (C, kPag, kg/m3, cP, etc.)
    Columns 2+: Stream numbers (S-101, S-102, etc.) with their values

Example:
    Stream   Unit   S-101    S-102
    TEMP     C      55       60
    PRES     kPag   101      105
    LF               1.0      1.0
    LIQDEN   kg/m3  1010     995
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pykorf.fluid import Fluid
from pykorf.use_case.exceptions import ExcelConversionError, StreamNotFoundError
from pykorf.use_case.line_number import parse_stream_from_notes

if TYPE_CHECKING:
    from pykorf.model import Model

logger = logging.getLogger("HMB")


@dataclass
class FluidProperties:
    """Fluid properties from HMB.

    Attributes:
        stream_no: Stream identifier (e.g., S-101)
        temp: Temperature in °C
        pres: Pressure in kPag
        lf: Liquid fraction (0-1)
        liqden: Liquid density in kg/m³
        liqvisc: Liquid viscosity in cP
        liqsur: Liquid surface tension in dyne/cm
        liqcon: Liquid thermal conductivity in W/m/K
        liqcp: Liquid specific heat in kJ/kg/K
        vapden: Vapor density in kg/m³
        vapvisc: Vapor viscosity in cP
        vapcon: Vapor thermal conductivity in W/m/K
        vapcp: Vapor specific heat in kJ/kg/K
    """

    stream_no: str
    temp: float | None = None
    pres: float | None = None
    lf: float | None = None
    liqden: float | None = None
    liqvisc: float | None = None
    liqsur: float | None = None
    liqcon: float | None = None
    liqcp: float | None = None
    vapden: float | None = None
    vapvisc: float | None = None
    vapcon: float | None = None
    vapcp: float | None = None


class HmbReader:
    """Reader for HMB data with Excel to JSON conversion."""

    PROPERTY_MAP = {
        "TEMP": "temp",
        "PRES": "pres",
        "LF": "lf",
        "LIQDEN": "liqden",
        "LIQVISC": "liqvisc",
        "LIQSUR": "liqsur",
        "LIQCON": "liqcon",
        "LIQCP": "liqcp",
        "VAPDEN": "vapden",
        "VAPVISC": "vapvisc",
        "VAPCON": "vapcon",
        "VAPCP": "vapcp",
    }

    def __init__(self, input_dir: Path | str | None = None):
        """Initialize HMB reader.

        Args:
            input_dir: Directory containing input Excel files. Defaults to Input subdirectory.
        """
        if input_dir is None:
            input_dir = Path(__file__).parent / "Input"
        self.input_dir = Path(input_dir)
        self._data: dict[str, FluidProperties] = {}

    def convert_excel_to_json(
        self,
        excel_path: Path | str,
        json_path: Path | str | None = None,
    ) -> Path:
        """Convert HMB Excel file to JSON.

        Args:
            excel_path: Path to Excel file
            json_path: Path for output JSON file. Defaults to same name with .json extension

        Returns:
            Path to created JSON file

        Raises:
            ExcelConversionError: If conversion fails
        """
        try:
            import pandas as pd
        except ImportError as e:
            raise ExcelConversionError("pandas is required for Excel conversion") from e

        from pykorf.utils import read_excel_safe

        excel_path = Path(excel_path)
        if json_path is None:
            json_path = excel_path.with_suffix(".json")
        else:
            json_path = Path(json_path)

        df = read_excel_safe(excel_path, header=None)

        stream_numbers: list[str] = []
        stream_data: dict[str, dict[str, float]] = {}

        for idx, row in df.iterrows():
            if idx == 0:
                for col_idx in range(2, len(row)):
                    val = row.iloc[col_idx]
                    if pd.notna(val):
                        stream_numbers.append(str(val).strip())
                        stream_data[str(val).strip()] = {}
                continue

            property_name = str(row.iloc[0]).strip().upper() if pd.notna(row.iloc[0]) else ""
            if not property_name or property_name == "NAN":
                continue

            prop_key = self.PROPERTY_MAP.get(property_name)
            if prop_key is None:
                continue

            for stream_no in stream_numbers:
                stream_col_idx = stream_numbers.index(stream_no) + 2
                if stream_col_idx < len(row):
                    val = row.iloc[stream_col_idx]
                    if pd.notna(val):
                        try:
                            stream_data[stream_no][prop_key] = float(val)
                        except (ValueError, TypeError):
                            pass

        hmb_data: dict[str, dict] = {}
        for stream_no, props in stream_data.items():
            hmb_data[stream_no] = props

        json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(hmb_data, f, indent=2)

        return json_path

    def load_json(self, json_path: Path | str) -> None:
        """Load HMB data from JSON file.

        Args:
            json_path: Path to JSON file
        """
        json_path = Path(json_path)

        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        self._data = {}
        for stream_no, props in data.items():
            self._data[stream_no] = FluidProperties(
                stream_no=stream_no,
                temp=props.get("temp"),
                pres=props.get("pres"),
                lf=props.get("lf"),
                liqden=props.get("liqden"),
                liqvisc=props.get("liqvisc"),
                liqsur=props.get("liqsur"),
                liqcon=props.get("liqcon"),
                liqcp=props.get("liqcp"),
                vapden=props.get("vapden"),
                vapvisc=props.get("vapvisc"),
                vapcon=props.get("vapcon"),
                vapcp=props.get("vapcp"),
            )

    def load(self, source: Path | str) -> None:
        """Load HMB data from Excel or JSON.

        Automatically converts Excel to JSON if needed.

        Args:
            source: Path to Excel or JSON file
        """
        source = Path(source)

        if source.suffix.lower() == ".xlsx":
            json_path = source.with_suffix(".json")

            if not json_path.exists():
                self.convert_excel_to_json(source, json_path)

            self.load_json(json_path)
        else:
            self.load_json(source)

    def lookup(self, stream_no: str) -> FluidProperties | None:
        """Lookup fluid properties by stream number.

        Args:
            stream_no: Stream identifier (e.g., S-101)

        Returns:
            FluidProperties if found, None otherwise
        """
        return self._data.get(stream_no)

    def get_all_streams(self) -> list[str]:
        """Get list of all stream numbers."""
        return list(self._data.keys())

    def get_properties(self, stream_no: str) -> FluidProperties | None:
        """Get fluid properties for a stream (alias for lookup)."""
        return self.lookup(stream_no)


# ------------------------------------------------------------------
# Standalone functions for simplified API
# ------------------------------------------------------------------


def get_stream_path(filename: str = "stream_data.json") -> Path:
    """Get the path to a stream data JSON file.

    Args:
        filename: Name of the stream data file (default: stream_data.json)

    Returns:
        Path to the stream data file in the data directory.
    """
    from pykorf.use_case.paths import ensure_data_dir

    safe_filename = Path(filename).name
    return ensure_data_dir() / safe_filename


def load_stream_data(filename: str = "stream_data.json") -> dict[str, Any]:
    """Load stream data from a JSON file.

    Args:
        filename: Name of the stream data file to load.

    Returns:
        Dictionary containing stream data.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    stream_path = get_stream_path(filename)
    with open(stream_path, encoding="utf-8") as f:
        return json.load(f)


def save_stream_data(data: dict[str, Any], filename: str = "stream_data.json") -> None:
    """Save stream data to a JSON file.

    Args:
        data: Dictionary containing stream data.
        filename: Name of the stream data file to save.
    """
    stream_path = get_stream_path(filename)
    with open(stream_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def import_stream_from_excel(
    excel_path: str | Path,
    output_filename: str = "stream_data.json",
) -> Path:
    """Import stream data from an Excel file and save as JSON.

    Uses the same logic as convert_hmb_excel() but saves to the data directory.

    Args:
        excel_path: Path to the Excel file containing stream data.
        output_filename: Name for the output JSON file.

    Returns:
        Path to the created JSON file.

    Raises:
        FileNotFoundError: If the Excel file doesn't exist.
        ImportError: If required Excel libraries are not installed.
    """
    excel_path = Path(excel_path)
    if not excel_path.exists():
        raise FileNotFoundError(f"Excel file not found: {excel_path}")

    output_path = get_stream_path(output_filename)
    convert_hmb_excel(excel_path, output_path)

    return output_path


def convert_hmb_excel(
    excel_path: Path | str,
    json_path: Path | str | None = None,
) -> Path:
    """Convert an HMB Excel file to JSON format.

    Args:
        excel_path: Path to the HMB Excel file.
        json_path: Output path.  Defaults to *excel_path* with ``.json`` suffix.

    Returns:
        Path to the created JSON file.

    Raises:
        ExcelConversionError: If pandas is not installed or conversion fails.
    """
    reader = HmbReader()
    return reader.convert_excel_to_json(excel_path, json_path)


def load_hmb(source: Path | str) -> dict[str, dict[str, Any]]:
    """Load HMB data from a JSON file (or Excel, auto-converting first).

    Args:
        source: Path to HMB ``.json`` or ``.xlsx`` file.

    Returns:
        ``{stream_no: {property_name: value}}`` where *property_name*
        matches :class:`FluidProperties` field names.
    """
    reader = HmbReader()
    reader.load(source)
    return {
        stream_no: {k: v for k, v in vars(props).items() if k != "stream_no" and v is not None}
        for stream_no, props in reader._data.items()
    }


def lookup_stream(
    hmb_data: dict[str, dict[str, Any]],
    stream_no: str,
) -> dict[str, Any]:
    """Look up fluid properties by stream number.

    Args:
        hmb_data: Loaded HMB data (from :func:`load_hmb`).
        stream_no: Stream identifier (e.g., ``"S-101"``).

    Returns:
        ``{temp: 55.0, pres: 101.0, ...}`` dict of properties.

    Raises:
        StreamNotFoundError: If the stream number is not found.
    """
    if stream_no not in hmb_data:
        raise StreamNotFoundError(f"Stream not found: {stream_no}")
    return hmb_data[stream_no]


def _create_fluid_from_props(props: dict[str, Any]) -> Fluid:
    """Create a Fluid object from HMB properties dict."""
    return Fluid(
        temp=props.get("temp"),
        pres=props.get("pres"),
        lf=props.get("lf"),
        liqden=props.get("liqden"),
        liqvisc=props.get("liqvisc"),
        liqsur=props.get("liqsur"),
        liqcon=props.get("liqcon"),
        liqcp=props.get("liqcp"),
        vapden=props.get("vapden"),
        vapvisc=props.get("vapvisc"),
        vapcon=props.get("vapcon"),
        vapcp=props.get("vapcp"),
    )


def apply_hmb(
    hmb_source: Path | str,
    model: Model,
    *,
    delimiter: str = ";",
    save: bool = True,
) -> list[str]:
    """Apply HMB fluid properties to all pipes in *model*.

    For each pipe whose ``NOTES`` field contains a stream number,
    this function looks up the fluid properties in the HMB data
    and applies them directly to the pipe using :class:`~pykorf.fluid.Fluid`.

    Pipes with empty NOTES or missing stream numbers are silently skipped.

    Args:
        hmb_source: Path to HMB JSON (or Excel) file.
        model: Loaded :class:`~pykorf.model.Model`.
        delimiter: NOTES field delimiter (default ``";"``).
        save: Whether to save the model after applying changes (default ``True``).

    Returns:
        List of pipe names that were updated.

    Raises:
        StreamNotFoundError: If a stream number from NOTES is not found in HMB.

    Example:
        ```python
        from pykorf import Model
        from pykorf.use_case.hmb import apply_hmb

        model = Model("model.kdf")
        updated_pipes = apply_hmb("Stream Data.json", model)
        print(f"Updated {len(updated_pipes)} pipes with fluid properties")
        ```
    """
    hmb_data = load_hmb(hmb_source)
    updated_pipes: list[str] = []

    for idx in range(1, model.num_pipes + 1):
        pipe = model.pipes[idx]
        notes = pipe.notes

        if not notes or not notes.strip():
            logger.warning("Pipe %s: empty NOTES, skipping HMB", pipe.name)
            continue

        stream_no = parse_stream_from_notes(notes, delimiter)
        if not stream_no:
            logger.warning("Pipe %s: no stream number in NOTES: %r, skipping HMB", pipe.name, notes)
            continue

        try:
            props = lookup_stream(hmb_data, stream_no)
        except StreamNotFoundError as exc:
            logger.warning("Pipe %s: %s, skipping HMB", pipe.name, exc)
            continue

        fluid = _create_fluid_from_props(props)

        # Apply fluid directly to the pipe
        fluid.apply_to_pipes(model, [pipe.name])

        logger.info(
            "Pipe %s: stream=%s -> temp=%s, pres=%s",
            pipe.name,
            stream_no,
            props.get("temp"),
            props.get("pres"),
        )

        updated_pipes.append(pipe.name)

    if save and updated_pipes:
        model.save()

    return updated_pipes
