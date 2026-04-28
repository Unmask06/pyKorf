from __future__ import annotations

import logging
import re
from pathlib import Path

import pandas as pd

from pykorf import Model
from pykorf.app.operation.integration.sizing_criteria import (
    code_to_state,
    lookup_criteria,
)
from pykorf.core.reports.korf_parser import (
    CaseInfo,
    KorfCaseData,
    PipeData,
    parse_korf_excel,
)
from pykorf.core.reports.reporter import _BaseReporter

_logger = logging.getLogger(__name__)

DUMMY_LINE_RE = re.compile(r"\bLine d")  # exclude dummy lines from validation


class KorfReporter(_BaseReporter):
    """Extracts element data from a KORF Excel report + KDF Model for report generation.

    This reporter reads multi-case result data from a KORF-generated Excel file,
    and supplements it with input-side fields (criteria codes, line numbers)
    from the KDF model. Criteria values (dp max, velocity min/max, rho_v2 min/max)
    are looked up from the sizing criteria TOML files using the criteria code.

    The output format mirrors PykorfReporter so the same ReportExporter
    formatting logic can be used.
    """

    def __init__(
        self,
        excel_path: str | Path,
        model: Model,
        basis: str = "",
        remarks: str = "",
        hold: str = "",
        references: list[dict] | None = None,
    ):
        super().__init__(model, basis=basis, remarks=remarks, hold=hold, references=references)
        self._excel_path = Path(excel_path)

        self._case_data: dict[CaseInfo, KorfCaseData] | None = None

    def _get_case_data(self) -> dict[CaseInfo, KorfCaseData]:
        if self._case_data is None:
            self._case_data = parse_korf_excel(self._excel_path)
        return self._case_data

    def get_source_name(self) -> str:
        """Return the KORF Excel file name."""
        return self._excel_path.name

    def get_case_names(self) -> list[str]:
        """Return case names extracted from the KORF Excel sheet names."""
        case_data = self._get_case_data()
        return [
            f"{ci.number} - {ci.name}"
            for ci in sorted(case_data.keys(), key=lambda c: int(c.number))
        ]

    def get_validation_dataframe(self) -> pd.DataFrame:
        """Combine validation issues from all KORF Excel cases."""
        all_issues: list[dict[str, str]] = []
        case_data = self._get_case_data()

        excluded_names: set[str] = set()
        for cd in case_data.values():
            for p in cd.pipes:
                if p.name.startswith("d"):
                    excluded_names.add(p.name)
                elif p.length is not None and p.length < 5.0:
                    dp = (
                        abs(p.pressure_in - p.pressure_out)
                        if p.pressure_in is not None and p.pressure_out is not None
                        else None
                    )
                    if dp is None or dp <= 0.5:
                        excluded_names.add(p.name)

        for case_info in sorted(case_data.keys(), key=lambda c: int(c.number)):
            cd = case_data[case_info]
            for entry in cd.validations:
                msg = entry.message
                if DUMMY_LINE_RE.search(msg):
                    continue
                severity, category, elem = self.classify_issue(msg)
                if elem and elem in excluded_names:
                    continue
                all_issues.append(
                    {
                        "Severity": severity,
                        "Category": category,
                        "Element": elem,
                        "Message": f"[{case_info.name}] {msg}",
                    }
                )

        if not all_issues:
            return pd.DataFrame(columns=["Severity", "Category", "Element", "Message"])
        return pd.DataFrame(all_issues)

    def generate_dataframes(self) -> dict[str, pd.DataFrame]:
        """Generate DataFrames for all element types using the first (or primary) case."""
        case_data = self._get_case_data()
        if not case_data:
            _logger.warning("No case data found in KORF Excel: %s", self._excel_path)
            return {}

        primary_case = sorted(case_data.keys(), key=lambda c: int(c.number))[0]
        cd = case_data[primary_case]
        return self._build_case_dataframes(cd)

    def generate_all_case_dataframes(self) -> dict[str, dict[str, pd.DataFrame]]:
        """Generate DataFrames for all element types, one dict per case.

        Returns a dict mapping case name (e.g. "1 - Rated") to a dict of
        element-type DataFrames (same structure as ``generate_dataframes()``).
        """
        case_data = self._get_case_data()
        if not case_data:
            _logger.warning("No case data found in KORF Excel: %s", self._excel_path)
            return {}

        result: dict[str, dict[str, pd.DataFrame]] = {}
        for case_info in sorted(case_data.keys(), key=lambda c: int(c.number)):
            case_name = f"{case_info.number} - {case_info.name}"
            cd = case_data[case_info]
            result[case_name] = self._build_case_dataframes(cd)
        return result

    def _build_case_dataframes(self, cd: KorfCaseData) -> dict[str, pd.DataFrame]:
        """Build element DataFrames for a single case."""
        dfs: dict[str, pd.DataFrame] = {}

        feeds_data = self._extract_feeds(cd)
        if feeds_data:
            dfs["Feeds"] = pd.DataFrame(feeds_data)

        products_data = self._extract_products(cd)
        if products_data:
            dfs["Products"] = pd.DataFrame(products_data)

        pipes_data = self._extract_pipes(cd)
        if pipes_data:
            dfs["Pipes"] = pd.DataFrame(pipes_data)

        pumps_data = self._extract_pumps(cd)
        if pumps_data:
            dfs["Pumps"] = pd.DataFrame(pumps_data)

        valves_data = self._extract_valves(cd)
        if valves_data:
            dfs["Valves"] = pd.DataFrame(valves_data)

        orifices_data = self._extract_orifices(cd)
        if orifices_data:
            dfs["Orifices"] = pd.DataFrame(orifices_data)

        compressors_data = self._extract_compressors(cd)
        if compressors_data:
            dfs["Compressors"] = pd.DataFrame(compressors_data)

        exchangers_data = self._extract_exchangers(cd)
        if exchangers_data:
            dfs["Exchangers"] = pd.DataFrame(exchangers_data)

        misc_data = self._extract_misc_equipment(cd)
        if misc_data:
            dfs["Misc Equipment"] = pd.DataFrame(misc_data)

        return dfs

    # ── FEEDS ─────────────────────────────────────────────────────────

    def _extract_feeds(self, cd: KorfCaseData) -> list[dict]:
        return [
            {
                "Source": f"{f.name} , {f.description}" if f.description else f.name,
                "Pressure [barg]": f.pressure,
            }
            for f in cd.feeds
        ]

    # ── PRODUCTS ──────────────────────────────────────────────────────

    def _extract_products(self, cd: KorfCaseData) -> list[dict]:
        return [
            {
                "Sink": f"{p.name} , {p.description}" if p.description else p.name,
                "Pressure [barg]": p.pressure,
            }
            for p in cd.products
        ]

    # ── PIPES ──────────────────────────────────────────────────────────

    def _extract_pipes(self, cd: KorfCaseData) -> list[dict]:
        results = []
        for pd_pipe in cd.pipes:
            if pd_pipe.name.startswith("d"):
                continue
            if pd_pipe.length is not None and pd_pipe.length < 5.0:
                dp = (
                    abs(pd_pipe.pressure_in - pd_pipe.pressure_out)
                    if pd_pipe.pressure_in is not None and pd_pipe.pressure_out is not None
                    else None
                )
                if dp is None or dp <= 0.5:
                    continue

            pipe_model = self._find_pipe_in_model(pd_pipe.name)

            criteria_code = ""
            line_number = ""
            rho_v2_min: float | None = None
            rho_v2_max: float | None = None

            if pipe_model and pipe_model.index != 0:
                criteria_code = pipe_model.criteria_code or ""
                from pykorf.app.operation.data_import.line_number import LineNumber

                parsed = LineNumber.parse(pipe_model.notes)
                line_number = parsed.raw_line_number if parsed else ""

                if criteria_code:
                    state = code_to_state(criteria_code)
                    if state:
                        try:
                            size_inch = (
                                float(pipe_model.diameter_inch)
                                if pipe_model.diameter_inch
                                else None
                            )
                        except (ValueError, TypeError):
                            size_inch = None
                        pressures = pipe_model.pressure or []
                        try:
                            pressure_barg = pressures[0] / 100.0 if pressures else None
                        except (IndexError, TypeError):
                            pressure_barg = None
                        crit = lookup_criteria(state, criteria_code, size_inch, pressure_barg)
                        if crit:
                            rho_v2_min = round(crit.rho_v2_min) if crit.rho_v2_min else None
                            rho_v2_max = (
                                round(crit.rho_v2_max) if crit.rho_v2_max is not None else None
                            )

            units = pd_pipe.units
            length_unit = units.get("length", "m")
            dp_length_unit = units.get("dp_length", "bar/100m")
            dp_crit_unit = units.get("dp_length_criteria_max", "bar/100m")
            vel_unit = units.get("velocity_in", "m/s")
            vel_max_unit = units.get("velocity_criteria_max", "m/s")
            vel_min_unit = units.get("velocity_criteria_min", "m/s")
            rho_v2_unit = units.get("rho_v2_in", "Pa")

            row = {
                "Pipe Name": pd_pipe.name,
                "Criteria Code": criteria_code,
                "Line Number": line_number,
                "Line Size": pd_pipe.size or "",
                f"Line Length [{length_unit}]": pd_pipe.length,
                f"dP max Criteria [{dp_crit_unit}]": pd_pipe.dp_length_criteria_max,
                f"v min Criteria [{vel_min_unit}]": pd_pipe.velocity_criteria_min,
                f"v max Criteria [{vel_max_unit}]": pd_pipe.velocity_criteria_max,
                "ρV² min Criteria [Pa]": rho_v2_min,  # noqa: RUF001
                "ρV² max Criteria [Pa]": rho_v2_max,  # noqa: RUF001
                f"DP/Length [{dp_length_unit}]": pd_pipe.dp_length,
                f"Velocity [{vel_unit}]": pd_pipe.velocity_in,
                f"ρV² calc [{rho_v2_unit}]": (  # noqa: RUF001
                    round(pd_pipe.rho_v2_in) if pd_pipe.rho_v2_in is not None else None
                ),
                "Criteria Check": self._check_pipe_criteria(pd_pipe),
            }
            results.append(row)

        return results

    def _find_pipe_in_model(self, name: str):
        """Find a pipe in the model by name."""
        for idx, pipe in self.model.pipes.items():
            if idx != 0 and pipe.name == name:
                return pipe
        return None

    def _check_pipe_criteria(self, pd_pipe: PipeData) -> str:
        """Check pipe criteria and return PASS/FAIL status."""
        if (
            pd_pipe.dp_length_criteria_max is not None
            and pd_pipe.dp_length is not None
            and pd_pipe.dp_length_criteria_max > 0
        ):
            if abs(pd_pipe.dp_length) > abs(pd_pipe.dp_length_criteria_max):
                return "FAIL"
        if (
            pd_pipe.velocity_criteria_max is not None
            and pd_pipe.velocity_in is not None
            and pd_pipe.velocity_criteria_max > 0
        ):
            if abs(pd_pipe.velocity_in) > abs(pd_pipe.velocity_criteria_max):
                return "FAIL"
        if pd_pipe.velocity_criteria_min is not None and pd_pipe.velocity_in is not None:
            if (
                pd_pipe.velocity_criteria_min > 0
                and abs(pd_pipe.velocity_in) < pd_pipe.velocity_criteria_min
            ):
                return "FAIL"
        return "PASS"

    # ── PUMPS ──────────────────────────────────────────────────────────

    def _extract_pumps(self, cd: KorfCaseData) -> list[dict]:
        results = []
        for pump in cd.pumps:
            # Find inlet pipe data by name to get temperature and viscosity
            inlet_pipe = next((p for p in cd.pipes if p.name == pump.pipe_inlet), None)
            temperature = inlet_pipe.temperature_out if inlet_pipe else None
            viscosity = inlet_pipe.viscosity if inlet_pipe else None

            row = {
                "Pump Name": pump.name,
                "Section_Liquid Characteristics": "Liquid Characteristics",
                "Vapour Pressure [bara]": pump.vapour_pressure,
                "Density [kg/m³]": pump.density,
                "Viscosity [cP]": viscosity,
                "Section_Operating Conditions": "Operating Conditions",
                "Pump Datum Elevation [m]": pump.elevation,
                "Pumping Temperature [°C]": temperature,
                "Volumetric Flow [m³/h]": pump.vol_flow,
                "Discharge Pressure [barg]": pump.pressure_out,
                "Suction Pressure [barg]": pump.pressure_in,
                "Differential Pressure [bar]": pump.dp,
                "Differential Head [m]": pump.head,
                "NPSH Available [m]": pump.npsha_calc,
                "Hydraulic Power [kW]": pump.power,
                "Section_Performance Characteristics": "Performance Characteristics",
                "Raise to Shutoff DP []": pump.raise_to_shutoff_dp,
                "Suc Vessel Design Pressure [barg]": pump.vessel_pressure,
                "Suc Vessel Max Level [m]": pump.vessel_max_level,
                "Shut-Off DP [bar]": pump.shutoff_dp,
                "Suction Max Pressure [barg]": pump.suction_max_pressure,
                "Discharge Shut-Off Pressure [barg]": pump.shutoff_pressure,
            }
            results.append(row)
        return results

    # ── VALVES ─────────────────────────────────────────────────────────

    def _extract_valves(self, cd: KorfCaseData) -> list[dict]:
        results = []
        for valve in cd.valves:
            inlet_pipe = next((p for p in cd.pipes if p.name == valve.pipe_inlet), None)
            flow_rate = inlet_pipe.mass_flow if inlet_pipe else None

            row = {
                "Valve Name": valve.name,
                "Flow Rate [kg/h]": flow_rate,
                "Inlet Pressure [barg]": valve.pressure_in,
                "Differential Pressure [bar]": valve.dp,
                "Opening [%]": None,
            }
            results.append(row)
        return results

    # ── ORIFICES ──────────────────────────────────────────────────────

    def _extract_orifices(self, cd: KorfCaseData) -> list[dict]:
        # Orifice Name, Type, DP Pipe Tap, Inlet Pressure, Outlet Pressure
        results = []
        for orif in cd.orifices:
            row = {
                "Orifice Name": f"{orif.name} , {orif.description}"
                if orif.description
                else orif.name,
                "Type": orif.type,
                "DP Pipe Tap [bar]": orif.dp_pipe_tap,
                "Inlet Pressure [barg]": orif.pressure_in,
                "Outlet Pressure [barg]": orif.pressure_out,
            }
            results.append(row)
        return results

    # ── COMPRESSORS ───────────────────────────────────────────────────

    def _extract_compressors(self, cd: KorfCaseData) -> list[dict]:
        # Aligns with Compressor.summary(export=True):
        # Compressor Name, Suction Pressure, Discharge Pressure,
        # Differential Pressure, Gas Volumetric Flow, Power
        results = []
        for comp in cd.compressors:
            display_name = f"{comp.name} , {comp.description}" if comp.description else comp.name
            row = {
                "Compressor Name": display_name,
                "Suction Pressure [barg]": comp.pressure_in,
                "Discharge Pressure [barg]": comp.pressure_out,
                "Differential Pressure [bar]": comp.dp,
                "Gas Volumetric Flow [m³/h]": comp.flow,
                "Power [kW]": comp.power,
            }
            results.append(row)
        return results

    # ── EXCHANGERS ────────────────────────────────────────────────────

    def _extract_exchangers(self, cd: KorfCaseData) -> list[dict]:
        # Aligns with HeatExchanger.summary(export=True):
        # Heat Exchanger Name, Type, Side, Pressure Drop,
        # Inlet Pressure, Outlet Pressure
        results = []
        for hx in cd.exchangers:
            row = {
                "Heat Exchanger Name": hx.name,
                "Type": hx.type,
                "Side": hx.side,
                "Pressure Drop [bar]": hx.dp,
                "Inlet Pressure [barg]": hx.pressure_in,
                "Outlet Pressure [barg]": hx.pressure_out,
            }
            results.append(row)
        return results

    # ── MISC EQUIPMENT ────────────────────────────────────────────────

    def _extract_misc_equipment(self, cd: KorfCaseData) -> list[dict]:
        # Aligns with MiscEquipment.summary(export=True):
        # Equipment Name, Pressure Drop
        results = []
        for misc in cd.misc_equipment:
            display_name = f"{misc.name} , {misc.description}" if misc.description else misc.name
            row = {
                "Equipment Name": display_name,
                "Pressure Drop [bar]": misc.dp,
            }
            results.append(row)
        return results
