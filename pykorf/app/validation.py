"""App-level validation for KDF models.

Handles checks that depend on external application configuration such as
the PMS specification file and line-number parsing logic.

These checks are kept separate from :mod:`pykorf.core.model.summary` so the
core model layer has zero dependencies on the app layer.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykorf.core.model import Model

_logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class AppValidationService:
    """Run app-level validation checks against a Model.

    App-level checks require external configuration (PMS file path,
    line-number parser) that lives in the app layer.

    Attributes:
        model: The Model instance to validate.
    """

    model: Model

    def validate(self) -> list[str]:
        """Run all app-level validation checks.

        Returns:
            List of human-readable issue descriptions. Empty list means all
            app-level checks passed.
        """
        issues: list[str] = []
        valid_pms_keys, pms_path = self._load_pms_config(issues)
        self._validate_pipe_line_numbers(issues, valid_pms_keys, pms_path)
        issues.extend(self._verify_pipe_properties())
        return issues

    # ── PMS config ────────────────────────────────────────────────────────

    def _load_pms_config(self, issues: list[str]) -> tuple[set[str], Path | None]:
        """Load PMS configuration and return valid PMS keys and the resolved path.

        Args:
            issues: List to append error messages to.

        Returns:
            Tuple of (valid_pms_keys, pms_path_or_none).
        """
        from pykorf.app.operation.config.config import get_pms_path

        valid_pms_keys: set[str] = set()
        pms_path = get_pms_path()
        if pms_path and pms_path.exists():
            try:
                with open(pms_path, encoding="utf-8") as f:
                    pms_data = json.load(f)
                    for material_data in pms_data.values():
                        if isinstance(material_data, dict) and "specifications" in material_data:
                            specs = material_data["specifications"]
                            if isinstance(specs, dict):
                                valid_pms_keys.update(specs.keys())
                        elif isinstance(material_data, dict):
                            valid_pms_keys.update(material_data.keys())
                    valid_pms_keys.update(pms_data.keys())
            except Exception:
                issues.append("Failed to load PMS config file.")
        return valid_pms_keys, pms_path

    # ── Pipe line numbers ─────────────────────────────────────────────────

    def _validate_pipe_line_numbers(
        self, issues: list[str], valid_pms_keys: set[str], pms_path: Path | None
    ) -> None:
        """Validate pipe line numbers in NOTES and verify against PMS.

        Args:
            issues: List to append validation issues to.
            valid_pms_keys: Set of valid PMS keys from configuration.
            pms_path: Resolved PMS file path.
        """
        from pykorf.app.operation.data_import.line_number import LineNumber

        for pipe_idx, pipe in self.model.pipes.items():
            if pipe_idx == 0:
                continue
            name = pipe.name
            if not name:
                issues.append(f"Pipe {pipe_idx} is missing a name.")
                continue
            if name.startswith("d"):
                continue
            notes_rec = pipe.get_param("NOTES")
            notes_val = notes_rec.values[0] if notes_rec and notes_rec.values else ""
            if not notes_val:
                issues.append(f"Pipe '{name}' is missing a line number in NOTES.")
                continue
            line_data = LineNumber.parse(notes_val)
            if line_data:
                self._verify_pms_for_pipe(issues, name, line_data, valid_pms_keys, pms_path)
            else:
                issues.append(
                    f"Pipe '{name}': NOTES value '{notes_val}' is not a valid line number."
                )

    def _verify_pms_for_pipe(
        self,
        issues: list[str],
        name: str,
        line_data,
        valid_pms_keys: set[str],
        pms_path: Path | None,
    ) -> None:
        """Verify PMS, NPS, and schedule for a single pipe.

        Args:
            issues: List to append validation issues to.
            name: Pipe name.
            line_data: Parsed line number data.
            valid_pms_keys: Set of valid PMS keys.
            pms_path: Resolved PMS file path.
        """
        pms_val = line_data.pms_code
        if valid_pms_keys and pms_val not in valid_pms_keys:
            issues.append(f"Pipe '{name}': PMS '{pms_val}' (from NOTES) not found in PMS file.")
        else:
            nps = line_data.nominal_pipe_size
            try:
                from pykorf.app.operation.data_import.pms import (
                    load_all_pms,
                    lookup_pms_across_materials,
                )

                all_materials = load_all_pms(pms_path)
                _, spec, _, _ = lookup_pms_across_materials(all_materials, pms_val, float(nps))
                pms_value = spec.get("value") or spec.get("schedule", "")
                if not pms_value:
                    issues.append(
                        f"Pipe '{name}': Schedule not defined for PMS '{pms_val}' at NPS {nps}\"."
                    )
            except Exception as exc:
                err_msg = str(exc)
                if "not defined" in err_msg.lower() or "not available" in err_msg.lower():
                    issues.append(f"Pipe '{name}': {err_msg}")

    # ── Pipe property verification ────────────────────────────────────────

    def _verify_pipe_properties(self) -> list[str]:
        """Verify pipe properties match the Line Number + PMS specification.

        Compares DIA/SCH/ID/MAT against expected values from PMS for every
        pipe that has a parseable line number in its NOTES field.

        Returns:
            List of validation issue descriptions.
        """
        from pykorf.app.operation.config.config import get_pms_path
        from pykorf.app.operation.data_import.line_number import LineNumber, format_nps
        from pykorf.app.operation.data_import.pms import (
            load_all_pms,
            lookup_pms_across_materials,
        )
        from pykorf.core.elements import Pipe

        issues: list[str] = []

        pms_path = get_pms_path()
        if not pms_path or not pms_path.exists():
            return issues

        try:
            all_materials = load_all_pms(pms_path)
        except Exception:
            return issues

        for pipe_idx, pipe in self.model.pipes.items():
            if pipe_idx == 0:
                continue
            name = pipe.name
            if not name or name.lower().startswith("d"):
                continue
            notes_rec = pipe.get_param("NOTES")
            notes_val = notes_rec.values[0] if notes_rec and notes_rec.values else ""
            if not notes_val:
                continue
            line_data = LineNumber.parse(notes_val)
            if not line_data:
                continue

            nps = line_data.nominal_pipe_size
            pms_code = line_data.pms_code
            try:
                material, spec, od_mm, _ = lookup_pms_across_materials(
                    all_materials, pms_code, float(nps)
                )
            except Exception:
                continue

            pms_value = spec.get("value") or spec.get("schedule", "")
            expected_sch = pms_value if pms_value else None
            expected_mat = material if material else None
            is_id_based = expected_sch and "mm" in expected_sch.lower()

            dia_rec = pipe.get_param(Pipe.DIA)
            sch_rec = pipe.get_param(Pipe.SCH)
            id_rec = pipe.get_param(Pipe.ID)
            mat_rec = pipe.get_param(Pipe.MAT)
            actual_dia = dia_rec.values[0] if dia_rec and dia_rec.values else None
            actual_sch = sch_rec.values[0] if sch_rec and sch_rec.values else None
            actual_id = id_rec.values[0] if id_rec and id_rec.values else None
            actual_mat = mat_rec.values[0] if mat_rec and mat_rec.values else None

            mismatches: list[str] = []

            if actual_dia:
                expected_nps_str = format_nps(nps)
                if not self._compare_nps(str(actual_dia), expected_nps_str):
                    mismatches.append(f"NPS={expected_nps_str}")

            if is_id_based and actual_id and expected_sch:
                wall_str = expected_sch.lower().replace("mm", "").strip()
                try:
                    wall_mm = float(wall_str)
                    expected_id_m = (od_mm - 2 * wall_mm) / 1000.0
                    actual_id_val = float(actual_id)
                    if abs(actual_id_val - expected_id_m) > 0.001:
                        mismatches.append(f"ID={expected_id_m:.1f}mm")
                except (ValueError, TypeError):
                    pass
            elif expected_sch and actual_sch:
                actual_sch_norm = str(actual_sch).strip().upper()
                expected_sch_norm = expected_sch.strip().upper()
                if expected_sch_norm.startswith("SCH "):
                    expected_sch_norm = expected_sch_norm[4:]
                if actual_sch_norm != expected_sch_norm:
                    mismatches.append(f"SCH={expected_sch}")

            if expected_mat and actual_mat:
                if str(actual_mat).strip().upper() != expected_mat.strip().upper():
                    mismatches.append(f"MAT={expected_mat}")

            if mismatches:
                expected_parts = mismatches
                actual_parts: list[str] = []
                if "NPS=" in ", ".join(mismatches):
                    actual_parts.append(f"NPS={actual_dia}")
                if "SCH=" in ", ".join(mismatches) and actual_sch:
                    actual_parts.append(f"SCH={actual_sch}")
                if "ID=" in ", ".join(mismatches) and actual_id:
                    actual_parts.append(f"ID={actual_id}")
                if "MAT=" in ", ".join(mismatches) and actual_mat:
                    actual_parts.append(f"MAT={actual_mat}")
                issues.append(
                    f"Pipe '{name}': Line number expects {', '.join(expected_parts)} "
                    f"but model has {', '.join(actual_parts)}"
                )

        return issues

    # ── NPS comparison helpers ────────────────────────────────────────────

    @staticmethod
    def _compare_nps(actual: str, expected: str) -> bool:
        """Compare NPS values, handling fractions like '1/2' or '1-1/2'."""
        actual_normalized = AppValidationService._normalize_nps(actual)
        expected_normalized = AppValidationService._normalize_nps(expected)
        try:
            return abs(float(actual_normalized) - float(expected_normalized)) < 0.01
        except (ValueError, TypeError):
            return actual.strip() == expected.strip()

    @staticmethod
    def _normalize_nps(nps_str: str) -> str:
        """Convert NPS string to decimal for comparison."""
        if not nps_str:
            return nps_str
        s = nps_str.strip()
        if "-" in s:
            parts = s.split("-", 1)
            try:
                whole = float(parts[0])
                fraction_str = parts[1]
                if "/" in fraction_str:
                    num, den = fraction_str.split("/", 1)
                    frac = float(num) / float(den)
                    return str(whole + frac)
            except (ValueError, TypeError, ZeroDivisionError):
                pass
        if "/" in s:
            try:
                num, den = s.split("/", 1)
                return str(float(num) / float(den))
            except (ValueError, TypeError, ZeroDivisionError):
                pass
        return s


_SEVERITY_RULES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"fails sizing|exceeds criteria|mismatch", re.I), "Sizing"),
    (re.compile(r"references pipe index .+ which does not exist", re.I), "Connectivity"),
    (re.compile(r"missing line number|missing NAME|missing CON|missing|not found in PMS", re.I), "Missing Data"),
    (re.compile(r"Add Title", re.I), "Model Setup"),
    (re.compile(r"pipe.*criteria", re.I), "Sizing"),
    (re.compile(r"CONN|connectiv|nozzle|CON value", re.I), "Connectivity"),
    (re.compile(r"missing criteria code", re.I), "Criteria Code"),
]


def classify_issue(msg: str) -> str:
    """Classify a validation message into a category.

    Args:
        msg: Human-readable validation issue string.

    Returns:
        Category string (e.g., "Sizing", "Connectivity", "Missing Data").
    """
    for pattern, category in _SEVERITY_RULES:
        if pattern.search(msg):
            return category
    return "Other"


def validate(model: Model) -> list[str]:
    """Run app-level validation checks on *model*.

    Convenience entry point used by :meth:`Model.validate`.

    Args:
        model: The model to validate.

    Returns:
        List of human-readable issue descriptions.
    """
    return AppValidationService(model).validate()
