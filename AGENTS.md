# pyKorf — AI Agent Guide

Guidance for agentic coding assistants working in this repository. Focus on **absolute accuracy**, **system-wide integrity**, and **pragmatic completeness**.

## Environment

- **Shell**: PowerShell on Windows — use PowerShell syntax (`;` or `&&` for chaining, `$null` / `| Out-Null` instead of `/dev/null`, no bash heredocs).
- **Python**: Managed via `uv`. Always prefix commands with `uv run` — never call `python` directly.
- **Python version**: 3.13 exactly (enforced in `pyproject.toml` and `.python-version`).

## Build, Lint & Test Commands

```bash
# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/test_model_api.py -v

# Run a single test class
uv run pytest tests/test_model_api.py::TestModelConstructor -v

# Run a single test method
uv run pytest tests/test_model_api.py::TestModelConstructor::test_model_no_args_creates_default -v

# Run with specific markers
uv run pytest -m unit           # Unit tests only
uv run pytest -m integration    # Integration tests
uv run pytest -m "not slow"     # Exclude slow tests

# Lint (ruff — covers isort, pyflakes, pycodestyle, and more)
uv run ruff check pykorf tests

# Format code
uv run ruff format pykorf tests

# Type check (mypy with relaxed strict mode)
uv run mypy pykorf

# Launch the application
uv run pykorf
uv run pykorf --port 9000
uv run pykorf --debug
```

## Code Style Guidelines

### Imports
- Use `from __future__ import annotations` at the top of every file
- Group imports: stdlib → third-party → first-party (`pykorf`)
- Use explicit imports (no `from module import *`)
- Use `import tomllib` for TOML files (stdlib in Python 3.13)

### Formatting
- **Ruff** handles all formatting (line-length: 100)
- Use double quotes for strings
- Trailing commas are optional
- Follow existing patterns in the codebase over strict rules

### Types
- Use `TYPE_CHECKING` blocks for imports used only for type hints
- New code should be fully typed
- Use modern syntax: `str | None` not `Optional[str]`, `list[int]` not `List[int]`
- Mypy is configured with relaxed strict mode — focus on practical type safety

### Naming Conventions
- **Modules**: snake_case (`pipe_criteria.py`)
- **Classes**: PascalCase (`Model`, `ElementService`)
- **Functions/Methods**: snake_case (`get_element_by_name`)
- **Constants**: UPPER_SNAKE_CASE (`ELEMENT_REGISTRY`)
- **Private members**: Leading underscore (`_element_service`)
- Allow unit suffixes like `kPag`, `kW` in variable names

### Error Handling
- Use specific exception types from `pykorf.exceptions`
- Prefer `try/except` over `contextlib.suppress` for clarity
- Log errors with `structlog` before raising where appropriate
- In FastAPI routes, raise `UseCaseError` or `KorfError`; the registered exception handlers in `app.py` convert these to JSON responses

### Docstrings
- Google style docstrings
- Required for public modules, classes, and functions
- OK to skip docstrings for tests and private methods

## Architecture Overview

pyKorf is a toolkit for reading, editing, and writing KORF hydraulic model files (`.kdf`).

### Model Layer (`pykorf/model/`)

Public surface: `Model` (alias `KorfModel`), a facade that delegates to six services:

| Service | Attribute | Responsibility |
|---|---|---|
| `ElementService` | `model._element_service` | CRUD for elements (add, update, delete, copy, move) |
| `QueryService` | `model.query` | Filtering, parameter get/set |
| `ConnectivityService` | `model._connectivity_service` | Connect/disconnect elements, pipe reference validation |
| `LayoutService` | `model._layout_service` | XY positioning, visualization |
| `IOService` | `model._io_service` | save, to_dataframes, to_excel, from_excel |
| `SummaryService` | `model._summary_service` | validate() (core layer), summary(), element accessors |

`Model(path)` parses `.kdf` via `KdfParser` into memory. Changes persist only on `model.io.save()`.

**Validation architecture:** `Model.validate()` combines three layers:
1. **Core** (`SummaryService`) — pipe sizing criteria from KDF SIZ records, title symbol check
2. **App** (`pykorf.app.validation`) — PMS spec compliance, line-number parsing, pipe properties
3. **Connectivity** (`ConnectivityService`) — dangling references, unconnected elements

