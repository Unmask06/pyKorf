"""Fluid properties container for KORF pipe elements.

This module provides a :class:`Fluid` class that encapsulates all fluid
properties (liquid and vapor) for a pipe element. It can be passed directly
to a :class:`Pipe` to update the KDF file without requiring intermediate
text file imports.

Example::

    from pykorf import Model
    from pykorf.fluid import Fluid

    model = Model("model.kdf")
    pipe = model.pipes[1]

    # Create fluid properties
    fluid = Fluid(
        temp_inlet=52.25,
        temp_outlet=52.25,
        pres_inlet=398.7,
        pres_outlet=398.7,
        liquid_density=570.24,
        liquid_viscosity=0.153,
        liquid_surface_tension=20.0,
    )

    # Apply to pipe (directly updates KDF)
    pipe.set_fluid(fluid)
    model.save()
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from pykorf.definitions import Pipe as PipeParams


@dataclass
class Fluid:
    """Container for fluid properties in a KORF pipe element.

    This class encapsulates all fluid properties including:
    - Operating conditions (temperature, pressure, liquid fraction)
    - Liquid phase properties (density, viscosity, surface tension, etc.)
    - Vapor phase properties (for two-phase flow)

    All properties support multi-case values (list of values for each case).

    **Units:** This class uses KORF's internal metric units. KORF automatically
    converts these to your preferred display units in the GUI:

    - **Temperature:** °C (KORF converts to °F if needed)
    - **Pressure:** kPag (KORF converts to barg, psig, etc.)
    - **Density:** kg/m³ (KORF converts to lb/ft³)
    - **Viscosity:** cP (centipoise - unit is the same in all systems)
    - **Surface Tension:** dyne/cm (KORF converts to N/m)

    Example - Single Case::

        fluid = Fluid(
            temp_inlet=52.25,
            temp_outlet=52.25,
            temp_average=52.25,
            pres_inlet=398.7,
            pres_outlet=398.7,
            pres_average=398.7,
            liquid_fraction=1.0,
            liquid_density=570.24,
            liquid_viscosity=0.153,
        )

    Example - Multi-Case::

        fluid = Fluid(
            temp_inlet=[52.25, 55.0, 50.0],  # NORMAL, RATED, MINIMUM
            temp_outlet=[52.25, 55.0, 50.0],
            pres_inlet=[398.7, 420.0, 380.0],
            liquid_density=[570.24, 565.0, 575.0],
        )

    Args:
        temp_inlet: Inlet temperature (°C) - scalar or list per case
        temp_outlet: Outlet temperature (°C) - scalar or list per case
        temp_average: Average temperature (°C) - scalar or list per case
        pres_inlet: Inlet pressure (kPag) - scalar or list per case
        pres_outlet: Outlet pressure (kPag) - scalar or list per case
        pres_average: Average pressure (kPag) - scalar or list per case
        liquid_fraction: Liquid fraction (0-1) - scalar or list per case
        liquid_density: Liquid density (kg/m³) - scalar or list per case
        liquid_viscosity: Liquid viscosity (cP) - scalar or list per case
        liquid_surface_tension: Liquid surface tension (dyne/cm)
        liquid_conductivity: Liquid thermal conductivity (W/m/K)
        liquid_cp: Liquid specific heat (kJ/kg/K)
        liquid_mw: Liquid molecular weight
        vapor_density: Vapor density (kg/m³)
        vapor_viscosity: Vapor viscosity (cP)
        vapor_conductivity: Vapor thermal conductivity (W/m/K)
        vapor_cp: Vapor specific heat (kJ/kg/K)
        vapor_mw: Vapor molecular weight
        vapor_z: Vapor compressibility factor
        vapor_k: Vapor K-value
        flow_direction: Flow direction (-1 = out to in, 1 = in to out)
    """

    # Operating conditions
    temp_inlet: float | list[float] = 25.0
    temp_outlet: float | list[float] = 25.0
    temp_average: float | list[float] = 25.0
    temp_unit: str = "C"

    pres_inlet: float | list[float] = 100.0
    pres_outlet: float | list[float] = 100.0
    pres_average: float | list[float] = 100.0
    pres_unit: str = "kPag"

    liquid_fraction: float | list[float] = 1.0
    flow_direction: int = -1

    # Liquid properties
    liquid_density: float | list[float] = 1000.0
    liquid_density_unit: str = "kg/m3"
    liquid_viscosity: float | list[float] = 1.0
    liquid_viscosity_unit: str = "cP"
    liquid_surface_tension: float | list[float] = 62.4
    liquid_surface_tension_unit: str = "dyne/cm"
    liquid_conductivity: float | list[float] = 0.5
    liquid_conductivity_unit: str = "W/m/K"
    liquid_cp: float | list[float] = 1.0
    liquid_cp_unit: str = "kJ/kg/K"
    liquid_mw: float | list[float] = 18.0

    # Vapor properties (for two-phase flow)
    vapor_density: float | list[float] = 0.0
    vapor_density_unit: str = "kg/m3"
    vapor_viscosity: float | list[float] = 0.0
    vapor_viscosity_unit: str = "cP"
    vapor_conductivity: float | list[float] = 0.025
    vapor_conductivity_unit: str = "W/m/K"
    vapor_cp: float | list[float] = 1.0
    vapor_cp_unit: str = "kJ/kg/K"
    vapor_mw: float | list[float] = 0.0
    vapor_z: float | list[float] = 0.0
    vapor_k: float | list[float] = 0.0

    def __post_init__(self) -> None:
        """Normalize scalar values to lists for multi-case support."""
        # Determine number of cases from array values
        num_cases = self._get_num_cases()

        # Convert scalars to lists (cast to inform mypy of the transformation)
        self.temp_inlet = cast(list[float], self._normalize_to_list(self.temp_inlet, num_cases))
        self.temp_outlet = cast(list[float], self._normalize_to_list(self.temp_outlet, num_cases))
        self.temp_average = cast(list[float], self._normalize_to_list(self.temp_average, num_cases))
        self.pres_inlet = cast(list[float], self._normalize_to_list(self.pres_inlet, num_cases))
        self.pres_outlet = cast(list[float], self._normalize_to_list(self.pres_outlet, num_cases))
        self.pres_average = cast(list[float], self._normalize_to_list(self.pres_average, num_cases))
        self.liquid_fraction = cast(list[float], self._normalize_to_list(self.liquid_fraction, num_cases))
        self.liquid_density = cast(list[float], self._normalize_to_list(self.liquid_density, num_cases))
        self.liquid_viscosity = cast(
            list[float], self._normalize_to_list(self.liquid_viscosity, num_cases)
        )
        self.liquid_surface_tension = cast(
            list[float], self._normalize_to_list(self.liquid_surface_tension, num_cases)
        )
        self.liquid_conductivity = cast(
            list[float], self._normalize_to_list(self.liquid_conductivity, num_cases)
        )
        self.liquid_cp = cast(list[float], self._normalize_to_list(self.liquid_cp, num_cases))
        self.liquid_mw = cast(list[float], self._normalize_to_list(self.liquid_mw, num_cases))
        self.vapor_density = cast(list[float], self._normalize_to_list(self.vapor_density, num_cases))
        self.vapor_viscosity = cast(list[float], self._normalize_to_list(self.vapor_viscosity, num_cases))
        self.vapor_conductivity = cast(
            list[float], self._normalize_to_list(self.vapor_conductivity, num_cases)
        )
        self.vapor_cp = cast(list[float], self._normalize_to_list(self.vapor_cp, num_cases))
        self.vapor_mw = cast(list[float], self._normalize_to_list(self.vapor_mw, num_cases))
        self.vapor_z = cast(list[float], self._normalize_to_list(self.vapor_z, num_cases))
        self.vapor_k = cast(list[float], self._normalize_to_list(self.vapor_k, num_cases))

    def _get_num_cases(self) -> int:
        """Determine number of cases from any list values."""
        list_values = [
            self.temp_inlet,
            self.temp_outlet,
            self.temp_average,
            self.pres_inlet,
            self.pres_outlet,
            self.pres_average,
            self.liquid_fraction,
            self.liquid_density,
            self.liquid_viscosity,
        ]
        for val in list_values:
            if isinstance(val, (list, tuple)):
                return len(val)
        return 1

    def _normalize_to_list(
        self, value: float | list[float], num_cases: int
    ) -> list[float]:
        """Convert scalar to list if needed."""
        if isinstance(value, (list, tuple)):
            return list(value)
        return [float(value)] * num_cases

    @property
    def num_cases(self) -> int:
        """Number of cases in this fluid specification."""
        return len(self.temp_inlet)

    # ------------------------------------------------------------------
    # KDF-compatible value arrays
    # ------------------------------------------------------------------

    @property
    def temp_array(self) -> list[float]:
        """Temperature array [inlet, outlet, average] for KDF.

        For multi-case, returns concatenated values.
        """
        if self.num_cases == 1:
            return [self.temp_inlet[0], self.temp_outlet[0], self.temp_average[0]]
        # Multi-case: interleave values
        result = []
        for i in range(self.num_cases):
            result.extend(
                [
                    self.temp_inlet[i],
                    self.temp_outlet[i],
                    self.temp_average[i],
                ]
            )
        return result

    @property
    def pres_array(self) -> list[float]:
        """Pressure array [inlet, outlet, average] for KDF."""
        if self.num_cases == 1:
            return [self.pres_inlet[0], self.pres_outlet[0], self.pres_average[0]]
        result = []
        for i in range(self.num_cases):
            result.extend(
                [
                    self.pres_inlet[i],
                    self.pres_outlet[i],
                    self.pres_average[i],
                ]
            )
        return result

    @property
    def lf_array(self) -> list[float]:
        """Liquid fraction array [inlet, outlet, average] for KDF."""
        if self.num_cases == 1:
            return [self.liquid_fraction[0]] * 3
        result = []
        for i in range(self.num_cases):
            result.extend(
                [
                    self.liquid_fraction[i],
                    self.liquid_fraction[i],
                    self.liquid_fraction[i],
                ]
            )
        return result

    # ------------------------------------------------------------------
    # Factory methods
    # ------------------------------------------------------------------

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Fluid:
        """Create Fluid from a dictionary.

        Args:
            data: Dictionary with fluid property values

        Example::

            fluid = Fluid.from_dict(
                {
                    "temp_inlet": 52.25,
                    "temp_outlet": 52.25,
                    "pres_inlet": 398.7,
                    "liquid_density": 570.24,
                    "liquid_viscosity": 0.153,
                }
            )
        """
        # Map common aliases
        aliases = {
            "temp": "temp_average",
            "temperature": "temp_average",
            "pres": "pres_average",
            "pressure": "pres_average",
            "density": "liquid_density",
            "viscosity": "liquid_viscosity",
            "liqden": "liquid_density",
            "liqvisc": "liquid_viscosity",
            "liqsur": "liquid_surface_tension",
            "vapden": "vapor_density",
            "vapvisc": "vapor_viscosity",
        }

        # Apply aliases
        normalized = {}
        for key, value in data.items():
            normalized_key = aliases.get(key.lower(), key)
            normalized[normalized_key] = value

        # Filter valid fields
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in normalized.items() if k in valid_fields}

        return cls(**filtered)

    @classmethod
    def from_excel_row(cls, row: dict[str, Any], case: int = 1) -> Fluid:
        """Create Fluid from an Excel row dictionary.

        Args:
            row: Dictionary representing an Excel row
            case: Case number (1-based) for multi-case models

        Example::

            import pandas as pd

            df = pd.read_excel("fluids.xlsx")
            for _, row in df.iterrows():
                fluid = Fluid.from_excel_row(row.to_dict())
                pipe.set_fluid(fluid)
        """
        # Map Excel column names to Fluid fields
        column_mapping = {
            # Temperature
            "Temp_In": "temp_inlet",
            "Temp_Out": "temp_outlet",
            "Temp_Avg": "temp_average",
            "Temperature": "temp_average",
            # Pressure
            "Pres_In": "pres_inlet",
            "Pres_Out": "pres_outlet",
            "Pres_Avg": "pres_average",
            "Pressure": "pres_average",
            # Liquid fraction
            "LF": "liquid_fraction",
            "Liquid_Fraction": "liquid_fraction",
            "LF_In": "liquid_fraction",
            # Liquid properties
            "LiqDen": "liquid_density",
            "LiqVisc": "liquid_viscosity",
            "LiqSur": "liquid_surface_tension",
            "LiqCon": "liquid_conductivity",
            "LiqCp": "liquid_cp",
            "LiqMW": "liquid_mw",
            # Vapor properties
            "VapDen": "vapor_density",
            "VapVisc": "vapor_viscosity",
            "VapCon": "vapor_conductivity",
            "VapCp": "vapor_cp",
            "VapMW": "vapor_mw",
            "VapZ": "vapor_z",
            "VapK": "vapor_k",
        }

        normalized = {}
        for key, value in row.items():
            if key in column_mapping:
                normalized[column_mapping[key]] = value

        return cls.from_dict(normalized)

    @classmethod
    def from_hysys_export(
        cls,
        temp: float,
        pres: float,
        liqden: float,
        liqvisc: float,
        liqsur: float = 20.0,
        vapden: float = 0.0,
        vapvisc: float = 0.0,
        lf: float = 1.0,
    ) -> Fluid:
        """Create Fluid from HYSYS/Unisim export values.

        Args:
            temp: Temperature (°C)
            pres: Pressure (barg) - will be converted to kPag
            liqden: Liquid density (kg/m³)
            liqvisc: Liquid viscosity (cP)
            liqsur: Liquid surface tension (dyne/cm)
            vapden: Vapor density (kg/m³)
            vapvisc: Vapor viscosity (cP)
            lf: Liquid fraction

        Example::

            fluid = Fluid.from_hysys_export(
                temp=52.25,
                pres=3.98,  # barg
                liqden=570.24,
                liqvisc=0.153,
            )
        """
        # Convert barg to kPag (1 barg = 100 kPag + atmospheric offset)
        # KORF uses kPag, so 3.98 barg ≈ 398.7 kPag (plus ~100 kPa atm)
        pres_kpag = pres * 100  # Simplified conversion

        return cls(
            temp_inlet=temp,
            temp_outlet=temp,
            temp_average=temp,
            pres_inlet=pres_kpag,
            pres_outlet=pres_kpag,
            pres_average=pres_kpag,
            liquid_fraction=lf,
            liquid_density=liqden,
            liquid_viscosity=liqvisc,
            liquid_surface_tension=liqsur,
            vapor_density=vapden,
            vapor_viscosity=vapvisc,
        )

    @classmethod
    def single_phase_liquid(
        cls,
        temp: float,
        pres: float,
        density: float,
        viscosity: float,
        surface_tension: float = 62.4,
    ) -> Fluid:
        """Create a single-phase liquid Fluid.

        Args:
            temp: Temperature (°C)
            pres: Pressure (kPag)
            density: Liquid density (kg/m³)
            viscosity: Liquid viscosity (cP)
            surface_tension: Surface tension (dyne/cm)

        Example::

            water = Fluid.single_phase_liquid(
                temp=25.0,
                pres=100.0,
                density=1000.0,
                viscosity=1.0,
                surface_tension=62.4,
            )
        """
        return cls(
            temp_inlet=temp,
            temp_outlet=temp,
            temp_average=temp,
            pres_inlet=pres,
            pres_outlet=pres,
            pres_average=pres,
            liquid_fraction=1.0,
            liquid_density=density,
            liquid_viscosity=viscosity,
            liquid_surface_tension=surface_tension,
            vapor_density=0.0,
            vapor_viscosity=0.0,
        )

    @classmethod
    def water_at_temp(cls, temp: float = 25.0, pres: float = 100.0) -> Fluid:
        """Create Fluid for water at given temperature.

        Uses standard water properties with temperature-dependent
        density and viscosity approximation.

        Args:
            temp: Temperature (°C)
            pres: Pressure (kPag)

        Example::

            water_50c = Fluid.water_at_temp(temp=50.0)
        """
        # Approximate temperature corrections
        # Density decreases slightly with temperature
        density = 1000.0 - 0.5 * (temp - 25.0)  # kg/m³
        # Viscosity decreases significantly with temperature
        viscosity = 1.0 * (0.9 ** ((temp - 25.0) / 10))  # cP

        return cls.single_phase_liquid(
            temp=temp,
            pres=pres,
            density=density,
            viscosity=viscosity,
            surface_tension=62.4,
        )

    # ------------------------------------------------------------------
    # Utility methods
    # ------------------------------------------------------------------

    def to_kdf_records(self) -> dict[str, list]:
        """Convert to KDF record format.

        Returns:
            Dictionary mapping parameter names to value lists
        """
        return {
            PipeParams.TEMP: self.temp_array + [self.temp_unit],
            PipeParams.PRES: self.pres_array + [self.pres_unit],
            PipeParams.LF: self.lf_array,
            PipeParams.OUTIN: [self.flow_direction],
            PipeParams.LIQDEN: list(self.liquid_density) + [self.liquid_density_unit],
            PipeParams.LIQVISC: list(self.liquid_viscosity) + [self.liquid_viscosity_unit],
            PipeParams.LIQSUR: list(self.liquid_surface_tension)
            + [self.liquid_surface_tension_unit],
            PipeParams.LIQCON: list(self.liquid_conductivity) + [self.liquid_conductivity_unit],
            PipeParams.LIQCP: list(self.liquid_cp) + [self.liquid_cp_unit],
            PipeParams.LIQMW: list(self.liquid_mw),
            PipeParams.VAPDEN: list(self.vapor_density) + [self.vapor_density_unit],
            PipeParams.VAPVISC: list(self.vapor_viscosity) + [self.vapor_viscosity_unit],
            PipeParams.VAPCON: list(self.vapor_conductivity) + [self.vapor_conductivity_unit],
            PipeParams.VAPCP: list(self.vapor_cp) + [self.vapor_cp_unit],
            PipeParams.VAPMW: list(self.vapor_mw),
            PipeParams.VAPZ: list(self.vapor_z),
            PipeParams.VAPK: list(self.vapor_k),
        }

    def summary(self) -> dict[str, Any]:
        """Return a summary dictionary of key properties."""
        return {
            "num_cases": self.num_cases,
            "temp_range": (min(self.temp_inlet), max(self.temp_inlet)),
            "pres_range": (min(self.pres_inlet), max(self.pres_inlet)),
            "liquid_density_avg": sum(self.liquid_density) / len(self.liquid_density),
            "liquid_viscosity_avg": sum(self.liquid_viscosity)
            / len(self.liquid_viscosity),
            "liquid_fraction_avg": sum(self.liquid_fraction)
            / len(self.liquid_fraction),
            "is_two_phase": any(lf < 1.0 for lf in self.liquid_fraction),
        }

    def __repr__(self) -> str:
        return (
            f"Fluid(cases={self.num_cases}, "
            f"T={self.temp_inlet[0]:.1f}C, "
            f"P={self.pres_inlet[0]:.1f}kPag, "
            f"rho={self.liquid_density[0]:.1f}kg/m3, "
            f"mu={self.liquid_viscosity[0]:.4f}cP)"
        )
