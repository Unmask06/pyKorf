# Export & Import

Exporting and importing model data in various formats.

## DataFrame Conversion (Lossless Round-Trip)

pyKorf can convert any `.kdf` model to a dict of pandas DataFrames and back
**without losing any data**. Each element type (`GEN`, `PIPE`, `PUMP`, …) gets its own DataFrame, and a special `_HEADER` DataFrame stores the version header.

### KDF → DataFrames

```python
from pykorf import Model

model = Model("Pumpcases.kdf")
dfs = model.io.to_dataframes()

# Inspect the sheets
for name, df in dfs.items():
    print(f"{name}: {len(df)} records")
```

### DataFrames → KDF

```python
# Reconstruct a Model from DataFrames
reconstructed = Model()
reconstructed.io.from_dataframes(dfs)
reconstructed.save("Pumpcases_copy.kdf")
```

### KDF → Excel

```python
model = Model("Pumpcases.kdf")
model.io.to_excel("Pumpcases.xlsx")
```

Each element type is written to a separate Excel sheet.

### Excel → KDF

```python
model = Model()
model.io.from_excel("Pumpcases.xlsx")
model.save("Pumpcases_from_excel.kdf")
```

### Full Round-Trip Example

```python
from pykorf import Model

# Original
model = Model("Pumpcases.kdf")

# KDF → Excel
model.io.to_excel("Pumpcases.xlsx")

# Excel → KDF
restored = Model()
restored.io.from_excel("Pumpcases.xlsx")
restored.save("Pumpcases_restored.kdf")

# The two .kdf files are byte-identical
```

## Export Report (Human-Readable)

For a formatted Excel report with element summaries, use the `ResultExporter`:

```python
from pykorf import Model
from pykorf.core.reports.exporter import ResultExporter

model = Model("Pumpcases.kdf")
exporter = ResultExporter(model)
exporter.export_to_excel("Pumpcases_report.xlsx")
```

The report includes:
- Element summaries (Pipes, Pumps, Feeds, Products, Valves, Compressors, Heat Exchangers, Junctions, Misc Equipment)
- Pipe sizing criteria check (PASS/FAIL per pipe)
- Min-Max summary row for DP/DL and velocity
- Overall criteria verdict

### With Design Basis and References

If you have stored design basis, remarks, hold items, or references via the **References** page in the Web UI, they are automatically included in the report:

```python
from pykorf.app.operation.project.references import ReferencesStore

ref_store = ReferencesStore.load(model._parser.path)
exporter = ResultExporter(
    model,
    basis=ref_store.basis,
    remarks=ref_store.remarks,
    hold=ref_store.hold,
    references=[
        {"name": r.name, "category": r.category, "link": r.link, "description": r.description}
        for r in ref_store.references
    ],
)
exporter.export_to_excel("Pumpcases_report.xlsx")
```

## Batch Report

Generate a combined report across multiple KDF files:

```python
from pykorf.app.operation.processor.batch_report import BatchReportGenerator

reporter = BatchReportGenerator(folder_path="/path/to/kdf/files")
reporter.generate_report(output_path="batch_report.xlsx")
```

See the [Batch Report](#batch-report) section above for details.

## Best Practices

### 1. Export Before Editing

```python
# Create a backup before making changes
model.io.to_excel("model_backup.xlsx")

# Make changes
model.update_element(...)
model.save()
```

### 2. Export for Analysis

```python
# Use Results for calculated values
from pykorf.core.reports.results import Results

results = Results(model)
df = results.to_dataframe()
```

### 3. Lossless Round-Trip

Always use `model.io.to_dataframes()` / `model.io.from_dataframes()` or `model.io.to_excel()` / `model.io.from_excel()` for lossless conversion. Manual reconstruction via `model.add_element()` will lose data.

## Next Steps

- [Working with Elements](working-with-elements.md)
