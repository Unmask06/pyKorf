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
- In Flask routes, collect errors in lists and display to user

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
| `ConnectivityService` | `model.connectivity` | Connect/disconnect elements, validation |
| `LayoutService` | `model.layout` | XY positioning, visualization |
| `IOService` | `model.io` | save, to_dataframes, to_excel, from_excel |
| `SummaryService` | `model.summary_service` | validate, repr, element accessors |

`Model(path)` parses `.kdf` via `KdfParser` into memory. Changes persist only on `model.io.save()`.

### Element Types (`pykorf/elements/`)

17 typed element types. `ELEMENT_REGISTRY` maps KDF tokens (e.g. `\PIPE`) to classes. Multi-case parameters stored as semicolon-separated strings.

### Web Layer (`pykorf/use_case/web/`)

Single-user, localhost-only Flask application. Entry point: `pykorf.cli:main`.

**Session State** (`session.py`): One model lives in process memory at a time. Key functions:
- `load(model, kdf_path)` — store model after opening
- `get_model()` / `get_kdf_path()` — retrieve active model
- `reload()` — re-parse KDF from disk (call after every `model.io.save()`)

**Route Guards**: All routes except `/` and `/preferences` require active session:
```python
model = require_model()
if is_redirect(model):
    return model
```

### Import Rules

**Always import from `pykorf.use_case.config`** in routes, not sub-modules (`preferences.py`, `pms.py`, etc.) directly.

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
- After `model.io.save()`, always call `_sess.reload()` so in-memory state matches disk.

## Guardrails

- **Global Research**: Before refactoring, use grep/glob to map all dependencies and callsites.
- **Safe Rollbacks**: Use `git stash` or branches for complex changes.
- **Exhaustive Validation**: After any change, run `uv run pytest`, `uv run ruff check pykorf tests`, and `uv run mypy pykorf`.
- **Multi-File Changes**: When a feature spans 2+ files, present options with tradeoffs before implementing.
- **Definition of Done**: Conclude sessions with: files changed, architectural decisions, and validation suite output.
