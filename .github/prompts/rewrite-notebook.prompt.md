# Rewrite `korf_automation.ipynb` – Complete pyKorf Feature Demonstration

## Goal

Replace the entire contents of `korf_automation.ipynb` with a comprehensive, well-documented Jupyter notebook that demonstrates **every feature** of the `pykorf` Python package. Use rich **Markdown cells** between every code cell to explain concepts. The old notebook only had 6 raw pywinauto cells — the new one should be a proper tutorial with ~30 cells.

Also **delete** the file `pykorf.py` in the repo root (it is an obsolete standalone script superseded by the `pykorf/` package).

---

## Critical Safety Rule (enforce everywhere)

> **NEVER create a new KORF instance.** KORF is trial-licensed (limited opens). All automation must use `Application().connect()` / `KorfApp.connect()`. Never use `Application().start()`, `subprocess.Popen`, or `os.startfile` on the KORF executable.

---

## Notebook Structure

Use the exact section structure below. Each `##` heading is a **Markdown cell**, followed by one or more **code cells**.

### Title & Table of Contents (Markdown only)

```
# pyKorf – Complete Feature Demonstration

**pyKorf** is a Python toolkit for programmatically reading, editing and writing
KORF hydraulic model files (`.kdf`). All modifications happen through the Python
API — you never need to manually edit a `.kdf` file.

(Include a numbered Table of Contents linking to each section heading below)
```

---

### Section 1 – KORF Hydraulics Background (Markdown only)

Cover these concepts from `library/korf_manual.md`:

- KORF treats all pipe flow rates and equipment inlet/outlet pressures as **unknowns (variables)**
- **Internal specifications**: mass balance across every equipment + ΔP across every pipe
- **User specifications**: additional pressures, flows, equipment sizes the user provides
- Key rule: `number of user specs == number of remaining unknowns`
- **Specs vs Inputs**: KORF distinguishes SPECIFIED values (counted) from INPUT values (diameter, length, properties — not counted). Specify flow on only ONE pipe in a series circuit.
- **Multi-case simulation**: multiple operating scenarios in one run, semicolon-delimited values (`"50;55;20"`)
- The marker `";C"` means a value was calculated by KORF
- **Equipment types table** — list every type with its KDF tag, pyKorf class, and one-line description:
  - `\PIPE` → `Pipe`, `\PUMP` → `Pump`, `\FEED` → `Feed`, `\PROD` → `Product`
  - `\VALVE` → `Valve`, `\CHECK` → `CheckValve`, `\FO` → `FlowOrifice`
  - `\HX` → `HeatExchanger`, `\COMP` → `Compressor`, `\EXPAND` → `Expander`
  - `\JUNC` → `Junction`, `\TEE` → `Tee`, `\VESSEL` → `Vessel`, `\MISC` → `MiscEquipment`
- **Recycle circuits** need a junction/vessel with a feed/product line
- **Choked flow**: KORF supports compressible fluids including choked flow
- **Process methodology**: KORF can also do Heat & Mole Balance (HMB) and flash calculations

---

### Section 2 – Package Architecture (Markdown only)

Show this directory tree:

```
pykorf/
├── __init__.py      ← public API: KorfModel, CaseSet, Results, open_ui
├── model.py         ← KorfModel  – top-level container
├── parser.py        ← KdfParser  – low-level CSV tokeniser/serialiser
├── cases.py         ← CaseSet    – multi-case helpers
├── results.py       ← Results    – extract calculated output values
├── automation.py    ← KorfApp    – pywinauto GUI wrapper (connect-only)
├── exceptions.py    ← KorfError, ParseError, ElementNotFound, etc.
├── utils.py         ← CSV parsing, multi-case helpers
└── elements/        ← one class per KORF element type
    ├── base.py      ← BaseElement (shared record access)
    ├── pipe.py, pump.py, feed.py, prod.py, valve.py …
```

Show the data-flow diagram:

```
.kdf file → KdfParser.load() → list[KdfRecord] → KorfModel
                                                    ├── .general
                                                    ├── .pipes
                                                    ├── .pumps  …
                                                    (edit in memory)
                                                    → KdfParser.save() → .kdf file
```

Explain that every element object holds a **live reference** to the parser — changes immediately affect the record list.

---

### Section 3 – Safety Rule (Markdown only)

