"""I/O service for KORF models.

This module provides the :class:`IOService` which encapsulates save/export/import
capabilities for a model. It delegates to the model's parser for low-level
operations while providing high-level I/O methods.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

import pandas as pd

from pykorf.exceptions import ExportError
from pykorf.log import get_logger, log_operation
from pykorf.types import ExportOptions

if TYPE_CHECKING:
    from pykorf.model import Model

logger = get_logger(__name__)

# DataFrame column constants
_HEADER_SHEET = "_HEADER"
_LINE_NO_COL = "line_no"
_ETYPE_COL = "element_type"
_INDEX_COL = "index"
_PARAM_COL = "param"
_VALUES_COL = "values"
_RAW_LINE_COL = "raw_line"
_DF_COLUMNS = [
    _LINE_NO_COL,
    _ETYPE_COL,
    _INDEX_COL,
    _PARAM_COL,
    _VALUES_COL,
    _RAW_LINE_COL,
]
_HEADER_COLUMNS = [_LINE_NO_COL, _RAW_LINE_COL]


@dataclass(frozen=True, slots=True)
class IOService:
    """Service providing I/O and export functionality for a Model.

    This service encapsulates all file operations including saving to KDF format,
    exporting to Excel/DataFrames, and related serialization tasks. It requires
    a Model instance to operate on.

    Attributes:
        model: The Model instance this service operates on.

    Example:
        >>> from pykorf import Model
        >>> model = Model("Pumpcases.kdf")
        >>> model.io.save()  # Delegates to IOService
        >>> dfs = model.io.to_dataframes()
    """

    model: Model

    def save(self, path: str | Path | None = None, *, check_layout: bool = True) -> None:
        """Serialize the (possibly modified) model back to a .kdf file.

        Parameters
        ----------
        path:
            Destination path. If *None*, overwrites the source file.
        check_layout:
            If True (default), validate layout before saving and warn about
            overlapping elements or elements outside bounds.

        Example:
            >>> model.io.save()  # Overwrite original
            >>> model.io.save("new_file.kdf")  # Save as new file
        """
        if check_layout:
            issues = self.model.check_layout()
            if issues:
                _logger = logging.getLogger(__name__)
                _logger.warning(
                    f"Layout issues detected ({len(issues)}): "
                    "Run model.auto_layout() to fix, or save with check_layout=False to ignore"
                )
                for issue in issues[:5]:  # Log first 5
                    _logger.warning(f"  - {issue}")

        dest_path = path or self.model._parser.path
        print(f"Saving model to {dest_path}...")
        self.model._parser.save(path)

    def save_as(self, path: str | Path, *, check_layout: bool = True) -> None:
        """Save to a new path (alias for :meth:`save` with a path argument).

        Parameters
        ----------
        path:
            Destination path for the saved file.
        check_layout:
            If True (default), validate layout before saving.
        """
        self.save(path, check_layout=check_layout)

    def to_dataframes(self) -> dict[str, pd.DataFrame]:
        """Convert the model to a dict of DataFrames (one per element type).

        Each DataFrame preserves the raw KDF record lines so that the model
        can be perfectly reconstructed. Verbatim / header lines are stored
        in a ``"_HEADER"`` DataFrame.

        Returns:
            ``dict[str, pd.DataFrame]`` keyed by element type name.

        Raises:
            ExportError: If *pandas* is not installed.

        Example:
            >>> dfs = model.io.to_dataframes()
            >>> for name, df in dfs.items():
            ...     print(name, len(df))
        """
        return self._model_to_dataframes()

    def to_excel(self, path: str | Path) -> None:
        """Export the model to an Excel workbook with lossless round-trip fidelity.

        Each element type is written to a separate sheet. The workbook
        can be read back to produce an identical ``.kdf`` file.

        Parameters
        ----------
        path:
            Destination ``.xlsx`` file path.

        Raises:
            ExportError: If *pandas* or *openpyxl* is not installed.

        Example:
            >>> model.io.to_excel("Pumpcases.xlsx")
        """
        dfs = self._model_to_dataframes()
        self._dataframes_to_excel(dfs, path)

    def export_to_json(
        self,
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
                data = self._model_to_dict(options)

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
        self,
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

                data = self._model_to_dict(options)

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
        self,
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
                            str(self.model.path),
                            self.model.version,
                            self.model.num_cases,
                            self.model.num_pipes,
                            self.model.num_pumps,
                            len([e for e in self.model.feeds.values() if e.index > 0]),
                            len([e for e in self.model.products.values() if e.index > 0]),
                            len([e for e in self.model.valves.values() if e.index > 0]),
                            len([e for e in self.model.check_valves.values() if e.index > 0]),
                            len([e for e in self.model.orifices.values() if e.index > 0]),
                            len([e for e in self.model.exchangers.values() if e.index > 0]),
                            len([e for e in self.model.compressors.values() if e.index > 0]),
                            len([e for e in self.model.vessels.values() if e.index > 0]),
                        ],
                    }
                    pd.DataFrame(summary_data).to_excel(writer, sheet_name="Summary", index=False)

                    # Pipes sheet
                    pipe_rows = []
                    for idx, pipe in self.model.pipes.items():
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
                    for idx, pump in self.model.pumps.items():
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
                    if hasattr(self.model, "general"):
                        case_data = {
                            "Case Number": self.model.general.case_numbers,
                            "Description": self.model.general.case_descriptions,
                        }
                        pd.DataFrame(case_data).to_excel(writer, sheet_name="Cases", index=False)

                logger.info("export_to_excel_success", path=str(path))

            except ImportError as e:
                raise ExportError(
                    "pandas and openpyxl are required for Excel export. "
                    "Install with: pip install pandas openpyxl",
                ) from e
            except Exception as e:
                raise ExportError(f"Failed to export to Excel: {e}") from e

    def export_to_csv(
        self,
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
                # Export pipes
                if element_type in ("all", "pipes"):
                    pipe_rows = []
                    for idx, pipe in self.model.pipes.items():
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
                    for idx, pump in self.model.pumps.items():
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

    def _model_to_dataframes(self) -> dict[str, pd.DataFrame]:
        """Convert the model to a dict of DataFrames, one per element type.

        Each DataFrame preserves the raw KDF record lines so that the model can
        be perfectly reconstructed. Verbatim/header lines (version string, blank
        lines) are stored in a special ``"_HEADER"`` DataFrame. All other records
        are grouped by their element type (``"GEN"``, ``"PIPE"``, ``"PUMP"``, etc.).

        Every DataFrame contains a ``line_no`` column that records the original
        line position. This is used during reconstruction to restore the exact
        file ordering.

        Returns:
            A dict mapping sheet name → DataFrame.

        Raises:
            ExportError: If pandas is not installed.
        """
        header_rows: list[dict] = []
        typed_rows: dict[str, list[dict]] = {}

        from pykorf.utils import format_line

        for line_no, rec in enumerate(self.model._parser.records):
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
                        _VALUES_COL: format_line(rec.values),
                        _RAW_LINE_COL: raw,
                    }
                )

        result: dict[str, pd.DataFrame] = {}
        if header_rows:
            result[_HEADER_SHEET] = pd.DataFrame(header_rows, columns=_HEADER_COLUMNS)
        for etype, rows in typed_rows.items():
            result[etype] = pd.DataFrame(rows, columns=_DF_COLUMNS)
        return result

    def _model_to_dict(self, options: ExportOptions) -> dict[str, Any]:
        """Convert model to dictionary representation."""
        data: dict[str, Any] = {
            "metadata": {
                "version": self.model.version,
                "file": str(self.model.path),
                "num_cases": self.model.num_cases,
            },
            "elements": {},
        }

        if options.include_metadata and hasattr(self.model, "general"):
            data["metadata"]["cases"] = self.model.general.case_descriptions
            data["metadata"]["units"] = (
                self.model.general.units if hasattr(self.model.general, "units") else None
            )

        # Export elements
        for elem in self.model.elements:
            etype = elem.etype.lower() + "s"
            if etype not in data["elements"]:
                data["elements"][etype] = []
            data["elements"][etype].append(self._element_to_dict(elem, options))

        if options.include_connectivity:
            data["connectivity"] = self._extract_connectivity()

        return data

    def _element_to_dict(self, elem: Any, options: ExportOptions) -> dict[str, Any]:
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
                pos = self.model._layout_service._get_position(elem)
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

    def _extract_connectivity(self) -> list[dict[str, Any]]:
        """Extract connectivity information."""
        connections = []

        for elem in self.model.elements:
            if elem.etype == "PIPE":
                continue

            try:
                conns = self.model.get_connection(elem.name)
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

    def _dataframes_to_excel(
        self,
        dfs: dict[str, pd.DataFrame],
        path: str | Path,
    ) -> None:
        """Write a dict of DataFrames to an Excel workbook.

        Each DataFrame becomes a separate sheet. The sheet names
        correspond to the element types (``"GEN"``, ``"PIPE"``, etc.) plus
        a ``"_HEADER"`` sheet for verbatim lines.

        Parameters
        ----------
        dfs:
            Dict of DataFrames keyed by sheet name.
        path:
            Destination ``.xlsx`` file path.

        Raises:
            ExportError: If pandas or openpyxl is not installed.
        """
        path = Path(path)
        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            for sheet_name, df in dfs.items():
                # Excel sheet names max 31 chars
                safe_name = sheet_name[:31]
                df.to_excel(writer, sheet_name=safe_name, index=False)

    @staticmethod
    def _excel_to_dataframes(path: str | Path) -> dict[str, pd.DataFrame]:
        """Read an Excel workbook back into a dict of DataFrames.

        This is the inverse of :meth:`_dataframes_to_excel`.

        Parameters
        ----------
        path:
            Path to the ``.xlsx`` file.

        Returns:
            Dict of DataFrames keyed by sheet name.

        Raises:
            ExportError: If pandas or openpyxl is not installed, or the file
                cannot be read.
        """
        from pykorf.utils import read_excel_safe

        path = Path(path)
        sheets = read_excel_safe(path, sheet_name=None, dtype=str)
        if not isinstance(sheets, dict):
            sheets = {path.stem: sheets}

        result: dict[str, pd.DataFrame] = {}
        for sheet_name, df in sheets.items():
            if _LINE_NO_COL in df.columns:
                df[_LINE_NO_COL] = df[_LINE_NO_COL].astype(int)
            result[sheet_name] = df
        return result

    @staticmethod
    def _parse_values_string(values_str: str) -> list[str]:
        """Parse a comma-separated values string back to a list.

        Handles quoted strings and numeric values correctly.

        Parameters
        ----------
        values_str:
            Comma-separated values string to parse.

        Returns:
            List of parsed value strings.
        """
        from pykorf.utils import parse_line

        if not values_str:
            return []
        # Use parse_line to properly handle CSV quoting
        parsed = parse_line(values_str)
        return parsed if parsed else []

    @staticmethod
    def _build_kdf_line(etype: str, idx: int, param: str, values: list[str]) -> str:
        r"""Build a KDF line from element type, index, param, and values.

        Format: \\ETYPE,idx,"PARAM",value1,value2,...

        Parameters
        ----------
        etype:
            Element type (e.g., "PIPE", "PUMP").
        idx:
            Element index.
        param:
            Parameter name.
        values:
            List of parameter values.

        Returns:
            Formatted KDF line string.
        """
        from pykorf.utils import format_line

        parts: list = [f"\\{etype.upper()}", idx, param]
        parts.extend(values)
        return format_line(parts)

    @classmethod
    def model_from_dataframes(cls, dfs: dict[str, pd.DataFrame]) -> Model:
        """Create a :class:`Model` from a dict of DataFrames.

        This is the inverse of :meth:`_model_to_dataframes`. Records are
        built directly from the DataFrame columns and injected into a
        :class:`Model` instance — no temporary file is created.

        Args:
            dfs: Dict of DataFrames as returned by :meth:`_model_to_dataframes`.

        Returns:
            A new :class:`Model` instance.

        Raises:
            ExportError: If reconstruction fails.

        Example:
            ```python
            from pykorf.model.services.io import IOService
            dfs = model.io.to_dataframes()
            reconstructed = IOService.model_from_dataframes(dfs)
            ```
        """
        from pykorf.model import Model as _Model

        try:
            records = cls._dataframes_to_records(dfs)
        except ExportError:
            raise
        except Exception as exc:
            raise ExportError(f"Failed to reconstruct model from DataFrames: {exc}") from exc

        model = _Model()  # blank model from default template
        model._parser._records = records
        model._parser.path = Path("untitled.kdf")  # prevent accidental template overwrite
        model._build_collections()
        return model

    @classmethod
    def dataframes_to_kdf(
        cls,
        dfs: dict[str, pd.DataFrame],
        path: str | Path,
        encoding: str = "latin-1",
    ) -> None:
        r"""Write a dict of DataFrames (as produced by :meth:`_model_to_dataframes`) to a ``.kdf`` file.

        The raw lines are reassembled in their original order using the
        ``line_no`` column and written with ``latin-1`` encoding and ``\r\n``
        line endings — exactly as the KORF format requires.

        Args:
            dfs: Dict of DataFrames keyed by sheet name.
            path: Destination ``.kdf`` file path.
            encoding: File encoding (default ``"latin-1"``).

        Raises:
            ExportError: If the DataFrames are missing required columns.

        Example:
            ```python
            from pykorf.model.services.io import IOService
            dfs = model.io.to_dataframes()
            IOService.dataframes_to_kdf(dfs, "reconstructed.kdf")
            ```
        """
        all_rows: list[tuple[int, str]] = []

        for sheet_name, df in dfs.items():
            if _LINE_NO_COL not in df.columns:
                raise ExportError(
                    f"Sheet {sheet_name!r} is missing required column {_LINE_NO_COL!r}.",
                )

            # Check if this is a header sheet (no element_type column)
            is_header_sheet = _ETYPE_COL not in df.columns

            for _, row in df.iterrows():
                line_no = int(row[_LINE_NO_COL])  # type: ignore[arg-type]

                if is_header_sheet:
                    # Header sheet: use raw_line column
                    raw_line_val = row.get(_RAW_LINE_COL, "")
                    raw_line = str(raw_line_val) if pd.notna(raw_line_val) else ""  # type: ignore[arg-type]
                    all_rows.append((line_no, raw_line))
                else:
                    # Element sheet: prefer raw_line for perfect fidelity
                    raw_line_val = row.get(_RAW_LINE_COL) if _RAW_LINE_COL in df.columns else None
                    if raw_line_val is not None and pd.notna(raw_line_val):  # type: ignore[arg-type]
                        # Use raw_line directly to preserve original quoting
                        raw_line = str(raw_line_val)
                        all_rows.append((line_no, raw_line))
                    elif _VALUES_COL in df.columns:
                        # Fallback: rebuild from values column
                        values_val = row.get(_VALUES_COL)
                        if values_val is not None and pd.notna(values_val):  # type: ignore[arg-type]
                            # Rebuild KDF line from parsed columns
                            etype = str(row[_ETYPE_COL])
                            idx = int(row[_INDEX_COL])  # type: ignore[arg-type]
                            param = str(row[_PARAM_COL])
                            values_str = str(values_val)
                            # Parse values string (comma-separated) back to list
                            values = cls._parse_values_string(values_str)
                            # Build KDF line
                            kdf_line = cls._build_kdf_line(etype, idx, param, values)
                            all_rows.append((line_no, kdf_line))
                    else:
                        # Skip rows with no data
                        continue

        # Sort by original line number to restore file order
        all_rows.sort(key=lambda t: t[0])

        dest = Path(path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("w", encoding=encoding, newline="") as fh:
            for _, line in all_rows:
                fh.write(line + "\r\n")

    @classmethod
    def _dataframes_to_records(
        cls,
        dfs: dict[str, pd.DataFrame],
    ) -> list:
        """Convert DataFrames to a sorted list of :class:`KdfRecord` objects.

        Builds records directly from DataFrame columns without writing a
        temporary file. Header rows use the ``raw_line`` column; element
        rows reconstruct records from ``element_type``, ``index``,
        ``param``, and ``values`` columns.

        Args:
            dfs: Dict of DataFrames as produced by :meth:`_model_to_dataframes`.

        Returns:
            Sorted list of KdfRecord objects in original file order.

        Raises:
            ExportError: If required columns are missing.
        """
        from pykorf.parser import _ETYPE_RE, KdfRecord
        from pykorf.utils import parse_line

        indexed: list[tuple[int, KdfRecord]] = []

        for sheet_name, df in dfs.items():
            if _LINE_NO_COL not in df.columns:
                raise ExportError(
                    f"Sheet {sheet_name!r} is missing required column {_LINE_NO_COL!r}.",
                )

            is_header = _ETYPE_COL not in df.columns

            for _, row in df.iterrows():
                line_no = int(row[_LINE_NO_COL])

                if is_header:
                    raw_val = row.get(_RAW_LINE_COL, "")
                    raw = str(raw_val) if pd.notna(raw_val) else ""
                    indexed.append((line_no, KdfRecord(None, None, None, [], raw_line=raw)))
                    continue

                # Element sheet — use raw_line for perfect round-trip fidelity
                raw_val = row.get(_RAW_LINE_COL) if _RAW_LINE_COL in df.columns else None
                if raw_val is not None and pd.notna(raw_val):
                    # Rebuild from raw_line to preserve original quoting
                    raw_line = str(raw_val)
                    tokens = parse_line(raw_line)
                    if tokens:
                        m = _ETYPE_RE.match(tokens[0])
                        if m and len(tokens) >= 3:
                            etype = m.group(1).upper()
                            try:
                                idx = int(tokens[1])
                            except (ValueError, IndexError):
                                indexed.append(
                                    (line_no, KdfRecord(None, None, None, [], raw_line=raw_line))
                                )
                                continue
                            param = tokens[2].strip('"').upper()
                            vals = tokens[3:]
                            indexed.append(
                                (line_no, KdfRecord(etype, idx, param, vals, raw_line=raw_line))
                            )
                        else:
                            indexed.append(
                                (line_no, KdfRecord(None, None, None, [], raw_line=raw_line))
                            )
                    else:
                        indexed.append(
                            (line_no, KdfRecord(None, None, None, [], raw_line=raw_line))
                        )
                elif _VALUES_COL in df.columns:
                    # Fallback: rebuild from values column (when raw_line not available)
                    values_val = row.get(_VALUES_COL)
                    if values_val is not None and pd.notna(values_val):
                        etype = str(row[_ETYPE_COL]).upper()
                        idx = int(row[_INDEX_COL])
                        param = str(row[_PARAM_COL]).upper()
                        values = cls._parse_values_string(str(values_val))
                        indexed.append((line_no, KdfRecord(etype, idx, param, values, raw_line="")))
                else:
                    # Skip rows with no data
                    continue

        # Sort by original line number to restore file order
        indexed.sort(key=lambda t: t[0])
        return [rec for _, rec in indexed]

    @classmethod
    def excel_to_dataframes(cls, path: str | Path) -> dict[str, pd.DataFrame]:
        """Read an Excel workbook back into a dict of DataFrames.

        This is the inverse of :meth:`dataframes_to_excel`.

        Args:
            path: Path to the ``.xlsx`` file.

        Returns:
            Dict of DataFrames keyed by sheet name.

        Raises:
            ExportError: If pandas or openpyxl is not installed, or the file
                cannot be read.

        Example:
            ```python
            from pykorf.model.services.io import IOService
            dfs = IOService.excel_to_dataframes("model.xlsx")
            model = IOService.model_from_dataframes(dfs)
            ```
        """
        return cls._excel_to_dataframes(path)

    @classmethod
    def dataframes_to_excel(
        cls,
        dfs: dict[str, pd.DataFrame],
        path: str | Path,
    ) -> None:
        """Write a dict of DataFrames to an Excel workbook.

        Each DataFrame becomes a separate sheet. The sheet names
        correspond to the element types (``"GEN"``, ``"PIPE"``, etc.) plus
        a ``"_HEADER"`` sheet for verbatim lines.

        Args:
            dfs: Dict of DataFrames keyed by sheet name.
            path: Destination ``.xlsx`` file path.

        Raises:
            ExportError: If pandas or openpyxl is not installed.

        Example:
            ```python
            from pykorf.model.services.io import IOService
            dfs = model.io.to_dataframes()
            IOService.dataframes_to_excel(dfs, "model.xlsx")
            ```
        """
        path = Path(path)
        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            for sheet_name, df in dfs.items():
                # Excel sheet names max 31 chars
                safe_name = sheet_name[:31]
                df.to_excel(writer, sheet_name=safe_name, index=False)


# Note: from_dataframes and from_excel are classmethods that CREATE Model instances.
# These remain on the Model class as factory methods, not in this service.
# The service only handles instance-based operations (save, export) where a Model
# instance already exists.


# Backward compatibility: module-level functions that delegate to IOService


def model_to_dataframes(model: Model) -> dict[str, pd.DataFrame]:
    """Convert a Model to a dict of DataFrames, one per element type.

    Each DataFrame preserves the raw KDF record lines so that the model can
    be perfectly reconstructed via :func:`dataframes_to_kdf`.

    Verbatim/header lines (version string, blank lines) are stored in a
    special ``"_HEADER"`` DataFrame. All other records are grouped by their
    element type (``"GEN"``, ``"PIPE"``, ``"PUMP"``, etc.).

    Every DataFrame contains a ``line_no`` column that records the original
    line position. This is used during reconstruction to restore the exact
    file ordering.

    Args:
        model: The model to convert.

    Returns:
        A dict mapping sheet name → DataFrame.

    Raises:
        ExportError: If pandas is not installed.
    """
    return IOService(model=model)._model_to_dataframes()


def model_from_dataframes(dfs: dict[str, pd.DataFrame]) -> Model:
    """Create a :class:`Model` from a dict of DataFrames.

    This is the inverse of :func:`model_to_dataframes`. Records are
    built directly from the DataFrame columns and injected into a
    :class:`Model` instance — no temporary file is created.

    Args:
        dfs: Dict of DataFrames as returned by :func:`model_to_dataframes`.

    Returns:
        A new :class:`Model` instance.

    Raises:
        ExportError: If reconstruction fails.
    """
    return IOService.model_from_dataframes(dfs)


def dataframes_to_kdf(
    dfs: dict[str, pd.DataFrame],
    path: str | Path,
    encoding: str = "latin-1",
) -> None:
    """Write a dict of DataFrames to a ``.kdf`` file.

    Args:
        dfs: Dict of DataFrames keyed by sheet name.
        path: Destination ``.kdf`` file path.
        encoding: File encoding (default ``"latin-1"``).
    """
    IOService.dataframes_to_kdf(dfs, path, encoding)


def dataframes_to_excel(
    dfs: dict[str, pd.DataFrame],
    path: str | Path,
) -> None:
    """Write a dict of DataFrames to an Excel workbook.

    Args:
        dfs: Dict of DataFrames keyed by sheet name.
        path: Destination ``.xlsx`` file path.
    """
    IOService.dataframes_to_excel(dfs, path)


def excel_to_dataframes(path: str | Path) -> dict[str, pd.DataFrame]:
    """Read an Excel workbook back into a dict of DataFrames.

    Args:
        path: Path to the ``.xlsx`` file.

    Returns:
        Dict of DataFrames keyed by sheet name.
    """
    return IOService.excel_to_dataframes(path)


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
    IOService(model=model).export_to_json(path, options=options)


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
    IOService(model=model).export_to_yaml(path, options=options)


def export_to_excel(
    model: Model,
    path: str | Path,
    *,
    include_results: bool = True,
) -> None:
    """Export model data to Excel workbook.

    Args:
        model: The model to export
        path: Output file path
        include_results: Whether to include calculated results

    Raises:
        ExportError: If export fails
    """
    IOService(model=model).export_to_excel(path, include_results=include_results)


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
    return IOService(model=model).export_to_csv(
        directory, element_type=element_type, include_results=include_results
    )


__all__ = [
    "IOService",
    # Module-level functions for backward compatibility
    "dataframes_to_excel",
    "dataframes_to_kdf",
    "excel_to_dataframes",
    "export_to_csv",
    "export_to_excel",
    "export_to_json",
    "export_to_yaml",
    "model_from_dataframes",
    "model_to_dataframes",
]
