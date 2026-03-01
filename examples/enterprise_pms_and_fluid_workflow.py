#!/usr/bin/env python3
"""Enterprise Workflow: PMS Schedule Update + Fluid Properties Import.

This example demonstrates a complete enterprise workflow that:
1. Loads a KDF hydraulic model
2. Updates pipe schedules based on PMS codes from Line Notes
3. Imports fluid properties from Excel (simulation data)
4. Validates the updates
5. Saves the updated model

Usage:
    python enterprise_pms_and_fluid_workflow.py \
        --kdf "input.kdf" \
        --pms-excel "pms_data.xlsx" \
        --fluid-excel "fluid_data.xlsx" \
        --output "updated_model.kdf" \
        --dry-run

Requirements:
    - pykorf
    - pandas
    - openpyxl
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from pykorf import Model
from pykorf.definitions import Pipe
from pykorf.log import get_logger, log_operation

logger = get_logger()


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class PMSSpecification:
    """PMS specification data."""

    code: str
    nominal_size: float
    od_inch: float
    schedule: str
    id_inch: float
    material: str
    wall_thickness_mm: float | None = None


@dataclass
class FluidProperties:
    """Fluid properties for a single case."""

    temp: list[float]  # [inlet, outlet, average]
    pres: list[float]  # [inlet, outlet, average]
    lf: list[float]  # [inlet, outlet, average] - liquid fraction
    liqden: float
    liqvisc: float
    liqsur: float
    liqcon: float = 0.5
    liqcp: float = 1.0
    liqmw: float = 18.0
    vapden: float = 0.0
    vapvisc: float = 0.0
    vapcon: float = 0.025
    vapcp: float = 1.0
    vapmw: float = 0.0
    vapz: float = 0.0


# =============================================================================
# PMS Workflow Functions
# =============================================================================


def extract_pms_code(notes: str) -> str | None:
    """Extract PMS code from NOTES parameter.

    Format: "PMS:<CODE>;" where CODE is the PMS specification code.

    Examples:
        >>> extract_pms_code("PMS:PMS-A11-CS2; LINE-001;")
        'PMS-A11-CS2'
        >>> extract_pms_code("LINE-001; SERVICE:COOLING;")
        None
    """
    if not notes or "PMS:" not in notes:
        return None

    start = notes.find("PMS:") + 4
    end = notes.find(";", start)

    if end == -1:
        return notes[start:].strip()
    return notes[start:end].strip()


def load_pms_master(excel_path: Path) -> dict[str, PMSSpecification]:
    """Load PMS master data from Excel.

    Args:
        excel_path: Path to Excel file with PMS_Master sheet

    Returns:
        Dictionary mapping PMS_Code to PMSSpecification
    """
    logger.info("Loading PMS master data", file=str(excel_path))

    df = pd.read_excel(excel_path, sheet_name="PMS_Master")

    # Validate required columns
    required = ["PMS_Code", "Nominal_Size", "OD_inch", "Schedule", "ID_inch"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in PMS_Master: {missing}")

    pms_data = {}
    for _, row in df.iterrows():
        spec = PMSSpecification(
            code=row["PMS_Code"],
            nominal_size=float(row["Nominal_Size"]),
            od_inch=float(row["OD_inch"]),
            schedule=str(row["Schedule"]),
            id_inch=float(row["ID_inch"]),
            material=row.get("Material", "Steel"),
            wall_thickness_mm=float(row["Wall_Thickness_mm"])
            if "Wall_Thickness_mm" in row and pd.notna(row["Wall_Thickness_mm"])
            else None,
        )
        pms_data[spec.code] = spec

    logger.info("PMS master loaded", count=len(pms_data))
    return pms_data


def inch_to_meter(inch: float) -> float:
    """Convert inches to meters."""
    return inch * 0.0254


def update_pipe_schedule(
    model: Model,
    line_name: str,
    pms_spec: PMSSpecification,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Update pipe parameters based on PMS specification.

    Args:
        model: KorfModel instance
        line_name: Name of the pipe element
        pms_spec: PMS specification
        dry_run: If True, only report changes without applying

    Returns:
        Update result dictionary
    """
    pipe = model.get_element(line_name)

    # Prepare updates
    updates = {
        Pipe.DIA: str(int(pms_spec.nominal_size))
        if pms_spec.nominal_size == int(pms_spec.nominal_size)
        else str(pms_spec.nominal_size),
        Pipe.SCH: pms_spec.schedule,
        Pipe.ID: inch_to_meter(pms_spec.id_inch),
        Pipe.ODF: inch_to_meter(pms_spec.od_inch),
        Pipe.MAT: pms_spec.material,
    }

    # Get current values for reporting
    old_values = {param: pipe.get_param(param, "N/A") for param in updates}

    if not dry_run:
        for param, value in updates.items():
            pipe.set_param(param, value)

    return {
        "line": line_name,
        "pms_code": pms_spec.code,
        "old_values": old_values,
        "new_values": updates,
        "dry_run": dry_run,
    }


# =============================================================================
# Fluid Properties Functions
# =============================================================================


