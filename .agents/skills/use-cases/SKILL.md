---
name: use-cases
description: Workflows for PMS, HMB, Global Settings, multi-case management (CaseSet), and Results extraction
---

# pyKorf Use Cases & Workflow

## Core Workflows
The `pykorf.use_case` module handles bulk updates to KDF files using external data sources.

### PMS (Piping Material Specification)
Maps line numbers (stored in `NOTES`) to pipe sizes/schedules.
- **Data Source:** CSV/Excel containing pipe specifications.
- **Logic:** Extracts line numbers using `LineNumber` parser, looks up spec, updates `DIA`, `SCH`, `MAT`.

### HMB (Heat and Material Balance)
Maps stream numbers to fluid physical properties.
- **Fluid Class:** Use `pykorf.fluid.Fluid` to encapsulate properties (density, viscosity, etc.).
- **Application:** `pipe.set_fluid(fluid_obj)` directly updates the KDF records.

```python
from pykorf.fluid import Fluid
fluid = Fluid(temp=52.25, pres=398.7, liqden=570.2, liqvisc=0.15)
pipe.set_fluid(fluid) # Updates TEMP, PRES, LIQDEN, LIQVISC records
```

### Global Settings
Applies bulk structural changes (dummy pipe adjustments, design margins) via `pykorf/use_case/global_settings.py`.

## Multi-Case Management (`CaseSet`)
KORF supports multiple scenarios (cases) in one file. Each case is a semicolon-delimited value.

```python
from pykorf import Model, CaseSet
model = Model("Pumpcases.kdf")
cases = CaseSet(model)

print(cases.names)  # ['NORMAL', 'RATED', 'MINIMUM']
cases.activate_cases([1, 2]) # Activate/Deactivate specific cases
cases.set_pipe_flows(1, [50, 55, 20]) # Set flows for all cases
```

## Results Extraction (`Results`)
Extract calculated values after a KORF run has been saved.

```python
from pykorf import Results
res = Results(model)
pumps = res.all_pump_results()
velocities = res.pipe_velocities()
df = res.to_dataframe() # Requires pandas
```

## Textual TUI Architecture
Run the TUI via `pykorf` command or `python -m pykorf.cli`.
- **Async Execution:** Heavy operations MUST use `@work(thread=True)`.
- **Logging:** Output to `RichLog` using `pykorf/use_case/tui/logging.py` helpers.
