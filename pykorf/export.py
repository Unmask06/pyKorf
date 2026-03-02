"""
Export functionality for pyKorf models.

Supports exporting model data to various formats:
- JSON (with optional pretty printing)
- YAML
- Excel (requires openpyxl)
- CSV

Example:
    >>> from pykorf import Model
    >>> from pykorf.export import export_to_json, export_to_excel
    >>>
    >>> model = Model("Pumpcases.kdf")
    >>> export_to_json(model, "output.json", include_results=True)
    >>> export_to_excel(model, "output.xlsx")
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from pykorf.config import get_config
from pykorf.exceptions import ExportError
from pykorf.log import get_logger, log_operation
from pykorf.types import ExportOptions

if TYPE_CHECKING:
    from pykorf.model import Model

logger = get_logger(__name__)


def _element_to_dict(elem: Any, options: ExportOptions) -> dict[str, Any]:
    """Convert an element to a dictionary."""
    data: dict[str, Any] = {
        "index": elem.index,
        "name": elem.name,
        "type": elem.etype,
    }

    if elem.description:
        data["description"] = elem.description

    if options.include_geometry:
        try:
            from pykorf.layout import get_position

            pos = get_position(elem)
            if pos:
                data["position"] = {"x": pos[0], "y": pos[1]}
        except Exception:
            pass

    if options.include_results and hasattr(elem, "summary"):
        try:
            data["summary"] = elem.summary()
        except Exception:
            pass

    return data


def export_to_json(
    model: Model,
    path: str | Path,
    *,
    options: ExportOptions | None = None,
) -> None:
    """Export model data to JSON.

    Args:
        model: The model to export
        path: Output file path
        options: Export options

    Raises:
        ExportError: If export fails
    """
    options = options or ExportOptions()
    path = Path(path)

    with log_operation("export_to_json", path=str(path)):
        try:
            data = _model_to_dict(model, options)

            json_kwargs: dict[str, Any] = {
                "ensure_ascii": False,
            }
            if options.indent:
                json_kwargs["indent"] = options.indent

            # Use orjson if available for better performance
            try:
                import orjson

                output = orjson.dumps(data, option=orjson.OPT_INDENT_2 if options.indent else 0)
                path.write_bytes(output)
            except ImportError:
                path.write_text(
                    json.dumps(data, **json_kwargs),
                    encoding=options.encoding,
                )

            logger.info("export_to_json_success", path=str(path))

        except Exception as e:
            raise ExportError(
                f"Failed to export to JSON: {e}",
                context=None,
            ) from e


def export_to_yaml(
    model: Model,
    path: str | Path,
    *,
    options: ExportOptions | None = None,
) -> None:
    """Export model data to YAML.

    Args:
        model: The model to export
        path: Output file path
        options: Export options

    Raises:
        ExportError: If export fails
    """
    options = options or ExportOptions()
    path = Path(path)

    with log_operation("export_to_yaml", path=str(path)):
        try:
            import yaml

            data = _model_to_dict(model, options)

            yaml_content = yaml.dump(
                data,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )

            path.write_text(yaml_content, encoding=options.encoding)
            logger.info("export_to_yaml_success", path=str(path))

        except ImportError as e:
            raise ExportError(
                "PyYAML is required for YAML export. Install with: pip install pyyaml",
            ) from e
        except Exception as e:
            raise ExportError(f"Failed to export to YAML: {e}") from e


def export_to_excel(
    model: Model,
    path: str | Path,
    *,
    include_results: bool = True,
) -> None:
    """Export model data to Excel workbook.

    Creates multiple sheets:
    - Summary: Model overview
    - Pipes: Pipe data
    - Pumps: Pump data
    - Valves: Valve data
    - Feeds: Feed boundary conditions
    - Products: Product boundary conditions
    - Connectivity: Connection matrix

    Args:
        model: The model to export
        path: Output file path
        include_results: Whether to include calculated results

    Raises:
        ExportError: If export fails
    """
    path = Path(path)

    with log_operation("export_to_excel", path=str(path)):
        try:
            import pandas as pd

            with pd.ExcelWriter(path, engine="openpyxl") as writer:
                # Summary sheet
                summary_data = {
                    "Property": [
                        "File",
                        "Version",
                        "Cases",
                        "Pipes",
                        "Pumps",
                        "Feeds",
                        "Products",
                        "Valves",
                        "Check Valves",
                        "Orifices",
                        "Heat Exchangers",
                        "Compressors",
                        "Vessels",
                    ],
                    "Value": [
                        str(model.path),
                        model.version,
                        model.num_cases,
                        model.num_pipes,
                        model.num_pumps,
                        len([e for e in model.feeds.values() if e.index > 0]),
                        len([e for e in model.products.values() if e.index > 0]),
                        len([e for e in model.valves.values() if e.index > 0]),
                        len([e for e in model.check_valves.values() if e.index > 0]),
                        len([e for e in model.orifices.values() if e.index > 0]),
                        len([e for e in model.exchangers.values() if e.index > 0]),
                        len([e for e in model.compressors.values() if e.index > 0]),
                        len([e for e in model.vessels.values() if e.index > 0]),
                    ],
                }
                pd.DataFrame(summary_data).to_excel(writer, sheet_name="Summary", index=False)

                # Pipes sheet
                pipe_rows = []
                for idx, pipe in model.pipes.items():
                    if idx == 0:
                        continue
                    row = {
                        "Index": idx,
                        "Name": pipe.name,
                        "Diameter (in)": pipe.diameter_inch,
                        "Schedule": pipe.schedule,
                        "Length (m)": pipe.length_m,
                        "Material": pipe.material,
                    }
                    if include_results:
                        row["dP/100m (kPa)"] = pipe.pressure_drop_per_100m
                        row["Reynolds"] = pipe.reynolds_number
                    pipe_rows.append(row)

                if pipe_rows:
                    pd.DataFrame(pipe_rows).to_excel(writer, sheet_name="Pipes", index=False)

                # Pumps sheet
                pump_rows = []
                for idx, pump in model.pumps.items():
                    if idx == 0:
                        continue
                    row = {
                        "Index": idx,
                        "Name": pump.name,
                        "Type": pump.pump_type if hasattr(pump, "pump_type") else "Unknown",
                    }
                    if include_results and hasattr(pump, "head_m"):
                        row["Head (m)"] = pump.head_m
                        row["Power (kW)"] = pump.power_kW
                        row["Efficiency"] = pump.efficiency
                    pump_rows.append(row)

                if pump_rows:
                    pd.DataFrame(pump_rows).to_excel(writer, sheet_name="Pumps", index=False)

                # Case info
                if hasattr(model, "general"):
                    case_data = {
                        "Case Number": model.general.case_numbers,
                        "Description": model.general.case_descriptions,
                    }
                    pd.DataFrame(case_data).to_excel(writer, sheet_name="Cases", index=False)

            logger.info("export_to_excel_success", path=str(path), sheets=writer.sheets.keys())

        except ImportError as e:
            raise ExportError(
                "pandas and openpyxl are required for Excel export. "
                "Install with: pip install pandas openpyxl",
            ) from e
        except Exception as e:
            raise ExportError(f"Failed to export to Excel: {e}") from e


def export_to_csv(
    model: Model,
    directory: str | Path,
    *,
    element_type: Literal["all", "pipes", "pumps", "valves"] = "all",
    include_results: bool = True,
) -> list[Path]:
    """Export model data to CSV files.

    Args:
        model: The model to export
        directory: Output directory
        element_type: Which elements to export
        include_results: Whether to include calculated results

    Returns:
        List of created file paths

    Raises:
        ExportError: If export fails
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)

    created_files: list[Path] = []

    with log_operation("export_to_csv", directory=str(directory)):
        try:
            import pandas as pd

            # Export pipes
            if element_type in ("all", "pipes"):
                pipe_rows = []
                for idx, pipe in model.pipes.items():
                    if idx == 0:
                        continue
                    row = {
                        "index": idx,
                        "name": pipe.name,
                        "diameter_inch": pipe.diameter_inch,
                        "schedule": pipe.schedule,
                        "length_m": pipe.length_m,
                        "material": pipe.material,
                    }
                    if include_results:
                        row["pressure_drop_kpa_100m"] = pipe.pressure_drop_per_100m
                        row["reynolds_number"] = pipe.reynolds_number
                    pipe_rows.append(row)

                if pipe_rows:
                    path = directory / "pipes.csv"
                    pd.DataFrame(pipe_rows).to_csv(path, index=False)
                    created_files.append(path)

            # Export pumps
            if element_type in ("all", "pumps"):
                pump_rows = []
                for idx, pump in model.pumps.items():
                    if idx == 0:
                        continue
                    row = {"index": idx, "name": pump.name}
                    if include_results:
                        row["head_m"] = pump.head_m if hasattr(pump, "head_m") else None
                        row["power_kw"] = pump.power_kW if hasattr(pump, "power_kW") else None
                    pump_rows.append(row)

                if pump_rows:
                    path = directory / "pumps.csv"
                    pd.DataFrame(pump_rows).to_csv(path, index=False)
                    created_files.append(path)

            logger.info("export_to_csv_success", files=[str(f) for f in created_files])
            return created_files

        except ImportError as e:
            raise ExportError(
                "pandas is required for CSV export. Install with: pip install pandas",
            ) from e
        except Exception as e:
            raise ExportError(f"Failed to export to CSV: {e}") from e