def load_fluid_properties(excel_path: Path) -> dict[str, dict[int, FluidProperties]]:
    """Load fluid properties from Excel.

    Args:
        excel_path: Path to Excel file with Fluid_Properties sheet

    Returns:
        Dictionary mapping line names to case-indexed fluid properties
    """
    logger.info("Loading fluid properties", file=str(excel_path))

    df = pd.read_excel(excel_path, sheet_name="Fluid_Properties")

    fluid_data: dict[str, dict[int, FluidProperties]] = {}

    for _, row in df.iterrows():
        line_name = str(row["Line_Name"]).strip()
        case = int(row["Case"]) - 1  # Convert to 0-based index

        if line_name not in fluid_data:
            fluid_data[line_name] = {}

        props = FluidProperties(
            temp=[
                float(row["Temp_In"]),
                float(row["Temp_Out"]),
                float(row["Temp_Avg"]),
            ],
            pres=[
                float(row["Pres_In"]),
                float(row["Pres_Out"]),
                float(row["Pres_Avg"]),
            ],
            lf=[float(row["LF_In"]), float(row["LF_Out"]), float(row["LF_Avg"])],
            liqden=float(row["LiqDen"]),
            liqvisc=float(row["LiqVisc"]),
            liqsur=float(row.get("LiqSur", 62.4)),
            liqcon=float(row.get("LiqCon", 0.5)),
            liqcp=float(row.get("LiqCp", 1.0)),
            liqmw=float(row.get("LiqMW", 18.0)),
            vapden=float(row.get("VapDen", 0.0)),
            vapvisc=float(row.get("VapVisc", 0.0)),
            vapcon=float(row.get("VapCon", 0.025)),
            vapcp=float(row.get("VapCp", 1.0)),
            vapmw=float(row.get("VapMW", 0.0)),
            vapz=float(row.get("VapZ", 0.0)),
        )

        fluid_data[line_name][case] = props

    logger.info("Fluid properties loaded", lines=len(fluid_data))
    return fluid_data


