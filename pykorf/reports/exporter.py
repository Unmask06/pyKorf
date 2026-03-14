import re

import openpyxl
import pandas as pd
from openpyxl.utils import get_column_letter

from pykorf import Model
from pykorf.reports.unit_converter import converter


class ResultExporter:
    """A scalable exporter to extract calculated results and input criteria from a pyKorf Model
    and save them into a multi-sheet Excel report or DataFrame dictionary.

    This class correctly relies on the element 'summary' methods to parse the dynamic units
    directly from the underlying KDF records and format them for export.
    """

    def __init__(self, model: Model):
        self.model = model

        # ---------------------------------------------------------
        # REGISTRY: Add new element extractors here in the future
        # ---------------------------------------------------------
        self._extractors = {
            "Pipes": self._extract_pipes,
            "Pumps": self._extract_pumps,
            "Compressors": self._extract_compressors,
        }

    def generate_dataframes(self) -> dict[str, pd.DataFrame]:
        """Runs all registered extractors and returns a dictionary of DataFrames."""
        dfs = {}
        for sheet_name, extractor_func in self._extractors.items():
            data = extractor_func()
            if data:  # Only add the sheet if there are actual elements
                converted_data = converter.convert_summary(data)
                dfs[sheet_name] = pd.DataFrame(converted_data)
        return dfs

    def export_to_excel(self, output_path: str, sheet_name: str = "Model Summary") -> str:
        """Generates the DataFrames and writes them sequentially to a single formatted Excel sheet."""
        from openpyxl.utils.dataframe import dataframe_to_rows
        
        dfs_flat = self.generate_dataframes()
        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.title = sheet_name

        # Set page setup for A4 landscape
        worksheet.page_setup.paperSize = worksheet.PAPERSIZE_A4
        worksheet.page_setup.orientation = worksheet.ORIENTATION_LANDSCAPE

        current_row = 1

        # Export elements in the defined order of extractors
        for element_type in self._extractors.keys():
            if element_type not in dfs_flat:
                continue

            df_flat = dfs_flat[element_type]
            if df_flat.empty:
                continue

            # Write title
            cell = worksheet.cell(row=current_row, column=1, value=f"{element_type} Summary")
            cell.font = openpyxl.styles.Font(bold=True, size=14)
            current_row += 2

            # Parse headers into descriptions and units
            descriptions = []
            units = []
            pattern = re.compile(r"^(.*?) \[(.*?)\]$")
            for col in df_flat.columns:
                match = pattern.match(col)
                if match:
                    descriptions.append(match.group(1))
                    units.append(f"[{match.group(2)}]")
                else:
                    descriptions.append(col)
                    units.append("")

            if element_type == "Pumps":
                pump_names = df_flat.iloc[:, 0].tolist()
                headers = ["Parameter", "Unit"] + pump_names
                
                # Write top header row
                for c_idx, val in enumerate(headers, start=1):
                    cell = worksheet.cell(row=current_row, column=c_idx, value=val)
                    cell.font = openpyxl.styles.Font(bold=True)
                
                current_row += 1

                # Write data rows
                for p_idx in range(1, len(descriptions)):
                    desc = descriptions[p_idx]
                    unit = units[p_idx]
                    
                    row_data = [desc, unit] + df_flat.iloc[:, p_idx].tolist()
                    for c_idx, val in enumerate(row_data, start=1):
                        cell = worksheet.cell(row=current_row, column=c_idx, value=val)
                        if c_idx == 1:
                            cell.font = openpyxl.styles.Font(bold=True)
                        elif c_idx == 2:
                            cell.font = openpyxl.styles.Font(italic=True, color="555555")
                    current_row += 1

                # Auto-adjust column widths
                for c_idx in range(1, len(headers) + 1):
                    col_letter = get_column_letter(c_idx)
                    max_len = 0
                    for r_idx in range(current_row - len(descriptions), current_row):
                        val = worksheet.cell(row=r_idx, column=c_idx).value
                        if val is not None:
                            max_len = max(max_len, len(str(val)))
                    
                    current_width = worksheet.column_dimensions[col_letter].width or 10
                    worksheet.column_dimensions[col_letter].width = max(current_width, max_len + 2)

                current_row += 2
            else:
                # Write headers
                for c_idx, desc in enumerate(descriptions, start=1):
                    cell = worksheet.cell(row=current_row, column=c_idx, value=desc)
                    cell.font = openpyxl.styles.Font(bold=True)

                for c_idx, unit in enumerate(units, start=1):
                    cell = worksheet.cell(row=current_row + 1, column=c_idx, value=unit)
                    cell.font = openpyxl.styles.Font(italic=True, color="555555")

                current_row += 2

                # Write data rows
                for r_idx, row_data in enumerate(dataframe_to_rows(df_flat, index=False, header=False), start=current_row):
                    for c_idx, val in enumerate(row_data, start=1):
                        worksheet.cell(row=r_idx, column=c_idx, value=val)

                # Auto-adjust column widths
                for i, (desc, unit) in enumerate(zip(descriptions, units)):
                    col_letter = get_column_letter(i + 1)
                    max_data_len = df_flat.iloc[:, i].astype(str).map(len).max() if len(df_flat) > 0 else 0
                    col_len = max(len(desc), len(unit), max_data_len)

                    current_width = worksheet.column_dimensions[col_letter].width or 10
                    worksheet.column_dimensions[col_letter].width = max(current_width, col_len + 2)

                # Update current_row: DataRows + Padding(2)
                current_row += len(df_flat) + 2

        workbook.save(output_path)
        return str(output_path)

    # =========================================================
    # ELEMENT EXTRACTORS
    # =========================================================

    def _extract_pipes(self) -> list[dict]:
        return [pipe.summary(export=True) for idx, pipe in self.model.pipes.items() if idx != 0]

    def _extract_pumps(self) -> list[dict]:
        return [pump.summary(export=True) for idx, pump in self.model.pumps.items() if idx != 0]

    def _extract_compressors(self) -> list[dict]:
        return [
            comp.summary(export=True) for idx, comp in self.model.compressors.items() if idx != 0
        ]