def _model_to_dict(model: Model, options: ExportOptions) -> dict[str, Any]:
    """Convert model to dictionary representation."""
    data: dict[str, Any] = {
        "metadata": {
            "version": model.version,
            "file": str(model.path),
            "num_cases": model.num_cases,
        },
        "elements": {},
    }

    if options.include_metadata and hasattr(model, "general"):
        data["metadata"]["cases"] = model.general.case_descriptions
        data["metadata"]["units"] = model.general.units if hasattr(model.general, "units") else None

    # Export elements
    for elem in model.elements:
        etype = elem.etype.lower() + "s"
        if etype not in data["elements"]:
            data["elements"][etype] = []
        data["elements"][etype].append(_element_to_dict(elem, options))

    if options.include_connectivity:
        data["connectivity"] = _extract_connectivity(model)

    return data


def _extract_connectivity(model: Model) -> list[dict[str, Any]]:
    """Extract connectivity information."""
    connections = []

    for elem in model.elements:
        if elem.etype == "PIPE":
            continue

        try:
            from pykorf.connectivity import get_connections

            conns = get_connections(model, elem.name)
            if conns:
                connections.append(
                    {
                        "element": elem.name,
                        "type": elem.etype,
                        "connected_to": conns,
                    }
                )
        except Exception:
            pass

    return connections


