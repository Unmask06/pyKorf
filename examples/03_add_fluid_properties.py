"""Example 3: Add Fluid Properties to KORF Model.

This example demonstrates how to:
- Define fluid properties (density, viscosity, etc.)
- Create or update fluid entries in KORF
- Use the Fluid class for type-safe fluid management
- Assign fluids to pipes and equipment
"""

from __future__ import annotations

from typing import Any

from pykorf import Model
from pykorf.elements import Common, Pipe


class Fluid:
    """Represents a fluid with properties for KORF simulation.

    This class provides a type-safe way to manage fluid properties
    and convert them to KORF-compatible formats.

    Attributes:
        name: Fluid name (e.g., "Water", "Crude Oil").
        phase: Phase type ("Liquid", "Vapor", "Two-Phase").
        density_kg_m3: Density at operating conditions.
        viscosity_cp: Dynamic viscosity in centipoise.
        molecular_weight: Molecular weight in kg/kmol.
        specific_heat_kj_kg_k: Specific heat capacity.
        thermal_conductivity: Thermal conductivity in W/m·K.
        vapor_pressure_kpa: Vapor pressure in kPa.
        compressibility: Compressibility factor Z.
        notes: Additional notes or description.

    Example:
        ```python
        water = Fluid(
            name="Water at 25C",
            phase="Liquid",
            density_kg_m3=997.0,
            viscosity_cp=0.89,
        )
        ```
    """

    def __init__(
        self,
        name: str,
        phase: str = "Liquid",
        density_kg_m3: float | None = None,
        viscosity_cp: float | None = None,
        molecular_weight: float | None = None,
        specific_heat_kj_kg_k: float | None = None,
        thermal_conductivity: float | None = None,
        vapor_pressure_kpa: float | None = None,
        compressibility: float | None = None,
        notes: str = "",
    ):
        self.name = name
        self.phase = phase
        self.density_kg_m3 = density_kg_m3
        self.viscosity_cp = viscosity_cp
        self.molecular_weight = molecular_weight
        self.specific_heat_kj_kg_k = specific_heat_kj_kg_k
        self.thermal_conductivity = thermal_conductivity
        self.vapor_pressure_kpa = vapor_pressure_kpa
        self.compressibility = compressibility
        self.notes = notes

    def to_korf_params(self) -> dict[str, str]:
        """Convert fluid properties to KORF parameter dictionary.

        Returns:
            Dictionary of KDF parameter names to string values.
        """
        # Using pipe parameters for fluid properties
        params: dict[str, str] = {
            "NAME": self.name,
            Pipe.TEMP: str(self.density_kg_m3) if self.density_kg_m3 else "25",
        }

        # Liquid properties stored in pipe records
        if self.density_kg_m3 is not None:
            params[Pipe.LIQDEN] = str(self.density_kg_m3)
        if self.viscosity_cp is not None:
            params[Pipe.LIQVISC] = str(self.viscosity_cp)
        if self.specific_heat_kj_kg_k is not None:
            params[Pipe.LIQCP] = str(self.specific_heat_kj_kg_k)
        if self.notes:
            params[Common.NOTES] = self.notes

        return params

    @classmethod
    def water(cls, temperature_c: float = 25.0) -> Fluid:
        """Create water fluid at specified temperature.

        Uses approximate properties for water at atmospheric pressure.

        Args:
            temperature_c: Temperature in Celsius (affects properties).

        Returns:
            Fluid instance for water.
        """
        # Approximate values - in production use proper thermodynamic data
        if temperature_c <= 30:
            return cls(
                name=f"Water at {temperature_c} degC",
                phase="Liquid",
                density_kg_m3=997.0 - (temperature_c - 20) * 0.2,
                viscosity_cp=0.89 + (25 - temperature_c) * 0.01,
                specific_heat_kj_kg_k=4.18,
                thermal_conductivity=0.6,
                molecular_weight=18.015,
                notes=f"Water properties at {temperature_c} degC, atmospheric pressure",
            )
        else:
            # Higher temperature approximation
            return cls(
                name=f"Water at {temperature_c} degC",
                phase="Liquid",
                density_kg_m3=990.0 - (temperature_c - 30) * 0.5,
                viscosity_cp=0.8 - (temperature_c - 25) * 0.005,
                specific_heat_kj_kg_k=4.18,
                thermal_conductivity=0.6,
                molecular_weight=18.015,
                notes=f"Water properties at {temperature_c} degC",
            )

    @classmethod
    def crude_oil(
        cls,
        name: str = "Crude Oil",
        api_gravity: float = 30.0,
        temperature_c: float = 60.0,
    ) -> Fluid:
        """Create crude oil fluid.

        Args:
            name: Specific name for this crude.
            api_gravity: API gravity (affects density).
            temperature_c: Operating temperature.

        Returns:
            Fluid instance for crude oil.
        """
        # Calculate approximate density from API gravity
        density = 141.5 / (api_gravity + 131.5) * 1000  # kg/m3

        return cls(
            name=f"{name} (API {api_gravity})",
            phase="Liquid",
            density_kg_m3=round(density, 1),
            viscosity_cp=5.0 + (40 - api_gravity) * 0.2,  # Rough approximation
            specific_heat_kj_kg_k=2.0,
            thermal_conductivity=0.15,
            molecular_weight=200.0,  # Approximate for mixture
            notes=f"Crude oil, API {api_gravity}, {temperature_c} degC",
        )

    @classmethod
    def natural_gas(
        cls,
        name: str = "Natural Gas",
        pressure_bara: float = 50.0,
        temperature_c: float = 20.0,
    ) -> Fluid:
        """Create natural gas fluid.

        Args:
            name: Gas name/description.
            pressure_bara: Operating pressure.
            temperature_c: Operating temperature.

        Returns:
            Fluid instance for natural gas.
        """
        return cls(
            name=f"{name} at {pressure_bara}bara",
            phase="Vapor",
            density_kg_m3=pressure_bara * 16.04 / (8.314 * (273.15 + temperature_c)),
            viscosity_cp=0.011,
            molecular_weight=16.04,  # Methane basis
            specific_heat_kj_kg_k=2.2,
            thermal_conductivity=0.03,
            compressibility=0.9,  # Approximate at moderate pressures
            notes=f"Natural gas at {pressure_bara} bara, {temperature_c} degC",
        )

    def __repr__(self) -> str:
        return f"Fluid(name='{self.name}', phase='{self.phase}')"


