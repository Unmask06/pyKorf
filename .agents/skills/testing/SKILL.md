---
name: testing
description: Pytest markers, fixtures, test patterns, coverage, and code quality commands
---

# Testing Guide

## Commands

```bash
uv sync                              # ensure deps
pytest                               # all tests
pytest -m unit                       # fast unit tests only
pytest -m "not automation"           # skip GUI tests (most common)
pytest -m "not slow"                 # skip slow tests
pytest --cov=pykorf --cov-report=term-missing  # with coverage
pytest -x                            # stop on first failure
```

## Markers

| Marker                     | Purpose                       | When to skip         |
| -------------------------- | ----------------------------- | -------------------- |
| `@pytest.mark.unit`        | Fast, no I/O                  | Never                |
| `@pytest.mark.integration` | Integration tests             | CI-lite              |
| `@pytest.mark.slow`        | Long-running                  | Quick feedback loops |
| `@pytest.mark.automation`  | GUI tests (need KORF running) | Almost always        |

## Fixtures & Test Data

- Sample KDF files: `pykorf/library/` (`Pumpcases.kdf`, `New.kdf`, `crane10.kdf`, etc.)
- Fluid data: `pykorf/library/fluids.txt`
- Pipe data: `pykorf/library/pipeid.lib`, `pipefit.csv`
- Use-case inputs: `pykorf/use_case/Input/`

## Test File Mapping

| Source module     | Test file                                             |
| ----------------- | ----------------------------------------------------- |
| `model/`          | `tests/test_model_api.py`                             |
| `parser.py`       | `tests/test_parser.py`                                |
| `elements/`       | `tests/test_elements.py`, `tests/test_definitions.py` |
| `model/services/connectivity.py` | `tests/test_connectivity.py`           |
| `model/services/layout.py`       | `tests/test_layout.py`                 |
| `model/services/summary.py`      | `tests/test_validation.py`             |
| `use_case/`       | `tests/test_use_case.py`                              |
| `cases.py`        | `tests/test_cases.py`                                 |
| `automation.py`   | `tests/test_automation.py`                            |
| `utils.py`        | `tests/test_utils.py`                                 |
| `visualization/`  | `tests/test_visualization.py`                         |

## Code Quality

```bash
ruff check pykorf tests              # lint
ruff format pykorf tests             # format
mypy pykorf                          # type check
```

## Writing New Tests

- Use `tmp_path` fixture for temp files (not manual tempfile)
- Load test models from `pykorf/library/`
- Assert on constants, not raw strings: `assert pipe.get(Pipe.LEN) == ...`
- Mark appropriately: `@pytest.mark.unit` for pure logic, `@pytest.mark.integration` for file I/O
