# pyKorf Examples

This directory contains comprehensive use case examples demonstrating the full capabilities of pyKorf.

## Quick Start

```bash
# Install dependencies (if not already installed)
pip install pykorf[pandas,visualization]

# Run all examples
cd examples
python 01_create_pump_circuit.py
python 02_add_pms_from_excel.py
python 03_add_fluid_properties.py
python 04_multi_case_analysis.py
python 05_export_and_visualize.py
```

## Use Cases

### 1. Create Pump Circuit (`01_create_pump_circuit.py`)

Demonstrates creating a complete hydraulic circuit from scratch:

- **Feed Source** - Boundary condition with pressure/temperature
- **Pump** - Centrifugal pump with efficiency and differential head
- **Heat Exchanger** - Shell & tube cooler
- **Control Valve** - Linear CV valve with opening percentage
- **Product Sink** - Back pressure boundary

**Key Features:**
- Connect elements with pipes
- Set flow rates for all pipes
- Configure pipe properties (length, diameter, schedule)
- Validate connectivity
- Save model to KDF file

```python
from examples.01_create_pump_circuit import create_pump_circuit

model = create_pump_circuit(
    output_path="my_circuit.kdf",
    flow_rate=150.0,
    feed_pressure=100.0,
)
```

**Output:** `examples/output/pump_circuit.kdf`

---

### 2. Add PMS from Excel (`02_add_pms_from_excel.py`)

Shows how to import Piping Material Specification (PMS) data:

- Read PMS from Excel or JSON files
- Create PipeData library entries
- Map materials, schedules, and dimensions
- Validate PMS assignments
- Assign PMS specifications to actual pipes

**Key Features:**
- Sample PMS data generation
- Excel/JSON import
- PipeData element creation
- Material validation

```python
from examples.02_add_pms_from_excel import (
    read_pms_from_excel,
    add_pms_to_model,
    assign_pms_to_pipes,
)

# Read PMS data
specs = read_pms_from_excel("pms_data.xlsx")

# Add to model
model = Model("pump_circuit.kdf")
created = add_pms_to_model(model, specs)

# Assign to pipes
assign_pms_to_pipes(model, {
    "SUCT_L1": "CS-40-6",
    "DISC_L2": "CS-80-4",
})
```

**Output:** `examples/output/pump_circuit_with_pms.kdf`

---

### 3. Add Fluid Properties (`03_add_fluid_properties.py`)

Demonstrates fluid property management:

- Create fluid definitions with properties
- Support for water, crude oil, natural gas
- Temperature-dependent properties
- Type-safe Fluid class
- Assign fluids to pipes

**Key Features:**
- Predefined fluid templates
- Custom fluid creation
- Property validation
- Fluid assignment to pipes

```python
from examples.03_add_fluid_properties import Fluid, add_fluid_to_model

# Use predefined fluid
water = Fluid.water(temperature_c=50)

# Or custom fluid
custom = Fluid(
    name="Thermal Oil",
    phase="Liquid",
    density_kg_m3=850,
    viscosity_cp=5.0,
)

# Add to model
add_fluid_to_model(model, water, "COOLING_WATER")
```

**Output:** `examples/output/pump_circuit_with_fluids.kdf`

---

### 4. Multi-Case Analysis (`04_multi_case_analysis.py`)

Sets up multiple simulation scenarios:

- Define case scenarios (MIN, NORMAL, PEAK, EMERGENCY)
- Configure case-specific parameters
- Generate comparison tables
- Export case data
- Sensitivity analysis

**Key Features:**
- Multi-case parameter configuration
- Case comparison tables (Markdown, CSV, HTML)
- Per-case data export
- Statistical analysis

```python
from examples.04_multi_case_analysis import setup_multicase_scenarios

scenarios = [
    {"name": "MIN", "flow": 50, "pressure": 80},
    {"name": "NORM", "flow": 100, "pressure": 100},
    {"name": "MAX", "flow": 150, "pressure": 120},
]

cases = setup_multicase_scenarios(model, scenarios)

# Generate comparison
table = generate_case_comparison_table(model, cases, "markdown")
```

