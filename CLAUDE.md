# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment

- **Shell**: PowerShell on Windows. Use PowerShell syntax — `;` or `&&` for chaining, `$null` / `| Out-Null` instead of `/dev/null`.
- **Python**: Managed via `uv`. Always prefix commands with `uv run`.
- **Python version**: 3.13 exactly (enforced in `pyproject.toml` and `.python-version`).

## Common Commands

```bash
# Run all tests
uv run pytest

# Run a single test file or test
uv run pytest tests/test_model_api.py
uv run pytest tests/test_model_api.py::TestModelConstructor::test_model_no_args_creates_default

# Lint (ruff)
uv run ruff check pykorf tests

# Type check
uv run mypy pykorf

# Launch the web application
uv run pykorf
uv run pykorf --port 9000
uv run pykorf --debug
```

## Architecture Overview

pyKorf is a toolkit for reading, editing, and writing KORF hydraulic model files (`.kdf`). There are two main layers: a **model API** and a **Flask web application**.

### Model Layer (`pykorf/model/`)

The public surface is `Model` (alias `KorfModel`), a facade that delegates to six services:

| Service | Attribute | Responsibility |
|---|---|---|
| `ElementService` | `model._element_service` | CRUD for elements (add, update, delete, copy, move) |
| `QueryService` | `model.query` | Filtering, parameter get/set |
| `ConnectivityService` | `model.connectivity` | Connect/disconnect elements, validation |
| `LayoutService` | `model.layout` | XY positioning, visualization |
| `IOService` | `model.io` | save, to_dataframes, to_excel, from_excel |
| `SummaryService` | `model.summary_service` | validate, repr, element accessors |

`Model(path)` parses the `.kdf` file via `KdfParser` into an in-memory structure. Changes are not persisted until `model.io.save()` is called.

Element types (17 total) are typed wrappers in `pykorf/elements/`. The `ELEMENT_REGISTRY` in `elements/__init__.py` maps KDF tokens (e.g. `\PIPE`) to element classes. Multi-case parameters are stored as semicolon-separated strings.

### Web Layer (`pykorf/use_case/web/`)

Single-user, localhost-only Flask application. Entry point: `pykorf.cli:main` → `run_server()`.

#### Session State (`session.py`)

No cookies or database — one model lives in process memory at a time. Key functions:
- `load(model, kdf_path)` — store model after opening a file
- `get_model()` / `get_kdf_path()` — retrieve active model
- `reload()` — re-parse KDF from disk; call this after every `model.io.save()` so the UI reflects what was actually persisted
- `clear()` — unload model

#### Route Blueprints (`routes/`)

All routes except `/` and `/preferences` require an active session model; `require_model()` + `is_redirect()` in `helpers.py` enforce this. The standard guard is:
```python
model = require_model()
if is_redirect(model):
    return model
```

| Blueprint | URL | Purpose |
|---|---|---|
| `file_picker` | `/`, `/open` | KDF file picker; loads model into session |
| `model_core` | `/model`, `/model/save` | Main menu (summary + prereq checks); save + reload |
| `data` | `/model/data` | Apply PMS or HMB Excel data to model |
| `settings` | `/model/settings` | Apply global parameter presets |
| `report` | `/model/report` | Generate report, batch report, export/import Excel |
| `model_info` | `/model/info` | Model stats, pipe list, validation issues |
| `bulk_copy` | `/model/bulk-copy` | Bulk copy fluids between pipes |
| `references` | `/model/references` | Design basis and reference links manager |
| `preferences` | `/preferences` | SharePoint path overrides |
| `browse` | `/api/browse` | Directory listing API for path picker widgets |

#### App Wiring (`app.py`)

`create_app()` registers all 10 blueprints and adds custom Jinja2 filters: `split`, `basename`, `dirname`, `ternary`.

### Use Case / Preferences Layer (`pykorf/use_case/`)

