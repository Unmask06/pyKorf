# pyKorf — AI Agent Guide (Smart & Autonomous Mode)

Focus on **Absolute Accuracy**, **Completeness**, and **System-Wide Integrity**. Token consumption is not a concern; focus on being the smartest agent possible.

## Smart Operational Strategy

1.  **High-Resolution Context:** Use `read_file` to read entire modules or large logical blocks (500+ lines). Seeing the "big picture" (imports, global state, decorators) is essential for accuracy.
2.  **Global Research:** Before refactoring or fixing, use `grep_search` and `glob` to map all dependencies and callsites across the entire project. Never assume a change is local.
3.  **Proactive Expertise:** Always `activate_skill` for the relevant domain at the start of a task. This loads specialized knowledge and "Best Practice" patterns.
4.  **Skill Evolution:** If new architectural insights, element types, or services are discovered or provided by the developer, **immediately** use the `skill-creator` skill to update the relevant project-specific skills in `.agents/skills/`. This ensures the agent's long-term memory remains accurate.
5.  **Exhaustive Validation:** After any change, run the **entire** relevant test suite, plus `ruff` and `mypy` if applicable. Validation is the only path to finality.
6.  **Autonomous Problem Solving:** If a test fails or a dependency is missing, investigate and fix it autonomously. Do not stop for permission on technical roadblocks.

## Critical Rules

- **NEVER** launch a new KORF process. Always `Application().connect(path="korf.exe")`.
- **NEVER** use hardcoded strings for element types/params. Use `pykorf.elements` constants.
- All model operations are **in-memory**. Persistent only on `model.save()`.
- Use `uv` for all environment and dependency management.

## Architecture & Service Map

| Module | Purpose |
| :--- | :--- |
| `model` | Facade & Services (CRUD, Connectivity, Layout, I/O, Summary) |
| `parser` | `KdfParser`, low-level record handling and latin-1 encoding |
| `elements` | Typed wrappers + parameter constants (e.g., `Pipe.LEN`) |
| `use_case` | Workflows (PMS, HMB), Global Settings, and Textual TUI |
| `cases`/`results` | Multi-case management and calculated output extraction |
| `automation` | GUI automation via `KorfApp` (Win32 backend) |
| `visualization`| PyVis interactive network visualization |

## Mandatory Skills (Load these first!)

- **model-services** — For any change to core model logic or service layers.
- **use-cases** — For TUI, batch processing, or external data workflows.
- **kdf-format** — For low-level parser or record-level changes.
- **elements** — For anything involving element types or parameters.
- **testing** — For test patterns, fixtures, and quality commands.
- **automation** — For GUI automation or `KorfApp` logic.
- **visualization** — For network diagrams and PyVis-based reporting.