### Element Types (`pykorf/elements/`)

17 typed element types. `ELEMENT_REGISTRY` maps KDF tokens (e.g. `\PIPE`) to classes. Multi-case parameters stored as semicolon-separated strings.

### Web Layer (`pykorf/app/api/` + `pykorf/app/frontend/`)

Single-user, localhost-only FastAPI + Vue 3 SPA application. Entry point: `pykorf.__main__:main` → `run_server()` → uvicorn serving `create_app()`. The built Vue SPA lives in `pykorf/app/frontend/dist/`; FastAPI serves it via a catch-all `/{path:path}` route.

**Session State** (`pykorf/app/api/session_state.py`): One model lives in process memory at a time. Async-safe via `asyncio.Lock`. Key functions:
- `load(model, kdf_path)` / `load_sync(...)` — store model after opening
- `get_model()` / `get_kdf_path()` — async accessors
- `reload()` / `reload_sync()` — re-parse KDF from disk; call after every `model.io.save()`
- `is_stale()` / `is_stale_sync()` — detect if KDF changed externally (e.g., by KORF GUI)
- `flag_reload()` / `pop_reload_flag()` — stale-header flag for `_StaleHeaderMiddleware`

Use `_sync` variants inside `asyncio.to_thread()` callbacks; use async variants in route handlers.

**External Change Detection**: `require_model()` in `pykorf.app.api.deps` auto-reloads when the KDF is stale and sets the `X-Model-Stale: true` response header via middleware. The frontend axios client intercepts this header and shows a reload toast. KORF GUI changes always take priority.

**Route Guards**: Routes requiring an active model use:
```python
from pykorf.app.api.deps import require_model
model = await require_model()
```
401/409 from any route causes the axios client to redirect to `/`.

**Routers** (`pykorf/app/api/routers/`): `session`, `model`, `data`, `settings`, `report`, `browse`, `doc_register`, `preferences`, `references`, `about` — all mounted under `/api/*`.

**Frontend** (`pykorf/app/frontend/`): Vue 3 + Vite + Pinia + Tailwind CSS + TypeScript.
- `src/stores/session.ts` — model status, `skipSpOverride` (doc register search guard), `kdfPath`
- `src/types/api.ts` — Pydantic-mirrored TypeScript interfaces (auto-generated via `npm run build-types`)
- `npm run dev` (from `pykorf/app/frontend/`) — HMR dev server, proxies `/api/*` to localhost:8000
- `npm run build` — produces `dist/` consumed by FastAPI
- `npm run build-types` — generates TypeScript types from OpenAPI schema (`/openapi.json`)

### Import Rules

**Always import from `pykorf.app.operation.config.config`** in routes, not sub-modules (`preferences.py`, `pms.py`, etc.) directly.

## Test Patterns

```python
SAMPLES_DIR = Path(__file__).parent.parent / "pykorf" / "library"
model = KorfModel.load(SAMPLES_DIR / "Pumpcases.kdf")
```

Test markers: `unit`, `integration`, `slow`, `automation` (requires KORF GUI installed).

## Critical Rules

- **NEVER** launch a new KORF process. Always `Application().connect(path="korf.exe")`.
- **NEVER** use hardcoded strings for element types/params. Use `pykorf.elements` constants.
- **NEVER** delete files to resolve errors. Fix or rewrite tests; don't delete them.
- All model operations are **in-memory**. Persistent only on `model.save()`.
- Use `uv` for all package management and running commands.
- After `model.io.save()`, always call `session_state.reload_sync()` (inside `asyncio.to_thread`) so in-memory state matches disk.
- **KORF data priority**: If KDF file is modified externally (e.g., by KORF GUI), pyKorf automatically reloads from disk on next navigation. Unsaved pyKorf changes are discarded — users should save before switching applications.

## Guardrails

- **Global Research**: Before refactoring, use grep/glob to map all dependencies and callsites.
- **Safe Rollbacks**: Use `git stash` or branches for complex changes.
- **Exhaustive Validation**: After any change, run `uv run pytest`, `uv run ruff check pykorf tests`, and `uv run mypy pykorf`.
- **Multi-File Changes**: When a feature spans 2+ files, present options with tradeoffs before implementing.
- **Definition of Done**: Conclude sessions with: files changed, architectural decisions, and validation suite output.
