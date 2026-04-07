"""Global Settings Excel to JSON converter and reader.

This module handles reading global settings from Excel files.

Excel Format Expected:
    First column: Setting names
    Second column: Setting values

Settings Supported:
    - notes_delimiter: Delimiter for NOTES parsing (default: ";")
    - default_material: Default pipe material (default: "Carbon Steel")
    - pms_file: Path to PMS file
    - hmb_file: Path to HMB file
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pykorf.app.exceptions import ExcelConversionError


@dataclass
class UseCaseSettings:
    """Configuration settings for PipedataProcessor.

    Attributes:
        notes_delimiter: Delimiter for NOTES field parsing
        default_material: Default pipe material
        pms_file: Path to PMS JSON file
        hmb_file: Path to HMB JSON file
        input_dir: Directory containing input files
    """

    notes_delimiter: str = ";"
    default_material: str = "Carbon Steel"
    pms_file: Path | None = None
    hmb_file: Path | None = None
    input_dir: Path = field(default_factory=lambda: Path(__file__).parent / "Input")


class SettingsReader:
    """Reader for Global Settings with Excel to JSON conversion."""

    def __init__(self, input_dir: Path | str | None = None):
        """Initialize Settings reader.

        Args:
            input_dir: Directory containing input Excel files. Defaults to Input subdirectory.
        """
        if input_dir is None:
            input_dir = Path(__file__).parent / "Input"
        self.input_dir = Path(input_dir)
        self._settings: UseCaseSettings = UseCaseSettings()

    def convert_excel_to_json(
        self,
        excel_path: Path | str,
        json_path: Path | str | None = None,
    ) -> Path:
        """Convert Global Settings Excel file to JSON.

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
        except ImportError:
            raise ExcelConversionError(
                "pandas is required for Excel conversion. Install with: pip install pandas openpyxl"
            )

        from pykorf.core.utils import read_excel_safe

        excel_path = Path(excel_path)
        if json_path is None:
            json_path = excel_path.with_suffix(".json")
        else:
            json_path = Path(json_path)

        df = read_excel_safe(excel_path, header=None)

        settings_data: dict[str, Any] = {}

        for idx, row in df.iterrows():
            key = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
            if not key:
                continue

            value = row.iloc[1] if len(row) > 1 and pd.notna(row.iloc[1]) else None

            if value is not None:
                settings_data[key] = value

        json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(settings_data, f, indent=2)

        return json_path

    def load_json(self, json_path: Path | str) -> UseCaseSettings:
        """Load settings from JSON file.

        Args:
            json_path: Path to JSON file

        Returns:
            UseCaseSettings instance
        """
        json_path = Path(json_path)

        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        self._settings = UseCaseSettings(
            notes_delimiter=str(data.get("notes_delimiter", ";")),
            default_material=str(data.get("default_material", "Carbon Steel")),
            pms_file=Path(data["pms_file"]) if data.get("pms_file") else None,
            hmb_file=Path(data["hmb_file"]) if data.get("hmb_file") else None,
        )

        return self._settings

    def load(self, source: Path | str | None = None) -> UseCaseSettings:
        """Load settings from Excel or JSON.

        Args:
            source: Path to Excel or JSON file, or None for defaults

        Returns:
            UseCaseSettings instance
        """
        if source is None:
            return UseCaseSettings()

        source = Path(source)

        if source.suffix.lower() == ".xlsx":
            json_path = source.with_suffix(".json")

            if not json_path.exists():
                self.convert_excel_to_json(source, json_path)

            return self.load_json(json_path)
        else:
            return self.load_json(source)

    def get_settings(self) -> UseCaseSettings:
        """Get current settings."""
        return self._settings
