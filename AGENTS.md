# AGENTS.md

This file provides guidance to Coding Agents when working with code in this repository.

## Scope
Use this guide for practical development work in this repo: running the app, testing, linting, editing architecture-critical paths, and validating changes before handoff.

## Common commands
## Setup
```bash
uv pip install -e ".[dev]"
```

## Run application
```bash
uv run pykorf
uv run pykorf --port 9000
uv run pykorf --debug
uv run pykorf --no-debug
uv run pykorf --trial
```

## Tests
```bash
uv run pytest
uv run pytest tests/test_model_api.py
uv run pytest tests/test_model_api.py::TestModelConstructor::test_model_no_args_creates_default
uv run pytest -m unit
uv run pytest -m integration
uv run pytest -m "not slow"
```

## Lint / format / type-check
```bash
uv run ruff check pykorf tests
uv run ruff format pykorf tests
uv run mypy pykorf
```

## Frontend (run from `pykorf/app/frontend`)
```bash
npm run dev
npm run build
npm run generate-types
```

## Docs (optional)
```bash
uv run mkdocs serve
uv run mkdocs build
```

## High-level architecture
## Core model and parser
- `pykorf/core/model/` exposes `Model`, a service-composed facade (element/query/connectivity/layout/io/summary).
- `Model` changes are in-memory until `save()`/`io.save()` persists to disk.
- `pykorf/core/parser.py` (`KdfParser`) owns `.kdf` parse/serialize fidelity.
- `pykorf/core/elements/` defines typed element classes and `ELEMENT_REGISTRY`.

## API and session lifecycle
- `pykorf/app/api/app.py` creates the FastAPI app and mounts routers under `/api/*`.
- `pykorf/app/api/session_state.py` stores a single active model in-process.
- `pykorf/app/api/deps.py::require_model()` auto-reloads stale KDF state and coordinates stale notifications.
- Most mutating routes save model changes and then reload session state.

## Business workflows
- `pykorf/app/operation/data_import/`: PMS/HMB import + line-number parsing.
- `pykorf/app/operation/integration/sizing_criteria.py`: criteria lookup/prediction/application.
- `pykorf/app/operation/processor/`: processing orchestration and batch report flows.
- `pykorf/app/operation/project/`: sidecar metadata (`.pykorf`) such as references/justifications.
- Use config accessors via `pykorf.app.operation.config.config` in route-level code.

## Reporting system
- `pykorf/core/reports/reporter.py` defines the reporter protocol and single-case extraction path.
- `pykorf/core/reports/exporter.py` handles workbook generation/styling, validation sheet, and references.
- Multi-case mode depends on KORF Excel pairing (`{kdf_stem}.xlsx`) and staleness checks in `app/api/routers/report.py`.

## Frontend integration
- Frontend is Vue + Vite + Pinia in `pykorf/app/frontend`.
- `vite.config.ts` proxies `/api` to backend.
- `src/api/client.ts` handles stale-model header and session-related API behavior.
- Stores (`src/stores/session.ts`, `src/stores/model.ts`) mirror backend session/model contracts.

## Agent behavior (carry-over from previous AGENTS guidance)
- No auto-commits: do not commit unless explicitly asked.
- Prefer global impact analysis before refactors: identify call sites/dependencies first.
- Use non-destructive workflows: avoid deleting files to “fix” failures.
- Keep changes architecture-consistent rather than patching isolated symptoms.
- After meaningful code changes, run the full validation set:
  - `uv run pytest`
  - `uv run ruff check pykorf tests`
  - `uv run mypy pykorf`
- For API paths that mutate persisted model data, ensure in-memory session state is reloaded after save operations.