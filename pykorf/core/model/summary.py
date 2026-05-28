"""SummaryService - validation, convenience accessors, and summary methods.

This service provides methods for validating models and accessing
summary information about model contents.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from pykorf.core.elements import Element, Feed, Pipe, Product, Pump
from pykorf.core.elements.pipe import criteria_flags_to_labels as _criteria_flags_to_labels
from pykorf.core.exceptions import ElementNotFound

if TYPE_CHECKING:
    from pykorf.core.model import Model

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
        kdf_path: Optional path to the KDF file (used for loading justifications).
    """

    model: Model
    kdf_path: Path | None = None

    def validate(
        self,
        *,
        check_connectivity: bool = True,
    ) -> list[str]:
        """Validate KDF format compliance.

        Returns a list of validation issues (empty = valid model).

        Args:
            check_connectivity: Whether to check connectivity consistency (deprecated, ignored).

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
        """Internal core validation (KDF-format compliance only)."""
        issues: list[str] = []

        self._validate_pipe_sizing_criteria(issues)
        self._validate_pipe_criteria_codes(issues)
        self._validate_pump_vessel_pressure(issues)
        issues.extend(self._check_title_symbol())

        return issues

    def _validate_pipe_sizing_criteria(self, issues: list[str]) -> None:
        """Validate pipe sizing criteria (DP/DL, Velocity, rho*V^2).

        For each pipe (excluding dummy pipes):
        - Check if calculated DPL <= SIZ dP/dL criteria (skip if criteria is 0)
        - Check if velocity <= max velocity criteria (skip if criteria is 0)
        - Check if rho*V^2 is within min/max bounds (skip if bounds are 0 or None)
        - Skip pipes that have justifications (violations are accepted with justification)

        Args:
            issues: List to append validation issues to.
        """
        from pykorf.app.operation.project.pykorf_file import get_justifications

        valid_indices = {idx for idx in self.model.pipes if idx != 0}
        justifications = (
            get_justifications(self.kdf_path, valid_pipe_indices=valid_indices)
            if self.kdf_path
            else {}
        )

        for pipe_idx, pipe in self.model.pipes.items():
            if pipe_idx == 0:
                continue

            name = pipe.name
            if not name or name.startswith("d"):
                continue
            if pipe.length_m < 5.0:
                p = pipe.pressure
                if len(p) < 2 or abs(p[0] - p[1]) <= 50.0:
                    continue

            if not hasattr(pipe, "check_criteria"):
                continue

            is_justified = pipe_idx in justifications
            result = pipe.check_criteria(justified=is_justified)

            if result["status"] == "FAIL":
                self._build_criteria_failure_message(issues, name, pipe)
            elif result["status"] == "JUSTIFIED":
                failed_criteria = _criteria_flags_to_labels(result)
                criteria_str = ", ".join(failed_criteria) if failed_criteria else "criteria"
                reason = justifications.get(pipe_idx, "")
                _logger.debug(
                    "Pipe '%s': %s violation justified%s",
                    name,
                    criteria_str,
                    f" - {reason}" if reason else "",
                )

    def _validate_pipe_criteria_codes(self, issues: list[str]) -> None:
        """Validate that all pipes have a criteria code assigned.

        For each pipe (excluding dummy pipes starting with 'd'):
        - Check if criteria_code is set (non-empty)
        - Skip pipes that don't have the criteria_code property

        Args:
            issues: List to append validation issues to.
        """
        for pipe_idx, pipe in self.model.pipes.items():
            if pipe_idx == 0:
                continue

            name = pipe.name
            if not name or name.startswith("d"):
                continue
            if pipe.length_m < 5.0:
                p = pipe.pressure
                if len(p) < 2 or abs(p[0] - p[1]) <= 50.0:
                    continue

            if not hasattr(pipe, "criteria_code"):
                continue

            criteria_code = pipe.criteria_code
            if not criteria_code or not criteria_code.strip():
                issues.append(f"Pipe '{name}' (idx {pipe_idx}): missing criteria code")

    def _validate_pump_vessel_pressure(self, issues: list[str]) -> None:
        """Validate that pump suction vessel design pressure is specified."""
        for pump_idx, pump in self.model.pumps.items():
            if pump_idx == 0:
                continue

            if not hasattr(pump, "suction_vessel_max_pressure_kPag"):
                continue

            vessel_pres = pump.suction_max_pressure_kPag
            if vessel_pres <= 0:
                issues.append(
                    f"Pump '{pump.name}' (idx {pump_idx}): "
                    f"vessel pressure must be greater than 0 (found {vessel_pres:.2f} kPag)"
                )

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

        vel_calc = float(pipe.velocity[0]) if pipe.velocity else 0.0

        max_vel = pipe.max_velocity_criteria
        if max_vel is not None and max_vel > 0 and vel_calc > max_vel:
            failures.append(f"Vel({vel_calc:.2f} > {max_vel})")

        min_vel = pipe.min_velocity_criteria
        if min_vel is not None and min_vel > 0 and vel_calc < min_vel:
            failures.append(f"Vel({vel_calc:.2f} < {min_vel})")

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
            declared = len(collection)
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

            if pipe.name.startswith("d"):
                continue
            if pipe.length_m < 5.0:
                p = pipe.pressure
                if len(p) < 2 or abs(p[0] - p[1]) <= 50.0:
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
        from pykorf.core.elements import Symbol

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

        for idx in range(1, len(self.model.pipes) + 1):
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
            "num_pipes": len(self.model.pipes),
            "num_pumps": len(self.model.pumps),
            "num_junctions": len(self.model.junctions),
            "num_feeds": len(self.model.feeds),
            "num_products": len(self.model.products),
            "num_valves": len(self.model.valves),
            "num_orifices": len(self.model.orifices),
            "num_exchangers": len(self.model.exchangers),
            "num_misc": len(self.model.misc_equipment),
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
            collection = self.model._collection_for_etype(etype)
            count = len(collection) if collection else 0
            parts.append(f"{display_name}={count}")
        parts.append(f"cases={self.model.general.num_cases}")

        return f"Model({', '.join(parts)})"


__all__ = ["SummaryService"]
