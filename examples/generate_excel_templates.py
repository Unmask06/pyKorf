#!/usr/bin/env python3
"""
Generate Excel Templates for pyKorf Enterprise Workflows.

This script creates ready-to-use Excel templates for:
1. PMS Master data (pipe specifications)
2. Fluid Properties data

Usage:
    python generate_excel_templates.py --output-dir ./templates

The generated Excel files can be used with:
    - enterprise_pms_and_fluid_workflow.py
    - Custom scripts following the pyKorf documentation
"""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    print("Error: pandas is required. Install with: pip install pandas openpyxl")
    raise


def create_pms_master_data() -> pd.DataFrame:
    """Create sample PMS master data.

    Returns:
        DataFrame with sample PMS specifications
    """
    data = {
        "PMS_Code": [
            "PMS-A11-CS2",
            "PMS-A11-CS4",
            "PMS-A11-CS6",
            "PMS-A22-CS2",
            "PMS-A22-CS4",
            "PMS-A33-CS2",
            "PMS-A33-CS4",
            "PMS-A44-CS2",
            "PMS-B11-SS2",
            "PMS-B11-SS4",
            "PMS-B22-SS2",
            "PMS-B22-SS4",
        ],
        "Nominal_Size": [
            2, 2, 2,      # 2-inch
            4, 4,         # 4-inch
            6, 6,         # 6-inch
            8,            # 8-inch
            2, 2,         # 2-inch SS
            4, 4,         # 4-inch SS
        ],
        "OD_inch": [
            2.375, 2.375, 2.375,  # 2-inch OD
            4.500, 4.500,        # 4-inch OD
            6.625, 6.625,        # 6-inch OD
            8.625,               # 8-inch OD
            2.375, 2.375,        # 2-inch SS OD
            4.500, 4.500,        # 4-inch SS OD
        ],
        "Schedule": [
            "40", "80", "160",   # 2-inch schedules
            "40", "80",          # 4-inch schedules
            "40", "80",          # 6-inch schedules
            "40",                # 8-inch schedule
            "40S", "80S",        # 2-inch SS schedules
            "40S", "80S",        # 4-inch SS schedules
        ],
        "ID_inch": [
            2.067, 1.939, 1.689,  # 2-inch IDs
            4.026, 3.826,        # 4-inch IDs
            6.065, 5.761,        # 6-inch IDs
            7.981,               # 8-inch ID
            2.157, 1.771,        # 2-inch SS IDs
            4.026, 3.826,        # 4-inch SS IDs
        ],
        "Material": [
            "Carbon Steel", "Carbon Steel", "Carbon Steel",
            "Carbon Steel", "Carbon Steel",
            "Carbon Steel", "Carbon Steel",
            "Carbon Steel",
            "Stainless Steel", "Stainless Steel",
            "Stainless Steel", "Stainless Steel",
        ],
        "Wall_Thickness_mm": [
            3.91, 6.02, 8.74,    # 2-inch wall thicknesses
            6.02, 8.56,          # 4-inch wall thicknesses
            7.11, 10.97,         # 6-inch wall thicknesses
            8.18,                # 8-inch wall thickness
            5.54, 9.53,          # 2-inch SS wall thicknesses
            6.02, 8.56,          # 4-inch SS wall thicknesses
        ],
        "Description": [
            '2" Sch 40 CS',
            '2" Sch 80 CS',
            '2" Sch 160 CS',
            '4" Sch 40 CS',
            '4" Sch 80 CS',
            '6" Sch 40 CS',
            '6" Sch 80 CS',
            '8" Sch 40 CS',
            '2" Sch 40S SS',
            '2" Sch 80S SS',
            '4" Sch 40S SS',
            '4" Sch 80S SS',
        ],
    }

    return pd.DataFrame(data)


