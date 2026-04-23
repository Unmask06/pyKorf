import logging
import re
from collections.abc import Mapping
from typing import Any

import openpyxl
import pandas as pd
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.utils.dataframe import dataframe_to_rows

from pykorf import Model
from pykorf.core.reports.unit_converter import UnitConverter

_logger = logging.getLogger(__name__)


# ── Validation string parsing ──────────────────────────────────────────

_SEVERITY_RULES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"fails sizing|exceeds criteria|mismatch", re.I), "Error"),
    (re.compile(r"references pipe index .+ which does not exist", re.I), "Error"),
    (
        re.compile(r"missing line number|missing NAME|missing CON|missing|not found in PMS", re.I),
        "Warning",
    ),
    (re.compile(r"Add Title", re.I), "Info"),
    (re.compile(r"pipe.*criteria", re.I), "Error"),
    (re.compile(r"CONN|connectiv|nozzle|CON value", re.I), "Error"),
]


def _classify_issue(msg: str) -> tuple[str, str, str]:
    """Classify a validation message into (severity, category, element_name).

    Args:
        msg: Human-readable validation issue string.

    Returns:
        Tuple of (severity, category, element_name_or_empty).
    """
    from pykorf.app.validation import classify_issue

    elem_name = ""
    for pat in [
        re.compile(r"Pipe ['\"]?(\S+?)['\"]?[:\s]"),
        re.compile(r"PIPE (\S+?) \("),
        re.compile(r"^(\S+?) \((?:VALVE|PUMP|FEED|PRODUCT|COMPRESSOR|TEE|JUNC|VESSEL)\)"),
    ]:
        m = pat.search(msg)
        if m:
            elem_name = m.group(1)
            break

    category = classify_issue(msg)

    for pattern, severity in _SEVERITY_RULES:
        if pattern.search(msg):
            return severity, category, elem_name

    return "Warning", category, elem_name