- `preferences.py` — All user config (JSON via `appdirs`). Functions: `get_recent_files`, `get_last_kdf_path`, `get_pms_excel_path`, `get_sp_overrides`, `get_global_parameters_selected`, etc.
- `config.py` — Facade that re-exports from `preferences.py`, `paths.py`, `pms.py`, `hmb.py`. **Import from `config.py` in routes, not sub-modules directly.**
- `processor.py` — `PipedataProcessor`: main orchestrator for PMS/HMB workflows.
- `pms.py` / `hmb.py` — Excel readers for Piping Material Spec and Heat & Material Balance data.
- `batch_report.py` — `BatchReportGenerator`: generates a combined report across multiple `.kdf` files in a folder.
- `global_parameters.py` — Four preset bulk-modification functions registered in `_GLOBAL_SETTINGS`:
  1. `dummy_pipe` — Set LEN/ID/SCH/LBL on pipes starting with "d"; hide all junction labels
  2. `dp_margin` — Apply `DP_DES_FAC` to all pipes (default 1.25)
  3. `rename_line` — Extract line number from NOTES field and rename pipe; propagates to EQN records
  4. `pipe_criteria` — Apply SIZ parameter (dP/dL + velocity bounds) to all pipes

### Sizing Criteria Data (`pykorf/reports/`)

Three TOML files (read via stdlib `tomllib`) define hydraulic line sizing lookup tables. Each entry has `code`, `service`, optional `pressure`, optional `line_size`, `vel = [min, max]`, `dp = [normal, max]` fields. Lookup pattern: filter by `code` → sort by the filter dimension → first entry where value ≤ threshold. Omitting `line_size` or `pressure` means no upper limit (catch-all row). `vel[1] = 0.0` or `dp[1] = 0.0` means no criterion for that bound (`CriteriaValues.max_vel` / `max_dp` → `None`).

| File | Fluid type | Filter dimensions | Extra fields |
|---|---|---|---|
| `sizing_criteria_liquid.toml` | Liquid | `line_size`, `pressure` (P-DIS only) | — |
| `sizing_criteria_gas.toml` | Gas / Steam | `pressure`, `line_size` | `rho_v2` (ρV² momentum limit) |
| `sizing_criteria_twophase.toml` | Two-phase | none (single entry) | `rho_v2` [min,max], `rho_v3` [min,max] |

dp values are in **kPa/100m** (source tables are bar/100m; multiplied ×100). All three files are included in `package-data` via `"reports/*.toml"`.

### Parser (`pykorf/parser.py`)

`KdfParser` tokenises raw `.kdf` text into `KdfRecord` objects. The model layer consumes this; you rarely need to touch the parser directly.

### CLI (`pykorf/cli.py`)

Web-only since v0.5.0 (TUI removed). `main()` runs: splash screen → trial check → update check → `run_server(port)`. Arguments: `--port` (default 8000), `--trial`, `--debug`.

## Test Patterns

Tests live in `tests/` and use sample `.kdf` files from `pykorf/library/` (`Pumpcases.kdf`, `crane10.kdf`, `Cooling Water Circuit.kdf`).

```python
SAMPLES_DIR = Path(__file__).parent.parent / "pykorf" / "library"
model = KorfModel.load(SAMPLES_DIR / "Pumpcases.kdf")
```

Test markers available: `unit`, `integration`, `slow`, `automation` (automation tests require the KORF GUI to be installed).

## Code Style

- **Docstrings**: Google style
- **Linting**: ruff (isort, pyflakes, pycodestyle, and more — see `pyproject.toml`)
- **Types**: mypy with relaxed strict mode; new code should be fully typed

## Key Constraints

- **Shell**: PowerShell — use PowerShell syntax (`$null`, `;` chaining, no heredocs).
- **Zero-destruction policy**: Never delete files to resolve errors.
- **Global research before refactoring**: Use grep/glob to find all usages before renaming or moving anything.
- **Full validation before finishing**: `uv run pytest` + `uv run ruff check pykorf tests` + `uv run mypy pykorf` must all pass.
- **Safe rollbacks**: Use `git stash` or feature branches for complex changes.
- **Config imports**: Always import preference functions from `pykorf.use_case.config`, not from sub-modules.
- **Model save + reload**: After `model.io.save()`, always call `_sess.reload()` so the in-memory state matches disk.
