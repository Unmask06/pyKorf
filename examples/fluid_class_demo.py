#!/usr/bin/env python3
"""
Fluid Class Demo - Direct KDF Fluid Properties Management

This example demonstrates the new Fluid class that allows direct
manipulation of fluid properties in KDF files without requiring
intermediate text file imports.

The old fluids.txt format has records like:
    TEMP,52.25,52.25,52.25,"C"
    PRES,39.8,39.8,39.8,"barg"
    LPROP,570.23815,"kg/m3",0.1531296,"cP",20,"dynes/cm"

Can now be replaced with direct Python code:
    fluid = Fluid(
        temp_inlet=52.25,
        temp_outlet=52.25,
        pres_inlet=398.7,  # kPag
        liquid_density=570.24,
        liquid_viscosity=0.153,
    )
    pipe.set_fluid(fluid)
    model.save()
"""

from __future__ import annotations

from pykorf import Fluid, Model


def demo_basic_usage():
    """Demonstrate basic Fluid class usage."""
    print("=" * 70)
    print("DEMO 1: Basic Fluid Usage")
    print("=" * 70)
    print("NOTE: Use metric units. KORF will auto-convert to your display units!")
    print("      (e.g., kPag -> barg/psig, °C -> °F)")
    print()

    # Create a single-phase liquid fluid
    # These are METRIC units - KORF will convert to your preferred display units
    water = Fluid.single_phase_liquid(
        temp=25.0,           # °C -> KORF shows 77°F if using imperial
        pres=100.0,          # kPag -> KORF shows 1 barg or 14.5 psig
        density=1000.0,      # kg/m³
        viscosity=1.0,       # cP
        surface_tension=62.4,  # dyne/cm
    )

    print(f"Created: {water}")
    print(f"Summary: {water.summary()}")
    print()

    # Create fluid from HYSYS export
    oil = Fluid.from_hysys_export(
        temp=52.25,
        pres=3.987,      # barg -> converted to kPag internally
        liqden=570.24,
        liqvisc=0.153,
        liqsur=20.0,
    )

    print(f"From HYSYS: {oil}")
    print()


def demo_load_and_apply():
    """Demonstrate loading a model and applying fluid properties."""
    print("=" * 70)
    print("DEMO 2: Load Model and Apply Fluid")
    print("=" * 70)

    # Load the model
    model = Model("pykorf/trail_files/Cooling Water Circuit-EES-IT-LT-00141.kdf")
    print(f"Loaded model: {model.version}")
    print(f"Pipes: {len(model.pipes) - 1}")  # Exclude template (index 0)
    print()

    # Get pipe L1
    pipe = model.get_element("L1")
    print(f"Selected pipe: {pipe.name}")

    # Get current fluid properties
    current_fluid = pipe.get_fluid()
    print(f"Current fluid: {current_fluid}")
    print()

    # Create new fluid properties (simulating HYSYS import)
    new_fluid = Fluid(
        temp_inlet=55.0,
        temp_outlet=53.0,
        temp_average=54.0,
        pres_inlet=420.0,
        pres_outlet=410.0,
        pres_average=415.0,
        liquid_fraction=1.0,
        liquid_density=565.0,
        liquid_viscosity=0.145,
        liquid_surface_tension=19.5,
    )

    print(f"New fluid to apply: {new_fluid}")

    # Apply to pipe (directly updates KDF)
    pipe.set_fluid(new_fluid)
    print("✓ Fluid properties applied to pipe")

    # Verify the update
    updated_fluid = pipe.get_fluid()
    print(f"Updated fluid: {updated_fluid}")
    print()

    # Save would be done here:
    # model.save_as("updated_model.kdf")


def demo_multicase():
    """Demonstrate multi-case fluid properties."""
    print("=" * 70)
    print("DEMO 3: Multi-Case Fluid Properties")
    print("=" * 70)

    # Create fluid for multiple cases (NORMAL, RATED, MINIMUM)
    multicase_fluid = Fluid(
        temp_inlet=[52.25, 55.0, 50.0],
        temp_outlet=[52.25, 55.0, 50.0],
        temp_average=[52.25, 55.0, 50.0],
        pres_inlet=[398.7, 420.0, 380.0],
        pres_outlet=[398.7, 420.0, 380.0],
        pres_average=[398.7, 420.0, 380.0],
        liquid_fraction=[1.0, 1.0, 1.0],
        liquid_density=[570.24, 565.0, 575.0],
        liquid_viscosity=[0.153, 0.145, 0.160],
    )

    print(f"Created multi-case fluid with {multicase_fluid.num_cases} cases")
    print(f"Temperature range: {multicase_fluid.temp_range}")
    print(f"Pressure range: {multicase_fluid.pres_range}")
    print()

    # Show KDF record format
    records = multicase_fluid.to_kdf_records()
    print("KDF Records:")
    for param, values in records.items():
        if param in ["TEMP", "PRES", "LIQDEN", "LIQVISC"]:
            print(f"  {param}: {values}")
    print()


def demo_from_dict():
    """Demonstrate creating Fluid from dictionary."""
    print("=" * 70)
    print("DEMO 4: Create Fluid from Dictionary")
    print("=" * 70)

    # Simulate data from Excel or database
    excel_row = {
        "Temp_In": 60.0,
        "Temp_Out": 58.0,
        "Temp_Avg": 59.0,
        "Pres_In": 450.0,
        "Pres_Out": 440.0,
        "Pres_Avg": 445.0,
        "LiqDen": 550.0,
        "LiqVisc": 0.12,
        "LiqSur": 18.0,
    }

    fluid = Fluid.from_excel_row(excel_row)
    print(f"From Excel row: {fluid}")
    print()

    # From generic dict with aliases
    data = {
        "temp": 70.0,
        "pressure": 500.0,
        "density": 500.0,
        "viscosity": 0.10,
    }

    fluid2 = Fluid.from_dict(data)
    print(f"From dict with aliases: {fluid2}")
    print()


