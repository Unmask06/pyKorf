"""Example 5: Export and Visualization.

This example demonstrates:
- Exporting models to various formats (JSON, Excel, CSV)
- Creating network visualizations
- Generating reports
- Automating documentation workflows
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pykorf import Model


def export_to_json_detailed(
    model: Model,
    output_path: str | Path,
    include_geometry: bool = True,
    include_results: bool = True,
) -> Path:
    """Export model to detailed JSON format.
    
    Args:
        model: The KORF model.
        output_path: Output file path.
        include_geometry: Include XY positions.
        include_results: Include calculated results.
        
    Returns:
        Path to exported file.
    """
    print("=" * 60)
    print("Exporting to JSON")
    print("=" * 60)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Build comprehensive export structure
    export_data: dict[str, Any] = {
        "metadata": {
            "file": str(model.path) if model.path else "blank",
            "version": model.version,
            "num_cases": model.num_cases,
            "export_options": {
                "include_geometry": include_geometry,
                "include_results": include_results,
            },
        },
        "elements": {},
        "connectivity": [],
    }

    # Export all element types
    element_collections = {
        "general": [model.general] if hasattr(model, "general") else [],
        "pipes": list(model.pipes.values()),
        "pumps": list(model.pumps.values()),
        "valves": list(model.valves.values()),
        "feeds": list(model.feeds.values()),
        "products": list(model.products.values()),
        "exchangers": list(model.exchangers.values()),
        "compressors": list(model.compressors.values()),
        "vessels": list(model.vessels.values()),
        "tees": list(model.tees.values()),
        "junctions": list(model.junctions.values()),
        "fluids": list(model.fluids.values()),
        "pipedata": list(model.pipedata.values()),
    }

    for elem_type, elements in element_collections.items():
        if not elements:
            continue

        export_data["elements"][elem_type] = []
        for elem in elements:
            if elem.index == 0:  # Skip template
                continue

            elem_data = {
                "name": elem.name,
                "index": elem.index,
                "type": elem.etype,
            }

            # Add all records
            elem_data["parameters"] = {}
            for rec in elem._parser.records:
                if rec.element_type == elem.etype and rec.index == elem.index:
                    elem_data["parameters"][rec.param] = {
                        "values": rec.values,
                        "raw": rec.raw_line,
                    }

            # Add geometry if requested
            if include_geometry and elem_type in ["pipes", "pumps", "valves"]:
                try:
                    xy_rec = elem._get("XY")
                    if xy_rec and xy_rec.values:
                        elem_data["geometry"] = {
                            "x": float(xy_rec.values[0]) if len(xy_rec.values) > 0 else 0,
                            "y": float(xy_rec.values[1]) if len(xy_rec.values) > 1 else 0,
                        }
                except Exception:
                    pass

            export_data["elements"][elem_type].append(elem_data)

        print(f"  ✓ Exported {len(export_data['elements'][elem_type])} {elem_type}")

    # Write JSON
    with open(output_path, "w") as f:
        json.dump(export_data, f, indent=2)

    print(f"\n  ✓ JSON export complete: {output_path}")
    print(f"  File size: {output_path.stat().st_size / 1024:.1f} KB")

    return output_path


def export_to_excel(
    model: Model,
    output_path: str | Path,
) -> Path:
    """Export model to Excel workbook with multiple sheets.
    
    Args:
        model: The KORF model.
        output_path: Output file path.
        
    Returns:
        Path to exported file.
        
    Raises:
        ImportError: If pandas/openpyxl not installed.
    """
    import pandas as pd

    print("\n" + "=" * 60)
    print("Exporting to Excel")
    print("=" * 60)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        # Sheet 1: Summary
        summary_data = {
            "Property": ["File", "Version", "Cases", "Pipes", "Pumps", "Valves"],
            "Value": [
                str(model.path) if model.path else "blank",
                model.version,
                model.num_cases,
                model.num_pipes,
                len([p for p in model.pumps.values() if p.index > 0]),
                len([v for v in model.valves.values() if v.index > 0]),
            ],
        }
        pd.DataFrame(summary_data).to_excel(writer, sheet_name="Summary", index=False)
        print("  ✓ Sheet: Summary")

        # Sheet 2: Pipes
        pipes_data = []
        for pipe in model.pipes.values():
            if pipe.index == 0:
                continue
            row = {"Name": pipe.name, "Index": pipe.index}

            # Try to get common parameters
            for param in ["LEN", "DIA", "SCH", "MAT", "TFLOW"]:
                rec = pipe._get(param)
                row[param] = rec.values[0] if rec and rec.values else ""

            pipes_data.append(row)

        if pipes_data:
            pd.DataFrame(pipes_data).to_excel(writer, sheet_name="Pipes", index=False)
            print(f"  ✓ Sheet: Pipes ({len(pipes_data)} rows)")

        # Sheet 3: Pumps
        pumps_data = []
        for pump in model.pumps.values():
            if pump.index == 0:
                continue
            row = {"Name": pump.name, "Index": pump.index}

            for param in ["TYPE", "EFFP", "DIFF"]:
                rec = pump._get(param)
                row[param] = rec.values[0] if rec and rec.values else ""

            pumps_data.append(row)

        if pumps_data:
            pd.DataFrame(pumps_data).to_excel(writer, sheet_name="Pumps", index=False)
            print(f"  ✓ Sheet: Pumps ({len(pumps_data)} rows)")

        # Sheet 4: Equipment Summary
        equipment_summary = []
        for elem_type, collection in [
            ("Feed", model.feeds),
            ("Product", model.products),
            ("Valve", model.valves),
            ("Heat Exchanger", model.exchangers),
        ]:
            for elem in collection.values():
                if elem.index == 0:
                    continue
                equipment_summary.append({
                    "Type": elem_type,
                    "Name": elem.name,
                    "Index": elem.index,
                })

        if equipment_summary:
            pd.DataFrame(equipment_summary).to_excel(
                writer, sheet_name="Equipment", index=False
            )
            print(f"  ✓ Sheet: Equipment ({len(equipment_summary)} rows)")

    print(f"\n  ✓ Excel export complete: {output_path}")
    return output_path


def export_to_csv_separate(
    model: Model,
    output_dir: str | Path,
) -> list[Path]:
    """Export model to separate CSV files per element type.
    
    Args:
        model: The KORF model.
        output_dir: Output directory.
        
    Returns:
        List of exported file paths.
    """
    import csv

    print("\n" + "=" * 60)
    print("Exporting to CSV Files")
    print("=" * 60)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    exported = []

    # Export pipes
    pipes_file = output_dir / "pipes.csv"
    with open(pipes_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "Index", "Length", "Diameter", "Schedule", "Material", "Flow"])

        for pipe in model.pipes.values():
            if pipe.index == 0:
                continue

            len_rec = pipe._get("LEN")
            dia_rec = pipe._get("DIA")
            sch_rec = pipe._get("SCH")
            mat_rec = pipe._get("MAT")
            flow_rec = pipe._get("TFLOW")

            writer.writerow([
                pipe.name,
                pipe.index,
                len_rec.values[0] if len_rec and len_rec.values else "",
                dia_rec.values[0] if dia_rec and dia_rec.values else "",
                sch_rec.values[0] if sch_rec and sch_rec.values else "",
                mat_rec.values[0] if mat_rec and mat_rec.values else "",
                flow_rec.values[0] if flow_rec and flow_rec.values else "",
            ])

    exported.append(pipes_file)
    print(f"  ✓ {pipes_file.name}")

    # Export connectivity
    conn_file = output_dir / "connectivity.csv"
    with open(conn_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["From", "To", "Pipe"])

        # This is a simplified connectivity export
        # Real implementation would parse CON/NOZL records
        for pipe in model.pipes.values():
            if pipe.index == 0:
                continue
            writer.writerow(["Source", "Target", pipe.name])

    exported.append(conn_file)
    print(f"  ✓ {conn_file.name}")

    print(f"\n  ✓ CSV export complete: {len(exported)} files")
    return exported


def create_network_visualization(
    model: Model,
    output_path: str | Path = "network.html",
    title: str = "KORF Network",
) -> Path | None:
    """Create interactive network visualization.
    
    Args:
        model: The KORF model.
        output_path: Output HTML file path.
        title: Graph title.
        
    Returns:
        Path to HTML file if successful, None otherwise.
        
    Raises:
        ImportError: If pyvis not installed.
    """
    try:
        from pyvis.network import Network
    except ImportError:
        print("\n  ⚠ pyvis not installed. Install with: pip install pyvis")
        print("  Creating text-based visualization instead...")
        return create_text_visualization(model, output_path)

    print("\n" + "=" * 60)
    print("Creating Network Visualization")
    print("=" * 60)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Create network
    net = Network(height="800px", width="100%", bgcolor="#ffffff", font_color="#000000")
    net.set_options("""
    {
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -50,
          "centralGravity": 0.01,
          "springLength": 100,
          "springConstant": 0.08
        },
        "maxVelocity": 50,
        "solver": "forceAtlas2Based",
        "timestep": 0.35,
        "stabilization": {"iterations": 150}
      }
    }
    """)

    # Color scheme by element type
    colors = {
        "FEED": "#4CAF50",      # Green
        "PROD": "#F44336",      # Red
        "PUMP": "#2196F3",      # Blue
        "VALVE": "#FF9800",     # Orange
        "PIPE": "#9E9E9E",      # Grey
        "HX": "#9C27B0",        # Purple
        "COMP": "#00BCD4",      # Cyan
        "VESSEL": "#795548",    # Brown
        "TEE": "#607D8B",       # Blue Grey
        "JUNC": "#607D8B",
    }

    # Add nodes for equipment (non-pipes)
    equipment_added = set()
    for collection in [model.feeds, model.products, model.pumps, model.valves,
                       model.exchangers, model.compressors, model.vessels]:
        for elem in collection.values():
            if elem.index == 0 or elem.name in equipment_added:
                continue

            color = colors.get(elem.etype, "#9E9E9E")
            size = 25 if elem.etype in ["PUMP", "COMP"] else 20

            net.add_node(
                elem.name,
                label=f"{elem.name}\n({elem.etype})",
                color=color,
                size=size,
                title=f"Type: {elem.etype}<br>Index: {elem.index}",
            )
            equipment_added.add(elem.name)

    # Add edges for pipes (simplified - actual would parse connectivity)
    for pipe in model.pipes.values():
        if pipe.index == 0:
            continue

        # Try to find connected equipment
        # This is a simplified representation
        connected = []
        for eq_name in equipment_added:
            # Check if pipe name suggests connection (simplified)
            if any(x in pipe.name for x in ["SUCT", "DISC", "IN", "OUT"]):
                connected.append(eq_name)

        if len(connected) >= 2:
            net.add_edge(
                connected[0], connected[1],
                label=pipe.name,
                color="#9E9E9E",
                width=2,
                title=f"Flow: {pipe.flow_string if hasattr(pipe, 'flow_string') else 'N/A'}",
            )

    # Generate HTML
    net.save_graph(str(output_path))
    print(f"  ✓ Network visualization: {output_path}")

    return output_path


def create_text_visualization(
    model: Model,
    output_path: str | Path,
) -> Path:
    """Create a text-based visualization as fallback.
    
    Args:
        model: The KORF model.
        output_path: Output file path.
        
    Returns:
        Path to text file.
    """
    output_path = Path(output_path).with_suffix(".txt")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "=" * 60,
        "KORF MODEL VISUALIZATION",
        "=" * 60,
        "",
        f"Model: {model.path}",
        f"Version: {model.version}",
        f"Cases: {model.num_cases}",
        "",
        "EQUIPMENT:",
        "-" * 60,
    ]

    # List equipment by type
    for elem_type, collection in [
        ("Feeds", model.feeds),
        ("Products", model.products),
        ("Pumps", model.pumps),
        ("Valves", model.valves),
        ("Heat Exchangers", model.exchangers),
    ]:
        items = [e.name for e in collection.values() if e.index > 0]
        if items:
            lines.append(f"\n{elem_type}:")
            for name in items:
                lines.append(f"  - {name}")

    # List pipes
    lines.extend([
        "",
        "PIPES:",
        "-" * 60,
    ])
    for pipe in model.pipes.values():
        if pipe.index > 0:
            lines.append(f"  - {pipe.name}")

    # Write file
    output_path.write_text("\n".join(lines))
    print(f"  ✓ Text visualization: {output_path}")

    return output_path


def generate_report(
    model: Model,
    output_path: str | Path = "report.md",
) -> Path:
    """Generate a markdown report of the model.
    
    Args:
        model: The KORF model.
        output_path: Output file path.
        
    Returns:
        Path to report file.
    """
    print("\n" + "=" * 60)
    print("Generating Report")
    print("=" * 60)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# KORF Model Report",
        "",
        f"**File:** `{model.path}`",
        f"**Version:** {model.version}",
        f"**Generated:** {__import__('datetime').datetime.now().isoformat()}",
        "",
        "## Summary",
        "",
        "| Property | Value |",
        "|----------|-------|",
        f"| Cases | {model.num_cases} |",
        f"| Pipes | {model.num_pipes} |",
        f"| Pumps | {len([p for p in model.pumps.values() if p.index > 0])} |",
        f"| Valves | {len([v for v in model.valves.values() if v.index > 0])} |",
        f"| Feeds | {len([f for f in model.feeds.values() if f.index > 0])} |",
        f"| Products | {len([p for p in model.products.values() if p.index > 0])} |",
        "",
        "## Pipes",
        "",
        "| Name | Length | Diameter | Material |",
        "|------|--------|----------|----------|",
    ]

    for pipe in model.pipes.values():
        if pipe.index == 0:
            continue

        len_val = pipe.length_m if hasattr(pipe, "length_m") else "N/A"
        dia_val = pipe.diameter_inch if hasattr(pipe, "diameter_inch") else "N/A"
        mat_val = pipe.material if hasattr(pipe, "material") else "N/A"

        lines.append(f"| {pipe.name} | {len_val} | {dia_val} | {mat_val} |")

    lines.extend([
        "",
        "## Equipment",
        "",
    ])

    for elem_type, collection in [
        ("Pumps", model.pumps),
        ("Valves", model.valves),
        ("Heat Exchangers", model.exchangers),
    ]:
        items = list(collection.values())
        if any(e.index > 0 for e in items):
            lines.extend([f"### {elem_type}", ""])
            for elem in items:
                if elem.index > 0:
                    lines.append(f"- **{elem.name}** (Index: {elem.index})")
            lines.append("")

    # Write report
    output_path.write_text("\n".join(lines))
    print(f"  ✓ Report generated: {output_path}")

    return output_path


if __name__ == "__main__":
    # Load model
    print("=" * 60)
    print("Export and Visualization Demo")
    print("=" * 60)

    # Try to find the most complete model
    model_paths = [
        "examples/output/pump_circuit_with_fluids.kdf",
        "examples/output/pump_circuit_with_pms.kdf",
        "examples/output/pump_circuit_multicase.kdf",
        "examples/output/pump_circuit.kdf",
    ]

    model = None
    for path in model_paths:
        try:
            model = Model(path)
            print(f"  ✓ Loaded model: {path}")
            break
        except FileNotFoundError:
            continue

    if model is None:
        print("  ⚠ No model found. Run previous examples first.")
        exit(1)

    output_base = Path("examples/output")

    # Export to JSON
    json_path = export_to_json_detailed(
        model,
        output_base / "export/model_data.json",
        include_geometry=True,
        include_results=True,
    )

    # Export to Excel (if pandas available)
    try:
        excel_path = export_to_excel(model, output_base / "export/model_data.xlsx")
    except ImportError:
        print("  (pandas not installed, skipping Excel export)")

    # Export to CSV
    csv_files = export_to_csv_separate(model, output_base / "export/csv")

    # Create visualization
    viz_path = create_network_visualization(
        model,
        output_base / "export/network.html",
        title="Pump Circuit Network",
    )

    # Generate report
    report_path = generate_report(model, output_base / "export/report.md")

    # Summary
    print("\n" + "=" * 60)
    print("Export Summary")
    print("=" * 60)
    print(f"  JSON:  {json_path}")
    print(f"  CSV:   {len(csv_files)} files")
    print(f"  Viz:   {viz_path}")
    print(f"  Report: {report_path}")