Show the ❌ forbidden patterns (`Application().start()`, `subprocess.Popen`, `os.startfile`) and the ✅ safe pattern (`KorfApp.connect()`). State that sections 1–14 work entirely on disk and never touch the KORF executable.

---

### Section: Setup – Imports & Paths (Code cell)

```python
import sys, pprint
from pathlib import Path

REPO_ROOT = Path(".").resolve()
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pykorf import KorfModel, CaseSet, Results
from pykorf.parser import KdfParser
from pykorf.utils import split_cases, join_cases, is_calculated

KDF_FILE = REPO_ROOT / "library" / "Pumpcases.kdf"
print(f"pyKorf ready.  Sample file: {KDF_FILE}")
```

---

### Section 4 – Loading a Model

**Markdown**: Explain `KorfModel.load()`, latin-1 encoding, index 0 = template, indices ≥1 = real instances.

**Code**: Load `Pumpcases.kdf`, print `repr(model)` and `model.summary()`.

---

### Section 5 – General Settings & Cases

**Markdown**: Table of `model.general` properties: `company`, `project`, `units`, `patm`, `case_numbers`, `case_descriptions`, `num_cases`, `compressibility_model`, `two_phase_model`. Explain what cases represent.

**Code**: Print every property of `model.general`.

---

### Section 6 – Multi-Case Concepts

**Markdown**: Explain semicolon-delimited values, `split_cases`, `join_cases`, `is_calculated`, and the `CaseSet` class with its methods.

**Code cell 1**: Demo `split_cases`, `join_cases`, `is_calculated`.

**Code cell 2**: Create `CaseSet(model)`, show `names`, `numbers`, `count`, `get_case_value()`, `set_case_value()`, and `pipe_flows_table()`.

---

### Section 7 – Working with Pipes

**Markdown**: Explain the `Pipe` class. Table of all properties grouped by category:
- Geometry: `diameter_inch`, `schedule`, `id_m`, `length_m`, `material`, `roughness_m`, `elevation_m`, `equivalent_length_m`
- Fluid: `liquid_density`, `liquid_viscosity`
- Flow spec: `flow_string`, `get_flow()`, `flow_unit`
- Results: `velocity`, `pressure`, `pressure_drop_per_100m`, `reynolds_number`, `flow_regime`

Explain KORF pipe data requirements and that flow should only be specified on ONE pipe in a series circuit.

**Code cell 1**: Inspect `pipe1` in detail — all geometry, fluid, flow, and result properties.

**Code cell 2**: Loop over all pipes and call `pipe.summary()`.

---

### Section 8 – Working with Pumps & Performance Curves

**Markdown**: Explain the two pump operating modes (specified ΔP vs performance curve). Explain performance curves (Q-H, Q-eff, Q-NPSH). Explain NPSH concept. Table of all `Pump` properties.

**Code**: Inspect `pump1` — type, connections, DP, efficiency, results (head, flow, power, NPSH), curve data, `has_curve`, and `summary()`.

---

### Section 9 – Feeds & Products (Boundary Conditions)

**Markdown**: Explain Feed = inlet boundary, Product = outlet boundary. At least one pressure must be specified. Show the `set_pressure()` API (list, string, single value forms).

**Code**: Loop over all feeds and products, print their properties and a few raw records.

---

### Section 10 – Valves & Orifices

**Markdown**: Explain control valve spec modes (ΔP, Cv+opening, unspecified). Explain flow orifices. Note the ΔP sign convention (drawing direction, not flow direction).

**Code**: Loop over valves (if any) showing all properties. Loop over orifices (if any).

---

### Section 11 – Other Equipment Types

**Markdown**: Explain that all elements inherit from `BaseElement` with shared `.name`, `.description`, `.notes`, `.records()`.

**Code**: Loop over `model.exchangers`, `model.compressors`, `model.expanders`, `model.junctions`, `model.tees`, `model.vessels`, `model.check_valves`, `model.misc_equipment` — print count and names for any that exist.

---

### Section 12 – Editing Values & Saving

**Markdown**: Table of ALL edit methods available:
- `Pipe.set_flow()`, `Pipe.length_m = ...`
- `Feed.set_pressure()`, `Product.set_pressure()`
- `Pump.set_dp()`, `Pump.set_efficiency()`, `Pump.set_curve()`
- `Valve.set_dp()`, `Valve.set_opening()`
- `CaseSet.set_pipe_flows()`, `CaseSet.set_feed_pressures()`, `CaseSet.set_product_pressures()`, `CaseSet.activate_cases()`
- `General.set_cases()`
- `BaseElement.notes = "..."`

