import json
import re
from pathlib import Path

UNITS_JSON_PATH = Path(__file__).parent / "units.json"


class UnitConverter:
    """Converter for model results based on unit systems."""

    def __init__(self, mapping_path: Path = UNITS_JSON_PATH, unit_system: str = "Engg_SI"):
        self.unit_system = unit_system
        self.conversions = {}
        if mapping_path.exists():
            with open(mapping_path, encoding="utf-8") as f:
                self.conversions = json.load(f)

    def convert_summary(self, summary_list: list[dict]) -> list[dict]:
        """Parses keys like '[Result] DP / DL [kPa/100m]', converts numeric values,
        and renames the key with the target unit.
        """
        pattern = re.compile(r"^(.*?) \[(.*?)\]$")
        new_summary_list = []

        def _fmt(v):
            if isinstance(v, float):
                return round(v, 2)
            if isinstance(v, (list, tuple)):
                return [_fmt(x) for x in v]
            return v

        # Get conversions for the specific unit system
        system_conversions = self.conversions.get(self.unit_system, {})

        for row in summary_list:
            new_row = {}
            for key, val in row.items():
                match = pattern.match(key)
                processed = False
                if match:
                    base_name, unit = match.groups()
                    if unit in system_conversions:
                        conv = system_conversions[unit]
                        target_unit = conv.get("target_unit", unit)
                        multiplier = conv.get("multiplier", 1.0)
                        offset = conv.get("offset", 0.0)

                        new_key = f"{base_name} [{target_unit}]"

                        if isinstance(val, (int, float)):
                            new_val = val * multiplier + offset
                        else:
                            # Try parsing string to float if possible
                            try:
                                new_val = float(val) * multiplier + offset
                            except (ValueError, TypeError):
                                new_val = val

                        new_row[new_key] = _fmt(new_val)
                        processed = True

                if not processed:
                    new_row[key] = _fmt(val)

            new_summary_list.append(new_row)

        return new_summary_list


# Global instance for easy access
converter = UnitConverter()