def apply_fluid_properties(
    model: Model,
    line_name: str,
    case_props: dict[int, FluidProperties],
    num_cases: int,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Apply fluid properties to a pipe element.

    Args:
        model: KorfModel instance
        line_name: Name of the pipe
        case_props: Dictionary mapping case index to FluidProperties
        num_cases: Total number of cases in model
        dry_run: If True, only report changes

    Returns:
        Update result dictionary
    """
    pipe = model.get_element(line_name)

    # Initialize arrays for multi-case parameters
    temp_array = [25.0] * num_cases
    pres_array = [100.0] * num_cases
    lf_array = [1.0] * num_cases

    # Fill arrays from case data
    for case_idx, props in case_props.items():
        if 0 <= case_idx < num_cases:
            temp_array[case_idx] = props.temp[2]  # Use average
            pres_array[case_idx] = props.pres[2]  # Use average
            lf_array[case_idx] = props.lf[2]  # Use average

    # Get base properties from first case for single-value parameters
    base_props = case_props.get(0, list(case_props.values())[0])

    if not dry_run:
        # Apply multi-case parameters
        pipe.set_param(Pipe.TEMP, temp_array)
        pipe.set_param(Pipe.PRES, pres_array)
        pipe.set_param(Pipe.LF, lf_array)

        # Apply single-value liquid properties
        pipe.set_param(Pipe.LIQDEN, base_props.liqden)
        pipe.set_param(Pipe.LIQVISC, base_props.liqvisc)
        pipe.set_param(Pipe.LIQSUR, base_props.liqsur)
        pipe.set_param(Pipe.LIQCON, base_props.liqcon)
        pipe.set_param(Pipe.LIQCP, base_props.liqcp)
        pipe.set_param(Pipe.LIQMW, base_props.liqmw)

        # Apply single-value vapor properties
        pipe.set_param(Pipe.VAPDEN, base_props.vapden)
        pipe.set_param(Pipe.VAPVISC, base_props.vapvisc)
        pipe.set_param(Pipe.VAPCON, base_props.vapcon)
        pipe.set_param(Pipe.VAPCP, base_props.vapcp)
        pipe.set_param(Pipe.VAPMW, base_props.vapmw)
        pipe.set_param(Pipe.VAPZ, base_props.vapz)

    return {
        "line": line_name,
        "status": "updated",
        "cases_updated": len(case_props),
        "temp_range": [min(temp_array), max(temp_array)],
        "pres_range": [min(pres_array), max(pres_array)],
        "dry_run": dry_run,
    }


# =============================================================================
# Main Workflow
# =============================================================================


def run_pms_workflow(
    model: Model,
    pms_excel: Path,
    dry_run: bool = False,
) -> list[dict]:
    """Run the PMS update workflow.

    Args:
        model: Loaded KorfModel
        pms_excel: Path to PMS Excel file
        dry_run: If True, simulate only

    Returns:
        List of update results
    """
    logger.info("Starting PMS workflow")

    # Load PMS master data
    pms_master = load_pms_master(pms_excel)

    results = []
    skipped = []
    not_found = []

    # Process each pipe
    for pipe in model.pipes.values():
        if pipe.index == 0:  # Skip template
            continue

        notes = pipe.get_param(Pipe.NOTES, "")
        pms_code = extract_pms_code(notes)

        if not pms_code:
            skipped.append(pipe.name)
            continue

        if pms_code not in pms_master:
            not_found.append((pipe.name, pms_code))
            logger.warning("PMS code not found", line=pipe.name, pms_code=pms_code)
            continue

        # Update pipe
        result = update_pipe_schedule(model, pipe.name, pms_master[pms_code], dry_run)
        results.append(result)

        logger.info(
            "Pipe schedule updated",
            line=pipe.name,
            pms_code=pms_code,
            schedule=pms_master[pms_code].schedule,
        )

    logger.info(
        "PMS workflow complete",
        updated=len(results),
        skipped=len(skipped),
        not_found=len(not_found),
    )

    return results


def run_fluid_workflow(
    model: Model,
    fluid_excel: Path,
    dry_run: bool = False,
) -> list[dict]:
    """Run the fluid properties import workflow.

    Args:
        model: Loaded KorfModel
        fluid_excel: Path to fluid properties Excel file
        dry_run: If True, simulate only

    Returns:
        List of update results
    """
    logger.info("Starting fluid properties workflow")

    # Load fluid properties
    fluid_data = load_fluid_properties(fluid_excel)

    # Determine number of cases from model
    gen = model.get_element("GEN")
    case_no = gen.get_param("CASENO", "1")
    if isinstance(case_no, str) and ";" in case_no:
        num_cases = len(case_no.split(";"))
    else:
        num_cases = 1

    logger.info("Model cases detected", num_cases=num_cases)

    results = []
    not_found = []

    # Apply properties
    for line_name, case_props in fluid_data.items():
        try:
            result = apply_fluid_properties(
                model, line_name, case_props, num_cases, dry_run
            )
            results.append(result)

            if result["status"] == "updated":
                logger.info(
                    "Fluid properties applied",
                    line=line_name,
                    cases=result["cases_updated"],
                )
        except Exception as e:
            logger.error("Failed to apply properties", line=line_name, error=str(e))
            not_found.append(line_name)

    logger.info(
        "Fluid workflow complete",
        updated=len(results),
        not_found=len(not_found),
    )

    return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Update KDF model with PMS schedules and fluid properties"
    )
    parser.add_argument("--kdf", required=True, help="Input KDF file path")
    parser.add_argument("--pms-excel", help="PMS Excel file path")
    parser.add_argument("--fluid-excel", help="Fluid properties Excel file path")
    parser.add_argument("--output", "-o", help="Output KDF file path")
    parser.add_argument(
        "--dry-run", action="store_true", help="Simulate without saving changes"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    args = parser.parse_args()

    if not args.pms_excel and not args.fluid_excel:
        parser.error("At least one of --pms-excel or --fluid-excel must be provided")

    with log_operation("enterprise_workflow"):
        # Load model
        logger.info("Loading KDF model", file=args.kdf)
        model = Model(args.kdf)
        logger.info("Model loaded", version=model.version)

        all_results = []

        # Run PMS workflow
        if args.pms_excel:
            pms_results = run_pms_workflow(model, Path(args.pms_excel), args.dry_run)
            all_results.extend(pms_results)
            print(f"\n{'=' * 60}")
            print(f"PMS Workflow: {len(pms_results)} pipes updated")
            print(f"{'=' * 60}")
            for r in pms_results[:5]:  # Show first 5
                print(
                    f"  {r['line']}: {r['pms_code']} -> "
                    f"DIA={r['new_values'][Pipe.DIA]}, "
                    f"SCH={r['new_values'][Pipe.SCH]}"
                )
            if len(pms_results) > 5:
                print(f"  ... and {len(pms_results) - 5} more")

        # Run fluid properties workflow
        if args.fluid_excel:
            fluid_results = run_fluid_workflow(
                model, Path(args.fluid_excel), args.dry_run
            )
            all_results.extend(fluid_results)
            print(f"\n{'=' * 60}")
            print(f"Fluid Properties Workflow: {len(fluid_results)} lines updated")
            print(f"{'=' * 60}")
            for r in fluid_results[:5]:
                print(
                    f"  {r['line']}: T={r['temp_range'][0]:.1f}-{r['temp_range'][1]:.1f}°C, "
                    f"Cases={r['cases_updated']}"
                )
            if len(fluid_results) > 5:
                print(f"  ... and {len(fluid_results) - 5} more")

        # Save model
        if not args.dry_run and args.output:
            model.save_as(args.output)
            logger.info("Model saved", output=args.output)
            print(f"\n{'=' * 60}")
            print(f"Model saved to: {args.output}")
            print(f"{'=' * 60}")
        elif args.dry_run:
            print(f"\n{'=' * 60}")
            print("DRY RUN - No changes saved")
            print(f"{'=' * 60}")

        print(f"\nTotal updates: {len(all_results)}")


if __name__ == "__main__":
    main()