_HEADER_SHEET = "_HEADER"
_LINE_NO_COL = "line_no"
_ETYPE_COL = "element_type"
_INDEX_COL = "index"
_PARAM_COL = "param"
_VALUES_COL = "values"
_RAW_LINE_COL = "raw_line"
_DF_COLUMNS = [_LINE_NO_COL, _ETYPE_COL, _INDEX_COL, _PARAM_COL, _VALUES_COL, _RAW_LINE_COL]
_HEADER_COLUMNS = [_LINE_NO_COL, _RAW_LINE_COL]


def model_to_dataframes(model: Model) -> dict[str, "pd.DataFrame"]:
    """Convert a Model to a dict of DataFrames, one per element type.

    Each DataFrame preserves the raw KDF record lines so that the model can
    be perfectly reconstructed via :func:`dataframes_to_kdf`.

    Verbatim/header lines (version string, blank lines) are stored in a
    special ``"_HEADER"`` DataFrame.  All other records are grouped by their
    element type (``"GEN"``, ``"PIPE"``, ``"PUMP"``, etc.).

    Every DataFrame contains a ``line_no`` column that records the original
    line position.  This is used during reconstruction to restore the exact
    file ordering.

    Args:
        model: The model to convert.

    Returns:
        A dict mapping sheet name → DataFrame.

    Raises:
        ExportError: If pandas is not installed.

    Example:
        ```python
        from pykorf import Model
        from pykorf.export import model_to_dataframes

        model = Model("Pumpcases.kdf")
        dfs = model_to_dataframes(model)
        for name, df in dfs.items():
            print(name, len(df))
        ```
    """
    try:
        import pandas as pd
    except ImportError as exc:
        raise ExportError(
            "pandas is required for DataFrame conversion. Install with: pip install pandas",
        ) from exc

    header_rows: list[dict[str, Any]] = []
    typed_rows: dict[str, list[dict[str, Any]]] = {}

    for line_no, rec in enumerate(model._parser.records):
        # Skip NUM records for non-zero indices (parser.save() skips these)
        if rec.element_type is not None and rec.param == "NUM" and rec.index != 0:
            continue

        raw = rec.to_line()
        if rec.element_type is None:
            header_rows.append({_LINE_NO_COL: line_no, _RAW_LINE_COL: raw})
        else:
            etype = rec.element_type
            typed_rows.setdefault(etype, []).append(
                {
                    _LINE_NO_COL: line_no,
                    _ETYPE_COL: etype,
                    _INDEX_COL: rec.index,
                    _PARAM_COL: rec.param,
                    _VALUES_COL: ",".join(str(v) for v in rec.values),
                    _RAW_LINE_COL: raw,
                }
            )

    result: dict[str, pd.DataFrame] = {}
    if header_rows:
        result[_HEADER_SHEET] = pd.DataFrame(header_rows, columns=_HEADER_COLUMNS)
    for etype, rows in typed_rows.items():
        result[etype] = pd.DataFrame(rows, columns=_DF_COLUMNS)
    return result