def demo_unit_conversion():
    """Demonstrate KORF's automatic unit conversion."""
    print("=" * 70)
    print("DEMO 5: KORF Automatic Unit Conversion")
    print("=" * 70)
    print("""
KORF handles unit conversion automatically! Just use metric units in Python,
and KORF will display them in your preferred units in the GUI.

Example:
    Python input (metric):        KORF GUI display:
    ──────────────────────────    ───────────────────────────────
    temp = 52.25    # °C    →     52.25°C  (or 126.05°F)
    pres = 398.7    # kPag  →     3.987 barg  (or 57.85 psig)
    dens = 570.24   # kg/m³ →     570.24 kg/m³ (or 35.6 lb/ft³)
    
You don't need to do any conversion - KORF handles it!
""")

    # Create fluid with metric units
    fluid = Fluid(
        temp_inlet=52.25,    # °C
        pres_inlet=398.7,    # kPag
        liquid_density=570.24,  # kg/m³
    )

    print("Python code:")
    print("-" * 40)
    print("""
fluid = Fluid(
    temp_inlet=52.25,      # °C
    pres_inlet=398.7,      # kPag
    liquid_density=570.24, # kg/m³
)
pipe.set_fluid(fluid)
""")
    print()
    print("KORF GUI will display (depending on your settings):")
    print("-" * 40)
    print("  Temperature: 52.25°C  (or 126.1°F)")
    print("  Pressure: 3.987 barg  (or 57.9 psig)")
    print("  Density: 570.24 kg/m³ (or 35.6 lb/ft³)")
    print()


def demo_comparison_with_text_import():
    """Compare old text file import vs new Fluid class approach."""
    print("=" * 70)
    print("DEMO 6: Comparison - Text Import vs Fluid Class")
    print("=" * 70)

    print("OLD WAY (text file import):")
    print("-" * 40)
    print("""
1. Create fluids.txt file:
   "KORF_3.0"
   "\\PIPE","L1","TEMP",52.25,52.25,52.25,"C"
   "\\PIPE","L1","PRES",398.7,398.7,398.7,"kPag"
   ...

2. Use KORF GUI: File → Import → Select fluids.txt

3. Check import log for errors

4. Save KDF file manually
""")

    print("NEW WAY (Fluid class):")
    print("-" * 40)
    print("""
1. Create Fluid object in Python:
   fluid = Fluid(
       temp_inlet=52.25,
       pres_inlet=398.7,
       liquid_density=570.24,
       ...
   )

2. Apply directly to pipe:
   pipe.set_fluid(fluid)

3. Save model:
   model.save()

✓ No intermediate files
✓ Programmatic control
✓ Validation before save
✓ Batch processing support
""")

    # Show equivalent code
    print("Equivalent Python code:")
    print("-" * 40)
    code = """
from pykorf import Model, Fluid

# Load model
model = Model("model.kdf")
pipe = model.get_element("L1")

# Create and apply fluid
fluid = Fluid(
    temp_inlet=52.25,
    temp_outlet=52.25,
    pres_inlet=398.7,
    pres_outlet=398.7,
    liquid_density=570.24,
    liquid_viscosity=0.153,
    liquid_surface_tension=20.0,
)
pipe.set_fluid(fluid)

# Save
model.save()
"""
    print(code)


def demo_batch_update():
    """Demonstrate batch updating multiple pipes."""
    print("=" * 70)
    print("DEMO 6: Batch Update Multiple Pipes")
    print("=" * 70)

    # Simulate fluid properties for multiple lines from Excel
    lines_data = {
        "L1": {"temp": 52.25, "pres": 398.7, "density": 570.24, "viscosity": 0.153},
        "L2": {"temp": 50.0, "pres": 350.0, "density": 600.0, "viscosity": 0.2},
        "L14": {"temp": 25.0, "pres": 100.0, "density": 1000.0, "viscosity": 1.0},
    }

    print("Simulating batch update from Excel data:")
    for line_name, data in lines_data.items():
        fluid = Fluid.single_phase_liquid(
            temp=data["temp"],
            pres=data["pres"],
            density=data["density"],
            viscosity=data["viscosity"],
        )
        print(f"  {line_name}: T={data['temp']}°C, P={data['pres']}kPag, "
              f"ρ={data['density']}kg/m³")

    print("\nCode to apply:")
    print("-" * 40)
    code = """
for line_name, data in lines_data.items():
    pipe = model.get_element(line_name)
    fluid = Fluid.single_phase_liquid(**data)
    pipe.set_fluid(fluid)
    
model.save()
"""
    print(code)


def main():
    """Run all demos."""
    print("\n")
    print("█" * 70)
    print("█" + " " * 68 + "█")
    print("█" + "  Fluid Class Demo - Direct KDF Fluid Management".center(68) + "█")
    print("█" + " " * 68 + "█")
    print("█" * 70)
    print()

    demo_basic_usage()
    demo_load_and_apply()
    demo_multicase()
    demo_from_dict()
    demo_unit_conversion()
    demo_comparison_with_text_import()
    demo_batch_update()

    print("=" * 70)
    print("All demos completed!")
    print("=" * 70)
    print()
    print("Key benefits of the Fluid class:")
    print("  ✓ No intermediate text files needed")
    print("  ✓ Type-safe property access")
    print("  ✓ Multi-case support built-in")
    print("  ✓ Easy integration with Excel/pandas")
    print("  ✓ Validation before saving")
    print("  ✓ Batch processing support")
    print("  ✓ Automatic unit conversion by KORF!")


if __name__ == "__main__":
    main()
