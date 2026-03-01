# Export & Import

Exporting and importing model data in various formats.

## Export Formats

pyKorf supports multiple export formats:

- **JSON** - Machine-readable, hierarchical
- **YAML** - Human-readable, hierarchical
- **Excel** - Multi-sheet workbook
- **CSV** - Tabular data files

## JSON Export

```python
from pykorf.export import export_to_json
from pykorf.types import ExportOptions

# Basic export
export_to_json(model, "output.json")

# With options
options = ExportOptions(
    include_results=True,
    include_geometry=True,
    include_connectivity=True,
    indent=2
)
export_to_json(model, "output.json", options=options)
```

### JSON Structure

```json
{
  "metadata": {
    "version": "KORF_3.6",
    "file": "model.kdf",
    "num_cases": 3
  },
  "elements": {
    "pipes": [...],
    "pumps": [...]
  },
  "connectivity": [...]
}
```

## YAML Export

```python
from pykorf.export import export_to_yaml

export_to_yaml(model, "output.yaml")
```

## Excel Export

```python
from pykorf.export import export_to_excel

export_to_excel(model, "output.xlsx", include_results=True)
```

### Excel Sheets

- **Summary** - Model overview
- **Pipes** - Pipe data
- **Pumps** - Pump data
- **Cases** - Case definitions

## CSV Export

```python
from pykorf.export import export_to_csv

# Export all elements
export_to_csv(model, "./csv_export/")

# Export specific type
export_to_csv(
    model,
    "./csv_export/",
    element_type="pipes",  # or "pumps", "valves"
    include_results=True
)
```

## Export Options

| Option | Default | Description |
|--------|---------|-------------|
| `include_results` | True | Include calculated values |
| `include_geometry` | True | Include XY positions |
| `include_connectivity` | True | Include connection data |
| `indent` | 2 | JSON indentation |
| `encoding` | "utf-8" | Output encoding |

## Import

Currently, pyKorf only supports importing KDF files directly:

```python
# Load KDF
model = Model("input.kdf")

# Modify
model.update_element(...)

# Save
model.save("output.kdf")
```

### From JSON (Manual)

```python
import json
from pykorf import Model
from pykorf.definitions import Element, Pipe

# Load JSON data
with open("data.json") as f:
    data = json.load(f)

# Create model
model = Model()

# Add elements from JSON
for pipe_data in data["elements"]["pipes"]:
    model.add_element(Element.PIPE, pipe_data["name"], {
        Pipe.LEN: pipe_data["length_m"],
        Pipe.DIA: pipe_data["diameter_inch"]
    })

model.save()
```

## Best Practices

### 1. Export for Backup

```python
# Before making changes
export_to_json(model, "backup.json")

# Make changes
model.update_element(...)

# Save
model.save()
```

### 2. Export for Analysis

```python
# Export to Excel for analysis in pandas
export_to_excel(model, "analysis.xlsx")

# Or use Results directly
from pykorf import Results
results = Results(model)
df = results.to_dataframe()
```

### 3. Selective Export

```python
# Export only what you need
options = ExportOptions(
    include_results=False,  # Smaller file
    include_geometry=False  # No positions
)
export_to_json(model, "minimal.json", options=options)
```

## Next Steps

- [Working with Elements](working-with-elements.md)
