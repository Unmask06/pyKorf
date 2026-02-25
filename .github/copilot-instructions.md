# Copilot Instructions for pyKorf

## Project Overview

pyKorf is a Python toolkit for programmatically reading, editing, and writing KORF hydraulic model files (`.kdf`) and other text files in the `library/` folder. The package is designed so that users never need to manually edit `.kdf` files; all modifications happen through the Python API.

## Critical Safety Rule

**NEVER create a new KORF instance (`korf.exe`).** KORF is a trial-licensed application with a limited number of opens (5 total). The executable must always be kept running, and all automation must connect to the **already-running** instance using `Application().connect()`. Never use `Application().start()` or `subprocess.Popen` to launch KORF.

## Architecture

| Module              | Purpose                                                                                 |
| ------------------- | --------------------------------------------------------------------------------------- |
| `pykorf.model`      | `KorfModel` – load / edit / save a `.kdf` file                                          |
| `pykorf.parser`     | `KdfParser` – low-level tokeniser for `.kdf` files                                      |
| `pykorf.cases`      | `CaseSet` – multi-case helpers                                                          |
| `pykorf.results`    | `Results` – extract calculated output values                                            |
| `pykorf.automation` | `KorfApp` – connect to a running KORF and drive the GUI (never launches a new instance) |
| `pykorf.elements`   | One class per KORF element type                                                         |
| `pykorf.utils`      | CSV / value helpers                                                                     |
| `pykorf.exceptions` | Package-wide exception types                                                            |

## Key Conventions

- **Element index 0** is the KORF default template; real instances start at **index 1**.
- Multi-case values are semicolon-delimited strings, e.g. `"50;55;20"`.
- The marker `";C"` means a value was calculated by KORF.
- All record access goes through `KdfParser.get()` / `KdfParser.set_value()`.
- The parser preserves exact line order for round-trip fidelity.
- File encoding is `latin-1`.

## KORF Reference

Refer to `library/korf_manual.md` for the full KORF user guide (converted from PDF). This contains all available elements, features, and specifications for the KORF hydraulic simulation software.

## Coding Standards

- Python ≥ 3.9 compatibility.
- Follow PEP 8; line length limit is 100 characters (configured via Ruff).
- Use type hints (`from __future__ import annotations`).
- Docstrings follow NumPy style.
- **Always use `uv` as the package manager** for dependency management and virtual environments.
- `pywinauto` and `pywin32` are optional dependencies (`[automation]` extra).
- No mandatory runtime dependencies for the core library.
- Tests use `pytest` and operate on sample `.kdf` files in `library/`.

## Automation (`open_ui` / `KorfApp`)

- `open_ui(file_path)` finds the running KORF process and opens the given file inside it.
- `KorfApp.connect()` attaches to KORF — it does **not** start a new process.
- Always re-acquire the window handle before each GUI action for robustness.

## Future Direction

A Vue-based GUI will be built on top of this package so users can edit `.kdf` files through a web interface. Keep the Python API clean and JSON-serialisable for easy integration with a frontend.
