# Copilot Instructions for pyKorf

## Project Intent

pyKorf is a Python API for reading, editing, validating, and writing KORF `.kdf` files.
Users should modify models through the API, not by manual line editing.

## Critical Safety Rule (Automation)

**Never launch a new KORF process.**
Always connect to the already-running instance using `Application().connect()`.
Do not use `Application().start()` or `subprocess.Popen` for `korf.exe`.

## Current Architecture

- `pykorf.model`: primary `Model` API (`KorfModel` alias kept for compatibility)
- `pykorf.parser`: `KdfParser` and record-level load/save/token handling
- `pykorf.elements`: typed element wrappers (`Pipe`, `Pump`, etc.)
- `pykorf.connectivity`: connect/disconnect/check connection logic
- `pykorf.layout`: positioning, clash checks, visualization
- `pykorf.validation`: KDF validation rules
- `pykorf.cases`: multi-case utilities
- `pykorf.results`: calculated-results extraction
- `pykorf.automation`: GUI automation wrapper (`KorfApp`)

## Persistence Contract (Important)

- `Model(...)` / `KorfModel.load(...)` reads the file into memory.
- All model operations (update/add/delete/copy/move/connect/disconnect) are in-memory.
- File writes happen only through `model.save()` / `model.save_as()`.
- Unsaved changes are lost when the Python process ends.

## Data & Format Conventions

- Sample assets are in `pykorf/library/` (not repo-root `library/`).
- Default template for `Model()` is `pykorf/library/New.kdf`.
- Element index `0` is the template; real instances start at `1`.
- Multi-case values use semicolon-delimited strings, e.g. `"50;55;20"`.
- Calculated marker `";C"` means KORF-generated value.
- KDF encoding is `latin-1`; line endings are `\r\n`.
- Preserve record order for round-trip fidelity.

## Version Awareness

KDF files encountered here include `KORF_2.0`, `KORF_3.0`, and `KORF_3.6`.
pyKorf should remain version-aware (e.g., `NOZ` vs `NOZL`, fitting format differences).

## Coding & Tooling Rules

- Python >= 3.9, PEP 8, type hints, NumPy-style docstrings.
- Keep changes minimal and backward compatible.
- Prefer existing helpers over duplicating parsing or mapping logic.
- Use `uv` for dependency/test commands.
- Use `cmd.exe` command style for shell examples in this repo.

## Testing Guidance

- Use `pytest` with fixtures from `pykorf/library/`.
- Include tests for persistence boundary (unchanged file before save).
- Include tests when behavior/API contracts are updated.
