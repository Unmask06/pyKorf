"""Example 1: Create a Basic Pump Circuit with Heat Exchanger.

This example demonstrates creating a complete hydraulic circuit from scratch:
- Feed source
- Pump
- Heat exchanger (cooler)
- Control valve
- Product sink

The circuit represents a typical cooling loop where fluid is pumped through
a heat exchanger and returned.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pykorf import Model
from pykorf.elements import Element, Feed, Pipe, Prod, Pump, Valve

if TYPE_CHECKING:
    from pathlib import Path


def create_pump_circuit(
    output_path: str | Path = "pump_circuit.kdf",
    flow_rate: float = 100.0,
    feed_pressure: float = 100.0,
) -> Model:
    """Create a pump circuit with heat exchanger.

    Args:
        output_path: Where to save the KDF file.
        flow_rate: Design flow rate in t/h.
        feed_pressure: Feed pressure in bara.

    Returns:
        The created Model instance.

    Example:
        ```python
        model = create_pump_circuit("my_circuit.kdf", flow_rate=150.0)
        ```
    """
    print("=" * 60)
    print("Creating Pump Circuit with Heat Exchanger")
    print("=" * 60)

    # Create blank model from defaults
    model = Model()
    print(f"Created blank model (version: {model.version})")

    # ===================================================================
    # Step 1: Add Feed Source
    # ===================================================================
    print("\n[1/6] Adding Feed Source...")
    model.add_element(
        Element.FEED,
        "FEED_01",
        {
            Feed.PRES: str(feed_pressure),  # Feed pressure in bara
            # Note: Temperature is typically set on pipes, not feeds
        },
    )
    print(f"  [OK] Added feed 'FEED_01' @ {feed_pressure} bara")

    # ===================================================================
    # Step 2: Add Pump
    # ===================================================================
    print("\n[2/6] Adding Pump...")
    model.add_element(
        Element.PUMP,
        "PUMP_01",
        {
            Pump.TYPE: "Centrifugal",
            Pump.EFFP: "0.75",  # Pump efficiency
            Pump.DP: "5.0",  # Differential pressure (bar)
        },
    )
    print("  [OK] Added centrifugal pump 'PUMP_01' (75% eff, 5 bar dP)")

    # ===================================================================
    # Step 3: Add Heat Exchanger (Cooler)
    # ===================================================================
    # Note: Using generic element with appropriate parameters
    print("\n[3/6] Adding Heat Exchanger...")
    model.add_element(
        Element.HX,
        "COOLER_01",
        {
            "TYPE": "Shell & Tube",  # Heat exchanger type
            "DT": "10",  # Temperature difference
        },
    )
    print("  [OK] Added shell & tube heat exchanger 'COOLER_01'")

    # ===================================================================
    # Step 4: Add Control Valve
    # ===================================================================
    print("\n[4/6] Adding Control Valve...")
    model.add_element(
        Element.VALVE,
        "CV_01",
        {
            Valve.TYPE: "Linear",
            Valve.CV: "50",  # Valve coefficient
            Valve.OPEN: "75",  # Opening percentage
        },
    )
    print("  [OK] Added linear control valve 'CV_01' @ 75% open")

    # ===================================================================
    # Step 5: Add Product Sink
    # ===================================================================
    print("\n[5/6] Adding Product Sink...")
    model.add_element(
        Element.PROD,
        "PROD_01",
        {
            Prod.PRES: "50",  # Back pressure in bara
        },
    )
    print("  [OK] Added product sink 'PROD_01' @ 50 bara")

    # ===================================================================
    # Step 6: Connect Elements with Pipes
    # ===================================================================
    print("\n[6/6] Connecting elements with pipes...")

    # Connect Feed -> Pump
    model.connect_elements("FEED_01", "PUMP_01", pipe_name="SUCT_L1")
    print("  [OK] Connected FEED_01 -> SUCT_L1 -> PUMP_01")

    # Connect Pump -> Cooler
    model.connect_elements("PUMP_01", "COOLER_01", pipe_name="DISC_L2")
    print("  [OK] Connected PUMP_01 -> DISC_L2 -> COOLER_01")

    # Connect Cooler -> Valve
    model.connect_elements("COOLER_01", "CV_01", pipe_name="COOL_L3")
    print("  [OK] Connected COOLER_01 -> COOL_L3 -> CV_01")

    # Connect Valve -> Product
    model.connect_elements("CV_01", "PROD_01", pipe_name="RETURN_L4")
    print("  [OK] Connected CV_01 -> RETURN_L4 -> PROD_01")

    # Set flow rates for all pipes
    for pipe_name in ["SUCT_L1", "DISC_L2", "COOL_L3", "RETURN_L4"]:
        model.update_element(
            pipe_name,
            {Pipe.TFLOW: str(flow_rate)},  # Total flow in t/h
        )
    print(f"  [OK] Set flow rate to {flow_rate} t/h for all pipes")

    # ===================================================================
    # Step 7: Set Pipe Properties
    # ===================================================================
    print("\n[7/7] Setting pipe properties...")
    pipe_specs = {
        "SUCT_L1": {Pipe.LEN: "2", Pipe.DIA: "6", Pipe.SCH: "40"},  # Suction: short, large
        "DISC_L2": {Pipe.LEN: "5", Pipe.DIA: "4", Pipe.SCH: "40"},  # Discharge: medium
        "COOL_L3": {Pipe.LEN: "8", Pipe.DIA: "4", Pipe.SCH: "40"},  # Cooler transfer
        "RETURN_L4": {Pipe.LEN: "15", Pipe.DIA: "6", Pipe.SCH: "40"},  # Return: longer
    }

    for pipe_name, specs in pipe_specs.items():
        model.update_element(pipe_name, specs)
        print(f'  [OK] Set {pipe_name}: L={specs[Pipe.LEN]}m, D={specs[Pipe.DIA]}"')

    # ===================================================================
    # Validation & Save
    # ===================================================================
    print("\n" + "=" * 60)
    print("Validating model...")
    issues = model.validate()

    if issues:
        print(f"  [WARN] Found {len(issues)} validation issue(s):")
        for issue in issues[:5]:  # Show first 5
            print(f"    - {issue}")
    else:
        print("  [OK] Model validation passed!")

    # Check connectivity
    print("\nChecking connectivity...")
    conn_issues = model.check_connectivity()
    if conn_issues:
        print(f"  [WARN] Connectivity issues: {conn_issues}")
    else:
        print("  [OK] All elements properly connected!")

    # Save the model
    model.save_as(output_path)
    print(f"\n  [OK] Model saved to: {output_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("Circuit Summary")
    print("=" * 60)
    summary = model.summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")

    return model


def add_multicase_support(model: Model, case_names: list[str] | None = None) -> None:
    """Add multi-case support to the pump circuit.

    Args:
        model: The pump circuit model.
        case_names: List of case names (default: ["MIN", "NORM", "MAX"]).
    """
    from pykorf import CaseSet

    if case_names is None:
        case_names = ["MIN", "NORM", "MAX"]

    print("\n" + "=" * 60)
    print("Adding Multi-Case Support")
    print("=" * 60)

    cases = CaseSet(model)

    # Set case names using the proper method
    case_numbers = list(range(1, len(case_names) + 1))
    model.general.set_cases(case_numbers, case_names)
    print(f"  Cases: {cases.names}")

    # Set different flow rates for each case
    # Format: value1;value2;value3
    flow_scenarios = {
        "MIN": "50;100;150",  # 50 t/h min, 100 t/h norm, 150 t/h max
        "NORM": "75;150;225",  # 75 t/h min, 150 t/h norm, 225 t/h max
        "MAX": "100;200;300",  # 100 t/h min, 200 t/h norm, 300 t/h max
    }

    # Update main pipe flow
    for pipe_name in ["SUCT_L1", "DISC_L2", "COOL_L3", "RETURN_L4"]:
        # Get current single value
        current = flow_scenarios.get(pipe_name[:3], "100;150;200")
        model.update_element(pipe_name, {Pipe.TFLOW: current})

    print(f"  [OK] Set multi-case flows for {len(case_names)} cases")

    # Activate all cases
    cases.activate_cases(list(range(1, len(case_names) + 1)))
    print("  [OK] Activated all cases")


if __name__ == "__main__":
    # Create basic pump circuit
    model = create_pump_circuit(
        output_path="examples/output/pump_circuit.kdf",
        flow_rate=150.0,
        feed_pressure=100.0,
    )

    # Add multi-case support
    add_multicase_support(model)

    # Save with multi-case
    model.save_as("examples/output/pump_circuit_multicase.kdf")
    print("\n  [OK] Multi-case model saved to: examples/output/pump_circuit_multicase.kdf")