def dataframes_to_kdf(
    dfs: dict[str, "pd.DataFrame"],
    path: str | Path,
    encoding: str = "latin-1",
) -> None:
    """Write a dict of DataFrames (as produced by :func:`model_to_dataframes`) to a ``.kdf`` file.

    The raw lines are reassembled in their original order using the
    ``line_no`` column and written with ``latin-1`` encoding and ``\\r\\n``
    line endings — exactly as the KORF format requires.

    Args:
        dfs: Dict of DataFrames keyed by sheet name.
        path: Destination ``.kdf`` file path.
        encoding: File encoding (default ``"latin-1"``).

    Raises:
        ExportError: If the DataFrames are missing required columns.

    Example:
        ```python
        from pykorf.export import model_to_dataframes, dataframes_to_kdf

        dfs = model_to_dataframes(model)
        dataframes_to_kdf(dfs, "reconstructed.kdf")
        ```
    """
    try:
        import pandas as pd
    except ImportError as exc:
        raise ExportError(
            "pandas is required for DataFrame conversion. Install with: pip install pandas",
        ) from exc

    all_rows: list[tuple[int, str]] = []

    for sheet_name, df in dfs.items():
        if _LINE_NO_COL not in df.columns or _RAW_LINE_COL not in df.columns:
            raise ExportError(
                f"Sheet {sheet_name!r} is missing required columns "
                f"({_LINE_NO_COL!r}, {_RAW_LINE_COL!r}).",
            )
        for _, row in df.iterrows():
            line_no = int(row[_LINE_NO_COL])
            raw_line = str(row[_RAW_LINE_COL]) if pd.notna(row[_RAW_LINE_COL]) else ""
            all_rows.append((line_no, raw_line))

    # Sort by original line number to restore file order
    all_rows.sort(key=lambda t: t[0])

    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", encoding=encoding, newline="") as fh:
        for _, raw_line in all_rows:
            fh.write(raw_line + "\r\n")


