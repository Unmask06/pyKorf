"""SummaryService - validation, convenience accessors, and summary methods.

This service provides methods for validating models and accessing
summary information about model contents.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from pykorf.elements import Element, Feed, Pipe, Product, Pump
from pykorf.exceptions import ElementNotFound

if TYPE_CHECKING:
    from pathlib import Path

    from pykorf.model import Model

_logger = logging.getLogger(__name__)

# Minimum required params per element type (params that must exist at index 0)
_REQUIRED_PARAMS: dict[str, tuple[str, ...]] = {
    "PIPE": ("NUM", "NAME", "LEN", "DIA", "MAT"),
    "FEED": ("NUM", "NAME", "TYPE", "PRES"),
    "PROD": ("NUM", "NAME", "TYPE", "PRES"),
    "PUMP": ("NUM", "NAME", "TYPE", "CON"),
    "VALVE": ("NUM", "NAME", "TYPE", "CON"),
    "CHECK": ("NUM", "NAME", "CON"),
    "FO": ("NUM", "NAME", "TYPE", "CON"),
    "HX": ("NUM", "NAME", "TYPE"),
    "COMP": ("NUM", "NAME", "TYPE", "CON"),
    "MISC": ("NUM", "NAME"),
    "EXPAND": ("NUM", "NAME", "TYPE", "CON"),
    "JUNC": ("NUM", "NAME"),
    "TEE": ("NUM", "NAME", "TYPE"),
    "VESSEL": ("NUM", "NAME", "TYPE"),
}


@dataclass(frozen=True, slots=True)
class SummaryService:
    """Service providing validation, convenience accessors, and summary methods.

    This service operates on a Model instance and provides methods for:
    - Validating KDF format compliance
    - Accessing elements by index with error handling
    - Generating model summaries and string representations

    Attributes:
        model: The Model instance to operate on.
    """

    model: Model

    def validate(
        self,
        *,
        check_connectivity: bool = True,
        check_layout: bool = True,
    ) -> list[str]:
        """Validate KDF format compliance.

        Returns a list of validation issues (empty = valid model).

        Args:
            check_connectivity: Whether to check connectivity consistency (deprecated, ignored).
            check_layout: Whether to check for layout issues (deprecated, ignored).

        Returns:
            List of validation issue descriptions.
        """
        _logger.info("── Validate ── %s", self.model._parser.path.name)
        issues = self._validate()
        if issues:
            _logger.warning("   Validation: %d issue(s) found", len(issues))
            for issue in issues:
                _logger.warning("   · %s", issue)
        else:
            _logger.info("   Validation passed — no issues")
        return issues

    def _validate(self) -> list[str]:
        """Internal validation implementation focusing on pipes and PMS."""
        issues: list[str] = []

        valid_pms_keys, pms_path = self._load_pms_config(issues)
        self._validate_pipe_line_numbers(issues, valid_pms_keys, pms_path)
        self._validate_pipe_sizing_criteria(issues)
        issues.extend(self._verify_pipe_properties())
        issues.extend(self._check_title_symbol())

        return issues

    def _load_pms_config(self, issues: list[str]) -> tuple[set[str], Path | str]:
        """Load PMS configuration and return valid PMS keys and the resolved path.

        Args:
            issues: List to append error messages to.

        Returns:
            Tuple of (valid_pms_keys, pms_path).
        """
        import json

        from pykorf.use_case.config import get_pms_path

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

    def _validate_pipe_line_numbers(
        self, issues: list[str], valid_pms_keys: set[str], pms_path: Path | str
    ) -> None:
        """Validate pipe line numbers in NOTES and verify against PMS.

        Args:
            issues: List to append validation issues to.
            valid_pms_keys: Set of valid PMS keys from configuration.
            pms_path: Resolved PMS file path (from _load_pms_config).
        """
        from pykorf.use_case.line_number import LineNumber

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
        pms_path: Path | str,
    ) -> None:
        """Verify PMS, NPS, and schedule for a single pipe.

        Args:
            issues: List to append validation issues to.
            name: Pipe name.
            line_data: Parsed line number data.
            valid_pms_keys: Set of valid PMS keys.
            pms_path: Resolved PMS file path (from _load_pms_config).
        """
        pms_val = line_data.pms_code
        if valid_pms_keys and pms_val not in valid_pms_keys:
            issues.append(f"Pipe '{name}': PMS '{pms_val}' (from NOTES) not found in PMS file.")
        else:
            nps = line_data.nominal_pipe_size
            try:
                from pykorf.use_case.pms import load_all_pms, lookup_pms_across_materials

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

    def _validate_pipe_sizing_criteria(self, issues: list[str]) -> None:
        """Validate pipe sizing criteria (DP/DL, Velocity, rho*V^2).

        For each pipe (excluding dummy pipes):
        - Check if calculated DPL <= SIZ dP/dL criteria (skip if criteria is 0)
        - Check if velocity <= max velocity criteria (skip if criteria is 0)
        - Check if rho*V^2 is within min/max bounds (skip if bounds are 0 or None)

        Args:
            issues: List to append validation issues to.
        """
        for pipe_idx, pipe in self.model.pipes.items():
            if pipe_idx == 0:
                continue

            name = pipe.name
            if not name or name.startswith("d"):
                continue

            if not hasattr(pipe, "check_criteria"):
                continue

            if not pipe.check_criteria():
                self._build_criteria_failure_message(issues, name, pipe)

    def _build_criteria_failure_message(self, issues: list[str], name: str, pipe) -> None:
        """Build detailed failure message for a pipe that failed sizing criteria.

        Args:
            issues: List to append validation issues to.
            name: Pipe name.
            pipe: Pipe instance.
        """
        failures = []

        try:
            dp_crit = float(pipe.sizing_dp_criteria)
            if dp_crit > 0:
                dp_calc = float(pipe.pressure_drop_per_100m) if pipe.pressure_drop_per_100m else 0.0
                if dp_calc > dp_crit:
                    failures.append(f"DP/DL({dp_calc:.2f} > {dp_crit})")
        except (ValueError, TypeError):
            pass

        try:
            vel_crit = float(pipe.sizing_velocity_criteria)
            if vel_crit > 0:
                vel_calc = float(pipe.velocity[0]) if pipe.velocity else 0.0
                if vel_calc > vel_crit:
                    failures.append(f"Vel({vel_calc:.2f} > {vel_crit})")
        except (ValueError, TypeError):
            pass

        rho_v2_calc = pipe.rho_v2
        if rho_v2_calc is not None:
            rho_v2_min = pipe.min_rho_v2_criteria
            rho_v2_max = pipe.max_rho_v2_criteria

            if rho_v2_min is not None and rho_v2_min > 0 and rho_v2_calc < rho_v2_min:
                failures.append(f"rhoV2({rho_v2_calc:.0f} < {rho_v2_min:.0f})")
            if rho_v2_max is not None and rho_v2_max > 0 and rho_v2_calc > rho_v2_max:
                failures.append(f"rhoV2({rho_v2_calc:.0f} > {rho_v2_max:.0f})")

        if failures:
            msg = " and ".join(failures)
            issues.append(f"Pipe '{name}' fails sizing criteria: {msg}.")
        else:
            issues.append(f"Pipe '{name}' fails sizing criteria.")

    def _check_num_counts(self, issues: list[str]) -> None:
        """Verify NUM records match actual instance counts."""
        etype_collection = {
            "PIPE": self.model.pipes,
            "FEED": self.model.feeds,
            "PROD": self.model.products,
            "PUMP": self.model.pumps,
            "VALVE": self.model.valves,
            "CHECK": self.model.check_valves,
            "FO": self.model.orifices,
            "HX": self.model.exchangers,
            "COMP": self.model.compressors,
            "MISC": self.model.misc_equipment,
            "EXPAND": self.model.expanders,
            "JUNC": self.model.junctions,
            "TEE": self.model.tees,
            "VESSEL": self.model.vessels,
        }

        for etype, collection in etype_collection.items():
            declared = self.model._parser.num_instances(etype)
            actual = sum(1 for idx in collection if idx >= 1)
            if declared != actual:
                issues.append(
                    f"{etype}: NUM declares {declared} instances but {actual} found in file"
                )

    def _check_required_params(self, issues: list[str]) -> None:
        """Check that template (index 0) has all required params."""
        for etype, required in _REQUIRED_PARAMS.items():
            template_recs = self.model._parser.get_all(etype, 0)
            if not template_recs:
                continue

            existing_params = {r.param for r in template_recs}
            for param in required:
                if param not in existing_params:
                    issues.append(f"{etype} template (index 0): missing required param {param!r}")

    def _check_instance_names(self, issues: list[str]) -> None:
        """Check that every real instance (index >= 1) has a NAME record."""
        for elem in self.model.elements:
            if elem.etype == "PIPEDATA":
                continue
            name_rec = elem.get_param("NAME")
            if name_rec is None or not name_rec.values:
                issues.append(f"{elem.etype} index {elem.index}: missing NAME record")
            elif not name_rec.values[0] or name_rec.values[0].strip() == "":
                issues.append(f"{elem.etype} index {elem.index}: NAME is empty")

    def _check_notes_format(self, issues: list[str]) -> None:
        """Check for malformed NOTES records."""
        for rec in self.model._parser.records:
            if rec.param == "NOTES":
                if not rec.values or len(rec.values) < 2:
                    if not rec.raw_line:
                        issues.append(f"{rec.element_type} idx {rec.index}: NOTES has no values")

    def _check_empty_values(self, issues: list[str]) -> None:
        """Check for empty or whitespace-only critical parameter values."""
        critical_params = {"NAME", "TYPE", "LEN", "DIA", "MAT", "PRES"}

        for elem in self.model.elements:
            for param_name in critical_params:
                rec = elem.get_param(param_name)
                if rec is not None and rec.values:
                    first_val = rec.values[0]
                    # Handle non-string values (e.g., floats) - they are considered valid
                    if isinstance(first_val, str):
                        val = first_val.strip() if first_val else ""
                        if not val:
                            issues.append(
                                f"{elem.etype} {elem.name} (index {elem.index}): "
                                f"{param_name} has empty or whitespace value"
                            )
                    # Non-string values (int, float) are considered valid/non-empty

    def _check_pipe_line_numbers(self, issues: list[str]) -> None:
        """Check that all pipes have line numbers in NOTES field.

        Pipes with names starting with 'd' (dummy lines) are exempt.
        """
        for pipe in self.model.pipes.values():
            if pipe.index == 0:
                continue

            if pipe.name.lower().startswith("d"):
                continue

            notes_rec = pipe.get_param("NOTES")
            if notes_rec is None or not notes_rec.values or not notes_rec.values[0]:
                issues.append(f"PIPE {pipe.name} (idx {pipe.index}): missing line number in NOTES")

    def _check_title_symbol(self) -> list[str]:
        """Check that model has at least one title symbol.

        A title symbol is identified by:
        - SYMBOL element with TYPE="Text" and FSIZ > 1.5

        Returns:
            List of validation issues (empty if title found).
        """
        from pykorf.elements import Symbol

        issues: list[str] = []
        has_title = False

        # Group records by index to check each symbol
        symbol_indices = {
            rec.index
            for rec in self.model._parser.records
            if rec.element_type == "SYMBOL" and rec.index is not None
        }

        for symbol_idx in symbol_indices:
            type_rec = self.model._parser.get("SYMBOL", symbol_idx, Symbol.TYPE)
            fsiz_rec = self.model._parser.get("SYMBOL", symbol_idx, Symbol.FSIZ)

            if type_rec and type_rec.values and fsiz_rec and fsiz_rec.values:
                type_val = type_rec.values[0]
                try:
                    fsiz_val = int(fsiz_rec.values[0])
                except (ValueError, TypeError):
                    fsiz_val = None

                if type_val == "Text" and fsiz_val is not None and fsiz_val > 1.5:
                    has_title = True
                    break

        if not has_title:
            issues.append("Add Title (Text with font size > 1.5)")

        return issues

    def _check_pipe_references(self, issues: list[str]) -> None:
        """Check pipe references in CON/NOZL/NOZ fields."""
        pipe_indices = set(self.model.pipes.keys())

        for elem in self.model.elements:
            con_rec = elem.get_param("CON")
            if con_rec and con_rec.values:
                for i, val in enumerate(con_rec.values):
                    try:
                        pipe_idx = int(val)
                        if pipe_idx > 0 and pipe_idx not in pipe_indices:
                            port_name = "inlet" if i == 0 else "outlet"
                            issues.append(
                                f"{elem.etype} {elem.name} (idx {elem.index}): "
                                f"CON {port_name} -> pipe {pipe_idx} not found"
                            )
                    except (ValueError, TypeError):
                        pass

            for nozzle_param in ("NOZL", "NOZ", "NOZI", "NOZO"):
                nozzle_rec = elem.get_param(nozzle_param)
                if nozzle_rec and nozzle_rec.values:
                    for val in nozzle_rec.values:
                        try:
                            pipe_idx = int(val)
                            if pipe_idx > 0 and pipe_idx not in pipe_indices:
                                issues.append(
                                    f"{elem.etype} {elem.name} (idx {elem.index}): "
                                    f"{nozzle_param} -> pipe {pipe_idx} not found"
                                )
                        except (ValueError, TypeError):
                            pass

            if elem.etype == "TEE" and con_rec and con_rec.values:
                port_names = ["combined", "main", "branch"]
                for i, val in enumerate(con_rec.values[:3]):
                    try:
                        pipe_idx = int(val)
                        if pipe_idx > 0 and pipe_idx not in pipe_indices:
                            issues.append(
                                f"TEE {elem.name} (index {elem.index}): "
                                f"CON {port_names[i] if i < len(port_names) else i} "
                                f"references non-existent pipe {pipe_idx}"
                            )
                    except (ValueError, TypeError):
                        pass

    def _validate_pipe_criteria(self) -> list[str]:
        """Validate pipe DPL, VEL, and rho*V^2 against SIZ criteria.

        For each pipe (index >= 1):
        - Check if calculated DPL <= SIZ dP/dL criteria (skip if criteria is 0)
        - Check if all VEL values (V_avg, V_in, V_out) are within SIZ min/max bounds (skip if 0)
        - Check if rho*V^2 is within min/max bounds from TOML lookup (skip if 0 or None)

        Only validates first case for multi-case models.

        Returns:
            List of validation issue descriptions.
        """
        issues: list[str] = []

        for idx in range(1, self.model.num_pipes + 1):
            pipe = self.model.pipes[idx]

            siz_rec = pipe.get_param(Pipe.SIZ)
            dpl_rec = pipe.get_param(Pipe.DPL)
            vel_rec = pipe.get_param(Pipe.VEL)

            if siz_rec is None or not siz_rec.values:
                continue

            if len(siz_rec.values) < 8:
                continue

            try:
                siz_dpdl = float(siz_rec.values[1])
                siz_max_vel = float(siz_rec.values[3])
                siz_min_vel = float(siz_rec.values[4])
            except (ValueError, TypeError, IndexError):
                continue

            if dpl_rec and dpl_rec.values and len(dpl_rec.values) >= 1:
                try:
                    calc_dpl = float(dpl_rec.values[0])
                    if siz_dpdl > 0 and calc_dpl > siz_dpdl:
                        issues.append(
                            f"PIPE {pipe.name} (idx {pipe.index}): "
                            f"DPL {calc_dpl:.3f} exceeds criteria {siz_dpdl:.3f} kPa/100m"
                        )
                except (ValueError, TypeError):
                    pass

            if vel_rec and vel_rec.values and len(vel_rec.values) >= 3:
                try:
                    v_avg = float(vel_rec.values[0])
                    v_in = float(vel_rec.values[1])
                    v_out = float(vel_rec.values[2])

                    for vel_name, vel_value in [("V_avg", v_avg), ("V_in", v_in), ("V_out", v_out)]:
                        if siz_max_vel > 0 and vel_value > siz_max_vel:
                            issues.append(
                                f"PIPE {pipe.name} (idx {pipe.index}): "
                                f"{vel_name} {vel_value:.3f} exceeds max criteria {siz_max_vel:.3f} m/s"
                            )
                        if siz_min_vel > 0 and vel_value < siz_min_vel:
                            issues.append(
                                f"PIPE {pipe.name} (idx {pipe.index}): "
                                f"{vel_name} {vel_value:.3f} below min criteria {siz_min_vel:.3f} m/s"
                            )
                except (ValueError, TypeError):
                    pass

            rho_v2_calc = pipe.rho_v2
            if rho_v2_calc is not None:
                rho_v2_min = pipe.min_rho_v2_criteria
                rho_v2_max = pipe.max_rho_v2_criteria

                if rho_v2_min is not None and rho_v2_min > 0 and rho_v2_calc < rho_v2_min:
                    issues.append(
                        f"PIPE {pipe.name} (idx {pipe.index}): "
                        f"rho*V^2 {rho_v2_calc:.0f} below min criteria {rho_v2_min:.0f} Pa"
                    )
                if rho_v2_max is not None and rho_v2_max > 0 and rho_v2_calc > rho_v2_max:
                    issues.append(
                        f"PIPE {pipe.name} (idx {pipe.index}): "
                        f"rho*V^2 {rho_v2_calc:.0f} exceeds max criteria {rho_v2_max:.0f} Pa"
                    )

        return issues

    def _verify_pipe_properties(self) -> list[str]:
        """Verify pipe properties match the Line Number + PMS specification.

        For each pipe with a valid line number in NOTES:
        1. Parse line number to get NPS and piping class
        2. Look up expected schedule/ID and material from PMS
        3. Compare with actual pipe properties:
           - NPS/DIA: Numerical comparison (handle fractions like "1/2", "1-1/2")
           - ID: Compare with 1mm tolerance (convert units as needed)
           - SCH: Case-insensitive string match
           - MAT: Case-insensitive string match
        4. Report mismatches

        Pipes where PMS lookup fails are skipped (already reported by existing validation).
        Dummy pipes (names starting with 'd') are skipped.

        Returns:
            List of validation issue descriptions for property mismatches.
        """
        issues: list[str] = []

        from pykorf.use_case.config import get_pms_path
        from pykorf.use_case.line_number import LineNumber, format_nps
        from pykorf.use_case.pms import load_all_pms, lookup_pms_across_materials

        # Load PMS data once for all pipes
        pms_path = get_pms_path()
        if not pms_path or not pms_path.exists():
            return issues  # PMS file not available, skip verification

        try:
            all_materials = load_all_pms(pms_path)
        except Exception:
            return issues  # Failed to load PMS, skip verification

        for pipe_idx, pipe in self.model.pipes.items():
            if pipe_idx == 0:
                continue

            name = pipe.name
            if not name:
                continue

            # Skip dummy pipes
            if name.lower().startswith("d"):
                continue

            # Parse line number from NOTES
            notes_rec = pipe.get_param("NOTES")
            notes_val = notes_rec.values[0] if notes_rec and notes_rec.values else ""

            if not notes_val:
                continue

            line_data = LineNumber.parse(notes_val)
            if not line_data:
                continue

            # Look up PMS data
            nps = line_data.nominal_pipe_size
            pms_code = line_data.pms_code

            try:
                material, spec, od_mm, _ = lookup_pms_across_materials(
                    all_materials, pms_code, float(nps)
                )
            except Exception:
                # PMS lookup failed - already reported by existing validation, skip
                continue

            # Get expected values from PMS
            pms_value = spec.get("value") or spec.get("schedule", "")
            expected_sch = pms_value if pms_value else None
            expected_mat = material if material else None

            # Determine if this is ID-based (wall thickness in mm) or SCH-based
            is_id_based = expected_sch and "mm" in expected_sch.lower()

            # Get actual pipe properties
            dia_rec = pipe.get_param(Pipe.DIA)
            sch_rec = pipe.get_param(Pipe.SCH)
            id_rec = pipe.get_param(Pipe.ID)
            mat_rec = pipe.get_param(Pipe.MAT)

            actual_dia = dia_rec.values[0] if dia_rec and dia_rec.values else None
            actual_sch = sch_rec.values[0] if sch_rec and sch_rec.values else None
            actual_id = id_rec.values[0] if id_rec and id_rec.values else None
            actual_mat = mat_rec.values[0] if mat_rec and mat_rec.values else None

            mismatches: list[str] = []

            # Verify NPS/DIA
            if actual_dia:
                expected_nps_str = format_nps(nps)
                if not self._compare_nps(str(actual_dia), expected_nps_str):
                    mismatches.append(f"NPS={expected_nps_str}")

            # Verify Schedule or ID
            if is_id_based and actual_id and expected_sch:
                # Parse wall thickness from "5 mm" format
                wall_str = expected_sch.lower().replace("mm", "").strip()
                try:
                    wall_mm = float(wall_str)
                    expected_id_m = (
                        od_mm - 2 * wall_mm
                    ) / 1000.0  # Convert to meters for comparison
                    # Parse actual ID (convert to mm if in meters)
                    actual_id_val = float(actual_id)

                    # Compare with 1mm tolerance
                    if abs(actual_id_val - expected_id_m) > 0.001:
                        mismatches.append(f"ID={expected_id_m:.1f}mm")
                except (ValueError, TypeError):
                    pass
            elif expected_sch and actual_sch:
                # Standard schedule comparison - normalize by stripping "SCH " prefix
                actual_sch_norm = str(actual_sch).strip().upper()
                expected_sch_norm = expected_sch.strip().upper()
                # Remove "SCH " prefix if present for comparison
                if expected_sch_norm.startswith("SCH "):
                    expected_sch_norm = expected_sch_norm[4:]
                if actual_sch_norm != expected_sch_norm:
                    mismatches.append(f"SCH={expected_sch}")

            # Verify Material
            if expected_mat and actual_mat:
                if str(actual_mat).strip().upper() != expected_mat.strip().upper():
                    mismatches.append(f"MAT={expected_mat}")

            # Report mismatches
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

                expected_str = ", ".join(expected_parts)
                actual_str = ", ".join(actual_parts)

                issues.append(
                    f"Pipe '{name}': Line number expects {expected_str} but model has {actual_str}"
                )

        return issues

    def _compare_nps(self, actual: str, expected: str) -> bool:
        """Compare NPS values, handling fractions.

        Args:
            actual: Actual DIA value from pipe.
            expected: Expected NPS value from line number.

        Returns:
            True if values match numerically.
        """
        actual_normalized = self._normalize_nps(actual)
        expected_normalized = self._normalize_nps(expected)

        try:
            return abs(float(actual_normalized) - float(expected_normalized)) < 0.01
        except (ValueError, TypeError):
            return actual.strip() == expected.strip()

    def _normalize_nps(self, nps_str: str) -> str:
        """Normalize NPS string to decimal for comparison.

        Handles fractions like "1/2", "3/4", "1-1/2".

        Args:
            nps_str: NPS string (e.g., "6", "1/2", "1-1/2").

        Returns:
            Decimal string representation.
        """
        if not nps_str:
            return nps_str

        s = nps_str.strip()

        # Handle whole-fraction combination (e.g., "1-1/2")
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

        # Handle standalone fraction (e.g., "3/4")
        if "/" in s:
            try:
                num, den = s.split("/", 1)
                return str(float(num) / float(den))
            except (ValueError, TypeError, ZeroDivisionError):
                pass

        return s

    def pipe(self, index: int) -> Pipe:
        """Return pipe *index*, raise :exc:`ElementNotFound` if absent.

        Args:
            index: The pipe index to look up.

        Returns:
            The Pipe instance at the given index.

        Raises:
            ElementNotFound: If the pipe index is not found.
        """
        if index not in self.model.pipes:
            raise ElementNotFound(f"Pipe {index} not found in model")
        return self.model.pipes[index]

    def pump(self, index: int) -> Pump:
        """Return pump *index*, raise :exc:`ElementNotFound` if absent.

        Args:
            index: The pump index to look up.

        Returns:
            The Pump instance at the given index.

        Raises:
            ElementNotFound: If the pump index is not found.
        """
        if index not in self.model.pumps:
            raise ElementNotFound(f"Pump {index} not found in model")
        return self.model.pumps[index]

    def feed(self, index: int) -> Feed:
        """Return feed *index*, raise :exc:`ElementNotFound` if absent.

        Args:
            index: The feed index to look up.

        Returns:
            The Feed instance at the given index.

        Raises:
            ElementNotFound: If the feed index is not found.
        """
        if index not in self.model.feeds:
            raise ElementNotFound(f"Feed {index} not found in model")
        return self.model.feeds[index]

    def product(self, index: int) -> Product:
        """Return product *index*, raise :exc:`ElementNotFound` if absent.

        Args:
            index: The product index to look up.

        Returns:
            The Product instance at the given index.

        Raises:
            ElementNotFound: If the product index is not found.
        """
        if index not in self.model.products:
            raise ElementNotFound(f"Product {index} not found in model")
        return self.model.products[index]

    def summary(self) -> dict:
        """Return a high-level dict describing the model.

        Returns:
            Dictionary with model metadata including file path, version,
            case descriptions, and element counts.
        """
        return {
            "file": str(self.model._parser.path),
            "version": self.model.version,
            "cases": self.model.general.case_descriptions,
            "num_pipes": self.model.num_pipes,
            "num_pumps": self.model.num_pumps,
            "num_junctions": self.model._parser.num_instances("JUNC"),
            "num_feeds": self.model._parser.num_instances("FEED"),
            "num_products": self.model._parser.num_instances("PROD"),
            "num_valves": self.model._parser.num_instances("VALVE"),
            "num_orifices": self.model._parser.num_instances("FO"),
            "num_exchangers": self.model._parser.num_instances("HX"),
            "num_misc": self.model._parser.num_instances("MISC"),
        }

    def __repr__(self) -> str:
        """Return string representation of the model.

        Returns:
            String in format "KorfModel(version='...', pipes=N, pumps=N, cases=N)".
        """
        token_to_name = {
            token: attr.lower()
            for attr, token in vars(Element).items()
            if attr.isupper() and isinstance(token, str)
        }

        parts = [f"version={self.model.version!r}"]
        for etype in Element.ALL:
            if etype in (Element.GEN, Element.SYMBOL, Element.TOOLS, Element.PSEUDO):
                continue
            display_name = token_to_name.get(etype, etype.lower())
            count = self.model._parser.num_instances(etype)
            parts.append(f"{display_name}={count}")
        parts.append(f"cases={self.model.num_cases}")

        return f"KorfModel({', '.join(parts)})"


__all__ = ["SummaryService"]
