---
name: automation
description: KORF GUI automation via pywinauto — KorfApp, connect pattern, safety rules
---

# KORF GUI Automation

## CRITICAL SAFETY RULE

**NEVER launch a new KORF process.** KORF limits file opens to 5 times.

```python
# CORRECT — connect to running instance
app = KorfApp.connect(korf_path="korf.exe")

# WRONG — NEVER do this
app = Application().start("korf.exe")
subprocess.Popen("korf.exe")
```

## KorfApp API

```python
from pykorf.automation import KorfApp, open_ui
# Also available as a top-level shortcut:
# from pykorf import open_ui

# Connect to running KORF
app = KorfApp.connect()

# One-liner: connect + open file
app = open_ui("model.kdf")

# Operations
app.reload_model("model.kdf")   # Ctrl+O → load file
app.run_hydraulics()             # trigger calculation
app.save()                       # Ctrl+S
app.disconnect()                 # release handle
```

## Requirements

- Windows only (uses `pywinauto`)
- KORF must already be running before calling `connect()`
- Install: `pip install pywinauto` (optional dependency)
- Raises `AutomationError` if KORF not found

## Test Marker

```python
@pytest.mark.automation  # skipped by default: pytest -m "not automation"
```

## Key Files

- `pykorf/automation.py` — `KorfApp` class, `open_ui()` helper
- `tests/test_automation.py` — automation tests (require running KORF)
