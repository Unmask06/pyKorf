# pyKorf Project Guide for AI Agents

This document provides essential information for AI coding agents working with the pyKorf project.

## Project Overview

**pyKorf** is an enterprise Python toolkit for reading, editing, validating, and writing KORF hydraulic model files (`.kdf`). KORF is a hydraulic simulation software used for pipeline and fluid system engineering.

### Key Capabilities

- Load, modify, and save `.kdf` hydraulic model files
- Work with all KORF element types (pipes, pumps, valves, heat exchangers, etc.)
- Extract calculated results and perform multi-case analysis
- Automate the KORF GUI (Windows only, requires running KORF instance)
- Export models to JSON, YAML, Excel, and CSV formats
- Visualize hydraulic networks with PyVis

## Technology Stack

| Category | Technology |
|----------|------------|
| Language | Python 3.10+ (primary: 3.13) |
| Build System | setuptools + setuptools-scm |
| Package Manager | uv (preferred) or pip |
| Type Hints | Full type annotations, mypy strict mode |
| Data Validation | Pydantic v2 |
| Logging | structlog (with stdlib fallback) |
| Testing | pytest with coverage |
| Linting | ruff (replaces flake8, black, isort) |
| CLI | click + rich |

## Project Structure

```
pyKorf/
├── pykorf/                      # Main package source
│   ├── __init__.py              # Public API exports
│   ├── model.py                 # Model / KorfModel - top-level container
│   ├── parser.py                # KdfParser - low-level file tokenizer
│   ├── cases.py                 # CaseSet - multi-case utilities
│   ├── results.py               # Results - calculated output extraction
│   ├── automation.py            # KorfApp - GUI automation (Windows only)
│   ├── connectivity.py          # Element connection management
│   ├── layout.py                # Element positioning and clash detection
│   ├── validation.py            # KDF format validation rules
│   ├── export.py                # Export to JSON/YAML/Excel/CSV
│   ├── query.py                 # Query DSL for filtering elements
│   ├── types.py                 # Pydantic data models
│   ├── config.py                # Configuration management
│   ├── log.py                   # Structured logging
│   ├── cli.py                   # Command-line interface
│   ├── utils.py                 # Shared CSV/value helpers
│   ├── exceptions.py            # Custom exception hierarchy
│   ├── elements/                # Typed element wrapper classes + constants
│   │   ├── base.py              # BaseElement abstract class + common constants
│   │   ├── pipe.py              # Pipe class + parameter constants
│   │   ├── pump.py              # Pump class + parameter constants
│   │   └── ...                  # One module per element type
│   ├── visualization/           # Network visualization
│   │   ├── visualizer.py        # PyVis-based visualizer
│   │   └── models.py            # Visualization data models
│   └── library/                 # Sample .kdf files and defaults
│       ├── New.kdf              # Default template for blank models
│       ├── Pumpcases.kdf        # Sample pump system model
│       ├── crane10.kdf          # Crane fluid flow sample
│       └── ...                  # Other sample files
├── tests/                       # Test suite
│   ├── test_model_api.py        # Model API tests
│   ├── test_parser.py           # Parser tests
│   ├── test_elements.py         # Element wrapper tests
│   ├── test_cases.py            # Multi-case tests
│   ├── test_automation.py       # GUI automation tests
│   └── ...                      # Other test modules
├── docs/                        # Documentation
│   ├── ENTERPRISE_API.md        # Enterprise features guide
│   └── CHANGES_SUMMARY.md       # Change history
├── examples/                    # Usage examples
│   └── basic_usage.py           # Basic usage examples
├── plans/                       # Development plans
├── pyproject.toml               # Project configuration
├── uv.lock                      # Locked dependency versions
└── README.md                    # User documentation
```

## Build and Test Commands

### Installation

```bash
# Install with uv (recommended)
uv sync                    # Install with default dev dependencies
uv sync --extra docs       # Include documentation dependencies

# Or with pip
pip install -e ".[dev]"

# Install specific extras
pip install -e ".[automation,visualization,dataframe,cli]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pykorf --cov-report=term-missing

# Run specific test categories
pytest -m unit           # Unit tests only
pytest -m "not slow"     # Exclude slow tests
pytest -m "not automation"  # Exclude GUI automation tests

# Run in parallel
pytest -x
```

### Code Quality

```bash
# Run ruff linter and formatter
ruff check pykorf tests
ruff format pykorf tests

# Run type checker
mypy pykorf

# Run pre-commit hooks
pre-commit run --all-files
```

### Documentation

```bash
# Build documentation
uv run mkdocs build --strict

# Serve documentation locally with live reload
uv run mkdocs serve

# Deploy to GitHub Pages
uv run mkdocs gh-deploy --force
```