def create_fluid_properties_data() -> pd.DataFrame:
    """Create sample fluid properties data.

    Returns:
        DataFrame with sample fluid properties for multiple lines and cases
    """
    # Example: Cooling water system with 3 cases (NORMAL, RATED, MINIMUM)
    data = {
        "Line_Name": [
            # L1 - Main supply line
            "L1", "L1", "L1",
            # L2 - Return line
            "L2", "L2", "L2",
            # L14 - Process feed (from sample file)
            "L14", "L14", "L14",
        ],
        "Case": [
            1, 2, 3,  # L1 cases
            1, 2, 3,  # L2 cases
            1, 2, 3,  # L14 cases
        ],
        # Temperature data (°C)
        "Temp_In": [
            52.25, 55.0, 50.0,   # L1
            48.0, 50.0, 45.0,    # L2
            25.0, 28.0, 22.0,    # L14
        ],
        "Temp_Out": [
            52.25, 55.0, 50.0,   # L1
            48.0, 50.0, 45.0,    # L2
            25.0, 28.0, 22.0,    # L14
        ],
        "Temp_Avg": [
            52.25, 55.0, 50.0,   # L1
            48.0, 50.0, 45.0,    # L2
            25.0, 28.0, 22.0,    # L14
        ],
        # Pressure data (kPag)
        "Pres_In": [
            398.7, 420.0, 380.0,  # L1
            350.0, 370.0, 330.0,  # L2
            100.0, 120.0, 80.0,   # L14
        ],
        "Pres_Out": [
            398.7, 420.0, 380.0,  # L1
            350.0, 370.0, 330.0,  # L2
            100.0, 120.0, 80.0,   # L14
        ],
        "Pres_Avg": [
            398.7, 420.0, 380.0,  # L1
            350.0, 370.0, 330.0,  # L2
            100.0, 120.0, 80.0,   # L14
        ],
        # Liquid fraction (1.0 = fully liquid)
        "LF_In": [
            1.0, 1.0, 1.0,  # L1
            1.0, 1.0, 1.0,  # L2
            1.0, 1.0, 1.0,  # L14
        ],
        "LF_Out": [
            1.0, 1.0, 1.0,  # L1
            1.0, 1.0, 1.0,  # L2
            1.0, 1.0, 1.0,  # L14
        ],
        "LF_Avg": [
            1.0, 1.0, 1.0,  # L1
            1.0, 1.0, 1.0,  # L2
            1.0, 1.0, 1.0,  # L14
        ],
        # Liquid properties
        "LiqDen": [
            570.24, 565.0, 575.0,  # L1 - Oil
            1000.0, 998.0, 1002.0, # L2 - Water
            1000.0, 998.0, 1002.0, # L14 - Water
        ],
        "LiqVisc": [
            0.153, 0.145, 0.160,   # L1
            1.0, 0.9, 1.1,         # L2
            1.0, 0.9, 1.1,         # L14
        ],
        "LiqSur": [
            20.0, 19.5, 20.5,   # L1
            62.4, 62.0, 62.8,   # L2
            62.4, 62.0, 62.8,   # L14
        ],
        "LiqCon": [
            0.5, 0.5, 0.5,   # L1
            0.6, 0.6, 0.6,   # L2
            0.6, 0.6, 0.6,   # L14
        ],
        "LiqCp": [
            1.0, 1.0, 1.0,   # L1
            4.18, 4.18, 4.18, # L2
            4.18, 4.18, 4.18, # L14
        ],
        "LiqMW": [
            200.0, 200.0, 200.0,  # L1 - Oil
            18.0, 18.0, 18.0,     # L2 - Water
            18.0, 18.0, 18.0,     # L14 - Water
        ],
        # Vapor properties (0 for single-phase liquid)
        "VapDen": [
            0.0, 0.0, 0.0,   # L1
            0.0, 0.0, 0.0,   # L2
            0.0, 0.0, 0.0,   # L14
        ],
        "VapVisc": [
            0.0, 0.0, 0.0,   # L1
            0.0, 0.0, 0.0,   # L2
            0.0, 0.0, 0.0,   # L14
        ],
        "VapCon": [
            0.025, 0.025, 0.025,   # L1
            0.025, 0.025, 0.025,   # L2
            0.025, 0.025, 0.025,   # L14
        ],
        "VapCp": [
            1.0, 1.0, 1.0,   # L1
            1.0, 1.0, 1.0,   # L2
            1.0, 1.0, 1.0,   # L14
        ],
        "VapMW": [
            0.0, 0.0, 0.0,   # L1
            0.0, 0.0, 0.0,   # L2
            0.0, 0.0, 0.0,   # L14
        ],
        "VapZ": [
            0.0, 0.0, 0.0,   # L1
            0.0, 0.0, 0.0,   # L2
            0.0, 0.0, 0.0,   # L14
        ],
        # Notes
        "Notes": [
            "Oil - NORMAL",
            "Oil - RATED",
            "Oil - MINIMUM",
            "Water - NORMAL",
            "Water - RATED",
            "Water - MINIMUM",
            "Cooling Water - NORMAL",
            "Cooling Water - RATED",
            "Cooling Water - MINIMUM",
        ],
    }

    return pd.DataFrame(data)


def create_line_to_pms_mapping() -> pd.DataFrame:
    """Create sample line-to-PMS mapping.

    This is optional - used when PMS codes are not already in Line Notes.

    Returns:
        DataFrame with line to PMS mapping
    """
    data = {
        "Line_Name": ["L1", "L2", "L4", "L6", "L14"],
        "PMS_Code": [
            "PMS-A33-CS2",   # L1 - 6" Sch 40
            "PMS-A33-CS2",   # L2 - 6" Sch 40
            "PMS-A22-CS2",   # L4 - 4" Sch 40
            "PMS-A11-CS2",   # L6 - 2" Sch 40
            "PMS-A11-CS2",   # L14 - 2" Sch 40
        ],
        "Line_Number": [
            "LINE-001",
            "LINE-002",
            "LINE-004",
            "LINE-006",
            "LINE-014",
        ],
        "Service": [
            "Cooling Water Supply",
            "Cooling Water Return",
            "Process Feed",
            "Process Return",
            "Vent Line",
        ],
    }

    return pd.DataFrame(data)


