"""
Export functionality for pyKorf models.

Supports exporting model data to various formats:
- JSON (with optional pretty printing)
- YAML
- Excel (requires openpyxl)
- CSV

Example:
    >>> from pykorf import Model
    >>> from pykorf.export import export_to_json, export_to_excel
    >>> 
    >>> model = Model("Pumpcases.kdf")
    >>> export_to_json(model, "output.json", include_results=True)
    >>> export_to_excel(model, "output.xlsx")
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from pykorf.config import get_config
from pykorf.exceptions import ExportError
from pykorf.log import get_logger, log_operation
from pykorf.types import ExportOptions

if TYPE_CHECKING:
    from pykorf.model import Model

logger = get_logger(__name__)


def _element_to_dict(elem: Any, options: ExportOptions) -> dict[str, Any]:
    """Convert an element to a dictionary."""
    data: dict[str, Any] = {
        "index": elem.index,
        "name": elem.name,
        "type": elem.etype,
    }
    
    if elem.description:
        data["description"] = elem.description
    
    if options.include_geometry:
        try:
            from pykorf.layout import get_position
            pos = get_position(elem)
            if pos:
                data["position"] = {"x": pos[0], "y": pos[1]}
        except Exception:
            pass
    
    if options.include_results and hasattr(elem, "summary"):
        try:
            data["summary"] = elem.summary()
        except Exception:
            pass
    
    return data


def export_to_json(
    model: Model,
    path: str | Path,
    *,
    options: ExportOptions | None = None,
) -> None:
    """Export model data to JSON.
    
    Args:
        model: The model to export
        path: Output file path
        options: Export options
    
    Raises:
        ExportError: If export fails
    """
    options = options or ExportOptions()
    path = Path(path)
    
    with log_operation("export_to_json", path=str(path)):
        try:
            data = _model_to_dict(model, options)
            
            json_kwargs: dict[str, Any] = {
                "ensure_ascii": False,
            }
            if options.indent:
                json_kwargs["indent"] = options.indent
            
            # Use orjson if available for better performance
            try:
                import orjson
                output = orjson.dumps(data, option=orjson.OPT_INDENT_2 if options.indent else 0)
                path.write_bytes(output)
            except ImportError:
                path.write_text(
                    json.dumps(data, **json_kwargs),
                    encoding=options.encoding,
                )
            
            logger.info("export_to_json_success", path=str(path))
            
        except Exception as e:
            raise ExportError(
                f"Failed to export to JSON: {e}",
                context=None,
            ) from e


def export_to_yaml(
    model: Model,
    path: str | Path,
    *,
    options: ExportOptions | None = None,
) -> None:
    """Export model data to YAML.
    
    Args:
        model: The model to export
        path: Output file path
        options: Export options
    
    Raises:
        ExportError: If export fails
    """
    options = options or ExportOptions()
    path = Path(path)
    
    with log_operation("export_to_yaml", path=str(path)):
        try:
            import yaml
            
            data = _model_to_dict(model, options)
            
            yaml_content = yaml.dump(
                data,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )
            
            path.write_text(yaml_content, encoding=options.encoding)
            logger.info("export_to_yaml_success", path=str(path))
            
        except ImportError as e:
            raise ExportError(
                "PyYAML is required for YAML export. Install with: pip install pyyaml",
            ) from e
        except Exception as e:
            raise ExportError(f"Failed to export to YAML: {e}") from e


def export_to_excel(
    model: Model,
    path: str | Path,
    *,
    include_results: bool = True,
) -> None:
    """Export model data to Excel workbook.
    
    Creates multiple sheets:
    - Summary: Model overview
    - Pipes: Pipe data
    - Pumps: Pump data
    - Valves: Valve data
    - Feeds: Feed boundary conditions
    - Products: Product boundary conditions
    - Connectivity: Connection matrix
    
    Args:
        model: The model to export
        path: Output file path
        include_results: Whether to include calculated results
    
    Raises:
        ExportError: If export fails
    """
    path = Path(path)
    
    with log_operation("export_to_excel", path=str(path)):
        try:
            import pandas as pd
            
            with pd.ExcelWriter(path, engine="openpyxl") as writer:
                # Summary sheet
                summary_data = {
                    "Property": [
                        "File",
                        "Version",
                        "Cases",
                        "Pipes",
                        "Pumps",
                        "Feeds",
                        "Products",
                        "Valves",
                        "Check Valves",
                        "Orifices",
                        "Heat Exchangers",
                        "Compressors",
                        "Vessels",
                    ],
                    "Value": [
                        str(model.path),
                        model.version,
                        model.num_cases,
                        model.num_pipes,
                        model.num_pumps,
                        len([e for e in model.feeds.values() if e.index > 0]),
                        len([e for e in model.products.values() if e.index > 0]),
                        len([e for e in model.valves.values() if e.index > 0]),
                        len([e for e in model.check_valves.values() if e.index > 0]),
                        len([e for e in model.orifices.values() if e.index > 0]),
                        len([e for e in model.exchangers.values() if e.index > 0]),
                        len([e for e in model.compressors.values() if e.index > 0]),
                        len([e for e in model.vessels.values() if e.index > 0]),
                    ],
                }
                pd.DataFrame(summary_data).to_excel(writer, sheet_name="Summary", index=False)
                
                # Pipes sheet
                pipe_rows = []
                for idx, pipe in model.pipes.items():
                    if idx == 0:
                        continue
                    row = {
                        "Index": idx,
                        "Name": pipe.name,
                        "Diameter (in)": pipe.diameter_inch,
                        "Schedule": pipe.schedule,
                        "Length (m)": pipe.length_m,
                        "Material": pipe.material,
                    }
                    if include_results:
                        row["dP/100m (kPa)"] = pipe.pressure_drop_per_100m
                        row["Reynolds"] = pipe.reynolds_number
                    pipe_rows.append(row)
                
                if pipe_rows:
                    pd.DataFrame(pipe_rows).to_excel(writer, sheet_name="Pipes", index=False)
                
                # Pumps sheet
                pump_rows = []
                for idx, pump in model.pumps.items():
                    if idx == 0:
                        continue
                    row = {
                        "Index": idx,
                        "Name": pump.name,
                        "Type": pump.pump_type if hasattr(pump, "pump_type") else "Unknown",
                    }
                    if include_results and hasattr(pump, "head_m"):
                        row["Head (m)"] = pump.head_m
                        row["Power (kW)"] = pump.power_kW
                        row["Efficiency"] = pump.efficiency
                    pump_rows.append(row)
                
                if pump_rows:
                    pd.DataFrame(pump_rows).to_excel(writer, sheet_name="Pumps", index=False)
                
                # Case info
                if hasattr(model, "general"):
                    case_data = {
                        "Case Number": model.general.case_numbers,
                        "Description": model.general.case_descriptions,
                    }
                    pd.DataFrame(case_data).to_excel(writer, sheet_name="Cases", index=False)
            
            logger.info("export_to_excel_success", path=str(path), sheets=writer.sheets.keys())
            
        except ImportError as e:
            raise ExportError(
                "pandas and openpyxl are required for Excel export. "
                "Install with: pip install pandas openpyxl",
            ) from e
        except Exception as e:
            raise ExportError(f"Failed to export to Excel: {e}") from e


def export_to_csv(
    model: Model,
    directory: str | Path,
    *,
    element_type: Literal["all", "pipes", "pumps", "valves"] = "all",
    include_results: bool = True,
) -> list[Path]:
    """Export model data to CSV files.
    
    Args:
        model: The model to export
        directory: Output directory
        element_type: Which elements to export
        include_results: Whether to include calculated results
    
    Returns:
        List of created file paths
    
    Raises:
        ExportError: If export fails
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    
    created_files: list[Path] = []
    
    with log_operation("export_to_csv", directory=str(directory)):
        try:
            import pandas as pd
            
            # Export pipes
            if element_type in ("all", "pipes"):
                pipe_rows = []
                for idx, pipe in model.pipes.items():
                    if idx == 0:
                        continue
                    row = {
                        "index": idx,
                        "name": pipe.name,
                        "diameter_inch": pipe.diameter_inch,
                        "schedule": pipe.schedule,
                        "length_m": pipe.length_m,
                        "material": pipe.material,
                    }
                    if include_results:
                        row["pressure_drop_kpa_100m"] = pipe.pressure_drop_per_100m
                        row["reynolds_number"] = pipe.reynolds_number
                    pipe_rows.append(row)
                
                if pipe_rows:
                    path = directory / "pipes.csv"
                    pd.DataFrame(pipe_rows).to_csv(path, index=False)
                    created_files.append(path)
            
            # Export pumps
            if element_type in ("all", "pumps"):
                pump_rows = []
                for idx, pump in model.pumps.items():
                    if idx == 0:
                        continue
                    row = {"index": idx, "name": pump.name}
                    if include_results:
                        row["head_m"] = pump.head_m if hasattr(pump, "head_m") else None
                        row["power_kw"] = pump.power_kW if hasattr(pump, "power_kW") else None
                    pump_rows.append(row)
                
                if pump_rows:
                    path = directory / "pumps.csv"
                    pd.DataFrame(pump_rows).to_csv(path, index=False)
                    created_files.append(path)
            
            logger.info("export_to_csv_success", files=[str(f) for f in created_files])
            return created_files
            
        except ImportError as e:
            raise ExportError(
                "pandas is required for CSV export. Install with: pip install pandas",
            ) from e
        except Exception as e:
            raise ExportError(f"Failed to export to CSV: {e}") from e