Explain save behaviour: `model.save()` overwrites, `model.save_as()` writes to new file. Parser preserves exact line order for round-trip fidelity.

**Code cell 1**: Load a copy, edit pipe flow (`set_flow([60, 65, 25])`), override pump efficiency (`set_efficiency(0.72)`), activate cases 1 & 2 (`activate_cases([1, 2])`), save to `Pumpcases_work.kdf`, reload and verify round-trip.

**Code cell 2**: Demo `pump.set_curve()` with sample Q/H/eff/NPSH data.

---

### Section 13 – Parser Internals

**Markdown**: Explain `KdfRecord` dataclass fields (`element_type`, `index`, `param`, `values`, `raw_line`). Explain low-level access via `parser.get()`, `parser.set_value()`, `parser.get_all()`. Describe the KDF file format (latin-1, CSV, `"\TYPE",idx,"PARAM",...`, version header, `NUM` records).

**Code cell 1**: Load parser, show total records, version, instance counts, first 10 structured records.

**Code cell 2**: Demo `parser.get("PIPE", 1, "TFLOW")` — show `.key()`, `.values`, `.to_line()`. Show `parser.get_all("PUMP", 1)` first 8 records.

---

### Section 14 – Results Extraction

**Markdown**: Table of all `Results` methods and what they return. Explain that results are embedded in the `.kdf` after a KORF run (`;C` marker).

**Code cell 1**: Load model, create `Results(model)`. Show `pump_summary(1)`, `all_pump_results()`, `pipe_velocities()`, `pipe_pressures()`, `pipe_dp_per_100m()`, `valve_dp()`, `orifice_dp()`.

**Code cell 2**: Demo `res.to_dataframe()` with try/except for missing pandas.

---

### Section 15 – KORF GUI Automation (`KorfApp`)

**Markdown**: Full documentation of `KorfApp` methods (table). Show `open_ui()` one-liner. Show context-manager form. Include the confirmed KORF menu structure tree (from live inspection):

```
Hy&draulics
  ├── &Title
  ├── &Cases
  ├── &Specifications
  ├── &Hydraulics
  │     ├── &Run
  │     ├── R&esume
  │     └── &Stop
  └── &Results
        ├── &View Report
        ├── &Save Report
        ├── View &RunLog
        ├── Save Run&Log
        └── View E&xcel Report
```

Note that pywinauto strips `&` during matching. Add warning that these cells require KORF to be open.

**Code cell 1**: Connect (`KorfApp.connect()`), wrapped in try/except, set `korf = None` on failure.

**Code cell 2**: Reload working model (`korf.reload_model(WORK_FILE)`).

**Code cell 3**: Run hydraulics + wait for run.

**Code cell 4**: Save and disconnect.

All automation cells should guard with `if korf is not None:`.

---

### Section 16 – Full End-to-End Automation Cycle

**Markdown**: Explain the 9-step workflow pattern (load → edit → save → connect → run → wait → save → disconnect → extract). Note this enables parameter sweeps from Python.

**Code cell 1**: Define `run_scenario()` function that does the full cycle. Call it once with sample flow rates.

**Code cell 2**: Parameter sweep — loop over flows `[40, 50, 60, 70, 80]`, edit + save each to `sweep_N.kdf` (no KORF required for this part).

---

### Cleanup Section

**Code**: Delete generated files (`sweep_*.kdf`, `Pumpcases_work.kdf`, `Pumpcases_result.kdf`).

---

## Style Guidelines

- Use `pprint.pprint()` for dicts and lists
- Clear all cell outputs (set `execution_count: null`, `outputs: []`)
- Keep the existing kernel metadata (`pykorf` / `python3` / `3.13.12`)
- Use `KORF_PATH = r"C:\Program Files (x86)\Korf 36\Korf_36.exe"` consistently
- Path constants: `REPO_ROOT`, `KDF_FILE`, `WORK_FILE`, `OUTPUT_FILE`
- Every code cell should produce visible output via `print()`
- Reference `library/korf_manual.md` concepts where relevant