**Output:** 
- `examples/output/pump_circuit_multicase.kdf`
- `examples/output/case_data/case_comparison.csv`

---

### 5. Export and Visualization (`05_export_and_visualize.py`)

Export models to various formats and create visualizations:

- JSON export with full metadata
- Excel workbook with multiple sheets
- CSV files per element type
- Interactive network visualization (PyVis)
- Markdown reports

**Key Features:**
- Multiple export formats
- Interactive HTML network graphs
- Automated report generation
- Geometry and results inclusion

```python
from examples.05_export_and_visualize import (
    export_to_json_detailed,
    export_to_excel,
    create_network_visualization,
)

# Export to JSON
export_to_json_detailed(model, "output.json")

# Export to Excel
export_to_excel(model, "output.xlsx")

# Create visualization
create_network_visualization(model, "network.html")
```

**Output:**
- `examples/output/export/model_data.json`
- `examples/output/export/model_data.xlsx`
- `examples/output/export/network.html`
- `examples/output/export/report.md`

---

## Running Examples

### Prerequisites

```bash
# Core dependencies
pip install pykorf

# For Excel export
pip install pandas openpyxl

# For visualization
pip install pyvis networkx
```

### Sequential Execution

The examples are designed to run sequentially, with each building on the previous:

```bash
cd examples

# 1. Create base model
python 01_create_pump_circuit.py

# 2. Add PMS
python 02_add_pms_from_excel.py

# 3. Add fluids
python 03_add_fluid_properties.py

# 4. Setup multi-case
python 04_multi_case_analysis.py

# 5. Export everything
python 05_export_and_visualize.py
```

### Individual Execution

Each example can run standalone with a blank model if the previous output doesn't exist.

---

## File Structure

```
examples/
├── README.md                          # This file
├── basic_usage.py                     # Basic API examples
├── enterprise_pms_and_fluid_workflow.py  # Enterprise workflow
├── fluid_class_demo.py                # Fluid class demo
├── generate_excel_templates.py        # Template generation
│
├── 01_create_pump_circuit.py          # Use Case 1
├── 02_add_pms_from_excel.py           # Use Case 2
├── 03_add_fluid_properties.py         # Use Case 3
├── 04_multi_case_analysis.py          # Use Case 4
├── 05_export_and_visualize.py         # Use Case 5
│
└── output/                            # Generated outputs
    ├── pump_circuit.kdf
    ├── pump_circuit_with_pms.kdf
    ├── pump_circuit_with_fluids.kdf
    ├── pump_circuit_multicase.kdf
    ├── pms_data.xlsx
    ├── pms_data.json
    ├── case_data/
    │   ├── case_comparison.csv
    │   └── case_*.json
    └── export/
        ├── model_data.json
        ├── model_data.xlsx
        ├── network.html
        └── report.md
```

---

## Tips

1. **Start Simple**: Run `01_create_pump_circuit.py` first to understand the basics
2. **Check Output**: Each example saves files to `examples/output/`
3. **Dependencies**: Install extras as needed (`pandas`, `pyvis`)
4. **Validation**: Examples include validation - watch for warnings
5. **Customization**: Modify the examples to match your specific use case

---

## Troubleshooting

### Import Errors

```bash
# If you get "Module not found"
pip install -e ".[all]"  # From project root
```

### Missing Dependencies

```bash
# For Excel support
pip install pandas openpyxl

# For visualization
pip install pyvis networkx

# For all features
pip install pykorf[all]
```

### File Not Found

Make sure you run examples from the `examples/` directory or use absolute paths.

---

## Next Steps

After running these examples:

1. **Explore the API**: Check `../docs/api/` for complete API reference
2. **Read User Guide**: See `../docs/user-guide/` for detailed documentation
3. **Customize**: Modify examples for your specific hydraulic models
4. **Contribute**: Submit your own examples via pull request
