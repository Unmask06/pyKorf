# pyKorf

**Python toolkit for reading, editing and writing KORF hydraulic model files (`.kdf`).**

---

## Overview

pyKorf lets you programmatically work with [KORF](https://www.korf.co.uk/) hydraulic simulation models without opening the KORF GUI. It also provides an optional `KorfApp` class that wraps the KORF GUI via **pywinauto** for full end-to-end automation.

| Module              | Purpose                                                 |
| ------------------- | ------------------------------------------------------- |
| `pykorf.model`      | `KorfModel` – load / edit / save a `.kdf` file          |
| `pykorf.parser`     | `KdfParser` – low-level tokeniser for `.kdf` files      |
| `pykorf.cases`      | `CaseSet` – multi-case helpers                          |
| `pykorf.results`    | `Results` – extract calculated output values            |
| `pykorf.automation` | `KorfApp` – connect to a running KORF and drive the GUI |
| `pykorf.elements`   | One class per KORF element type                         |
| `pykorf.utils`      | CSV / value helpers                                     |
| `pykorf.exceptions` | Package-wide exception types                            |

---

## Installation

```bash
# Install with dev dependencies (includes all extras)
uv pip install -e ".[dev]"
```

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

### 4. Multi-case helpers

```python
from pykorf.cases import CaseSet

cases = CaseSet(model)
print(cases.names)     # ['NORMAL', 'RATED', 'MINIMUM']

# Tabulate pipe flows across all cases
import pprint
pprint.pprint(cases.pipe_flows_table())
```

### 5. Read calculated results

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

### 6. Automate the KORF GUI (requires KORF to be already open)

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

## Supported KORF Element Types

| KDF keyword | pyKorf class    | Collection on model       |
| ----------- | --------------- | ------------------------- |
| `\GEN`      | `General`       | `model.general`           |
| `\PIPE`     | `Pipe`          | `model.pipes[n]`          |
| `\FEED`     | `Feed`          | `model.feeds[n]`          |
| `\PROD`     | `Product`       | `model.products[n]`       |
| `\PUMP`     | `Pump`          | `model.pumps[n]`          |
| `\VALVE`    | `Valve`         | `model.valves[n]`         |
| `\CHECK`    | `CheckValve`    | `model.check_valves[n]`   |
| `\FO`       | `FlowOrifice`   | `model.orifices[n]`       |
| `\HX`       | `HeatExchanger` | `model.exchangers[n]`     |
| `\COMP`     | `Compressor`    | `model.compressors[n]`    |
| `\MISC`     | `MiscEquipment` | `model.misc_equipment[n]` |
| `\EXPAND`   | `Expander`      | `model.expanders[n]`      |
| `\JUNC`     | `Junction`      | `model.junctions[n]`      |
| `\TEE`      | `Tee`           | `model.tees[n]`           |
| `\VESSEL`   | `Vessel`        | `model.vessels[n]`        |

> Index **0** in every collection is the KORF _default template_. Real instances start at **1**.

---

## Running Tests

```bash
pytest
```

All tests use the sample `.kdf` files in `pykorf/library/` and require no KORF licence.

---

## Project Structure

```
pyKorf/
├── pykorf/                   # Package source
│   ├── __init__.py           # Public API
│   ├── model.py              # KorfModel
│   ├── parser.py             # KdfParser (tokeniser)
│   ├── cases.py              # CaseSet
│   ├── results.py            # Results
│   ├── automation.py         # KorfApp (pywinauto)
│   ├── utils.py              # CSV / value helpers
│   ├── exceptions.py         # Custom exceptions
│   └── elements/
│       ├── __init__.py       # Element registry
│       ├── base.py           # BaseElement
│       ├── gen.py            # General
│       ├── pipe.py           # Pipe
│       ├── feed.py           # Feed
│       ├── prod.py           # Product
│       ├── pump.py           # Pump
│       ├── valve.py          # Valve
│       ├── check.py          # CheckValve
│       ├── orifice.py        # FlowOrifice
│       ├── hx.py             # HeatExchanger
│       ├── compressor.py     # Compressor
│       ├── misc.py           # MiscEquipment
│       ├── expand.py         # Expander
│       ├── junction.py       # Junction
│       ├── tee.py            # Tee
│       └── vessel.py         # Vessel
├── tests/
│   ├── test_parser.py
│   ├── test_elements.py
│   ├── test_cases.py
│   └── test_utils.py
├── pykorf/library/           # Sample .kdf files
│   ├── Pumpcases.kdf
│   └── crane10.kdf
├── korf_automation.ipynb     # Step-by-step automation notebook
├── pyproject.toml
└── README.md
```

---

## TUI Error/Warning Display Pattern

When building TUI screens that perform background operations, follow this pattern for displaying errors and warnings inline (avoiding popup screens):

1. **Background operations** use `logger.warning()` and `logger.error()` for issues
2. **After processing**, read the log file using `get_log_entries()` from `pykorf.use_case.tui.logging`
3. **Display inline** in the RichLog widget (yellow for warnings, red for errors)

Example:
```python
from pykorf.log import get_log_file
from pykorf.use_case.tui.logging import get_log_entries, log_warning, log_error

# After processing completes
log_file = get_log_file()
if log_file:
    entries = get_log_entries(
        log_file,
        levels={"WARNING", "ERROR", "CRITICAL"},
        logger_filter="pykorf.use_case.pms",
    )
    if entries:
        log_warning(results, "Warnings/Errors during processing:")
        for _ts, _name, level, message in entries:
            if level == "WARNING":
                log_warning(results, f"  ⚠ {message}")
            else:
                log_error(results, f"  ✗ {message}")
```

This keeps all feedback visible in the terminal output without blocking popups.

---

## KORF Automation Safety Note

KORF limits the number of times a file may be opened to **5**.
`KorfApp` **always** uses `Application().connect()` – it **never** calls
`Application().start()` – so it safely reuses the already-running instance.

---

## Licence

MIT
