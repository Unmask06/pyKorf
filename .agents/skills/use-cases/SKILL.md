---
name: use-cases
description: Workflows for PMS, HMB, Global Settings, batch processing, and the Textual TUI
---

# pyKorf Use Cases & TUI

## Core Workflows
The `pykorf.use_case` module handles bulk updates to KDF files using external data sources.
- **PMS (Piping Material Specification):** Maps line numbers (from `NOTES`) to pipe sizes/schedules. Extracted via `pykorf/use_case/pms.py`.
- **HMB (Heat and Material Balance):** Maps stream numbers to fluid properties. Extracted via `pykorf/use_case/hmb.py` and applied directly using `pykorf.fluid.Fluid`.
- **Global Settings:** Applies bulk structural changes (e.g., dummy pipe adjustments, design margins) via `pykorf/use_case/global_settings.py`.

## Line Number Parsing
Standard format: `N-AANNN-AAAA-NNN-AANANA-AAA-AA-XXX-XX`
Handled by `LineNumber` dataclass in `pykorf/use_case/line_number.py`.

## Textual TUI Architecture
Located in `pykorf/use_case/tui/`:
- `app.py`: Main application (`UseCaseTUI`).
- `screens/`: Individual UI states (`MainMenuScreen`, `ApplyPmsScreen`, `FilePickerScreen`, etc.).
- **Async Execution:** Heavy operations (applying PMS/HMB) MUST be run in a background thread using Textual's `@work(thread=True)` decorator to prevent blocking the UI.
- **UI Updates:** When updating the UI from a background thread, use `self.app.call_from_thread(...)`.
- **Logging:** Use `pykorf/use_case/tui/logging.py` helpers (`log_info`, `log_error`) to output to the `RichLog` widgets.