def add_fluid_to_model(
    model: Model,
    fluid: Fluid,
    fluid_element_name: str | None = None,
) -> str:
    """Register a fluid for use in the KORF model.

    Note: KORF stores fluid properties directly on pipe elements. This function
    registers the fluid definition for reference when assigning to pipes.

    Args:
        model: The KORF model.
        fluid: Fluid instance with properties.
        fluid_element_name: Optional custom name for the fluid.

    Returns:
        Name of the fluid (for reference).

    Example:
        ```python
        water = Fluid.water(temperature_c=25)
        fluid_name = add_fluid_to_model(model, water, "COOLING_WATER")
        ```
    """
    if fluid_element_name is None:
        # Generate name from fluid name
        fluid_element_name = fluid.name.replace(" ", "_").replace("deg", "DEG")[:9]

    print(f"  [OK] Registered fluid '{fluid_element_name}': {fluid.name}")
    print(f"    Density: {fluid.density_kg_m3} kg/m³, Viscosity: {fluid.viscosity_cp} cP")
    return fluid_element_name


def assign_fluid_to_pipes(
    model: Model,
    fluid: Fluid,
    pipe_names: list[str],
) -> None:
    """Apply fluid properties to multiple pipes.

    Args:
        model: The KORF model.
        fluid: Fluid instance with properties.
        pipe_names: List of pipe names to apply the fluid to.

    Example:
        ```python
        water = Fluid.water(temperature_c=50)
        assign_fluid_to_pipes(model, water, ["L1", "L2", "L3"])
        ```
    """
    print(f"\n  Assigning fluid '{fluid.name}' to pipes:")

    # Get fluid parameters for pipes
    params = fluid.to_korf_params()

    for pipe_name in pipe_names:
        try:
            model.update_element(pipe_name, params)
            print(f"    [OK] {pipe_name}")
        except Exception as e:
            print(f"    [WARN] {pipe_name}: {e}")


