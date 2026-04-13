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

# Frontend development (from pykorf/app/frontend/)
npm run dev      # Dev server with HMR
npm run build    # Build dist/ for production
```

## Architecture Overview

pyKorf is a toolkit for reading, editing, and writing KORF hydraulic model files (`.kdf`). There are two main layers: a **model API** and a **FastAPI + Vue SPA web application**.

### Model Layer (`pykorf/model/`)

The public surface is `Model` (alias `KorfModel`), a facade that delegates to six services:

| Service | Attribute | Responsibility |
|---|---|---|
| `ElementService` | `model._element_service` | CRUD for elements (add, update, delete, copy, move) |
| `QueryService` | `model.query` | Filtering, parameter get/set |
| `ConnectivityService` | `model._connectivity_service` | Connect/disconnect elements, pipe reference validation |
| `LayoutService` | `model._layout_service` | XY positioning, visualization |
| `IOService` | `model._io_service` | save, to_dataframes, to_excel, from_excel |
| `SummaryService` | `model._summary_service` | validate() (core layer), summary(), element accessors |

`Model(path)` parses the `.kdf` file via `KdfParser` into an in-memory structure. Changes are not persisted until `model.io.save()` is called.

**Validation architecture:** `Model.validate()` combines three layers:
1. **Core** (`SummaryService`) — pipe sizing criteria from KDF SIZ records, title symbol check
2. **App** (`pykorf.app.validation`) — PMS spec compliance, line-number parsing, pipe properties
3. **Connectivity** (`ConnectivityService`) — dangling references, unconnected elements

Element types (17 total) are typed wrappers in `pykorf/elements/`. The `ELEMENT_REGISTRY` in `elements/__init__.py` maps KDF tokens (e.g. `\PIPE`) to element classes. Multi-case parameters are stored as semicolon-separated strings.

### Web Layer (`pykorf/app/api/` + `pykorf/app/frontend/`)

Single-user, localhost-only FastAPI + Vue 3 SPA application. Entry point: `pykorf.__main__:main` → `run_server()` → uvicorn serving `create_app()`.

The built Vue SPA lives in `pykorf/app/frontend/dist/`. FastAPI serves it via a catch-all `/{path:path}` route that falls back to `index.html` for client-side routing.

#### Session State (`pykorf/app/api/session_state.py`)

No cookies or database — one model lives in process memory at a time. Async-safe via `asyncio.Lock`. Key functions:

- `load(model, kdf_path)` / `load_sync(...)` — store model after opening a file
- `get_model()` / `get_kdf_path()` — async accessors
- `reload()` / `reload_sync()` — re-parse KDF from disk; call after every `model.io.save()` so UI reflects persisted state
- `is_stale()` / `is_stale_sync()` — detect if disk file is newer than in-memory model
- `flag_reload()` / `pop_reload_flag()` — used by `_StaleHeaderMiddleware` to set `X-Model-Stale: true` response header

Use `_sync` variants inside `asyncio.to_thread()` callbacks; use async variants in FastAPI route handlers.

#### FastAPI Routers (`pykorf/app/api/routers/`)

Routes requiring an active model use `require_model()` from `pykorf.app.api.deps`:
```python
from pykorf.app.api.deps import require_model
# In a route:
model = await require_model()
```
`require_model()` also auto-reloads if the KDF is stale on disk.

| Router | URL prefix | Purpose |
|---|---|---|
| `session` | `/api/session` | Status, open/close KDF, shutdown |
| `model` | `/api/model` | Summary, save, pipe list, validation, bulk-modify |
| `data` | `/api/data` | Apply PMS or HMB Excel data to model |
| `settings` | `/api/settings` | Apply global parameter presets |
| `report` | `/api/report` | Generate report, batch report, export/import Excel |
| `browse` | `/api/browse` | Directory listing for path-picker widgets; pin/unpin folders |
| `doc_register` | `/api/doc-register` | SharePoint document register search (EDDR + query) |
| `preferences` | `/api/preferences` | SharePoint path overrides |
| `references` | `/api/references` | Design basis text, remarks, hold, reference CRUD |
| `about` | `/api/about` | Version info, update check |

#### Frontend (`pykorf/app/frontend/`)

Vue 3 + Vite + Pinia + Tailwind CSS + TypeScript.

```bash
# From pykorf/app/frontend/
npm run dev      # Dev server with HMR (proxies /api/* to localhost:8000)
npm run build    # Build to dist/ for production
```

Key structure:
- `src/views/` — Page-level Vue components (one per route)
- `src/components/` — Shared components (`PathBrowser.vue`, `ReferenceSearchView.vue`, …)
- `src/stores/` — Pinia stores: `session.ts` (model status, `skipSpOverride`, `kdfPath`), `model.ts` (summary), `preferences.ts`
- `src/api/client.ts` — Axios instance; intercepts `X-Model-Stale: true` to show a reload toast and 409 to redirect to `/`
- `src/types/api.ts` — Pydantic-mirrored TypeScript interfaces for all request/response bodies

`session.skipSpOverride` controls whether the SharePoint document register search button is available (disabled when `get_skip_sp_override()` returns `True` in config).

### App Layer (`pykorf/app/operation/`)

- `config/` — User configuration: `config.py` (facade), `preferences.py` (JSON via `appdirs`), `paths.py`, `global_parameters.py`. **Import from `config.py` in routes, not sub-modules directly.**
- `data_import/` — `pms.py`, `hmb.py` (Excel readers), `line_number.py` (pipe line-number parsing).
- `processor/` — `processor.py` (`PipedataProcessor` orchestrator), `batch_report.py` (`BatchReportGenerator`), `bulk_copy.py`.
- `project/` — `project_info.py`, `pykorf_file.py` (`.pykorf` sidecar for pipe criteria), `references.py` (`.pykorf` sidecar for remarks/hold/references).
- `integration/` — `sharepoint.py`, `license.py`, `sizing_criteria.py` (criteria lookup and application).

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

### CLI (`pykorf/__main__.py`)

Web-only since v0.5.0 (TUI removed). `main()` runs: splash screen → trial check → update check → `run_server(port, debug)`. Arguments: `--port` (default 8000), `--trial`, `--debug`, `--no-debug` (user mode: reduced logging, no reloader).

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
- **Config imports**: Always import preference functions from `pykorf.app.operation.config.config`, not from sub-modules.
- **Model save + reload**: After `model.io.save()`, always call `session_state.reload_sync()` (inside `asyncio.to_thread`) so the in-memory state matches disk.