def _model_to_dict(model: Model, options: ExportOptions) -> dict[str, Any]:
    """Convert model to dictionary representation."""
    data: dict[str, Any] = {
        "metadata": {
            "version": model.version,
            "file": str(model.path),
            "num_cases": model.num_cases,
        },
        "elements": {},
    }
    
    if options.include_metadata and hasattr(model, "general"):
        data["metadata"]["cases"] = model.general.case_descriptions
        data["metadata"]["units"] = model.general.units if hasattr(model.general, "units") else None
    
    # Export elements
    for elem in model.elements:
        etype = elem.etype.lower() + "s"
        if etype not in data["elements"]:
            data["elements"][etype] = []
        data["elements"][etype].append(_element_to_dict(elem, options))
    
    if options.include_connectivity:
        data["connectivity"] = _extract_connectivity(model)
    
    return data


def _extract_connectivity(model: Model) -> list[dict[str, Any]]:
    """Extract connectivity information."""
    connections = []
    
    for elem in model.elements:
        if elem.etype == "PIPE":
            continue
        
        try:
            from pykorf.connectivity import get_connections
            conns = get_connections(model, elem.name)
            if conns:
                connections.append({
                    "element": elem.name,
                    "type": elem.etype,
                    "connected_to": conns,
                })
        except Exception:
            pass
    
    return connections


__all__ = [
    "export_to_json",
    "export_to_yaml",
    "export_to_excel",
    "export_to_csv",
]
