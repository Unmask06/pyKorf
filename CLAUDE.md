# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment

- **Shell**: Git Bash on Windows. Use Unix syntax — `&&` for chaining, forward slashes in paths, `/dev/null` not `NUL`.
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

# Run the TUI application
uv run pykorf
uv run pykorf --debug
```

## Architecture Overview

pyKorf is a toolkit for reading, editing, and writing KORF hydraulic model files (`.kdf`). There are two main layers: a **model API** and a **TUI application**.

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

### TUI Layer (`pykorf/use_case/tui/`)

Built with [Textual](https://textual.textualize.io/). Entry point: `pykorf.cli:main` → `run_tui()` → `UseCaseTUI` app.

Screen navigation flow:
```
FilePickerScreen → MainMenuScreen → [operation screens]
```

Operation screens in `pykorf/use_case/tui/screens/`:
- `apply_pms.py` — Apply Piping Material Spec data
- `apply_hmb.py` — Apply Heat & Material Balance data
- `generate_report.py` — Batch report generation
- `bulk_copy.py` — Bulk element copying
- `global_settings.py` — Global pipe criteria
- `import_export.py` — Excel/JSON/YAML import/export
- `config_menu.py` / `model_info.py` — Config and info views

### Use Case / Preferences Layer (`pykorf/use_case/`)

- `preferences.py` — All user config (JSON via `appdirs`). Functions: `get_recent_files`, `add_recent_file`, `get_last_kdf_path`, `set_last_kdf_path`, etc.
- `config.py` — Facade that re-exports from `preferences.py`, `paths.py`, `pms.py`, `hmb.py`. **Import from `config.py` in TUI screens, not from the sub-modules directly.**
- `processor.py` — `PipedataProcessor`: main orchestrator for PMS/HMB workflows.
- `pms.py` / `hmb.py` — Excel readers for Piping Material Spec and Heat & Material Balance data.
- `batch_report.py` — Batch report generation across multiple `.kdf` files.

### Parser (`pykorf/parser.py`)

`KdfParser` tokenises raw `.kdf` text into `KdfRecord` objects. The model layer consumes this; you rarely need to touch the parser directly.

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

## Key Constraints from AGENTS.md

- **Shell**: Git Bash — use Unix syntax even though the OS is Windows.
- **Zero-destruction policy**: Never delete files to resolve errors.
- **Global research before refactoring**: Use grep/glob to find all usages before renaming or moving anything.
- **Full validation before finishing**: `uv run pytest` + `uv run ruff check pykorf tests` + `uv run mypy pykorf` must all pass.
- **Safe rollbacks**: Use `git stash` or feature branches for complex changes.