def create_fluid_library(model: Model) -> list[str]:
    """Create a standard library of common fluids.

    Args:
        model: The KORF model.

    Returns:
        List of created fluid element names.
    """
    print("=" * 60)
    print("Creating Standard Fluid Library")
    print("=" * 60)

    fluids = [
        # Water at different temperatures
        Fluid.water(temperature_c=20),
        Fluid.water(temperature_c=50),
        Fluid.water(temperature_c=80),
        # Crude oils
        Fluid.crude_oil(name="Light Crude", api_gravity=40),
        Fluid.crude_oil(name="Heavy Crude", api_gravity=20),
        # Natural gas
        Fluid.natural_gas(pressure_bara=30, temperature_c=20),
        Fluid.natural_gas(pressure_bara=100, temperature_c=50),
        # Custom fluid
        Fluid(
            name="Thermal Oil",
            phase="Liquid",
            density_kg_m3=850,
            viscosity_cp=5.0,
            specific_heat_kj_kg_k=2.5,
            thermal_conductivity=0.12,
            notes="Heat transfer fluid for high temperature applications",
        ),
    ]

    created = []
    for fluid in fluids:
        try:
            name = add_fluid_to_model(model, fluid)
            created.append(name)
        except Exception as e:
            print(f"  [WARN] Failed to add {fluid.name}: {e}")

    return created


def get_pipe_fluid_summary(model: Model) -> list[dict[str, Any]]:
    """Get summary of fluid properties from all pipes in the model.

    Returns:
        List of pipe fluid property dictionaries.
    """
    print("\n" + "=" * 60)
    print("Pipe Fluid Properties Summary")
    print("=" * 60)

    pipes_info = []
    for idx, pipe in model.pipes.items():
        if idx == 0:  # Skip template
            continue

        info = {
            "index": idx,
            "name": pipe.name,
        }

        # Try to get fluid properties from the pipe
        try:
            dens_rec = pipe._get(Pipe.LIQDEN)
            if dens_rec and dens_rec.values:
                info["density"] = dens_rec.values[0]
        except Exception:
            pass
        try:
            visc_rec = pipe._get(Pipe.LIQVISC)
            if visc_rec and visc_rec.values:
                info["viscosity"] = visc_rec.values[0]
        except Exception:
            pass
        try:
            temp_rec = pipe._get(Pipe.TEMP)
            if temp_rec and temp_rec.values:
                info["temp"] = temp_rec.values[0]
        except Exception:
            pass

        pipes_info.append(info)
        print(f"  [{idx}] {info['name']}")
        if "density" in info:
            print(f"      Density: {info['density']} kg/m³")
        if "viscosity" in info:
            print(f"      Viscosity: {info['viscosity']} cP")

    return pipes_info


if __name__ == "__main__":
    # Create or load a model
    print("=" * 60)
    print("Fluid Properties Demo")
    print("=" * 60)

    try:
        model = Model("examples/output/pump_circuit.kdf")
        print("  [OK] Loaded pump circuit model")
    except FileNotFoundError:
        print("  Creating new model...")
        model = Model()

    # Create fluid library
    fluid_objects = [
        Fluid.water(temperature_c=20),
        Fluid.water(temperature_c=50),
        Fluid.water(temperature_c=80),
    ]

    # Get summary
    print("\n" + "=" * 60)
    print("Fluid Library Summary")
    print("=" * 60)
    for i, fluid in enumerate(fluid_objects, 1):
        print(f"  [{i}] {fluid.name}")

    # Assign fluids to pipes if we have the pump circuit
    if "SUCT_L1" in [p.name for p in model.pipes.values()]:
        print("\n" + "=" * 60)
        print("Assigning Fluids to Pump Circuit")
        print("=" * 60)

        # Use the 50 degC water for the cooling circuit
        assign_fluid_to_pipes(model, fluid_objects[1], ["SUCT_L1", "DISC_L2", "RETURN_L3"])

    # Save model
    output_path = "examples/output/pump_circuit_with_fluids.kdf"
    model.save_as(output_path)
    print(f"\n  [OK] Model saved to: {output_path}")
