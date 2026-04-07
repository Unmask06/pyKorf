"""Fluid properties container for KORF pipe elements.

This module provides a :class:`Fluid` class that encapsulates all fluid
properties (liquid and vapor) for a pipe element. It can be passed directly
to a :class:`Pipe` to update the KDF file without requiring intermediate
text file imports.

Example::

    from pykorf import Model
    from pykorf.core.fluid import Fluid

    model = Model("model.kdf")
    pipe = model.pipes[1]

    # Create fluid properties - simple interface
    fluid = Fluid(
        temp=52.25,  # Average temperature
        pres=398.7,  # Average pressure
        liqden=570.24,
        liqvisc=0.153,
    )

    # Apply to pipe (directly updates KDF)
    pipe.set_fluid(fluid)
    model.save()

    # Partial update - only change LVFLOW
    partial = Fluid(lvflow=13470)
    pipe.set_fluid(partial)  # Only LVFLOW is modified
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pykorf.core.elements import Pipe


@dataclass
class Fluid:
    """Container for fluid properties in a KORF pipe element.

    This class provides a simple interface for fluid properties.
    All properties are optional - only set properties will be written to KDF.
    Unset properties (None) are left unchanged when applied to a pipe.

    **Units:** This class uses KORF's internal metric units. KORF automatically
    converts these to your preferred display units in the GUI:

    - **Temperature:** °C
    - **Pressure:** kPag
    - **Density:** kg/m³
    - **Viscosity:** cP
    - **Surface Tension:** dyne/cm

    Example - Full Update::

        fluid = Fluid(
            temp=52.25,
            pres=398.7,
            liqden=570.24,
            liqvisc=0.153,
        )

    Example - Partial Update (only LVFLOW)::

        fluid = Fluid(lvflow=13470)  # Only updates LVFLOW

    Example - Multi-Case::

        fluid = Fluid(
            temp=[52.25, 55.0, 50.0],  # INLET, OUTLET, AVERAGE
            pres=[398.7, 420.0, 380.0],
            liqden=[570.24, 565.0, 575.0],
        )
    """

    # Operating conditions
    temp: float | list[float] | None = None
    """Temperature (°C) - scalar or list [inlet, outlet, average]"""

    pres: float | list[float] | None = None
    """Pressure (kPag) - scalar or list [inlet, outlet, average]"""

    # Liquid properties
    liqden: float | list[float] | None = None
    """Liquid density (kg/m³) - scalar or list [inlet, outlet, average]"""

    liqvisc: float | list[float] | None = None
    """Liquid viscosity (cP) - scalar or list [inlet, outlet, average]"""

    liqsur: float | list[float] | None = None
    """Liquid surface tension (dyne/cm) - scalar or list [inlet, outlet, average]"""

    liqcon: float | list[float] | None = None
    """Liquid thermal conductivity (W/m/K) - scalar or list [inlet, outlet, average]"""

    liqcp: float | list[float] | None = None
    """Liquid specific heat (kJ/kg/K) - scalar or list [inlet, outlet, average]"""

    liqmw: float | list[float] | None = None
    """Liquid molecular weight - scalar or list [inlet, outlet, average]"""

    # Vapor properties (for two-phase flow)
    vapden: float | list[float] | None = None
    """Vapor density (kg/m³) - scalar or list [inlet, outlet, average]"""

    vapvisc: float | list[float] | None = None
    """Vapor viscosity (cP) - scalar or list [inlet, outlet, average]"""

    vapcon: float | list[float] | None = None
    """Vapor thermal conductivity (W/m/K) - scalar or list [inlet, outlet, average]"""

    vapcp: float | list[float] | None = None
    """Vapor specific heat (kJ/kg/K) - scalar or list [inlet, outlet, average]"""

    vapmw: float | list[float] | None = None
    """Vapor molecular weight - scalar or list [inlet, outlet, average]"""

    vapz: float | list[float] | None = None
    """Vapor compressibility factor - scalar or list [inlet, outlet, average]"""

    vapk: float | list[float] | None = None
    """Vapor K-value - scalar or list [inlet, outlet, average]"""

    lf: float | list[float] | None = None
    """Liquid fraction (0-1) - scalar or list [inlet, outlet, average]"""

    # Units (fixed, not editable)
    temp_unit: str = field(default="C", repr=False)
    pres_unit: str = field(default="kPag", repr=False)
    liqden_unit: str = field(default="kg/m3", repr=False)
    liqvisc_unit: str = field(default="cP", repr=False)
    liqsur_unit: str = field(default="dyne/cm", repr=False)
    liqcon_unit: str = field(default="W/m/K", repr=False)
    liqcp_unit: str = field(default="kJ/kg/K", repr=False)
    vapden_unit: str = field(default="kg/m3", repr=False)
    vapvisc_unit: str = field(default="cP", repr=False)
    vapcon_unit: str = field(default="W/m/K", repr=False)
    vapcp_unit: str = field(default="kJ/kg/K", repr=False)

    def __post_init__(self) -> None:
        """Normalize scalar values to lists for multi-case support.

        Only non-None values are normalized. None values remain None
        and will not be written to KDF.
        """
        num_cases = 3  # INLET, OUTLET, AVERAGE

        # Only normalize values that are explicitly set (not None)
        if self.temp is not None:
            self.temp = self._normalize_to_list(self.temp, num_cases)
        if self.pres is not None:
            self.pres = self._normalize_to_list(self.pres, num_cases)
        if self.liqden is not None:
            self.liqden = self._normalize_to_list(self.liqden, num_cases)
        if self.liqvisc is not None:
            self.liqvisc = self._normalize_to_list(self.liqvisc, num_cases)
        if self.liqsur is not None:
            self.liqsur = self._normalize_to_list(self.liqsur, num_cases)
        if self.liqcon is not None:
            self.liqcon = self._normalize_to_list(self.liqcon, num_cases)
        if self.liqcp is not None:
            self.liqcp = self._normalize_to_list(self.liqcp, num_cases)
        if self.liqmw is not None:
            self.liqmw = self._normalize_to_list(self.liqmw, num_cases)
        if self.vapden is not None:
            self.vapden = self._normalize_to_list(self.vapden, num_cases)
        if self.vapvisc is not None:
            self.vapvisc = self._normalize_to_list(self.vapvisc, num_cases)
        if self.vapcon is not None:
            self.vapcon = self._normalize_to_list(self.vapcon, num_cases)
        if self.vapcp is not None:
            self.vapcp = self._normalize_to_list(self.vapcp, num_cases)
        if self.vapmw is not None:
            self.vapmw = self._normalize_to_list(self.vapmw, num_cases)
        if self.vapz is not None:
            self.vapz = self._normalize_to_list(self.vapz, num_cases)
        if self.vapk is not None:
            self.vapk = self._normalize_to_list(self.vapk, num_cases)
        if self.lf is not None:
            self.lf = self._normalize_to_list(self.lf, num_cases)

    def _normalize_to_list(self, value: float | list[float], num_cases: int) -> list[float]:
        """Convert scalar to list of *num_cases* floats.

        - Scalar ``float``/``int`` -> replicated to ``[value] * num_cases``
        - List of correct length   -> returned as-is (converted to float)
        - List of wrong length     -> raises ``ValueError``
        """
        if isinstance(value, (list, tuple)):
            return [float(v) for v in value]
        return [float(value)] * num_cases

    def apply_to_pipes(self, model: Any, pipe_names: list[str]) -> None:
        """Apply this fluid to multiple pipes.

        Args:
            model: A Model instance containing the pipes
            pipe_names: List of pipe names to apply the fluid to

        Example::

            from pykorf import Model
            from pykorf.core.fluid import Fluid

            model = Model("model.kdf")
            fluid = Fluid.water_at_temp(temp=50.0)

            # Apply to multiple pipes
            fluid.apply_to_pipes(model, ["L1", "L2", "L3"])
            model.save()

        Raises:
            ElementNotFound: If a pipe name doesn't exist in the model
        """
        for name in pipe_names:
            pipe = model[name]
            pipe.set_fluid(self)

    def to_kdf_records(self) -> dict[str, list]:
        r"""Convert to KDF record format.

        Only non-None properties are included in the output.
        Each included property becomes ``[inlet, outlet, average, "unit"]``
        (3 float values + optional unit string), matching the KDF record
        layout for ``\PIPE,index,PARAM,...``.

        Returns:
            Dictionary mapping parameter names to value lists.
            Only includes parameters that were explicitly set.
        """

        def _normalize_to_3(val: float | list[float] | None) -> list[float]:
            """Ensure value is a list of exactly 3 floats."""
            if val is None:
                return [0.0, 0.0, 0.0]
            if isinstance(val, (int, float)):
                v = float(val)
                return [v, v, v]
            # It's a list
            vals = list(val)
            if len(vals) == 0:
                return [0.0, 0.0, 0.0]
            if len(vals) == 1:
                return [vals[0], vals[0], vals[0]]
            if len(vals) == 2:
                return [vals[0], vals[1], (vals[0] + vals[1]) / 2]
            if len(vals) >= 3:
                return [float(v) for v in vals[:3]]
            return [0.0, 0.0, 0.0]

        records: dict[str, list] = {}

        if self.temp is not None:
            records[Pipe.TEMP] = [*_normalize_to_3(self.temp), self.temp_unit]
        if self.pres is not None:
            records[Pipe.PRES] = [*_normalize_to_3(self.pres), self.pres_unit]
        if self.lf is not None:
            records[Pipe.LF] = _normalize_to_3(self.lf)
        if self.liqden is not None:
            records[Pipe.LIQDEN] = [*_normalize_to_3(self.liqden), self.liqden_unit]
        if self.liqvisc is not None:
            records[Pipe.LIQVISC] = [*_normalize_to_3(self.liqvisc), self.liqvisc_unit]
        if self.liqsur is not None:
            records[Pipe.LIQSUR] = [*_normalize_to_3(self.liqsur), self.liqsur_unit]
        if self.liqcon is not None:
            records[Pipe.LIQCON] = [*_normalize_to_3(self.liqcon), self.liqcon_unit]
        if self.liqcp is not None:
            records[Pipe.LIQCP] = [*_normalize_to_3(self.liqcp), self.liqcp_unit]
        if self.liqmw is not None:
            records[Pipe.LIQMW] = _normalize_to_3(self.liqmw)
        if self.vapden is not None:
            records[Pipe.VAPDEN] = [*_normalize_to_3(self.vapden), self.vapden_unit]
        if self.vapvisc is not None:
            records[Pipe.VAPVISC] = [*_normalize_to_3(self.vapvisc), self.vapvisc_unit]
        if self.vapcon is not None:
            records[Pipe.VAPCON] = [*_normalize_to_3(self.vapcon), self.vapcon_unit]
        if self.vapcp is not None:
            records[Pipe.VAPCP] = [*_normalize_to_3(self.vapcp), self.vapcp_unit]
        if self.vapmw is not None:
            records[Pipe.VAPMW] = _normalize_to_3(self.vapmw)
        if self.vapz is not None:
            records[Pipe.VAPZ] = _normalize_to_3(self.vapz)
        if self.vapk is not None:
            records[Pipe.VAPK] = _normalize_to_3(self.vapk)

        return records

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Fluid:
        """Create Fluid from a dictionary with flexible key names."""
        # Map common aliases
        aliases = {
            "temperature": "temp",
            "pressure": "pres",
            "liquid_density": "liqden",
            "liquid_viscosity": "liqvisc",
            "liquid_surface_tension": "liqsur",
            "liquid_conductivity": "liqcon",
            "liquid_cp": "liqcp",
            "liquid_mw": "liqmw",
            "vapor_density": "vapden",
            "vapor_viscosity": "vapvisc",
            "vapor_conductivity": "vapcon",
            "vapor_cp": "vapcp",
            "vapor_mw": "vapmw",
            "vapor_z": "vapz",
            "vapor_k": "vapk",
            "liquid_volume_flow": "lvflow",
            "liquid_fraction": "lf",
        }

        normalized = {}
        for key, value in data.items():
            normalized_key = aliases.get(key.lower(), key)
            normalized[normalized_key] = value

        # Filter valid fields
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in normalized.items() if k in valid_fields}

        return cls(**filtered)

    @classmethod
    def water_at_temp(cls, temp: float = 25.0, pres: float = 100.0) -> Fluid:
        """Create Fluid for water at given temperature.

        Args:
            temp: Temperature (°C)
            pres: Pressure (kPag)

        Example::

            water_50c = Fluid.water_at_temp(temp=50.0)
        """
        # Approximate temperature corrections for water
        density = 1000.0 - 0.5 * (temp - 25.0)  # kg/m³
        viscosity = 1.0 * (0.9 ** ((temp - 25.0) / 10))  # cP

        return cls(
            temp=temp,
            pres=pres,
            liqden=density,
            liqvisc=viscosity,
            liqsur=62.4,
        )

    def summary(self) -> dict[str, Any]:
        """Return a summary dictionary of key properties.

        Only includes properties that are set (not None).
        """
        result: dict[str, Any] = {"num_cases": self.num_cases}

        if self.temp is not None and isinstance(self.temp, list):
            result["temp_range"] = (min(self.temp), max(self.temp))
        if self.pres is not None and isinstance(self.pres, list):
            result["pres_range"] = (min(self.pres), max(self.pres))
        if self.liqden is not None and isinstance(self.liqden, list):
            result["liqden_avg"] = sum(self.liqden) / len(self.liqden)
        if self.liqvisc is not None and isinstance(self.liqvisc, list):
            result["liqvisc_avg"] = sum(self.liqvisc) / len(self.liqvisc)
        if self.lf is not None and isinstance(self.lf, list):
            result["is_two_phase"] = any(lf < 1.0 for lf in self.lf)

        return result

    def __repr__(self) -> str:
        parts = ["Fluid"]

        # Show which properties are set
        set_props = []
        if self.temp is not None:
            set_props.append(f"T={self.temp[0]:.1f}C")
        if self.pres is not None:
            set_props.append(f"P={self.pres[0]:.1f}kPag")
        if self.liqden is not None:
            set_props.append(f"rho={self.liqden[0]:.1f}kg/m3")
        if self.liqvisc is not None:
            set_props.append(f"mu={self.liqvisc[0]:.4f}cP")

        if set_props:
            parts.append("(" + ", ".join(set_props) + ")")
        else:
            parts.append("(empty)")

        return "".join(parts)
