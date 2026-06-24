"""Data models for KORF Excel report parsing."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CaseInfo:
    """Identifies a single case in the KORF Excel report."""

    number: str
    name: str


@dataclass
class PipeData:
    """Result data for a single pipe, parsed from a Piping sheet."""

    name: str
    length: float | None = None
    size: str | None = None
    schedule: str | None = None
    dp_length: float | None = None
    velocity_in: float | None = None
    rho_v2_in: float | None = None
    dp_overall: float | None = None
    dp_friction: float | None = None
    dp_elevation: float | None = None
    pressure_in: float | None = None
    pressure_out: float | None = None
    temperature_in: float | None = None
    temperature_out: float | None = None
    density_in: float | None = None
    density_out: float | None = None
    viscosity: float | None = None
    mass_flow: float | None = None
    vol_flow: float | None = None
    dp_length_criteria_max: float | None = None
    velocity_criteria_max: float | None = None
    velocity_criteria_min: float | None = None
    units: dict[str, str] = field(default_factory=dict)


@dataclass
class FeedData:
    """Result data for a single feed element from Equipment sheet."""

    name: str
    description: str = ""
    elevation: float | None = None
    fluid_level: float | None = None
    pressure: float | None = None


@dataclass
class ProductData:
    """Result data for a single product element from Equipment sheet."""

    name: str
    description: str = ""
    elevation: float | None = None
    fluid_level: float | None = None
    pressure: float | None = None


@dataclass
class OrificeData:
    """Result data for a single orifice from Equipment sheet."""

    name: str
    description: str = ""
    type: str = ""
    bore: float | None = None
    beta: float | None = None
    dp_flange_tap: float | None = None
    dp_pipe_tap: float | None = None
    pressure_in: float | None = None
    pressure_out: float | None = None
    pipe_inlet: str = ""
    pipe_outlet: str = ""


@dataclass
class ValveData:
    """Result data for a single valve from Equipment sheet."""

    name: str
    description: str = ""
    type: str = ""
    cv: float | None = None
    lift_pct: float | None = None
    dp: float | None = None
    pressure_in: float | None = None
    pressure_out: float | None = None
    pipe_inlet: str = ""
    pipe_outlet: str = ""


@dataclass
class PumpData:
    """Result data for a single pump from Equipment sheet."""

    name: str
    description: str = ""
    elevation: float | None = None
    efficiency: float | None = None
    shaft_power: float | None = None
    flow: float | None = None
    density: float | None = None
    vol_flow: float | None = None
    head: float | None = None
    dp: float | None = None
    pressure_in: float | None = None
    pressure_out: float | None = None
    pipe_inlet: str = ""
    pipe_outlet: str = ""
    npsha: float | None = None
    npshr: float | None = None
    shutoff_dp: float | None = None
    shutoff_pressure: float | None = None
    suction_max_pressure: float | None = None
    vessel_pressure: float | None = None
    vessel_max_level: float | None = None
    raise_to_shutoff_dp: float | None = None
    vapour_pressure: float | None = None
    pressure_in_unit: str = ""
    vapour_pressure_unit: str = ""
    density_unit: str = ""
    contigency: float = 0.0

    @property
    def npsha_calc(self) -> float | None:
        """Computed NPSH available [m].

        Uses the same formula as pykorf.core.elements.pump.npsha_calc.
        Inputs are assumed to be in kPag (suction pressure), kPa (vapour pressure),
        and kg/m3 (density).
        """
        from pykorf.core.elements.pump import npsha_calc

        if self.pressure_in is None or self.vapour_pressure is None or self.density is None:
            return None
        try:
            return npsha_calc(
                self.pressure_in * 100, self.vapour_pressure * 100, self.density, self.contigency
            )
        except (ZeroDivisionError, ValueError):
            return None

    @property
    def hydraulic_power(self) -> float | None:
        """Computed hydraulic power [kW] = shaft_power * efficiency."""
        if self.shaft_power is None or self.efficiency is None:
            return None
        if self.efficiency <= 0:
            return None
        return self.shaft_power * self.efficiency


@dataclass
class CompressorData:
    """Result data for a single compressor from Equipment sheet."""

    name: str
    description: str = ""
    elevation: float | None = None
    efficiency: float | None = None
    shaft_power: float | None = None
    mass_flow: float | None = None
    density: float | None = None
    vol_flow: float | None = None
    head: float | None = None
    dp: float | None = None
    pressure_in: float | None = None
    pressure_out: float | None = None
    pipe_inlet: str = ""
    pipe_outlet: str = ""

    @property
    def hydraulic_power(self) -> float | None:
        """Computed hydraulic power [kW] = shaft_power * efficiency."""
        if self.shaft_power is None or self.efficiency is None:
            return None
        if self.efficiency <= 0:
            return None
        return self.shaft_power * self.efficiency


@dataclass
class ExchangerData:
    """Result data for a single heat exchanger from Equipment sheet."""

    name: str
    description: str = ""
    type: str = ""
    side: str = ""
    elevation_in: float | None = None
    duty: float | None = None
    dp: float | None = None
    pressure_in: float | None = None
    pressure_out: float | None = None
    pipe_inlet: str = ""
    pipe_outlet: str = ""


@dataclass
class MiscEquipmentData:
    """Result data for a single misc equipment from Equipment sheet."""

    name: str
    description: str = ""
    elevation_in: float | None = None
    dp: float | None = None
    pressure_in: float | None = None
    pressure_out: float | None = None
    pipe_inlet: str = ""
    pipe_outlet: str = ""


@dataclass
class ValidationEntry:
    """A single validation issue from the Title sheet."""

    message: str


@dataclass
class KorfCaseData:
    """All parsed data for a single case from KORF Excel report."""

    case: CaseInfo
    pipes: list[PipeData] = field(default_factory=list)
    feeds: list[FeedData] = field(default_factory=list)
    products: list[ProductData] = field(default_factory=list)
    orifices: list[OrificeData] = field(default_factory=list)
    valves: list[ValveData] = field(default_factory=list)
    pumps: list[PumpData] = field(default_factory=list)
    compressors: list[CompressorData] = field(default_factory=list)
    exchangers: list[ExchangerData] = field(default_factory=list)
    misc_equipment: list[MiscEquipmentData] = field(default_factory=list)
    validations: list[ValidationEntry] = field(default_factory=list)
    run_message: str = ""
