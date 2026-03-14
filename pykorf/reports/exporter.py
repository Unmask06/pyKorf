import pandas as pd

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

    def export_to_excel(self, output_path: str) -> str:
        """Generates the DataFrames and writes them to a multi-sheet Excel file."""
        dfs = self.generate_dataframes()

        # Use pandas built-in excel exporter (requires openpyxl)
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            for sheet_name, df in dfs.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)

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
