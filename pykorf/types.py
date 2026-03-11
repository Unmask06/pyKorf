"""Type definitions and Pydantic models for pyKorf.

This module provides strongly-typed data models for all KDF elements,
ensuring data integrity and enabling IDE autocomplete support.

Example:
    >>> from pykorf.types import PipeData, FlowParameters
    >>> pipe = PipeData(
    ...     name="L1",
    ...     diameter_inch=6,
    ...     schedule="40",
    ...     length_m=100.0,
    ...     flow=FlowParameters(mass_flow_t_h=[50, 55, 20]),
    ... )
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Literal

# Import constants from elements
from pykorf.elements import (
    Element,
    Pipe,
)

# Try to import pydantic, fall back to dataclasses
try:
    from pydantic import BaseModel, ConfigDict, Field, field_validator

    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False

    # Create stub classes for when pydantic is not available
    class BaseModel:  # type: ignore[no-redef]
        def __init__(self, **kwargs: Any) -> None:
            for k, v in kwargs.items():
                setattr(self, k, v)

    class ConfigDict:  # type: ignore[no-redef]
        def __init__(self, **kwargs: Any) -> None:
            pass

    def Field(*args, **kwargs):  # type: ignore[no-redef]
        return None

    def field_validator(*args, **kwargs):  # type: ignore[no-redef]
        return lambda f: f


if TYPE_CHECKING:
    from pydantic import BaseModel, ConfigDict, Field, field_validator

# ============================================================================
# Enums
# ============================================================================


class KdfVersion(str, Enum):
    """Supported KDF file versions."""

    V2_0 = "KORF_2.0"
    V3_0 = "KORF_3.0"
    V3_6 = "KORF_3.6"


class UnitSystem(str, Enum):
    """Unit system options."""

    METRIC = "Metric"
    IMPERIAL = "Imperial"
    CUSTOM = "Custom"


class ElementType(str, Enum):
    """KDF element types."""

    GEN = "GEN"
    PIPE = "PIPE"
    FEED = "FEED"
    PROD = "PROD"
    VALVE = "VALVE"
    CHECK = "CHECK"
    ORIFICE = "FO"
    HX = "HX"
    PUMP = "PUMP"
    COMP = "COMP"
    MISC = "MISC"
    EXPAND = "EXPAND"
    JUNC = "JUNC"
    TEE = "TEE"
    VESSEL = "VESSEL"
    SYMBOL = "SYMBOL"
    TOOLS = "TOOLS"
    PSEUDO = "PSEUDO"
    PIPEDATA = "PIPEDATA"


class PumpType(str, Enum):
    """Pump types."""

    CENTRIFUGAL = "Centrifugal"
    RECIPROCATING = "Reciprocating"


class ValveType(str, Enum):
    """Valve characteristic types."""

    LINEAR = "Linear"
    EQUAL_PERCENT = "Equal%"
    QUICK = "Quick"


class ValveSubType(str, Enum):
    """Valve subtypes."""

    CONTROL = "Control"
    SAFETY = "Safety"


class PipeMaterial(str, Enum):
    """Pipe materials."""

    STEEL = "Steel"
    DUCTILE_IRON = "Ductile Iron"
    PVC = "PVC"
    COPPER = "Copper"
    STAINLESS_STEEL = "Stainless Steel"


class VesselOrientation(str, Enum):
    """Vessel orientations."""

    VERTICAL = "Vertical"
    HORIZONTAL = "Horizontal"


class FlashModel(str, Enum):
    """Flash calculation models."""

    KORF = "Korf"
    HYSYS = "Hysys"


class CompressibilityModel(str, Enum):
    """Compressibility models."""

    INCOMPRESSIBLE = "Incompressible"
    IDEAL = "Ideal"
    SRK = "SRK"
    PR = "PR"


class TwoPhaseModel(str, Enum):
    """Two-phase flow models."""

    HOMOGENEOUS = "Homogeneous"
    LOCKHART_MARTINELLI = "Lockhart-Martinelli"
    BEGGS_BRILL = "Beggs-Brill"


# ============================================================================
# Base Models
# ============================================================================


if HAS_PYDANTIC:

    class KdfBaseModel(BaseModel):  # type: ignore[no-redef]
        """Base model for all KDF data models."""

        model_config = ConfigDict(
            populate_by_name=True,
            str_strip_whitespace=True,
            validate_assignment=True,
            extra="forbid",
        )
else:

    @dataclass
    class KdfBaseModel:
        """Base model for all KDF data models (dataclass fallback)."""

        def __post_init__(self) -> None:
            pass

        def model_dump(self) -> dict[str, Any]:
            """Convert to dictionary."""
            result: dict[str, Any] = {}
            for key in self.__dataclass_fields__:
                value = getattr(self, key)
                if isinstance(value, KdfBaseModel):
                    result[key] = value.model_dump()
                elif isinstance(value, list):
                    result[key] = [
                        item.model_dump() if isinstance(item, KdfBaseModel) else item
                        for item in value
                    ]
                elif isinstance(value, Enum):
                    result[key] = value.value
                else:
                    result[key] = value
            return result


if HAS_PYDANTIC:

    class Position(KdfBaseModel):  # type: ignore[no-redef]
        """2D position coordinates."""

        x: float = Field(..., description="X coordinate")
        y: float = Field(..., description="Y coordinate")
else:

    @dataclass
    class Position(KdfBaseModel):  # type: ignore[no-redef]
        """2D position coordinates."""

        x: float
        y: float


if HAS_PYDANTIC:

    class Range3Case(KdfBaseModel):
        """Value range for 3 simulation cases."""

        case1: float = Field(..., alias="case_1", description="Value for case 1")
        case2: float = Field(..., alias="case_2", description="Value for case 2")
        case3: float = Field(..., alias="case_3", description="Value for case 3")

        model_config = ConfigDict(populate_by_name=True)
else:

    @dataclass
    class Range3Case(KdfBaseModel):  # type: ignore[no-redef]
        """Value range for 3 simulation cases."""

        case1: float
        case2: float
        case3: float


if HAS_PYDANTIC:

    class FlowParameters(KdfBaseModel):  # type: ignore[no-redef]
        """Flow-related parameters."""

        mass_flow_t_h: list[float] | None = Field(
            None, description="Mass flow rate in t/h for each case"
        )
        liquid_fraction: list[float] | None = Field(
            None, description="Liquid fraction (0-1) for each case"
        )
        temperature_c: list[float] | None = Field(
            None, description="Temperature in Celsius for each case"
        )
        pressure_kpag: list[float] | None = Field(
            None, description="Pressure in kPag for each case"
        )

        @field_validator("liquid_fraction")
        @classmethod
        def validate_fraction(cls, v: list[float] | None) -> list[float] | None:
            if v is not None:
                for val in v:
                    if not 0 <= val <= 1:
                        raise ValueError(f"Liquid fraction must be between 0 and 1, got {val}")
            return v
else:

    @dataclass
    class FlowParameters(KdfBaseModel):  # type: ignore[no-redef]
        """Flow-related parameters."""

        mass_flow_t_h: list[float] | None = None
        liquid_fraction: list[float] | None = None
        temperature_c: list[float] | None = None
        pressure_kpag: list[float] | None = None


if HAS_PYDANTIC:

    class FluidProperties(KdfBaseModel):  # type: ignore[no-redef]
        """Fluid properties per phase."""

        liquid_density_kg_m3: list[float] | None = Field(
            None, description="Liquid density in kg/m³"
        )
        liquid_viscosity_cp: list[float] | None = Field(None, description="Liquid viscosity in cP")
        liquid_surface_tension: list[float] | None = Field(
            None, description="Liquid surface tension in dyne/cm"
        )
        vapor_density_kg_m3: list[float] | None = Field(None, description="Vapor density in kg/m³")
        vapor_viscosity_cp: list[float] | None = Field(None, description="Vapor viscosity in cP")
        vapor_molecular_weight: list[float] | None = None
else:

    @dataclass
    class FluidProperties(KdfBaseModel):  # type: ignore[no-redef]
        """Fluid properties per phase."""

        liquid_density_kg_m3: list[float] | None = None
        liquid_viscosity_cp: list[float] | None = None
        liquid_surface_tension: list[float] | None = None
        vapor_density_kg_m3: list[float] | None = None
        vapor_viscosity_cp: list[float] | None = None
        vapor_molecular_weight: list[float] | None = None


# ============================================================================
# Element Data Models
# ============================================================================


if HAS_PYDANTIC:

    class ElementBase(KdfBaseModel):  # type: ignore[no-redef]
        """Base class for all element data models."""

        name: str = Field(..., min_length=1, max_length=9, description="Element name/tag")
        description: str | None = Field(None, max_length=50, description="Element description")
        index: int = Field(..., ge=0, description="Element index (0 = template)")
        position: Position | None = None
        color: int | None = Field(None, description="Display color as RGB integer")
        notes: str | None = None
else:

    @dataclass
    class ElementBase(KdfBaseModel):  # type: ignore[no-redef]
        """Base class for all element data models."""

        name: str
        description: str | None = None
        index: int = 0
        position: Position | None = None
        color: int | None = None
        notes: str | None = None


if HAS_PYDANTIC:

    class FittingData(KdfBaseModel):  # type: ignore[no-redef]
        """Pipe fitting data."""

        name: str
        count: int = Field(ge=0)
        k_factor: float
        ld_ratio: float
else:

    @dataclass
    class FittingData(KdfBaseModel):  # type: ignore[no-redef]
        """Pipe fitting data."""

        name: str
        count: int = 0
        k_factor: float = 0.0
        ld_ratio: float = 0.0


if HAS_PYDANTIC:

    class PipeData(ElementBase):
        """Pipe element data."""

        element_type: Literal["PIPE"] = Element.PIPE

        # Geometry
        diameter_inch: str = Field(default="4", description="Nominal diameter in inches")
        schedule: str = Field(default="40", description="Pipe schedule")
        length_m: float = Field(default=100.0, gt=0, description="Length in meters")
        roughness_m: float = Field(default=4.57e-5, ge=0, description="Wall roughness in meters")
        material: str = Field(default="Steel", description="Pipe material")

        # Flow
        flow: FlowParameters | None = None

        # Fluid properties
        fluid: FluidProperties | None = None

        # Heat transfer
        heat_transfer_coeff: float | None = Field(
            None, alias=Pipe.UI, description="Overall heat transfer coefficient"
        )
        ambient_temp_c: float | None = Field(
            None, alias=Pipe.TAMB, description="Ambient temperature in Celsius"
        )

        # Fittings
        fittings: list[FittingData] | None = None

        # Calculated results
        velocity_m_s: list[float] | None = None
        reynolds_number: float | None = None
        pressure_drop_kpa_100m: float | None = None
else:

    @dataclass
    class PipeData(ElementBase):  # type: ignore
        """Pipe element data."""

        element_type: str = Element.PIPE
        diameter_inch: str = "4"
        schedule: str = "40"
        length_m: float = 100.0
        roughness_m: float = 4.57e-5
        material: str = "Steel"
        flow: FlowParameters | None = None
        fluid: FluidProperties | None = None
        heat_transfer_coeff: float | None = None
        ambient_temp_c: float | None = None
        fittings: list[FittingData] | None = None
        velocity_m_s: list[float] | None = None
        reynolds_number: float | None = None
        pressure_drop_kpa_100m: float | None = None


if HAS_PYDANTIC:

    class PumpData(ElementBase):
        """Pump element data."""

        element_type: Literal["PUMP"] = Element.PUMP

        pump_type: PumpType = Field(default=PumpType.CENTRIFUGAL)
        efficiency: float | None = Field(None, ge=0, le=1, description="Pump efficiency (0-1)")
        system_efficiency: float | None = Field(None, ge=0, le=1)
        differential_pressure_kpag: float | None = None

        # Curve data
        curve_flow_points: list[float] | None = None
        curve_head_points: list[float] | None = None
        curve_efficiency_points: list[float] | None = None

        # Calculated results
        head_m: float | None = None
        power_kw: float | None = None
        flow_m3h: float | None = None
        npsh_required_m: float | None = None
else:

    @dataclass
    class PumpData(ElementBase):  # type: ignore
        """Pump element data."""

        element_type: str = Element.PUMP
        pump_type: PumpType = PumpType.CENTRIFUGAL
        efficiency: float | None = None
        system_efficiency: float | None = None
        differential_pressure_kpag: float | None = None
        curve_flow_points: list[float] | None = None
        curve_head_points: list[float] | None = None
        curve_efficiency_points: list[float] | None = None
        head_m: float | None = None
        power_kw: float | None = None
        flow_m3h: float | None = None
        npsh_required_m: float | None = None


if HAS_PYDANTIC:

    class ValveData(ElementBase):
        """Valve element data."""

        element_type: Literal["VALVE"] = Element.VALVE

        valve_type: ValveType = Field(default=ValveType.LINEAR)
        valve_subtype: ValveSubType = Field(default=ValveSubType.CONTROL)
        cv: float | None = Field(None, gt=0, description="Valve flow coefficient")
        percent_open: float = Field(default=100.0, ge=0, le=100)
        pressure_drop_kpag: float | None = None
        xt: float = Field(default=0.72, description="Pressure recovery factor")
        fl: float = Field(default=0.9, description="Liquid pressure recovery factor")
else:

    @dataclass
    class ValveData(ElementBase):  # type: ignore
        """Valve element data."""

        element_type: str = Element.VALVE
        valve_type: ValveType = ValveType.LINEAR
        valve_subtype: ValveSubType = ValveSubType.CONTROL
        cv: float | None = None
        percent_open: float = 100.0
        pressure_drop_kpag: float | None = None
        xt: float = 0.72
        fl: float = 0.9


if HAS_PYDANTIC:

    class FeedData(ElementBase):
        """Feed (source) boundary condition data."""

        element_type: Literal["FEED"] = Element.FEED

        feed_type: Literal["Pipe", "Vessel"] = "Pipe"
        pressure_kpag: list[float] | float | None = None
        elevation_m: float = 0.0
        level_m: float | None = None
else:

    @dataclass
    class FeedData(ElementBase):  # type: ignore
        """Feed (source) boundary condition data."""

        element_type: str = Element.FEED
        feed_type: str = "Pipe"
        pressure_kpag: list[float] | float | None = None
        elevation_m: float = 0.0
        level_m: float | None = None


if HAS_PYDANTIC:

    class ProductData(ElementBase):
        """Product (sink) boundary condition data."""

        element_type: Literal["PROD"] = Element.PROD

        product_type: Literal["Pipe", "Vessel"] = "Pipe"
        pressure_kpag: list[float] | float | None = None
        elevation_m: float = 0.0
else:

    @dataclass
    class ProductData(ElementBase):  # type: ignore
        """Product (sink) boundary condition data."""

        element_type: str = Element.PROD
        product_type: str = "Pipe"
        pressure_kpag: list[float] | float | None = None
        elevation_m: float = 0.0


if HAS_PYDANTIC:

    class CompressorData(ElementBase):
        """Compressor element data."""

        element_type: Literal["COMP"] = Element.COMP

        compressor_type: Literal["Centrifugal", "Reciprocating"] = "Centrifugal"
        efficiency: float | None = Field(None, ge=0, le=1)
        pressure_ratio: float | None = None
        power_kw: float | None = None
else:

    @dataclass
    class CompressorData(ElementBase):  # type: ignore
        """Compressor element data."""

        element_type: str = Element.COMP
        compressor_type: str = "Centrifugal"
        efficiency: float | None = None
        pressure_ratio: float | None = None
        power_kw: float | None = None


if HAS_PYDANTIC:

    class HeatExchangerData(ElementBase):
        """Heat exchanger element data."""

        element_type: Literal["HX"] = Element.HX

        hx_type: str = Field(default="S-T", description="HX type (S-T, Plate, etc.)")
        side: Literal["Tube", "Shell"] = "Tube"
        pressure_drop_kpag: float | None = None
        duty_kj_h: float | None = None
else:

    @dataclass
    class HeatExchangerData(ElementBase):  # type: ignore
        """Heat exchanger element data."""

        element_type: str = Element.HX
        hx_type: str = "S-T"
        side: str = "Tube"
        pressure_drop_kpag: float | None = None
        duty_kj_h: float | None = None


if HAS_PYDANTIC:

    class VesselData(ElementBase):
        """Vessel element data."""

        element_type: Literal["VESSEL"] = Element.VESSEL

        orientation: VesselOrientation = VesselOrientation.VERTICAL
        pressure_kpag: list[float] | float | None = None
        diameter_m: float | None = None
        height_m: float | None = None
else:

    @dataclass
    class VesselData(ElementBase):  # type: ignore
        """Vessel element data."""

        element_type: str = Element.VESSEL
        orientation: VesselOrientation = VesselOrientation.VERTICAL
        pressure_kpag: list[float] | float | None = None
        diameter_m: float | None = None
        height_m: float | None = None


# ============================================================================
# Model Metadata
# ============================================================================


if HAS_PYDANTIC:

    class ModelMetadata(KdfBaseModel):  # type: ignore[no-redef]
        """Metadata for a KDF model."""

        version: KdfVersion
        company: str | None = None
        location: str | None = None
        client: str | None = None
        project: str | None = None
        project_number: str | None = None
        engineer: str | None = None
        date: str | None = None
        revision: str | None = None
else:

    @dataclass
    class ModelMetadata(KdfBaseModel):  # type: ignore[no-redef]
        """Metadata for a KDF model."""

        version: KdfVersion = KdfVersion.V3_6
        company: str | None = None
        location: str | None = None
        client: str | None = None
        project: str | None = None
        project_number: str | None = None
        engineer: str | None = None
        date: str | None = None
        revision: str | None = None


if HAS_PYDANTIC:

    class CaseInfo(KdfBaseModel):  # type: ignore[no-redef]
        """Information about a simulation case."""

        number: int
        name: str
        description: str | None = None
        active: bool = True
        include_in_report: bool = True
else:

    @dataclass
    class CaseInfo(KdfBaseModel):  # type: ignore[no-redef]
        """Information about a simulation case."""

        number: int = 1
        name: str = ""
        description: str | None = None
        active: bool = True
        include_in_report: bool = True


if HAS_PYDANTIC:

    class UnitConfiguration(KdfBaseModel):  # type: ignore[no-redef]
        """Unit system configuration."""

        system: UnitSystem = UnitSystem.METRIC
        length: str = "m"
        mass_flow: str = "t/h"
        liq_vol_flow: str = "m3/h"
        gas_vol_flow: str = "m3/h"
        molar_flow: str = "kmol/h"
        density: str = "kg/m3"
        temperature: str = "C"
        pressure: str = "kPag"
        head: str = "m"
        dp_per_100: str = "kPa/100m"
        velocity: str = "m/s"
        power: str = "kW"
        enthalpy: str = "kJ/kg"
        heat_capacity: str = "kJ/kg/K"
        heat_flow: str = "kJ/h"
else:

    @dataclass
    class UnitConfiguration(KdfBaseModel):  # type: ignore[no-redef]
        """Unit system configuration."""

        system: UnitSystem = UnitSystem.METRIC
        length: str = "m"
        mass_flow: str = "t/h"
        liq_vol_flow: str = "m3/h"
        gas_vol_flow: str = "m3/h"
        molar_flow: str = "kmol/h"
        density: str = "kg/m3"
        temperature: str = "C"
        pressure: str = "kPag"
        head: str = "m"
        dp_per_100: str = "kPa/100m"
        velocity: str = "m/s"
        power: str = "kW"
        enthalpy: str = "kJ/kg"
        heat_capacity: str = "kJ/kg/K"
        heat_flow: str = "kJ/h"


# ============================================================================
# Export/Import Models
# ============================================================================


if HAS_PYDANTIC:

    class ExportOptions(KdfBaseModel):  # type: ignore[no-redef]
        """Options for exporting model data."""

        include_results: bool = True
        include_geometry: bool = True
        include_connectivity: bool = True
        indent: int | None = 2
        encoding: str = "utf-8"
else:

    @dataclass
    class ExportOptions(KdfBaseModel):  # type: ignore[no-redef]
        """Options for exporting model data."""

        include_results: bool = True
        include_geometry: bool = True
        include_connectivity: bool = True
        indent: int | None = 2
        encoding: str = "utf-8"


if HAS_PYDANTIC:

    class ValidationIssue(KdfBaseModel):  # type: ignore[no-redef]
        """A single validation issue."""

        severity: Literal["error", "warning", "info"] = "error"
        code: str
        message: str
        element_type: str | None = None
        element_name: str | None = None
        parameter: str | None = None
else:

    @dataclass
    class ValidationIssue(KdfBaseModel):  # type: ignore[no-redef]
        """A single validation issue."""

        severity: str = "error"
        code: str = ""
        message: str = ""
        element_type: str | None = None
        element_name: str | None = None
        parameter: str | None = None


__all__ = [
    # Metadata
    "CaseInfo",
    # Enums
    "CompressibilityModel",
    # Element data
    "CompressorData",
    "ElementBase",
    "ElementType",
    # Export
    "ExportOptions",
    "FeedData",
    "FittingData",
    "FlashModel",
    # Base models
    "FlowParameters",
    "FluidProperties",
    "HeatExchangerData",
    "KdfBaseModel",
    "KdfVersion",
    "ModelMetadata",
    "PipeData",
    "PipeMaterial",
    "Position",
    "ProductData",
    "PumpData",
    "PumpType",
    "Range3Case",
    "TwoPhaseModel",
    "UnitConfiguration",
    "UnitSystem",
    "ValidationIssue",
    "ValveData",
    "ValveSubType",
    "ValveType",
    "VesselData",
    "VesselOrientation",
]
