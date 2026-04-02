# pyKorf

**Python toolkit for reading, editing and writing KORF hydraulic model files (`.kdf`).**

---

## Overview

pyKorf lets you programmatically work with [KORF](https://www.korf.co.uk/) hydraulic simulation models without opening the KORF GUI. It provides a service-based model API, a local web interface, batch processing tools, and optional GUI automation via **pywinauto**.

| Module | Purpose |
| --- | --- |
| `pykorf.model` | `Model` – load / edit / save a `.kdf` file (service-based architecture) |
| `pykorf.parser` | `KdfParser` – low-level tokeniser / serializer for `.kdf` files |
| `pykorf.cases` | `CaseSet` – multi-case helpers |
| `pykorf.results` | `Results` – extract calculated output values |
| `pykorf.fluid` | `Fluid` – fluid properties |
| `pykorf.types` | Pydantic models: `PipeData`, `PumpData`, `ValveData`, etc. |
| `pykorf.automation` | `KorfApp` – connect to a running KORF and drive the GUI |
| `pykorf.elements` | One class per KORF element type (17+ types) |
| `pykorf.use_case` | High-level workflows: PMS, HMB, pipe criteria, batch reports |
| `pykorf.use_case.web` | Flask web UI for interactive model editing |
| `pykorf.visualization` | PyVis network visualization |
| `pykorf.reports` | Excel report generation |
| `pykorf.exceptions` | Package-wide exception hierarchy |

---

## Installation

```bash
# Install with dev dependencies (includes all extras)
uv pip install -e ".[dev]"
```

---

## CLI

```bash
uv run pykorf              # Launch web UI on default port 8000
uv run pykorf --port 9000  # Launch on custom port
uv run pykorf --debug      # Enable debug mode
uv run pykorf --trial      # Run in trial mode (7-day trial)
```

The CLI launches a single-user, local-only Flask web application with auto-update checking and browser launch.

---

## Quick Start

### Persistence model (important)

- `Model(...)` / `KorfModel.load(...)` reads the `.kdf` into memory.
- Any manipulation through the Model API (`update_element`, `add_element`,
  `delete_element`, `copy_element`, `move_element`, `connect_elements`, etc.)
  modifies only the in-memory model state.
- The source file is not edited directly during these operations.
- Disk writes happen only when you call `model.save(...)` or `model.save_as(...)`.
- If you do not save, changes are discarded when the Python process ends.

### Model Architecture

The `Model` class uses a **composition-based service architecture** with six services:

| Service | Attribute | Responsibility |
|---|---|---|
| `ElementService` | `model.elements_service` | CRUD: add, update, delete, copy, move, reindex, compact |
| `QueryService` | `model.query` | Filtering by type/name (glob support), get/set params |
| `ConnectivityService` | `model.connectivity` | Connect/disconnect elements, check connectivity |
| `LayoutService` | `model.layout` | XY positioning, polyline/bend management, orthogonal routing, alignment, grid snapping, centering |
| `IOService` | `model.io` | save/save_as, to_dataframes, to_excel, from_excel, from_dataframes |
| `SummaryService` | `model.summary_service` | validate(), summary(), indexed element accessors |

### Create a basic model from defaults

```python
from pykorf import Model

# Start from the bundled New.kdf defaults
model = Model()

# Add a minimal Feed -> Pipe -> Product network
model.add_element("FEED", "S1", {"PRES": "50"})
model.add_element("PIPE", "L1", {"LEN": "100", "DIA": "6", "TFLOW": "50"})
model.add_element("PROD", "D1", {"PRES": "1000"})

model.connect_elements("L1", "S1")
model.connect_elements("L1", "D1")

# Optional safety check before save
issues = model.validate()
if issues:
    raise ValueError(issues)

model.save("basic_model.kdf")
```

### 1. Load and inspect an existing model

```python
from pykorf import KorfModel

model = KorfModel.load("pykorf/library/Pumpcases.kdf")
print(model)
# KorfModel(version='KORF_2.0', pipes=5, pumps=1, cases=3)

print(model.general.case_descriptions)
# ['NORMAL', 'RATED', 'MINIMUM']

print(model.pipes[1].summary())
# {'name': 'L1', 'diameter_inch': '6', 'schedule': '40', 'length_m': 100.0, ...}

print(model.pumps[1].summary())
# {'name': 'P1', 'head_m': 155.6, 'power_kW': 24.16, 'efficiency': 0.351, ...}
```

### 2. Edit values

```python
# Set pipe flow for all 3 cases
model.pipes[1].set_flow([60, 65, 25])

# Or as a semicolon string
model.pipes[1].set_flow("60;65;25")

# Change pump efficiency
model.pumps[1].set_efficiency(0.72)

# Change feed pressure per case
model.feeds[1].set_pressure([55, 60, 45])

# Change back-pressure
model.products[1].set_pressure(1100)
```

### 3. Save

```python
model.save()                        # overwrites original
model.save_as("Pumpcases_new.kdf")  # save to new file
```

### 4. Excel round-trip

```python
# Export all model data to Excel
model.io.to_excel("model_export.xlsx")

# Import from Excel (lossless fidelity)
model.io.from_excel("model_export.xlsx")
```

### 5. Multi-case helpers

```python
from pykorf.cases import CaseSet

cases = CaseSet(model)
print(cases.names)     # ['NORMAL', 'RATED', 'MINIMUM']

# Tabulate pipe flows across all cases
import pprint
pprint.pprint(cases.pipe_flows_table())
```

### 6. Read calculated results

```python
from pykorf.results import Results

res = Results(model)
print(res.pump_summary(1))
# {'name': 'P1', 'head_m': 155.6, 'power_kW': 24.16, 'efficiency': 0.351, ...}

print(res.pipe_velocities())
# {1: [0.298, 0.298, 0.298, 0.0], 2: [...], ...}

# Export to DataFrame (requires pandas)
df = res.to_dataframe()
```

### 7. Automate the KORF GUI (requires KORF to be already open)

```python
from pykorf.automation import KorfApp

# Connect to the running KORF instance (no new window opened)
with KorfApp.connect() as app:
    app.reload_model("pykorf/library/Pumpcases.kdf")
    app.run_hydraulics()
    app.wait_for_run(timeout=30)
    app.save_model()
```

---

## Web UI

The `pykorf` CLI launches a Flask web application for interactive model editing.

| Feature | Routes | Description |
| --- | --- | --- |
| File Picker | `/`, `/open` | Open KDF files with recent files list |
| Model Core | `/model`, `/model/save`, `/model/reload` | Main menu, save/reload |
| Model Info | `/model/info` | Element stats, pipe list, categorized validation |
| Apply Data | `/model/data` | Apply PMS/HMB data from Excel/JSON |
| Global Parameters | `/model/settings` | Apply DP margins, shutoff margins |
| Pipe Criteria | `/model/pipe-criteria` | Pipe sizing criteria with auto-predict |
| Reports | `/model/report` | Generate reports, export/import Excel, batch report |
| Bulk Copy | `/model/bulk-copy` | Copy fluid properties between pipes |
| References | `/model/references/*` | Design basis, remarks, hold items, reference documents |
| Preferences | `/preferences` | SharePoint path overrides |

**SharePoint Integration:** Reads OneDrive sync registry to resolve local paths to SharePoint URLs with user-configurable overrides.

**References System:** Stores design basis, remarks, hold items, and reference document links in `.pykorf` sidecar JSON. Supports categories: P&ID, PFD, Datasheet, Specification, Calculation, Drawing, Report, Standard, Other.

---

## Workflows

### PMS (Piping Material Specification)

```python
from pykorf.use_case.pms import apply_pms

# Apply PMS from Excel or JSON to pipes
apply_pms(model, pms_source="pms.xlsx")
```

- Loads PMS from Excel or JSON (auto-converts Excel to JSON)
- Parses pipe NOTES field to extract line numbers
- Looks up PMS code + nominal pipe size across all materials
- Calculates ID from OD and wall thickness, or uses schedule
- Applies parameters: material, roughness, diameter, schedule/ID

### HMB (Heat & Material Balance)

```python
from pykorf.use_case.hmb import apply_hmb

# Apply HMB stream data from Excel or JSON
apply_hmb(model, hmb_source="hmb.xlsx")
```

- Loads stream data from Excel or JSON
- Applies fluid properties to pipes based on line numbers

### Pipe Sizing Criteria

```python
from pykorf.use_case.sizing_criteria import lookup_criteria, apply_criteria

# Look up criteria by state and code
criteria = lookup_criteria("LIQUID", "DP10")

# Apply to pipes
apply_criteria(model, criteria_code="DP10")
```

- Auto-predicts fluid state from liquid fraction
- Criteria code lookup by state (liquid/gas/two-phase)
- Applies to pipe SIZ parameters

### Global Parameters

```python
from pykorf.use_case.global_parameters import apply_global_parameters

# Apply design parameters (DP margins, shutoff margins)
apply_global_parameters(model, parameter_ids=[1, 2, 3])
```

### Bulk Fluid Copy

```python
from pykorf.use_case.bulk_calc import copy_fluids

# Copy fluid properties from reference pipe to multiple targets
copy_fluids(model, source_pipe_idx=1, target_pipe_indices=[2, 3, 4])
```

### Batch Reports

```python
from pykorf.use_case.batch_report import BatchReportGenerator

# Generate reports across multiple KDF files
reporter = BatchReportGenerator(folder_path="/path/to/kdf/files")
reporter.generate_report(output_path="batch_report.xlsx")
```

---

## Supported KORF Element Types

| KDF keyword | pyKorf class | Collection on model |
| --- | --- | --- |
| `\GEN` | `General` | `model.general` |
| `\PIPE` | `Pipe` | `model.pipes[n]` |
| `\FEED` | `Feed` | `model.feeds[n]` |
| `\PROD` | `Product` | `model.products[n]` |
| `\PUMP` | `Pump` | `model.pumps[n]` |
| `\VALVE` | `Valve` | `model.valves[n]` |
| `\CHECK` | `CheckValve` | `model.check_valves[n]` |
| `\FO` | `FlowOrifice` | `model.orifices[n]` |
| `\HX` | `HeatExchanger` | `model.exchangers[n]` |
| `\COMP` | `Compressor` | `model.compressors[n]` |
| `\MISC` | `MiscEquipment` | `model.misc_equipment[n]` |
| `\EXPAND` | `Expander` | `model.expanders[n]` |
| `\JUNC` | `Junction` | `model.junctions[n]` |
| `\TEE` | `Tee` | `model.tees[n]` |
| `\VESSEL` | `Vessel` | `model.vessels[n]` |
| `\SYMBOL` | `Symbol` | `model.symbols[n]` |
| `\TOOLS` | `Tools` | `model.tools[n]` |
| `\PSEUDO` | `Pseudo` | `model.pseudos[n]` |
| `\PIPEDATA` | `PipeData` | `model.pipedata[n]` |

> Index **0** in every collection is the KORF _default template_. Real instances start at **1**.

---

## Running Tests

```bash
uv run pytest                    # All tests
uv run pytest -m unit            # Unit tests only
uv run pytest -m integration     # Integration tests
uv run pytest -m "not slow"      # Exclude slow tests
uv run pytest tests/test_model_api.py -v  # Single file
```

All tests use the sample `.kdf` files in `pykorf/library/` and require no KORF licence.

```bash
# Lint
uv run ruff check pykorf tests

# Format
uv run ruff format pykorf tests

# Type check
uv run mypy pykorf
```

---

## Project Structure

```
pyKorf/
├── pykorf/                       # Package source
│   ├── __init__.py               # Public API
│   ├── _version.py               # Version info
│   ├── cli.py                    # CLI entry point (launches web UI)
│   ├── parser.py                 # KdfParser (tokeniser / serializer)
│   ├── cases.py                  # CaseSet
│   ├── results.py                # Results
│   ├── fluid.py                  # Fluid
│   ├── types.py                  # Pydantic models, enums, typed data
│   ├── log.py                    # Structured logging (structlog)
│   ├── update.py                 # Auto-update checker
│   ├── utils.py                  # CSV / value helpers
│   ├── exceptions.py             # Custom exceptions
│   ├── automation.py             # KorfApp (pywinauto)
│   ├── model/                    # Model layer (service-based)
│   │   ├── __init__.py           # Model class (facade)
│   │   ├── core.py               # _ModelBase (collections, parsing)
│   │   └── services/             # 6 service classes
│   │       ├── element.py        # ElementService (CRUD)
│   │       ├── query.py          # QueryService (filtering, params)
│   │       ├── connectivity.py   # ConnectivityService
│   │       ├── layout.py         # LayoutService (positioning, routing)
│   │       ├── io.py             # IOService (save, export, import)
│   │       └── summary.py        # SummaryService (validate, stats)
│   ├── elements/                 # 17+ element type classes
│   │   ├── base.py               # BaseElement
│   │   ├── gen.py, pipe.py, ...  # Element implementations
│   │   └── __init__.py           # ELEMENT_REGISTRY
│   ├── use_case/                 # High-level workflows
│   │   ├── config.py             # Unified facade (paths, prefs, PMS, HMB)
│   │   ├── preferences.py        # User preferences (config.json)
│   │   ├── paths.py              # Config/data directory management
│   │   ├── pms.py                # PMS processing
│   │   ├── hmb.py                # HMB processing
│   │   ├── global_parameters.py  # Global design parameters
│   │   ├── sizing_criteria.py    # Pipe sizing criteria
│   │   ├── line_number.py        # Line number parsing from NOTES
│   │   ├── processor.py          # PipedataProcessor (batch processing)
│   │   ├── batch_report.py       # BatchReportGenerator
│   │   ├── bulk_calc/            # Bulk calculation tools
│   │   ├── pykorf_file.py        # Per-file metadata
│   │   └── web/                  # Flask web UI
│   │       ├── app.py            # Flask app factory
│   │       ├── session.py        # In-process model state
│   │       ├── sharepoint.py     # OneDrive/SharePoint URL resolution
│   │       ├── references.py     # ReferencesStore
│   │       ├── routes/           # 11 Flask Blueprints
│   │       ├── templates/        # 12 HTML templates
│   │       └── static/           # CSS, JS, vendor assets
│   ├── visualization/            # PyVis network visualization
│   ├── reports/                  # Excel report generation
│   ├── templates/                # Template files
│   ├── library/                  # Sample .kdf files
│   └── docs/                     # Documentation source
├── tests/                        # Test suite (17 files)
├── pyproject.toml
└── README.md
```

---

## KORF Automation Safety Note

KORF limits the number of times a file may be opened to **5**.
`KorfApp` **always** uses `Application().connect()` – it **never** calls
`Application().start()` – so it safely reuses the already-running instance.

---

## Licence

MIT