class ResultExporter:
    """A scalable exporter to extract calculated results and input criteria from a pyKorf Model
    and save them into a multi-sheet Excel report or DataFrame dictionary.

    This class correctly relies on the element 'summary' methods to parse the dynamic units
    directly from the underlying KDF records and format them for export.
    """

    def __init__(
        self,
        model: Model,
        basis: str = "",
        remarks: str = "",
        hold: str = "",
        references: list[dict] | None = None,
        justifications: dict[str, str] | None = None,
    ):
        self.model = model
        self._basis = basis
        self._remarks = remarks
        self._hold = hold
        self._references = references or []
        self._justifications = justifications or {}

        self._converter = UnitConverter()

        # ---------------------------------------------------------
        # REGISTRY: Add new element extractors here in the future
        # ---------------------------------------------------------
        self._extractors = {
            "Feeds": self._extract_feeds,
            "Products": self._extract_products,
            "Pipes": self._extract_pipes,
            "Pumps": self._extract_pumps,
            "Compressors": self._extract_compressors,
            "Valves": self._extract_valves,
            "Heat Exchangers": self._extract_heat_exchangers,
            "Junctions": self._extract_junctions,
            "Misc Equipment": self._extract_misc,
        }

        # Header parsing pattern
        self._header_pattern = re.compile(r"^(.*?) \[(.*?)\]$")

        # Reuseable Styles
        self._styles = {
            "model_title": Font(bold=True, size=18, color="003366"),
            "title": Font(bold=True, size=14, color="003366"),
            "header": Font(bold=True, size=10),
            "unit": Font(italic=True, color="555555", size=10),
            "data": Font(size=10),
            "footer": Font(italic=True, size=9, color="888888"),
            "fill": PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid"),
            "thin_side": Side(style="thin"),
            "thick_side": Side(style="medium"),
        }

    def generate_dataframes(self) -> dict[str, pd.DataFrame]:
        """Runs all registered extractors and returns a dictionary of DataFrames."""
        dfs = {}
        for sheet_name, extractor_func in self._extractors.items():
            data = extractor_func()
            if data:  # Only add the sheet if there are actual elements
                converted_data = self._converter.convert_summary(data)
                dfs[sheet_name] = pd.DataFrame(converted_data)
        return dfs

    def _get_validation_dataframe(self) -> pd.DataFrame:
        """Run all model validation checks, return a structured DataFrame.

        Returns:
            DataFrame with columns: Severity, Category, Element, Message.
            Empty DataFrame if no issues found.
        """
        issues: list[dict[str, str]] = []

        # model.validate() now includes core + app-level + connectivity
        try:
            for msg in self.model.validate():
                severity, category, elem = _classify_issue(msg)
                issues.append(
                    {
                        "Severity": severity,
                        "Category": category,
                        "Element": elem,
                        "Message": msg,
                    }
                )
        except Exception as exc:
            _logger.warning("validation failed: %s", exc)

        # Add justified violations with "Justified" severity
        if self._justifications:
            for pipe_name, justification in self._justifications.items():
                issues.append(
                    {
                        "Severity": "Justified",
                        "Category": "Criteria",
                        "Element": pipe_name,
                        "Message": f"Pipe '{pipe_name}': criteria violation justified - {justification}",
                    }
                )

        if not issues:
            return pd.DataFrame(columns=["Severity", "Category", "Element", "Message"])
        return pd.DataFrame(issues)

    def export_to_excel(
        self,
        output_path: str,
        sheet_name: str = "Model Summary",
        elements: list[str] | None = None,
        template_path: str | None = None,
    ) -> str:
        """Generates the DataFrames and writes them sequentially to a single formatted Excel sheet."""
        from pathlib import Path

        from openpyxl import load_workbook

        source_name = Path(self.model._parser.path).name
        _logger.info("── Generate Report ── %s", source_name)
        dfs_flat = self.generate_dataframes()
        non_empty = [k for k, v in dfs_flat.items() if not v.empty]
        _logger.info("   Sections: %s", ", ".join(non_empty) if non_empty else "none")

        if template_path and Path(template_path).exists():
            workbook = load_workbook(template_path)
            worksheet = workbook.active
            assert worksheet is not None, "Template workbook should have an active sheet"
            worksheet.title = sheet_name
        else:
            workbook = openpyxl.Workbook()
            worksheet = workbook.active
            assert worksheet is not None, "New workbook should have an active sheet"
            worksheet.title = sheet_name

            # Set page setup for A3 Landscape, fit to 1 page wide x 1 page tall
            worksheet.page_setup.paperSize = worksheet.PAPERSIZE_A3
            worksheet.page_setup.orientation = worksheet.ORIENTATION_LANDSCAPE
            worksheet.page_setup.fitToPage = True
            worksheet.page_setup.fitToWidth = 1
            worksheet.page_setup.fitToHeight = 1

        # Insert References & Design Basis sheet as the first sheet (if data present)
        if self._basis or self._remarks or self._hold or self._references:
            self._write_references_sheet(workbook)

        # Insert Validation sheet as the first sheet (if issues exist)
        self._write_validation_sheet(workbook)

        # Row 1 — Model title from KORF SYMBOL (FSIZ=2)
        model_title = self._get_model_title()
        if model_title:
            title_cell = worksheet.cell(row=1, column=1, value=model_title)
            title_cell.font = self._styles["model_title"]
            worksheet.row_dimensions[1].height = 28

        # Row 2 — Source file
        source_name = Path(self.model._parser.path).name
        worksheet.cell(row=2, column=1, value=f"Source File: {source_name}").font = self._styles[
            "header"
        ]

        # Row 3 — Cases
        case_names = self.model.general.case_descriptions if hasattr(self.model, "general") else []
        if case_names:
            worksheet.cell(
                row=3, column=1, value=f"Cases: {'; '.join(case_names)}"
            ).font = self._styles["header"]

        current_row_left = 8 if template_path else 5
        current_row_right = 8 if template_path else 5
        max_left_col = 1

        element_keys = elements if elements is not None else list(self._extractors.keys())

        # First pass: calculate max column width for left-side standard tables
        # Only count Pipes, Compressors, Heat Exchangers (not Pumps/Valves which use transposed layout)
        for element_type in element_keys:
            if element_type not in dfs_flat or dfs_flat[element_type].empty:
                continue
            if element_type in ("Feeds", "Products", "Junctions", "Misc Equipment"):
                continue
            if element_type in ("Pumps", "Valves"):
                continue  # Transposed tables don't contribute to left-side width
            df = dfs_flat[element_type]
            num_cols = len(df.columns)
            end_col = 1 + num_cols - 1
            if end_col > max_left_col:
                max_left_col = end_col

        for element_type in element_keys:
            if element_type not in dfs_flat or dfs_flat[element_type].empty:
                continue

            df = dfs_flat[element_type]

            is_right_side = element_type in ("Feeds", "Products", "Junctions", "Misc Equipment")
            current_row = current_row_right if is_right_side else current_row_left
            start_col = max_left_col + 2 if is_right_side else 1

            start_table_row = current_row

            # 1. Write Title
            self._write_cell(
                worksheet, current_row, start_col, f"{element_type} Summary", style="title"
            )
            current_row += 2

            # 2. Write Table Content
            if element_type in ("Pumps", "Valves"):
                end_row, num_cols = self._write_transposed_table(
                    worksheet, df, current_row, start_col
                )
            else:
                end_row, num_cols = self._write_standard_table(
                    worksheet, df, current_row, start_col
                )

            # 3. Apply Styling & Borders
            self._apply_table_formatting(
                worksheet, start_table_row + 2, end_row, num_cols, start_col
            )

            # 4. Pipe stats block (max/min DP/DL and Velocity)
            if element_type == "Pipes":
                current_row = self._write_pipe_stats(worksheet, df, end_row + 2, start_col)
            else:
                current_row = end_row + 3

            if is_right_side:
                current_row_right = current_row
            else:
                current_row_left = current_row

        # Footer — auto-generated notice
        footer_row = max(current_row_left, current_row_right) + 1
        footer_text = (
            "This report is auto-generated from the KORF hydraulic model. "
            "Do not edit this document directly — any changes must be made in the source model "
            f"({source_name}) and the report regenerated."
        )
        footer_cell = worksheet.cell(row=footer_row, column=1, value=footer_text)
        footer_cell.font = self._styles["footer"]
        footer_cell.alignment = Alignment(wrap_text=False)
        worksheet.row_dimensions[footer_row].height = 30

        workbook.save(output_path)
        _logger.info("   Report saved | %s", output_path)
        return str(output_path)

    # =========================================================
    # INTERNAL WRITING HELPERS
    # =========================================================

    def _write_cell(
        self, ws: Any, row: int, col: int, value: Any, style: str | None = None
    ) -> None:
        """Helper to write a cell with an optional predefined style."""
        cell = ws.cell(row=row, column=col, value=value)
        if style and style in self._styles:
            cell.font = self._styles[style]
        return cell

    def _parse_headers(self, columns: list[str]) -> tuple[list[str], list[str]]:
        """Splits flat column names into (description, unit) tuples."""
        descriptions, units = [], []
        for col in columns:
            match = self._header_pattern.match(col)
            if match:
                descriptions.append(match.group(1))
                units.append(f"[{match.group(2)}]")
            else:
                descriptions.append(col)
                units.append("")
        return descriptions, units

    def _write_standard_table(
        self, ws: Any, df: pd.DataFrame, row: int, start_col: int = 1
    ) -> tuple[int, int]:
        """Writes a standard vertical table (Pipes, Compressors)."""
        descriptions, units = self._parse_headers(df.columns)

        # Write Two-Level Header
        ws.row_dimensions[row].height = 30
        for c_idx, (desc, unit) in enumerate(
            zip(descriptions, units, strict=True), start=start_col
        ):
            cell_desc = ws.cell(row=row, column=c_idx, value=desc)
            cell_desc.font = self._styles["header"]
            cell_desc.fill = self._styles["fill"]
            cell_desc.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

            cell_unit = ws.cell(row=row + 1, column=c_idx, value=unit)
            cell_unit.font = self._styles["unit"]
            cell_unit.fill = self._styles["fill"]
            cell_unit.alignment = Alignment(horizontal="center")

        # Write Data
        data_start_row = row + 2
        rhov2_col_indices = {
            start_col + i
            for i, col in enumerate(df.columns)
            if "ρV²" in col  # noqa: RUF001
        }
        criteria_col_idx = (
            start_col + len(descriptions) - 1 if "Criteria Check" in descriptions else None
        )
        for r_idx, row_data in enumerate(
            dataframe_to_rows(df, index=False, header=False), start=data_start_row
        ):
            for c_idx, val in enumerate(row_data, start=start_col):
                cell = ws.cell(row=r_idx, column=c_idx, value=val)
                cell.font = self._styles["data"]
                if c_idx != start_col:
                    cell.alignment = Alignment(horizontal="center")
                if c_idx in rhov2_col_indices:
                    cell.number_format = "#,##0"
                if criteria_col_idx is not None and c_idx == criteria_col_idx and val == "FAIL":
                    cell.font = Font(bold=True, size=10, color="9C0006")
                    cell.fill = PatternFill(
                        start_color="FFC7CE", end_color="FFC7CE", fill_type="solid"
                    )

        last_row = data_start_row + len(df) - 1
        self._apply_column_widths(ws, len(descriptions), start_col)

        return last_row, len(descriptions)

    def _write_transposed_table(
        self, ws: Any, df: pd.DataFrame, row: int, start_col: int = 1
    ) -> tuple[int, int]:
        """Writes a transposed table (Pumps, Valves).

        Detects section markers (rows where parameter name is empty and value is non-empty)
        and renders them as styled separator rows with section headings.
        """
        descriptions, units = self._parse_headers(df.columns)
        pump_names = df.iloc[:, 0].tolist()
        num_cols = 2 + len(pump_names)

        # Top Header Row (Parameter, Unit, Pump Names...)
        ws.row_dimensions[row].height = 30
        headers = ["Parameter", "Unit", *pump_names]
        for c_idx, val in enumerate(headers, start=start_col):
            cell = ws.cell(row=row, column=c_idx, value=val)
            cell.font = self._styles["header"]
            cell.fill = self._styles["fill"]
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        # Data Rows (One row per parameter)
        current_row = row + 1
        for p_idx in range(1, len(descriptions)):
            param_name = descriptions[p_idx]
            unit_text = units[p_idx]

            # Check if this is a section marker row
            # Section markers have empty unit and the column value equals the param name
            row_values = df.iloc[:, p_idx].tolist()
            is_section_marker = (
                param_name
                and unit_text == ""
                and len(row_values) > 0
                and row_values[0] == param_name
            )

            if is_section_marker:
                # Write section separator row
                section_name = param_name
                merged_cell = ws.cell(row=current_row, column=start_col, value=section_name)
                merged_cell.font = Font(bold=True, italic=True, size=11, color="003366")
                merged_cell.fill = PatternFill(
                    start_color="D6EAF8", end_color="D6EAF8", fill_type="solid"
                )
                merged_cell.alignment = Alignment(horizontal="left", vertical="center")

                # Merge cells across all columns for section header
                end_col = start_col + num_cols - 1
                ws.merge_cells(
                    start_row=current_row,
                    start_column=start_col,
                    end_row=current_row,
                    end_column=end_col,
                )
                ws.row_dimensions[current_row].height = 25
            else:
                # Param Name
                cell_p = ws.cell(row=current_row, column=start_col, value=param_name)
                cell_p.font = self._styles["header"]
                cell_p.fill = self._styles["fill"]

                # Unit
                cell_u = ws.cell(row=current_row, column=start_col + 1, value=unit_text)
                cell_u.font = self._styles["unit"]

                # Values across pumps
                vals = df.iloc[:, p_idx].tolist()
                for v_idx, val in enumerate(vals, start=start_col + 2):
                    cell_v = ws.cell(row=current_row, column=v_idx, value=val)
                    cell_v.font = self._styles["data"]
                    cell_v.alignment = Alignment(horizontal="center")
                    if "Differential Head" in param_name:
                        cell_v.number_format = "#,##0"
                    if "Discharge Shut-Off Pressure" in param_name:
                        cell_v.number_format = "#0.0"

            current_row += 1

        last_row = current_row - 1
        self._apply_column_widths(ws, num_cols, start_col)

        return last_row, num_cols

    def _apply_table_formatting(
        self, ws: Any, start_row: int, end_row: int, num_cols: int, start_col: int = 1
    ) -> None:
        """Applies internal borders and a thick outer border to a table block."""
        thin_s = self._styles["thin_side"]
        thick_s = self._styles["thick_side"]

        end_col = start_col + num_cols - 1
        for r in range(start_row, end_row + 1):
            for c in range(start_col, end_col + 1):
                cell = ws.cell(row=r, column=c)

                # Determine borders
                left = thick_s if c == start_col else thin_s
                right = thick_s if c == end_col else thin_s
                top = thick_s if r == start_row else thin_s
                bottom = thick_s if r == end_row else thin_s

                cell.border = Border(left=left, right=right, top=top, bottom=bottom)

    def _apply_column_widths(self, ws: Any, num_cols: int, start_col: int = 1) -> None:
        """Sets fixed column widths: Col 1 = 25, Others = 15."""
        ws.column_dimensions[get_column_letter(start_col)].width = 25
        for c in range(start_col + 1, start_col + num_cols):
            ws.column_dimensions[get_column_letter(c)].width = 15

    def _get_model_title(self) -> str:
        """Fetches the model title from the first SYMBOL with TYPE='Text' and FSIZ=2."""
        from pykorf.core.elements import Symbol

        symbol_indices = {
            rec.index
            for rec in self.model._parser.records
            if rec.element_type == "SYMBOL" and rec.index is not None
        }
        for idx in symbol_indices:
            type_rec = self.model._parser.get("SYMBOL", idx, Symbol.TYPE)
            fsiz_rec = self.model._parser.get("SYMBOL", idx, Symbol.FSIZ)
            text_rec = self.model._parser.get("SYMBOL", idx, Symbol.TEXT)
            if not (type_rec and fsiz_rec and text_rec):
                continue
            try:
                if type_rec.values[0] == "Text" and int(fsiz_rec.values[0]) == 2:
                    return str(text_rec.values[0]) if text_rec.values else ""
            except (ValueError, TypeError, IndexError):
                continue
        return ""

    def _write_references_sheet(self, workbook: Any) -> None:
        """Creates the 'References & Design Basis' sheet as the first sheet (A4 Landscape 80%)."""
        ref_ws = workbook.create_sheet("References & Design Basis", 0)
        assert ref_ws is not None, "Failed to create References & Design Basis sheet"
        ref_ws.page_setup.paperSize = ref_ws.PAPERSIZE_A4
        ref_ws.page_setup.orientation = ref_ws.ORIENTATION_LANDSCAPE
        ref_ws.page_setup.scale = 75

        # Fixed column widths for all four content columns
        for col_idx, width in enumerate([50, 15, 15, 50], start=1):
            ref_ws.column_dimensions[get_column_letter(col_idx)].width = width

        row = 1

        # Sheet title
        title_cell = ref_ws.cell(row=row, column=1, value="References & Design Basis")
        title_cell.font = self._styles["model_title"]
        ref_ws.row_dimensions[row].height = 30
        row += 2

        # ── Design Basis section ──────────────────────────────────────
        if self._basis and self._basis.strip():
            section_cell = ref_ws.cell(row=row, column=1, value="Design Basis")
            section_cell.font = self._styles["title"]
            row += 1

            for line in self._basis.splitlines():
                basis_cell = ref_ws.cell(row=row, column=1, value=line)
                basis_cell.font = Font(size=10)
                basis_cell.alignment = Alignment(wrap_text=False, horizontal="left")
                ref_ws.row_dimensions[row].height = 15
                row += 1
            row += 1  # blank separator

        # ── Remarks section ───────────────────────────────────────────
        if self._remarks and self._remarks.strip():
            section_cell = ref_ws.cell(row=row, column=1, value="Remarks")
            section_cell.font = self._styles["title"]
            row += 1

            for line in self._remarks.splitlines():
                cell = ref_ws.cell(row=row, column=1, value=line)
                cell.font = Font(size=10)
                cell.alignment = Alignment(wrap_text=False, horizontal="left")
                ref_ws.row_dimensions[row].height = 15
                row += 1
            row += 1  # blank separator

        # ── Hold Items section ────────────────────────────────────────
        if self._hold and self._hold.strip():
            section_cell = ref_ws.cell(row=row, column=1, value="Hold Items")
            section_cell.font = self._styles["title"]
            row += 1

            for line in self._hold.splitlines():
                cell = ref_ws.cell(row=row, column=1, value=line)
                cell.font = Font(size=10)
                cell.alignment = Alignment(wrap_text=False, horizontal="left")
                ref_ws.row_dimensions[row].height = 15
                row += 1
            row += 1  # blank separator

        # ── References table section ──────────────────────────────────
        if self._references:
            section_cell = ref_ws.cell(row=row, column=1, value="Reference Documents")
            section_cell.font = self._styles["title"]
            row += 1

            # Table headers
            headers = ["Name", "Category", "Link", "Description"]
            for c_idx, header in enumerate(headers, start=1):
                cell = ref_ws.cell(row=row, column=c_idx, value=header)
                cell.font = self._styles["header"]
                cell.fill = self._styles["fill"]
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            ref_ws.row_dimensions[row].height = 20
            header_row = row
            row += 1

            # Table rows
            for ref in self._references:
                ref_ws.cell(row=row, column=1, value=ref.get("name", "")).font = Font(
                    bold=True, size=10
                )
                ref_ws.cell(row=row, column=2, value=ref.get("category", "")).font = Font(size=10)
                raw_link = ref.get("link", "")
                link_cell = ref_ws.cell(row=row, column=3, value="Open Link" if raw_link else "")
                if raw_link:
                    link_cell.hyperlink = raw_link
                    link_cell.font = Font(size=10, color="0563C1", underline="single")
                    link_cell.alignment = Alignment(wrap_text=False)
                ref_ws.cell(row=row, column=4, value=ref.get("description", "")).font = Font(
                    italic=True, size=10, color="555555"
                )
                row += 1

            # Outer border around the table
            self._apply_table_formatting(ref_ws, header_row, row - 1, len(headers), 1)

    def _write_validation_sheet(self, workbook: Any) -> None:
        """Create a 'Validation' sheet with model-level and connectivity issues.

        Only added if there are actual issues. A4 Landscape, 90% scale.
        """
        df = self._get_validation_dataframe()
        if df.empty:
            return

        val_ws = workbook.create_sheet("Validation", 0)
        assert val_ws is not None, "Failed to create Validation sheet"
        val_ws.page_setup.paperSize = val_ws.PAPERSIZE_A4
        val_ws.page_setup.orientation = val_ws.ORIENTATION_LANDSCAPE
        val_ws.page_setup.scale = 90

        for col_idx, width in enumerate([12, 18, 15, 80], start=1):
            val_ws.column_dimensions[get_column_letter(col_idx)].width = width

        row = 1

        # Sheet title
        title_cell = val_ws.cell(row=row, column=1, value="Validation Results")
        title_cell.font = self._styles["model_title"]
        val_ws.row_dimensions[row].height = 28
        row += 1

        # Issue count summary
        error_count = (df["Severity"] == "Error").sum()
        warning_count = (df["Severity"] == "Warning").sum()
        info_count = (df["Severity"] == "Info").sum()
        justified_count = (df["Severity"] == "Justified").sum()
        summary_parts = [f"{len(df)} issue(s)"]
        if error_count:
            summary_parts.append(f"{error_count} error(s)")
        if warning_count:
            summary_parts.append(f"{warning_count} warning(s)")
        if info_count:
            summary_parts.append(f"{info_count} info")
        if justified_count:
            summary_parts.append(f"{justified_count} justified")
        summary = " — ".join(summary_parts)
        val_ws.cell(row=row, column=1, value=summary).font = Font(
            italic=True, size=10, color="555555"
        )
        row += 2

        # Table headers
        headers = list(df.columns)
        severity_colors: Mapping[str, str] = {
            "Error": "9C0006",
            "Warning": "9C5700",
            "Info": "003366",
            "Justified": "003366",
        }
        severity_fills: Mapping[str, str] = {
            "Error": "FFC7CE",
            "Warning": "FFEB9C",
            "Info": "D9E2F3",
            "Justified": "D9E2F3",
        }
        for c_idx, header in enumerate(headers, start=1):
            cell = val_ws.cell(row=row, column=c_idx, value=header)
            cell.font = self._styles["header"]
            cell.fill = self._styles["fill"]
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        val_ws.row_dimensions[row].height = 20
        header_row = row
        row += 1

        # Table rows
        for _, r in df.iterrows():
            severity = str(r.get("Severity", "")) if r.get("Severity", "") is not None else ""
            color = severity_colors.get(severity, "555555")
            fill = severity_fills.get(severity, "F2F2F2")

            val_ws.cell(
                row=row,
                column=1,
                value=str(r.get("Severity", "")) if r.get("Severity", "") is not None else "",
            ).font = Font(bold=True, size=10, color=color)
            val_ws.cell(row=row, column=1).fill = PatternFill(
                start_color=fill, end_color=fill, fill_type="solid"
            )
            val_ws.cell(row=row, column=2, value=r.get("Category", "")).font = Font(size=10)
            val_ws.cell(row=row, column=3, value=r.get("Element", "")).font = Font(
                bold=True, size=10
            )
            msg_cell = val_ws.cell(row=row, column=4, value=r.get("Message", ""))
            msg_cell.font = Font(size=10)
            msg_cell.alignment = Alignment(wrap_text=True, vertical="top")
            val_ws.row_dimensions[row].height = 15
            row += 1

        # Outer border
        self._apply_table_formatting(val_ws, header_row, row - 1, len(headers), 1)

    def _write_pipe_stats(self, ws: Any, df: Any, row: int, start_col: int) -> int:
        """Writes a Min-Max summary row and an overall Criteria Check row below the pipe table."""
        import pandas as pd

        dpdl_col = next((c for c in df.columns if "DP / DL" in c and "Criteria" not in c), None)
        vel_col = next((c for c in df.columns if "Velocity" in c and "Criteria" not in c), None)
        rhov2_col = next((c for c in df.columns if "ρV² calc" in c), None)  # noqa: RUF001
        criteria_col = next((c for c in df.columns if c == "Criteria Check"), None)

        if dpdl_col is None and vel_col is None and rhov2_col is None and criteria_col is None:
            return row + 3

        col_names = list(df.columns)
        criteria_col_idx = start_col + col_names.index(criteria_col) if criteria_col else None

        def _fmt(col: str, thousand_comma: bool = False) -> str | None:
            try:
                numeric = pd.to_numeric(df[col], errors="coerce")
                lo, hi = numeric.min(), numeric.max()
                if pd.isna(lo) or pd.isna(hi):
                    return None
                if thousand_comma:
                    return f"{lo:,.0f} - {hi:,.0f}"
                return f"{lo:.4g} - {hi:.4g}"
            except Exception:
                return None

        # Collect column indices that have data in Min-Max row
        data_col_indices = []
        if dpdl_col:
            data_col_indices.append(start_col + col_names.index(dpdl_col))
        if vel_col:
            data_col_indices.append(start_col + col_names.index(vel_col))
        if rhov2_col:
            data_col_indices.append(start_col + col_names.index(rhov2_col))
        if criteria_col:
            data_col_indices.append(criteria_col_idx)

        min_max_cols = [start_col, *data_col_indices]
        start_col_idx = min(min_max_cols)
        end_col_idx = max(min_max_cols)
        thin_s = self._styles["thin_side"]
        thick_s = self._styles["thick_side"]

        # -- Row 1: Min - Max ----------------------------------------------------
        lc = ws.cell(row=row, column=start_col, value="Min - Max")
        lc.font = Font(bold=True, size=10)

        if dpdl_col:
            c_idx = start_col + col_names.index(dpdl_col)
            cell = ws.cell(row=row, column=c_idx, value=_fmt(dpdl_col))
            cell.font = self._styles["data"]
            cell.alignment = Alignment(horizontal="center")

        if vel_col:
            c_idx = start_col + col_names.index(vel_col)
            cell = ws.cell(row=row, column=c_idx, value=_fmt(vel_col))
            cell.font = self._styles["data"]
            cell.alignment = Alignment(horizontal="center")

        if rhov2_col:
            c_idx = start_col + col_names.index(rhov2_col)
            cell = ws.cell(row=row, column=c_idx, value=_fmt(rhov2_col, thousand_comma=True))
            cell.font = self._styles["data"]
            cell.alignment = Alignment(horizontal="center")

        # Apply borders to Min-Max row
        for c_idx in range(start_col_idx, end_col_idx + 1):
            cell = ws.cell(row=row, column=c_idx)
            left = thick_s if c_idx == start_col_idx else thin_s
            right = thick_s if c_idx == end_col_idx else thin_s
            top = thick_s
            bottom = thin_s
            cell.border = Border(left=left, right=right, top=top, bottom=bottom)
            if c_idx not in min_max_cols:
                cell.alignment = Alignment(horizontal="center")

        # -- Row 2: Overall Criteria Check (OR logic - any FAIL -> FAIL) --------
        if criteria_col:
            has_fail = (df[criteria_col] == "FAIL").any()
            has_justified = (df[criteria_col] == "JUSTIFIED").any()

            if has_fail:
                overall = "FAIL"
                color = "9C0006"
                fill = "FFC7CE"
            elif has_justified:
                overall = "PASS with Justification"
                color = "003366"
                fill = "D9E2F3"
            else:
                overall = "PASS"
                color = "276221"
                fill = "C6EFCE"

            label_cell = ws.cell(row=row + 1, column=start_col, value="Overall Criteria")
            label_cell.font = Font(bold=True, size=10)

            c_idx = start_col + col_names.index(criteria_col)
            result_cell = ws.cell(row=row + 1, column=c_idx, value=overall)
            result_cell.font = Font(
                bold=True,
                size=10,
                color=color,
            )
            result_cell.fill = PatternFill(
                start_color=fill,
                end_color=fill,
                fill_type="solid",
            )
            result_cell.alignment = Alignment(horizontal="center")

            # Apply borders to Overall Criteria row
            for c_idx in range(start_col_idx, end_col_idx + 1):
                cell = ws.cell(row=row + 1, column=c_idx)
                left = thick_s if c_idx == start_col_idx else thin_s
                right = thick_s if c_idx == end_col_idx else thin_s
                top = thin_s
                bottom = thick_s
                cell.border = Border(left=left, right=right, top=top, bottom=bottom)
                if c_idx != start_col and c_idx != criteria_col_idx:
                    cell.alignment = Alignment(horizontal="center")

        return row + 3

    # =========================================================
    # ELEMENT EXTRACTORS
    # =========================================================

    def _extract_pipes(self) -> list[dict]:
        return [
            pipe.summary(export=True, justifications=self._justifications)
            for idx, pipe in self.model.pipes.items()
            if idx != 0 and not pipe.name.startswith("d")
        ]

    def _extract_pumps(self) -> list[dict]:
        return [
            pump.summary(export=True, model=self.model)
            for idx, pump in self.model.pumps.items()
            if idx != 0
        ]

    def _extract_compressors(self) -> list[dict]:
        return [
            comp.summary(export=True) for idx, comp in self.model.compressors.items() if idx != 0
        ]

    def _extract_feeds(self) -> list[dict]:
        return [feed.summary(export=True) for idx, feed in self.model.feeds.items() if idx != 0]

    def _extract_products(self) -> list[dict]:
        return [prod.summary(export=True) for idx, prod in self.model.products.items() if idx != 0]

    def _extract_valves(self) -> list[dict]:
        return [
            valve.summary(export=True, model=self.model)
            for idx, valve in self.model.valves.items()
            if idx != 0
        ]

    def _extract_heat_exchangers(self) -> list[dict]:
        return [hx.summary(export=True) for idx, hx in self.model.exchangers.items() if idx != 0]

    def _extract_junctions(self) -> list[dict]:
        """Extract junction data for export.

        Only includes junctions whose names do NOT start with "J".
        """
        return [
            junction.summary(export=True)
            for idx, junction in self.model.junctions.items()
            if idx != 0 and not junction.name.startswith("J")
        ]

    def _extract_misc(self) -> list[dict]:
        return [
            misc.summary(export=True) for idx, misc in self.model.misc_equipment.items() if idx != 0
        ]
