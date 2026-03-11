# pyKorf — AI Agent Guide

Enterprise Python toolkit for KORF hydraulic model files (`.kdf`).

## Critical Rules

- **NEVER** launch a new KORF process. Always `Application().connect(path="korf.exe")`.
- **NEVER** use hardcoded strings for element types/params. Use constants from `pykorf.elements`.
- All model operations are **in-memory**. File writes only via `model.save()` / `model.save_as()`.
- Use `uv` (not pip). Use `cmd.exe` command style.
- Element index `0` = template; real instances start at `1`.

## Quick Reference

```python
from pykorf import Model
from pykorf.elements import Element, Pipe, BaseElement

model = Model("pykorf/trail_files/Cooling Water Circuit.kdf")
pipe = model.pipes[1]
model.add_element(Element.PIPE, "L1", {Pipe.LEN: 100, Pipe.DIA: 50})
model.save()
```

## Test File
For testing any use cases, use:
`pykorf/trail_files/Cooling Water Circuit.kdf`

## Architecture

| Module         | Purpose                               |
| -------------- | ------------------------------------- |
| `model`        | Facade & Services (CRUD, Connectivity, I/O) |
| `parser`       | `KdfParser`, low-level record handling |
| `elements`     | Typed wrappers + parameter constants  |
| `use_case`     | Workflows (PMS, HMB) & Textual TUI    |
| `cases`/`results`| Multi-case & calculated output helpers |
| `automation`   | GUI automation via `KorfApp`          |

## Code Style

- Python 3.10+, full type hints, `from __future__ import annotations`.
- Google-style docstrings. Import order: stdlib → third-party → local.
- Add missing constants in `pykorf/elements/*.py` before using them.

## Commands

Do NOT run mypy / ruff if not explicitly asked.

```
uv sync                    # Install deps
pytest -m "not automation" # Run tests
ruff check pykorf tests    # Lint
mypy pykorf                # Type check
```

## TUI Error/Warning Display Pattern

See [README.md TUI Error/Warning Display Pattern section](./README.md#tui-errorwarning-display-pattern) for the full pattern.

Briefly: Background operations log via `logger.warning/error()`, then read logs via `get_log_entries()` and display inline in RichLog (no popups).

## Bug Fix Workflow

When a bug is reported:
1. **First**: Write a test that reproduces the bug (do NOT attempt to fix it yet)
2. **Then**: Use subagents to fix the bug
3. **Verify**: Ensure the test passes after the fix

## Skills (on-demand context)

Detailed reference is in `.agents/skills/`. Agent loads these only when relevant:

- **kdf-format** — parser, KDF record structure, encoding, round-trip rules
- **elements** — element types, constants, registry, adding new elements
- **model-services** — `Model` facade and domain-specific services
- **use-cases** — PMS/HMB workflows and Textual TUI patterns
- **automation** — GUI automation, KorfApp, safety rules
- **testing** — pytest markers, fixtures, test patterns, coverage