def model_from_dataframes(dfs: dict[str, "pd.DataFrame"]) -> Model:
    """Create a :class:`Model` from a dict of DataFrames.

    This is the inverse of :func:`model_to_dataframes`.  A temporary
    ``.kdf`` file is written and then loaded, so the returned model
    behaves identically to one loaded from a regular KDF file.

    Args:
        dfs: Dict of DataFrames as returned by :func:`model_to_dataframes`.

    Returns:
        A new :class:`Model` instance.

    Raises:
        ExportError: If reconstruction fails.

    Example:
        ```python
        from pykorf.export import model_to_dataframes, model_from_dataframes

        dfs = model_to_dataframes(model)
        reconstructed = model_from_dataframes(dfs)
        ```
    """
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".kdf", delete=False, mode="w") as tmp:
        tmp_path = tmp.name

    try:
        dataframes_to_kdf(dfs, tmp_path)
        from pykorf.model import Model as _Model

        return _Model(tmp_path)
    except Exception as exc:
        raise ExportError(f"Failed to reconstruct model from DataFrames: {exc}") from exc
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def dataframes_to_excel(
    dfs: dict[str, "pd.DataFrame"],
    path: str | Path,
) -> None:
    """Write a dict of DataFrames to an Excel workbook.

    Each DataFrame becomes a separate sheet.  The sheet names
    correspond to the element types (``"GEN"``, ``"PIPE"``, etc.) plus
    a ``"_HEADER"`` sheet for verbatim lines.

    Args:
        dfs: Dict of DataFrames keyed by sheet name.
        path: Destination ``.xlsx`` file path.

    Raises:
        ExportError: If pandas or openpyxl is not installed.

    Example:
        ```python
        from pykorf.export import model_to_dataframes, dataframes_to_excel

        dfs = model_to_dataframes(model)
        dataframes_to_excel(dfs, "model.xlsx")
        ```
    """
    try:
        import pandas as pd
    except ImportError as exc:
        raise ExportError(
            "pandas and openpyxl are required for Excel export. "
            "Install with: pip install pandas openpyxl",
        ) from exc

    path = Path(path)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet_name, df in dfs.items():
            # Excel sheet names max 31 chars
            safe_name = sheet_name[:31]
            df.to_excel(writer, sheet_name=safe_name, index=False)


def excel_to_dataframes(path: str | Path) -> dict[str, "pd.DataFrame"]:
    """Read an Excel workbook back into a dict of DataFrames.

    This is the inverse of :func:`dataframes_to_excel`.

    Args:
        path: Path to the ``.xlsx`` file.

    Returns:
        Dict of DataFrames keyed by sheet name.

    Raises:
        ExportError: If pandas or openpyxl is not installed, or the file
            cannot be read.

    Example:
        ```python
        from pykorf.export import excel_to_dataframes, model_from_dataframes

        dfs = excel_to_dataframes("model.xlsx")
        model = model_from_dataframes(dfs)
        ```
    """
    try:
        import pandas as pd
    except ImportError as exc:
        raise ExportError(
            "pandas and openpyxl are required for Excel import. "
            "Install with: pip install pandas openpyxl",
        ) from exc

    path = Path(path)
    result: dict[str, pd.DataFrame] = {}
    xls = pd.ExcelFile(path, engine="openpyxl")
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name, dtype=str)
        # Ensure line_no is integer (read back as string from dtype=str)
        if _LINE_NO_COL in df.columns:
            df[_LINE_NO_COL] = df[_LINE_NO_COL].astype(int)
        result[sheet_name] = df
    return result


__all__ = [
    "export_to_json",
    "export_to_yaml",
    "export_to_excel",
    "export_to_csv",
    "model_to_dataframes",
    "dataframes_to_kdf",
    "model_from_dataframes",
    "dataframes_to_excel",
    "excel_to_dataframes",
]
