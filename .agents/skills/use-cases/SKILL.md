---
name: use-cases
description: Workflows for PMS, HMB, Global Settings, multi-case (CaseSet), Results extraction, and Textual TUI management
---

# pyKorf Use Cases & TUI

## Core Workflows
The `pykorf.use_case` module handles bulk updates to KDF files using external data sources.
- **PMS (Piping Material Specification):** Maps line numbers (from `NOTES`) to pipe sizes/schedules. Extracted via `pykorf/use_case/pms.py`.
- **HMB (Heat and Material Balance):** Maps stream numbers to fluid properties. Extracted via `pykorf/use_case/hmb.py` and applied directly using `pykorf.fluid.Fluid`.
- **Global Settings:** Applies bulk structural changes (e.g., dummy pipe adjustments, design margins) via `pykorf/use_case/global_settings.py`.

## Multi-Case Management (`CaseSet`)
KORF supports running multiple scenarios (cases) in a single file. Each case is identified by its 1-based position in the semicolon-delimited value strings.

```python
from pykorf import Model, CaseSet
model = Model("Pumpcases.kdf")
cases = CaseSet(model)

print(cases.names)  # ['NORMAL', 'RATED', 'MINIMUM']
cases.activate_cases([1, 2]) # Activate only specific cases
cases.set_pipe_flows(1, [50, 55, 20])
```

## Results Extraction (`Results`)
After KORF calculates and saves the model, use the `Results` helper to extract values.

```python
from pykorf import Model, Results
model = Model("Calculated.kdf")
res = Results(model)

pumps = res.all_pump_results() # [{name, head_m, power_kW, ...}, ...]
velocities = res.pipe_velocities() # {pipe_index: [v1, v2, v3]}
df = res.to_dataframe() # Export to pandas
```

## Textual TUI Architecture
Located in `pykorf/use_case/tui/`:
- `app.py`: Main application (`UseCaseTUI`) with global bindings (R: Reload, Q: Quit, Esc: Back).
- `screens/`: Individual UI states.
- **File Picker Screen:** Supports long paths via multiline `TextArea` and includes a `Clear` button.
- **Header:** Displayed at the top, showing only the KDF filename (not full path).
- **Async Execution:** Heavy operations (applying PMS/HMB) MUST be run in a background thread using Textual's `@work(thread=True)` decorator.
- **UI Updates:** When updating the UI from a background thread, use `self.app.call_from_thread(...)`.
- **Logging:** Use `pykorf/use_case/tui/logging.py` helpers (`log_info`, `log_error`) to output to the `RichLog` widgets.
