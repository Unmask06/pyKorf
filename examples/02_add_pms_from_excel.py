"""Example 2: Add PMS (Piping Material Specification) from Excel.

This example demonstrates how to:
- Read PMS data from an Excel file
- Create PipeData library entries in KORF
- Assign materials and schedules to pipes
- Validate the PMS against industry standards
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pykorf import Model
from pykorf.definitions import Element, Pipe


def create_sample_pms_excel(output_path: str = "examples/output/pms_data.xlsx") -> None:
    """Create a sample Excel file with PMS data for demonstration.

    In production, this would be your actual PMS specification file.
    """
    try:
        import pandas as pd
    except ImportError:
        print("pandas not installed. Creating JSON sample instead...")
        create_sample_pms_json(output_path.replace(".xlsx", ".json"))
        return

    print("=" * 60)
    print("Creating Sample PMS Excel File")
    print("=" * 60)

    # Create PMS data
    pms_data = {
        "Material": [
            "Carbon Steel",
            "Carbon Steel",
            "Stainless Steel",
            "Stainless Steel",
        ],
        "Schedule": ["40", "80", "40", "80"],
        "Nominal_Diameter_inch": [4, 6, 4, 6],
        "Outer_Diameter_mm": [114.3, 168.3, 114.3, 168.3],
        "Wall_Thickness_mm": [6.02, 7.11, 6.02, 7.11],
        "Roughness_mm": [0.046, 0.046, 0.015, 0.015],
        "Max_Pressure_bar": [100, 150, 100, 150],
        "Max_Temp_C": [400, 400, 500, 500],
        "PMS_Code": ["CS-40-4", "CS-80-6", "SS-40-4", "SS-80-6"],
    }

    df = pd.DataFrame(pms_data)

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(output_path, index=False, sheet_name="PMS_Data")
    print(f"  ✓ Created sample PMS Excel: {output_path}")
    print(f"  ✓ Contains {len(df)} pipe specifications")


def create_sample_pms_json(output_path: str = "examples/output/pms_data.json") -> None:
    """Create a sample JSON file with PMS data."""
    print("=" * 60)
    print("Creating Sample PMS JSON File")
    print("=" * 60)

    pms_data = {
        "specifications": [
            {
                "material": "Carbon Steel",
                "schedule": "40",
                "nominal_diameter_inch": 4,
                "outer_diameter_mm": 114.3,
                "wall_thickness_mm": 6.02,
                "roughness_mm": 0.046,
                "max_pressure_bar": 100,
                "max_temp_c": 400,
                "pms_code": "CS-40-4",
            },
            {
                "material": "Carbon Steel",
                "schedule": "80",
                "nominal_diameter_inch": 6,
                "outer_diameter_mm": 168.3,
                "wall_thickness_mm": 7.11,
                "roughness_mm": 0.046,
                "max_pressure_bar": 150,
                "max_temp_c": 400,
                "pms_code": "CS-80-6",
            },
            {
                "material": "Stainless Steel",
                "schedule": "40",
                "nominal_diameter_inch": 4,
                "outer_diameter_mm": 114.3,
                "wall_thickness_mm": 6.02,
                "roughness_mm": 0.015,
                "max_pressure_bar": 100,
                "max_temp_c": 500,
                "pms_code": "SS-40-4",
            },
            {
                "material": "Stainless Steel",
                "schedule": "80",
                "nominal_diameter_inch": 6,
                "outer_diameter_mm": 168.3,
                "wall_thickness_mm": 7.11,
                "roughness_mm": 0.015,
                "max_pressure_bar": 150,
                "max_temp_c": 500,
                "pms_code": "SS-80-6",
            },
        ]
    }

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(pms_data, f, indent=2)
    print(f"  ✓ Created sample PMS JSON: {output_path}")
    print(f"  ✓ Contains {len(pms_data['specifications'])} pipe specifications")


def read_pms_from_excel(file_path: str) -> list[dict[str, Any]]:
    """Read PMS data from Excel file.

    Args:
        file_path: Path to Excel file.

    Returns:
        List of pipe specification dictionaries.

    Raises:
        ImportError: If pandas is not installed.
        FileNotFoundError: If file doesn't exist.
    """
    import pandas as pd

    df = pd.read_excel(file_path, sheet_name="PMS_Data")

    # Convert to list of dictionaries
    specs = df.to_dict(orient="records")

    print(f"  ✓ Read {len(specs)} PMS entries from Excel")
    return specs


def read_pms_from_json(file_path: str) -> list[dict[str, Any]]:
    """Read PMS data from JSON file."""
    with open(file_path) as f:
        data = json.load(f)

    specs = data.get("specifications", [])
    print(f"  ✓ Read {len(specs)} PMS entries from JSON")
    return specs


def add_pms_to_model(
    model: Model,
    pms_specs: list[dict[str, Any]],
    override_existing: bool = False,
) -> list[str]:
    """Add PMS specifications as PipeData library entries.

    Args:
        model: The KORF model to add PMS to.
        pms_specs: List of PMS specification dictionaries.
        override_existing: Whether to override existing PipeData entries.

    Returns:
        List of created PipeData entry names.

    Example:
        ```python
        model = Model()
        specs = read_pms_from_excel("pms.xlsx")
        created = add_pms_to_model(model, specs)
        ```
    """
    print("\n" + "=" * 60)
    print("Adding PMS to Model")
    print("=" * 60)

    created_names = []
    skipped = 0

    for spec in pms_specs:
        # Generate unique name from PMS code
        pms_code = spec.get("pms_code", f"PMS_{len(created_names)}")
        entry_name = f"PMS_{pms_code}"

        # Check if already exists
        if entry_name in [p.name for p in model.pipedata.values()]:
            if not override_existing:
                print(f"  ⏭ Skipping {entry_name} (already exists)")
                skipped += 1
                continue
            print(f"  📝 Overriding {entry_name}")

        # Create PipeData entry
        params = {
            Pipe.MAT: spec.get("material", "Carbon Steel"),
            Pipe.SCH: str(spec.get("schedule", "40")),
            Pipe.NBD: str(spec.get("nominal_diameter_inch", 4)),
            Pipe.OD: str(spec.get("outer_diameter_mm", 114.3)),
            Pipe.WT: str(spec.get("wall_thickness_mm", 6.0)),
            Pipe.RR: str(spec.get("roughness_mm", 0.046)),
            # Additional metadata in NOTES
            Common.NOTES: (
                f"PMS: {pms_code}, "
                f"MaxP: {spec.get('max_pressure_bar', 'N/A')}bar, "
                f"MaxT: {spec.get('max_temp_c', 'N/A')}�degC"
            ),
        }

        try:
            model.add_element(Element.PIPEDATA, entry_name, params)
            created_names.append(entry_name)
            print(f"  ✓ Created PipeData: {entry_name}")
            print(
                f"    Material: {params[Pipe.MAT]}, Sch {params[Pipe.SCH]}, "
                f'DN{params[Pipe.NBD]}"'
            )
        except Exception as e:
            print(f"  ✗ Failed to create {entry_name}: {e}")

    print(f"\n  Summary: {len(created_names)} created, {skipped} skipped")
    return created_names


def assign_pms_to_pipes(
    model: Model,
    pipe_pms_mapping: dict[str, str],
) -> None:
    """Assign PMS specifications to actual pipes in the model.

    Args:
        model: The KORF model.
        pipe_pms_mapping: Dict mapping pipe name to PMS code.

    Example:
        ```python
        mapping = {
            "SUCT_L1": "CS-40-6",  # Carbon Steel, Sch 40, 6"
            "DISC_L2": "CS-80-4",  # Carbon Steel, Sch 80, 4"
        }
        assign_pms_to_pipes(model, mapping)
        ```
    """
    print("\n" + "=" * 60)
    print("Assigning PMS to Pipes")
    print("=" * 60)

    for pipe_name, pms_code in pipe_pms_mapping.items():
        pipedata_name = f"PMS_{pms_code}"

        # Check if pipe exists
        if pipe_name not in [p.name for p in model.pipes.values()]:
            print(f"  ⚠ Pipe '{pipe_name}' not found in model")
            continue

        # Check if PipeData exists
        if pipedata_name not in [p.name for p in model.pipedata.values()]:
            print(f"  ⚠ PMS '{pms_code}' not found in library")
            continue

        # Get PipeData reference
        pipedata = model.pipedata[
            [k for k, v in model.pipedata.items() if v.name == pipedata_name][0]
        ]

        # Update pipe to reference this PMS
        try:
            model.update_element(
                pipe_name,
                {
                    Pipe.MAT: pipedata._get(Pipe.MAT).values[0],
                    Pipe.SCH: pipedata._get(Pipe.SCH).values[0],
                    Pipe.DIA: pipedata._get(Pipe.NBD).values[0],
                },
            )
            print(f"  ✓ {pipe_name} → {pms_code}")
        except Exception as e:
            print(f"  ✗ Failed to assign {pms_code} to {pipe_name}: {e}")


def validate_pms_assignments(model: Model) -> dict[str, list[str]]:
    """Validate PMS assignments in the model.

    Returns:
        Dictionary with validation results.
    """
    print("\n" + "=" * 60)
    print("Validating PMS Assignments")
    print("=" * 60)

    results = {
        "valid": [],
        "missing_pms": [],
        "incomplete": [],
    }

    for idx, pipe in model.pipes.items():
        if idx == 0:  # Skip template
            continue

        # Check if pipe has material
        mat_rec = pipe._get(Pipe.MAT)
        sch_rec = pipe._get(Pipe.SCH)

        if not mat_rec or not mat_rec.values[0]:
            results["missing_pms"].append(pipe.name)
            print(f"  ⚠ {pipe.name}: No material assigned")
        elif not sch_rec or not sch_rec.values[0]:
            results["incomplete"].append(pipe.name)
            print(f"  ⚠ {pipe.name}: Material but no schedule")
        else:
            results["valid"].append(pipe.name)
            print(f"  ✓ {pipe.name}: {mat_rec.values[0]} Sch {sch_rec.values[0]}")

    print(
        f"\n  Summary: {len(results['valid'])} valid, "
        f"{len(results['missing_pms'])} missing, "
        f"{len(results['incomplete'])} incomplete"
    )

    return results


if __name__ == "__main__":
    # Step 1: Create sample PMS data file
    create_sample_pms_excel("examples/output/pms_data.xlsx")
    create_sample_pms_json("examples/output/pms_data.json")

    # Step 2: Create or load a model
    print("\n" + "=" * 60)
    print("Creating Model for PMS Demo")
    print("=" * 60)

    # Try to load existing pump circuit, or create new
    try:
        model = Model("examples/output/pump_circuit.kdf")
        print("  ✓ Loaded existing pump circuit model")
    except FileNotFoundError:
        print("  Creating new blank model...")
        model = Model()
        # Add a sample pipe for demonstration
        from pykorf.definitions import Element

        model.add_element(Element.PIPE, "SAMPLE_PIPE")

    # Step 3: Read PMS data
    try:
        pms_specs = read_pms_from_excel("examples/output/pms_data.xlsx")
    except ImportError:
        print("  (Falling back to JSON)")
        pms_specs = read_pms_from_json("examples/output/pms_data.json")

    # Step 4: Add PMS to model
    created_pms = add_pms_to_model(model, pms_specs)

    # Step 5: Assign PMS to pipes (if we have the pump circuit)
    if "SUCT_L1" in [p.name for p in model.pipes.values()]:
        pipe_assignments = {
            "SUCT_L1": "CS-40-6",  # Suction: Carbon Steel, Sch 40, 6"
            "DISC_L2": "CS-80-4",  # Discharge: Carbon Steel, Sch 80, 4"
            "COOL_L3": "SS-40-4",  # Cooler line: Stainless Steel
            "RETURN_L4": "CS-40-6",  # Return: Carbon Steel
        }
        assign_pms_to_pipes(model, pipe_assignments)

    # Step 6: Validate
    validate_pms_assignments(model)

    # Step 7: Save
    output_path = "examples/output/pump_circuit_with_pms.kdf"
    model.save_as(output_path)
    print(f"\n  ✓ Model with PMS saved to: {output_path}")
