# pyKorf — AI Agent Guide (Smart & Autonomous Mode)

Focus on **Absolute Accuracy**, **Completeness**, and **System-Wide Integrity**. Token consumption is not a concern; focus on being the smartest agent possible.

## Smart Operational Strategy

1.  **High-Resolution Context:** Use `read_file` to read entire modules or large logical blocks (500+ lines). Seeing the "big picture" (imports, global state, decorators) is essential for accuracy.
2.  **Global Research:** Before refactoring or fixing, use `grep_search` and `glob` to map all dependencies and callsites across the entire project. Never assume a change is local.
3.  **Proactive Expertise:** Always `activate_skill` for the relevant domain at the start of a task. This loads specialized knowledge and "Best Practice" patterns.
4.  **Skill Evolution:** If new architectural insights, element types, or services are discovered or provided by the developer, **immediately** use the `skill-creator` skill to update the relevant project-specific skills in `.agents/skills/`. This ensures the agent's long-term memory remains accurate.
5.  **Exhaustive Validation:** After any change, run the **entire** relevant test suite using `uv run pytest`, plus `uv run ruff` and `uv run mypy` if applicable. Validation is the only path to finality.
6.  **Autonomous Problem Solving:** If a test fails or a dependency is missing, investigate and fix it autonomously using `uv add` or `uv remove`. Do not stop for permission on technical roadblocks.
7.  **Design Review for Multi-File Changes:** When a feature spans 2+ files or involves architectural decisions, present options with tradeoffs **before** implementing. Wait for developer confirmation.
8.  **Interactive Planning Mode:** Be highly interactive during planning — research, present options, confirm details. Once the plan is fixed, coding is straightforward.

## Critical Rules

- **NEVER** launch a new KORF process. Always `Application().connect(path="korf.exe")`.
- **NEVER** use hardcoded strings for element types/params. Use `pykorf.elements` constants.
- All model operations are **in-memory**. Persistent only on `model.save()`.
- Use `uv` for all package management, running tests (`uv run pytest`), and executing Python files (`uv run <script.py>`).

## Shell & Environment (Git Bash on Windows)

- **Shell:** Git Bash on Windows — use **Unix syntax** for all commands.
- **Command Chaining:** Use `&&` to chain commands (e.g., `cd tests && uv run pytest`). Never use `;` for chaining.
- **Paths:** Always use forward slashes. Use `/dev/null` not `NUL`.
- **Python:** Managed via `uv`. Always prefix with `uv run` — never call `python` directly.
- **Python version:** 3.13 exactly (enforced in `pyproject.toml` and `.python-version`).
- **File Tools First:** Always prefer the provided AI tools (`read_file`, `write_file`, `replace`, `grep_search`) over shell commands like `cat`, `touch`, or `echo > file`.

### Common Commands

```bash
uv run pytest                        # Run all tests
uv run pytest tests/test_model_api.py  # Single file
uv run ruff check pykorf tests       # Lint
uv run mypy pykorf                   # Type check
uv run pykorf                        # Launch TUI
uv run pykorf --debug                # Launch TUI (debug)
```

## Architecture & Service Map

| Module            | Purpose                                                      |
| :---------------- | :----------------------------------------------------------- |
| `model`           | Facade & Services (CRUD, Connectivity, Layout, I/O, Summary) |
| `parser`          | `KdfParser`, low-level record handling                       |
| `elements`        | Typed wrappers + parameter constants (e.g., `Pipe.LEN`)      |
| `use_case`        | Workflows (PMS, HMB), Global Settings, and Textual TUI       |
| `cases`/`results` | Multi-case management and calculated output extraction       |
| `automation`      | GUI automation via `KorfApp` (Win32 backend)                 |
| `visualization`   | PyVis interactive network visualization                      |

### Model Services (facade on `Model`)

| Service              | Attribute                   | Responsibility                              |
| :------------------- | :-------------------------- | :------------------------------------------ |
| `ElementService`     | `model._element_service`    | CRUD for elements (add, update, delete, copy, move) |
| `QueryService`       | `model.query`               | Filtering, parameter get/set                |
| `ConnectivityService`| `model.connectivity`        | Connect/disconnect elements, validation     |
| `LayoutService`      | `model.layout`              | XY positioning, visualization               |
| `IOService`          | `model.io`                  | save, to_dataframes, to_excel, from_excel   |
| `SummaryService`     | `model.summary_service`     | validate, repr, element accessors           |

### Key Patterns

- `Model(path)` parses `.kdf` via `KdfParser` into memory. Changes persist only on `model.io.save()`.
- Element types (17 total) are in `pykorf/elements/`. `ELEMENT_REGISTRY` in `elements/__init__.py` maps KDF tokens (e.g. `\PIPE`) to classes.
- Multi-case parameters are stored as semicolon-separated strings.
- **Import from `config.py`** in TUI screens — never from sub-modules (`preferences.py`, `pms.py`, etc.) directly.

### TUI Screen Flow

```
FilePickerScreen → MainMenuScreen → [operation screens]
```

Screens live in `pykorf/use_case/tui/screens/`: `apply_pms`, `apply_hmb`, `generate_report`, `bulk_copy`, `global_settings`, `import_export`, `config_menu`, `model_info`.

### Test Patterns

```python
SAMPLES_DIR = Path(__file__).parent.parent / "pykorf" / "library"
model = KorfModel.load(SAMPLES_DIR / "Pumpcases.kdf")
```

Markers: `unit`, `integration`, `slow`, `automation` (automation requires KORF GUI installed).

## Mandatory Skills (Load these first!)

- **model-services** — For any change to core model logic or service layers.
- **use-cases** — For TUI, batch processing, or external data workflows.
- **kdf-format** — For low-level parser or record-level changes.
- **elements** — For anything involving element types or parameters.
- **testing** — For test patterns, fixtures, and quality commands.
- **automation** — For GUI automation or `KorfApp` logic.
- **visualization** — For network diagrams and PyVis-based reporting.


## Guardrails & Boundaries

- **Zero-Destruction Policy:** NEVER delete source files, directories, or test cases simply to bypass errors. If a test is fundamentally flawed, rewrite it; do not delete it. Never modify files outside the immediate project root.
- **Safe Rollbacks:** Before executing multi-file architectural changes or modifying complex `.kdf` structures, create a temporary backup or use Git (`git stash` or branch). If autonomous fixes fail after **3 consecutive attempts**, revert to the last known-good state and halt. Do not enter an infinite debugging loop.
- **Anti-Hallucination Fallback:** If you encounter a domain-specific calculation, parameter relation, or architectural pattern you do not fully understand, **DO NOT guess**. Absolute accuracy supersedes autonomous completion. Stop and ask for clarification.
- **Definition of Done (DoD):** Do not abruptly stop when a task is finished. Conclude every successful session with a concise summary of:
  1. Files changed.
  2. Architectural decisions made.
  3. The final output of the validation suite (`uv run pytest`, `ruff`, etc.).