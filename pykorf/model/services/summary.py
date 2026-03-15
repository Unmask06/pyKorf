"""SummaryService - validation, convenience accessors, and summary methods.

This service provides methods for validating models and accessing
summary information about model contents.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from pykorf.elements import Element, Feed, Pipe, Product, Pump
from pykorf.exceptions import ElementNotFound

if TYPE_CHECKING:
    from pykorf.model import Model

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
        return self._validate()

    def _validate(self) -> list[str]:
        """Internal validation implementation focusing on pipes and PMS."""
        issues: list[str] = []

        # We need config to check PMS
        import json

        from pykorf.use_case.config import get_pms_path

        valid_pms_keys = set()
        pms_path = get_pms_path()
        if pms_path and pms_path.exists():
            try:
                with open(pms_path, encoding="utf-8") as f:
                    pms_data = json.load(f)
                    # Handle nested format: {material: {"specifications": {pms_code: ...}}}
                    for material_data in pms_data.values():
                        if isinstance(material_data, dict) and "specifications" in material_data:
                            specs = material_data["specifications"]
                            if isinstance(specs, dict):
                                valid_pms_keys.update(specs.keys())
                        elif isinstance(material_data, dict):
                            # Fallback for older formats or direct specs
                            valid_pms_keys.update(material_data.keys())

                    # Also include top-level keys just in case it's a legacy flat format
                    valid_pms_keys.update(pms_data.keys())
            except Exception:
                issues.append("Failed to load PMS config file.")

        from pykorf.use_case.line_number import LineNumber

        for pipe_idx, pipe in self.model.pipes.items():
            if pipe_idx == 0:
                continue

            name = pipe.name
            if not name:
                issues.append(f"Pipe {pipe_idx} is missing a name.")
                continue

            # Skip dummy pipes
            if name.startswith("d"):
                continue

            # 1. Line Number in NOTES Parsing
            notes_rec = pipe.get_param("NOTES")
            notes_val = notes_rec.values[0] if notes_rec and notes_rec.values else ""

            if not notes_val:
                issues.append(f"Pipe '{name}' is missing a line number in NOTES.")
                continue

            line_data = LineNumber.parse(notes_val)
            if line_data:
                # 2. PMS Verification
                pms_val = line_data.pms_code
                if valid_pms_keys and pms_val not in valid_pms_keys:
                    issues.append(
                        f"Pipe '{name}': PMS '{pms_val}' (from NOTES) not found in pms.json."
                    )
            else:
                issues.append(
                    f"Pipe '{name}': NOTES value '{notes_val}' is not a valid line number."
                )

            # 3. Sizing Criteria Check
            if hasattr(pipe, "check_criteria"):
                status = pipe.check_criteria()
                if status == "FAIL":
                    dp_crit = pipe.sizing_dp_criteria
                    vel_crit = pipe.sizing_velocity_criteria
                    dp_calc = pipe.pressure_drop_per_100m
                    vel_calc = pipe.velocity[0] if pipe.velocity else 0.0

                    failures = []
                    if dp_calc > dp_crit:
                        failures.append(f"DP/DL({dp_calc:.2f} > {dp_crit})")
                    if vel_calc > vel_crit:
                        failures.append(f"Vel({vel_calc:.2f} > {vel_crit})")

                    if failures:
                        msg = " and ".join(failures)
                        issues.append(f"Pipe '{name}' fails sizing criteria: {msg}.")
                    else:
                        # Fallback if status is FAIL but thresholds aren't crossed (rounding/edge cases)
                        issues.append(f"Pipe '{name}' fails sizing criteria.")

        return issues

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
        """Validate pipe DPL and VEL against SIZ criteria.

        For each pipe (index >= 1):
        - Check if calculated DPL <= SIZ dP/dL criteria
        - Check if all VEL values (V_avg, V_in, V_out) are within SIZ min/max bounds

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
                    if calc_dpl > siz_dpdl:
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
                        if vel_value > siz_max_vel:
                            issues.append(
                                f"PIPE {pipe.name} (idx {pipe.index}): "
                                f"{vel_name} {vel_value:.3f} exceeds max criteria {siz_max_vel:.3f} m/s"
                            )
                        if vel_value < siz_min_vel:
                            issues.append(
                                f"PIPE {pipe.name} (idx {pipe.index}): "
                                f"{vel_name} {vel_value:.3f} below min criteria {siz_min_vel:.3f} m/s"
                            )
                except (ValueError, TypeError):
                    pass

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
            "num_pipes": self.model.num_pipes,
            "num_pumps": self.model.num_pumps,
            "num_feeds": self.model._parser.num_instances("FEED"),
            "num_products": self.model._parser.num_instances("PROD"),
            "num_valves": self.model._parser.num_instances("VALVE"),
            "num_orifices": self.model._parser.num_instances("FO"),
            "num_exchangers": self.model._parser.num_instances("HX"),
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