def generate_templates(output_dir: Path) -> dict[str, Path]:
    """Generate all Excel templates.

    Args:
        output_dir: Directory to save templates

    Returns:
        Dictionary mapping template names to file paths
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    generated_files = {}

    # Template 1: Combined PMS and Fluid Properties
    combined_file = output_dir / "pms_and_fluid_template.xlsx"
    with pd.ExcelWriter(combined_file, engine="openpyxl") as writer:
        # Sheet 1: PMS Master
        pms_df = create_pms_master_data()
        pms_df.to_excel(writer, sheet_name="PMS_Master", index=False)

        # Sheet 2: Fluid Properties
        fluid_df = create_fluid_properties_data()
        fluid_df.to_excel(writer, sheet_name="Fluid_Properties", index=False)

        # Sheet 3: Line to PMS Mapping (optional)
        mapping_df = create_line_to_pms_mapping()
        mapping_df.to_excel(writer, sheet_name="Line_to_PMS_Mapping", index=False)

    generated_files["combined"] = combined_file
    print(f"* Created: {combined_file}")

    # Template 2: PMS Only
    pms_file = output_dir / "pms_template.xlsx"
    with pd.ExcelWriter(pms_file, engine="openpyxl") as writer:
        pms_df = create_pms_master_data()
        pms_df.to_excel(writer, sheet_name="PMS_Master", index=False)
        mapping_df = create_line_to_pms_mapping()
        mapping_df.to_excel(writer, sheet_name="Line_to_PMS_Mapping", index=False)

    generated_files["pms_only"] = pms_file
    print(f"* Created: {pms_file}")

    # Template 3: Fluid Properties Only
    fluid_file = output_dir / "fluid_properties_template.xlsx"
    with pd.ExcelWriter(fluid_file, engine="openpyxl") as writer:
        fluid_df = create_fluid_properties_data()
        fluid_df.to_excel(writer, sheet_name="Fluid_Properties", index=False)

    generated_files["fluid_only"] = fluid_file
    print(f"* Created: {fluid_file}")

    return generated_files


def print_usage_instructions(generated_files: dict[str, Path]):
    """Print usage instructions for the generated templates.

    Args:
        generated_files: Dictionary of generated file paths
    """
    print("\n" + "="*70)
    print("EXCEL TEMPLATES GENERATED SUCCESSFULLY")
    print("="*70)

    print("\n📁 Generated Files:")
    for name, path in generated_files.items():
        print(f"   • {name}: {path}")

    print("\n" + "-"*70)
    print("USAGE INSTRUCTIONS")
    print("-"*70)

    print("""
1. PMS Master Sheet (for Pipe Schedule Updates):
   ─────────────────────────────────────────────
   • PMS_Code: Unique identifier (e.g., "PMS-A11-CS2")
   • Nominal_Size: Pipe nominal size in inches
   • OD_inch: Outer diameter in inches
   • Schedule: Pipe schedule (40, 80, 160, STD, XS, XXS, 40S, 80S)
   • ID_inch: Inner diameter in inches
   • Material: Pipe material (Carbon Steel, Stainless Steel, etc.)

   Add PMS codes to your KDF Line Notes in format:
       PMS:PMS-A11-CS2; LINE-001;

2. Fluid Properties Sheet (for Importing Fluid Data):
   ───────────────────────────────────────────────────
   • Line_Name: Must match pipe name in KDF file
   • Case: Case number (1, 2, 3, ...) for multi-case models
   • Temp_In/Out/Avg: Temperatures in °C
   • Pres_In/Out/Avg: Pressures in kPag
   • LF_In/Out/Avg: Liquid fraction (0-1)
   • LiqDen: Liquid density in kg/m³
   • LiqVisc: Liquid viscosity in cP
   • LiqSur: Surface tension in dyne/cm

3. Line to PMS Mapping Sheet (Optional):
   ──────────────────────────────────────
   Use this if PMS codes are NOT already in KDF Line Notes.
   Maps line names to PMS codes for bulk updates.

""")

    print("-"*70)
    print("NEXT STEPS")
    print("-"*70)
    print("""
1. Open the generated Excel files
2. Replace sample data with your actual PMS specifications
3. Add your fluid properties data from HYSYS/Unisim/Aspen
4. Run the workflow script:

   python enterprise_pms_and_fluid_workflow.py \\
       --kdf "your_model.kdf" \\
       --pms-excel "pms_template.xlsx" \\
       --fluid-excel "fluid_properties_template.xlsx" \\
       --output "updated_model.kdf"

For dry run (preview changes without saving):

   python enterprise_pms_and_fluid_workflow.py \\
       --kdf "your_model.kdf" \\
       --pms-excel "pms_template.xlsx" \\
       --dry-run
""")

    print("="*70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate Excel templates for pyKorf enterprise workflows"
    )
    parser.add_argument(
        "--output-dir", "-o",
        default="./templates",
        help="Output directory for templates (default: ./templates)"
    )

    args = parser.parse_args()

    output_dir = Path(args.output_dir)

    print("Generating Excel templates for pyKorf enterprise workflows...")
    print()

    try:
        generated_files = generate_templates(output_dir)
        print_usage_instructions(generated_files)

        print(f"\n✅ Templates saved to: {output_dir.absolute()}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise


if __name__ == "__main__":
    main()