The documentation is built with MkDocs Material and includes:
- API reference generated by mkdocstrings
- User guides and tutorials
- CLI reference
- Material theme with dark/light mode

**Important:** For proper API documentation rendering, use markdown code blocks (\`\`\`python) not doctest format (>>>) in docstrings. The mkdocstrings parser renders markdown code blocks as proper syntax-highlighted code, while doctest format may render as plain text or blockquotes.

### Building and Distribution

```bash
# Build package
python -m build

# Install in editable mode for development
uv pip install -e ".[dev]"
```

## Code Style Guidelines

### Python Version and Typing

- Python 3.10+ required (project uses 3.13)
- Full type annotations required (mypy strict mode enabled)
- Use `from __future__ import annotations` for forward references
- Use `|` union syntax (e.g., `str | None`) instead of `Optional`

### Imports

```python
# Standard library imports first
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

# Third-party imports second
from pydantic import BaseModel

# Local imports last
from pykorf.elements import BaseElement, Element
from pykorf.exceptions import KorfError

# TYPE_CHECKING block for circular imports
if TYPE_CHECKING:
    from pykorf.parser import KdfParser
```

### Docstrings

Use Google-style docstrings with **markdown code blocks** (not doctest format):

```python
def load_model(path: str | Path) -> Model:
    """Load a KDF model from file.
    
    Args:
        path: Path to the .kdf file.
        
    Returns:
        Loaded Model instance.
        
    Raises:
        ParseError: If the file cannot be parsed.
        
    Example:
        ```python
        model = load_model("Pumpcases.kdf")
        print(model.version)
        ```
    """
```

### Rule 1: Always Use Constants from Element Classes

**STRICT RULE - NO EXCEPTIONS:** Never use hardcoded string literals for element types or parameter names. Always use constants from `pykorf.elements`:

```python
# CORRECT - Use constants
from pykorf.elements import Element, Pipe, Feed, BaseElement

model.add_element(Element.PIPE, "L1", {Pipe.LEN: 100, Pipe.TFLOW: "50"})

# INCORRECT - Hardcoded strings (NEVER DO THIS)
model.add_element("PIPE", "L1", {"LEN": 100, "TFLOW": "50"})
```

**Why this matters:**
- The element classes contain 400+ constants for all KDF element types and parameters
- Using constants prevents typos (e.g., "VAPCP" vs "VAPCP " with trailing space)
- Refactoring is easier when constants are used
- IDE autocomplete works better with constants
- The codebase is already using these constants extensively

**Common constants to use:**
- Element types: `Element.PIPE`, `Element.PUMP`, `Element.VALVE`, etc.
- Pipe params: `Pipe.LEN`, `Pipe.DIA`, `Pipe.TFLOW`, `Pipe.MAT`, etc.
- Common params: `BaseElement.NAME`, `BaseElement.NUM`, `BaseElement.XY`, `BaseElement.NOTES`
- Connection: `BaseElement.CON`, `BaseElement.NOZI`, `BaseElement.NOZO`, `BaseElement.NOZL`

**Checklist:**
- [ ] No hardcoded element types like `"PIPE"`, `"PUMP"`
- [ ] No hardcoded parameter names like `"LEN"`, `"TFLOW"`, `"PRES"`
- [ ] All KDF field aliases use constants (e.g., in Pydantic Field alias=Pipe.UI)
- [ ] All record lookups use constants (e.g., `elem._get(Pipe.TFLOW)`)}}  # type: ignore[pydantic]

## Architecture Patterns

### Model Persistence Contract

The most important architectural rule:

1. `Model(path)` / `KorfModel.load(path)` reads the `.kdf` file into memory
2. All manipulations (`update_element`, `add_element`, `delete_element`, etc.) modify only the in-memory state
3. **File writes happen only through `model.save()` or `model.save_as()`**
4. Unsaved changes are lost when the Python process ends

### Element Indexing

- Index **0** in every collection is the KORF default template
- Real instances start at index **1**
- Access patterns: `model.pipes[1]` gets the first real pipe

### KDF File Format

- Encoding: `latin-1` (not UTF-8)
- Line endings: `\r\n` (Windows CRLF)
- Multi-case values: semicolon-delimited strings (e.g., `"50;55;20"`)
- Calculated values marked with `";C"` suffix
- Record format: `\ETYPE,index,PARAM,value1,value2,...`

### Exception Hierarchy

```
KorfError (base)
├── ParseError
├── ElementNotFound
├── ElementAlreadyExists
├── CaseError
├── AutomationError
├── ValidationError
├── ConnectivityError
├── LayoutError
├── VersionError
├── ParameterError
├── ExportError
└── ImportError
```

All exceptions support structured context via `ErrorContext`.

## Testing Strategy

### Test Markers

| Marker | Description |
|--------|-------------|
| `@pytest.mark.unit` | Unit tests (fast, no I/O) |
| `@pytest.mark.integration` | Integration tests |
| `@pytest.mark.slow` | Slow tests (skip with `-m "not slow"`) |
| `@pytest.mark.automation` | GUI automation tests (require KORF) |

### Test Fixtures

Tests use sample files from `pykorf/library/`:

```python
SAMPLES_DIR = Path(__file__).parent.parent / "pykorf" / "library"
PUMP_KDF = SAMPLES_DIR / "Pumpcases.kdf"
```

### Writing Tests

```python
import pytest
from pykorf import Model
from pykorf.exceptions import ElementNotFound

class TestModelOperations:
    def test_load_model(self):
        """Test loading a valid KDF file."""
        model = Model(PUMP_KDF)
        assert model.num_pipes == 5
        
    def test_element_not_found(self):
        """Test accessing non-existent element."""
        model = Model(PUMP_KDF)
        with pytest.raises(ElementNotFound):
            model.get_element("NONEXISTENT")
```

## Security Considerations

### Automation Safety

**NEVER** launch a new KORF process. KORF limits file opens to 5 times. Always connect to an already-running instance:

```python
# CORRECT
from pywinauto import Application
app = Application().connect(path="korf.exe")

# INCORRECT - DO NOT DO THIS
app = Application().start("korf.exe")
```

### File Handling

- Always use `pathlib.Path` for file operations
- Validate file paths before operations
- Backup files before overwriting (configurable in `Config`)

### Input Validation

- Use Pydantic models for type-safe data
- Validate element names (max 9 characters by default)
- Sanitize file paths

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PYKORF_ENCODING` | Default file encoding | `latin-1` |
| `PYKORF_STRICT_VALIDATION` | Enable strict validation | `false` |
| `PYKORF_CACHE_SIZE` | LRU cache size | `128` |
| `PYKORF_LOG_LEVEL` | Logging level | `INFO` |

### Configuration File

```toml
# pykorf.toml
[io]
default_encoding = "latin-1"
backup_files = true

[validation]
strict_mode = false
check_connectivity_on_save = true

[logging]
level = "INFO"
format = "structured"  # or "console"
```

## Dependencies

### Core Dependencies

- `pydantic>=2.0,<3.0` - Data validation
- `typing-extensions>=4.5.0` - Type hints backports
- `structlog>=24.0` - Structured logging

### Optional Dependencies

| Extra | Packages | Purpose |
|-------|----------|---------|
| `automation` | pywinauto, pywin32 | GUI automation (Windows only) |
| `visualization` | pyvis, networkx | Network visualization |
| `dataframe` | pandas, openpyxl | DataFrame export |
| `export` | pyyaml, orjson | JSON/YAML export |
| `cli` | click, rich | Command-line interface |
| `docs` | mkdocs, mkdocs-material, mkdocstrings | Documentation build |
| `dev` | pytest, mypy, ruff, pre-commit | Development tools |

### Dependency Groups (uv)

| Group | Description |
|-------|-------------|
| `test` | pytest, coverage, asyncio, xdist |
| `lint` | ruff, mypy, pre-commit |
| `docs` | mkdocs, material theme, mkdocstrings |
| `dev` | Includes test + lint + docs groups |

## Version Support

KDF file format versions supported:
- `KORF_2.0`
- `KORF_3.0`
- `KORF_3.6`

The code should remain version-aware for compatibility (e.g., `NOZ` vs `NOZL` parameter names).

## Reference Materials

- `pykorf/library/korf_manual.md` - KORF manual in Markdown
- `pykorf/library/Korf Manual.pdf` - Original KORF manual
- `docs/ENTERPRISE_API.md` - Enterprise API features guide
- `.github/copilot-instructions.md` - Additional coding guidelines

## Common Tasks

### Adding a New Element Type

1. Create wrapper class with constants in `pykorf/elements/<element>.py`
2. Register in `pykorf/elements/__init__.py` ELEMENT_REGISTRY
4. Add collection property to `Model` class
5. Add tests in `tests/test_elements.py`

### Adding a New Export Format

1. Implement function in `pykorf/export.py`
2. Add options class in `pykorf/types.py`
3. Add CLI command in `pykorf/cli.py`
4. Add tests

### Modifying the Parser

1. Update `KdfRecord` dataclass if needed
2. Modify `KdfParser.load()` for reading
3. Modify `KdfRecord.to_line()` for writing
4. Ensure round-trip fidelity is maintained
5. Add tests in `tests/test_parser.py`
