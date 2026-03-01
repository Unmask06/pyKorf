"""Example 4: Multi-Case Analysis Workflow.

This example demonstrates:
- Setting up multiple simulation cases
- Configuring case-specific parameters
- Running batch analyses
- Comparing results across cases
- Generating case comparison reports
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pykorf import CaseSet, Model
from pykorf.definitions import Feed, Pipe, Prod


def setup_multicase_scenarios(
    model: Model,
    scenarios: list[dict[str, Any]] | None = None,
) -> CaseSet:
    """Set up multiple simulation scenarios.
    
    Args:
        model: The KORF model.
        scenarios: List of scenario dictionaries. If None, uses defaults.
        
    Returns:
        CaseSet configured with the scenarios.
        
    Example:
        ```python
        scenarios = [
            {"name": "MIN", "flow": 50, "pressure": 80},
            {"name": "NORM", "flow": 100, "pressure": 100},
            {"name": "MAX", "flow": 150, "pressure": 120},
        ]
        cases = setup_multicase_scenarios(model, scenarios)
        ```
    """
    print("=" * 60)
    print("Setting Up Multi-Case Scenarios")
    print("=" * 60)

    if scenarios is None:
        # Default scenarios for a pump circuit
        scenarios = [
            {
                "name": "MIN_LOAD",
                "description": "Minimum operating load",
                "feed_pressure": 90,
                "product_pressure": 45,
                "pump_speed": 80,  # %
                "pipe_flows": [40, 50, 30],  # Different flows per pipe
            },
            {
                "name": "NORMAL",
                "description": "Normal operating conditions",
                "feed_pressure": 100,
                "product_pressure": 50,
                "pump_speed": 100,
                "pipe_flows": [80, 100, 60],
            },
            {
                "name": "PEAK",
                "description": "Peak demand conditions",
                "feed_pressure": 110,
                "product_pressure": 55,
                "pump_speed": 110,
                "pipe_flows": [120, 150, 90],
            },
            {
                "name": "EMERGENCY",
                "description": "Emergency bypass operation",
                "feed_pressure": 120,
                "product_pressure": 40,
                "pump_speed": 120,
                "pipe_flows": [150, 100, 120],
            },
        ]

    # Set case names in the model
    case_names = [s["name"] for s in scenarios]
    model.general.case_descriptions = case_names
    print(f"  Created {len(case_names)} cases: {case_names}")

    # Get pipe names
    pipe_names = [p.name for p in model.pipes.values() if p.index > 0]
    print(f"  Found {len(pipe_names)} pipes to configure")

    # Configure each case
    for case_idx, scenario in enumerate(scenarios, 1):
        print(f"\n  [{case_idx}/{len(scenarios)}] Configuring: {scenario['name']}")
        print(f"    Description: {scenario.get('description', 'N/A')}")

        # Build semicolon-delimited strings for multi-case values
        # Format: case1;case2;case3;case4

        # Feed pressure
        feed_pressures = [str(s.get("feed_pressure", 100)) for s in scenarios]
        feed_pressure_str = ";".join(feed_pressures)

        # Product pressure
        prod_pressures = [str(s.get("product_pressure", 50)) for s in scenarios]
        prod_pressure_str = ";".join(prod_pressures)

        # Apply to feed
        for feed in model.feeds.values():
            if feed.index > 0:
                model.update_element(feed.name, {Feed.PRES: feed_pressure_str})
                print(f"    Feed '{feed.name}': {feed_pressure_str} bara")

        # Apply to product
        for prod in model.products.values():
            if prod.index > 0:
                model.update_element(prod.name, {Prod.PRES: prod_pressure_str})
                print(f"    Product '{prod.name}': {prod_pressure_str} bara")

        # Configure pipe flows
        for pipe_idx, pipe_name in enumerate(pipe_names):
            # Get flows for this pipe across all cases
            pipe_flows = []
            for s in scenarios:
                flows = s.get("pipe_flows", [100] * len(scenarios))
                # Use pipe-specific flow or default
                flow_val = flows[pipe_idx] if pipe_idx < len(flows) else flows[0]
                pipe_flows.append(str(flow_val))

            flow_str = ";".join(pipe_flows)
            model.update_element(pipe_name, {Pipe.TFLOW: flow_str})
            print(f"    Pipe '{pipe_name}': {flow_str} t/h")

        # Configure pump speed if available
        pump_speeds = [str(s.get("pump_speed", 100)) for s in scenarios]
        pump_speed_str = ";".join(pump_speeds)
        for pump in model.pumps.values():
            if pump.index > 0:
                # Note: Pump speed parameter depends on pump model
                try:
                    model.update_element(pump.name, {"SPEED": pump_speed_str})
                    print(f"    Pump '{pump.name}': {pump_speed_str}% speed")
                except Exception:
                    pass  # Speed parameter might not exist

    # Create and return CaseSet
    cases = CaseSet(model)
    print(f"\n  ✓ CaseSet configured: {cases.count} cases")

    # Activate all cases
    cases.activate_cases(list(range(1, cases.count + 1)))
    print("  ✓ All cases activated")

    return cases


def generate_case_comparison_table(
    model: Model,
    cases: CaseSet,
    output_format: str = "markdown",
) -> str:
    """Generate a comparison table of all cases.
    
    Args:
        model: The KORF model.
        cases: The CaseSet.
        output_format: "markdown", "csv", or "html".
        
    Returns:
        Formatted comparison table.
    """
    print("\n" + "=" * 60)
    print("Generating Case Comparison Table")
    print("=" * 60)

    # Collect data for each case
    headers = ["Parameter"] + cases.names
    rows = []

    # Feed pressures
    for feed in model.feeds.values():
        if feed.index > 0:
            pres_rec = feed._get(Feed.PRES)
            if pres_rec:
                values = pres_rec.values if pres_rec.values else ["N/A"] * cases.count
                # Pad if needed
                while len(values) < cases.count:
                    values.append(values[-1] if values else "N/A")
                rows.append([f"Feed '{feed.name}' Pressure (bara)"] + list(values[:cases.count]))

    # Product pressures
    for prod in model.products.values():
        if prod.index > 0:
            pres_rec = prod._get(Prod.PRES)
            if pres_rec:
                values = pres_rec.values if pres_rec.values else ["N/A"] * cases.count
                while len(values) < cases.count:
                    values.append(values[-1] if values else "N/A")
                rows.append([f"Product '{prod.name}' Pressure (bara)"] + list(values[:cases.count]))

    # Pipe flows
    for pipe in model.pipes.values():
        if pipe.index > 0:
            flow_rec = pipe._get(Pipe.TFLOW)
            if flow_rec:
                values = flow_rec.values if flow_rec.values else ["N/A"] * cases.count
                while len(values) < cases.count:
                    values.append(values[-1] if values else "N/A")
                rows.append([f"Pipe '{pipe.name}' Flow (t/h)"] + list(values[:cases.count]))

    # Generate output
    if output_format == "markdown":
        # Header
        result = "| " + " | ".join(headers) + " |\n"
        # Separator
        result += "|" + "|".join([" --- " for _ in headers]) + "|\n"
        # Rows
        for row in rows:
            result += "| " + " | ".join(row) + " |\n"

    elif output_format == "csv":
        result = ",".join(headers) + "\n"
        for row in rows:
            result += ",".join(row) + "\n"

    elif output_format == "html":
        result = "<table>\n<thead>\n<tr>"
        for h in headers:
            result += f"<th>{h}</th>"
        result += "</tr>\n</thead>\n<tbody>\n"
        for row in rows:
            result += "<tr>"
            for cell in row:
                result += f"<td>{cell}</td>"
            result += "</tr>\n"
        result += "</tbody>\n</table>"

    else:
        result = "Unsupported format"

    print(f"  ✓ Generated {output_format} table with {len(rows)} parameters")
    return result


def export_case_data(
    model: Model,
    cases: CaseSet,
    output_dir: str = "examples/output/case_data",
) -> dict[str, Path]:
    """Export case data to various formats.
    
    Args:
        model: The KORF model.
        cases: The CaseSet.
        output_dir: Directory for output files.
        
    Returns:
        Dictionary of exported file paths.
    """
    print("\n" + "=" * 60)
    print("Exporting Case Data")
    print("=" * 60)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    exported = {}

    # Export comparison table
    md_table = generate_case_comparison_table(model, cases, "markdown")
    md_path = output_path / "case_comparison.md"
    md_path.write_text(md_table)
    exported["markdown"] = md_path
    print(f"  ✓ Markdown table: {md_path}")

    csv_table = generate_case_comparison_table(model, cases, "csv")
    csv_path = output_path / "case_comparison.csv"
    csv_path.write_text(csv_table)
    exported["csv"] = csv_path
    print(f"  ✓ CSV table: {csv_path}")

    # Export per-case parameter files
    for case_idx, case_name in enumerate(cases.names, 1):
        case_data = {
            "case_name": case_name,
            "case_number": case_idx,
            "parameters": {}
        }

        # Collect parameters for this case
        for pipe in model.pipes.values():
            if pipe.index > 0:
                flow_rec = pipe._get(Pipe.TFLOW)
                if flow_rec and flow_rec.values:
                    flow_val = cases.get_case_value(
                        ";".join(flow_rec.values), case_idx
                    )
                    case_data["parameters"][f"{pipe.name}_flow"] = flow_val

        # Save as JSON
        import json
        json_path = output_path / f"case_{case_idx:02d}_{case_name}.json"
        json_path.write_text(json.dumps(case_data, indent=2))

    print(f"  ✓ Individual case files: {output_path}/case_*.json")

    return exported


def analyze_case_sensitivity(
    model: Model,
    cases: CaseSet,
    parameter: str = "flow",
) -> dict[str, float]:
    """Analyze sensitivity of parameter across cases.
    
    Args:
        model: The KORF model.
        cases: The CaseSet.
        parameter: Parameter to analyze ("flow", "pressure", etc.).
        
    Returns:
        Dictionary with min, max, avg, and variation.
    """
    print("\n" + "=" * 60)
    print(f"Case Sensitivity Analysis: {parameter}")
    print("=" * 60)

    values = []

    if parameter == "flow":
        for pipe in model.pipes.values():
            if pipe.index > 0:
                flow_rec = pipe._get(Pipe.TFLOW)
                if flow_rec and flow_rec.values:
                    for case_idx in range(1, cases.count + 1):
                        val = cases.get_case_value(
                            ";".join(flow_rec.values), case_idx
                        )
                        try:
                            values.append(float(val))
                        except (ValueError, TypeError):
                            pass

    if not values:
        print("  No data available for analysis")
        return {}

    import statistics

    analysis = {
        "min": min(values),
        "max": max(values),
        "mean": statistics.mean(values),
        "stdev": statistics.stdev(values) if len(values) > 1 else 0,
        "variation": (max(values) - min(values)) / statistics.mean(values) * 100,
    }

    print(f"  Min: {analysis['min']:.2f}")
    print(f"  Max: {analysis['max']:.2f}")
    print(f"  Mean: {analysis['mean']:.2f}")
    print(f"  StdDev: {analysis['stdev']:.2f}")
    print(f"  Variation: {analysis['variation']:.1f}%")

    return analysis


if __name__ == "__main__":
    # Load or create model
    print("=" * 60)
    print("Multi-Case Analysis Demo")
    print("=" * 60)

    try:
        model = Model("examples/output/pump_circuit.kdf")
        print("  ✓ Loaded pump circuit model")
    except FileNotFoundError:
        print("  ⚠ Pump circuit not found. Run 01_create_pump_circuit.py first")
        exit(1)

    # Setup multi-case scenarios
    cases = setup_multicase_scenarios(model)

    # Generate comparison table
    print("\n" + generate_case_comparison_table(model, cases, "markdown"))

    # Export case data
    exported_files = export_case_data(model, cases)

    # Sensitivity analysis
    analyze_case_sensitivity(model, cases, "flow")

    # Save the multi-case model
    output_path = "examples/output/pump_circuit_multicase.kdf"
    model.save_as(output_path)
    print(f"\n  ✓ Multi-case model saved to: {output_path}")

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"  Cases: {cases.count}")
    print(f"  Case Names: {cases.names}")
    print(f"  Exported files: {len(exported_files)}")
