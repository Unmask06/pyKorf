# pyKorf — AI Agent Guide

Enterprise Python toolkit for KORF hydraulic model files (`.kdf`).

## Critical Rules

- **NEVER** launch a new KORF process. Always `Application().connect(path="korf.exe")`.
- **NEVER** use hardcoded strings for element types/params. Use constants from `pykorf.elements`.
- All model operations are **in-memory**. File writes only via `model.save()` / `model.save_as()`.
- Use `uv` (not pip). Use `cmd.exe` command style.

## Quick Reference

```python
from pykorf import Model
from pykorf.elements import Element, Pipe, BaseElement

model = Model("Pumpcases.kdf")
pipe = model.pipes[1]           # Index 0 = template; real instances start at 1
model.add_element(Element.PIPE, "L1", {Pipe.LEN: 100, Pipe.DIA: 50})
model.save()
```

## Architecture

| Module                | Purpose                                           |
| --------------------- | ------------------------------------------------- |
| `pykorf.model`        | Primary `Model` API                               |
| `pykorf.parser`       | `KdfParser`, record-level load/save               |
| `pykorf.elements`     | Typed wrappers (`Pipe`, `Pump`, etc.) + constants |
| `pykorf.connectivity` | Connect/disconnect logic                          |
| `pykorf.layout`       | Positioning, clash checks                         |
| `pykorf.validation`   | KDF validation rules                              |
| `pykorf.cases`        | Multi-case utilities                              |
| `pykorf.results`      | Calculated-results extraction                     |
| `pykorf.automation`   | GUI automation (`KorfApp`)                        |
| `pykorf.export`       | JSON/YAML/Excel/CSV export                        |

## KDF Format

Encoding: `latin-1`, line endings: `\r\n`, record: `\ETYPE,index,PARAM,value1,...`
Multi-case: semicolons (`"50;55;20"`), calculated marker: `";C"`.
Versions: `KORF_2.0`, `KORF_3.0`, `KORF_3.6` (version-aware: `NOZ` vs `NOZL`).

## Code Style

- Python 3.10+, full type hints, `from __future__ import annotations`, `str | None` unions
- Google-style docstrings with markdown code blocks (not `>>>`)
- Import order: stdlib → third-party → local. Use `TYPE_CHECKING` for circular imports.
- Constants: `Element.PIPE`, `Pipe.LEN`, `BaseElement.NAME`, `BaseElement.CON`, etc.
- Add missing constants under `pykorf/definitions/` before using them.

## Commands

```
uv sync                                    # Install deps
pytest                                     # Run tests
pytest -m "not automation"                 # Skip GUI tests
ruff check pykorf tests; ruff format pykorf tests  # Lint
mypy pykorf                                # Type check
uv run mkdocs serve                        # Local docs
```

## Common Tasks

**New element type:** Create class in `pykorf/elements/`, register in `__init__.py`, add `Model` property, add tests.
**New export format:** Implement in `export.py`, options in `types.py`, CLI in `cli.py`.
**Parser changes:** Update `KdfRecord` → `KdfParser.load()` → `KdfRecord.to_line()` → ensure round-trip fidelity.

## Testing

Fixtures from `pykorf/library/`. Markers: `unit`, `integration`, `slow`, `automation`.

## Agent Workflow

- Ask clarifying questions before large changes (>5 files or breaking changes → suggest a branch).
- Small changes: proceed directly. Always verify with tests/linting.
- Use `pathlib.Path` for file ops. Validate paths. Backup before overwriting.
