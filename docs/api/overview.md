# API Overview

pyKorf provides a comprehensive Python API for working with KORF hydraulic models.

## Package Structure

```
pykorf/
├── __init__.py          # Public API exports
├── _version.py          # Version info
├── cli.py               # CLI entry point
├── core/                # Core implementation
│   ├── model/           # Model services
│   │   ├── __init__.py  # Model class (composition pattern)
│   │   ├── core.py      # _ModelBase
│   │   ├── element.py   # ElementService
│   │   ├── query.py     # QueryService
│   │   ├── connectivity.py  # ConnectivityService
│   │   ├── layout.py    # LayoutService
│   │   ├── io.py        # IOService
│   │   └── summary.py   # SummaryService
│   ├── elements/        # Element classes
│   │   ├── base.py      # BaseElement
│   │   ├── pipe.py      # Pipe
│   │   └── ...
│   ├── parser.py        # KdfParser
│   ├── cases.py         # CaseSet
│   ├── fluid.py         # Fluid
│   ├── types.py         # Pydantic models
│   ├── log.py           # Logging
│   ├── utils.py         # Utilities
│   ├── exceptions.py    # Exceptions
│   └── reports/         # Report generation
└── app/                 # Application layer
    ├── __init__.py      # Flask app factory
    ├── automation.py    # KorfApp (pywinauto)
    ├── web/             # Web utilities
    ├── operation/       # Business logic
    │   ├── config/      # Configuration
    │   ├── data_import/ # PMS, HMB
    │   ├── processor/   # Batch processing
    │   ├── project/     # Project info
    │   └── integration/ # SharePoint, etc.
    ├── routes/          # Flask Blueprints
    └── templates/       # HTML templates
```

## Main Classes

| Class | Description |
|-------|-------------|
| `Model` | Top-level container for KDF files (composition-based services) |
| `KdfParser` | Low-level file tokenizer |
| `CaseSet` | Multi-case scenario management |
| `Fluid` | Fluid properties |

## Element Classes

| Class | KDF Type | Description |
|-------|----------|-------------|
| `General` | `\GEN` | Global settings |
| `Pipe` | `\PIPE` | Process line |
| `Pump` | `\PUMP` | Pump equipment |
| `Valve` | `\VALVE` | Control valve |
| `Feed` | `\FEED` | Source boundary |
| `Product` | `\PROD` | | Sink boundary |
| `HeatExchanger` | `\HX` | Heat exchanger |
| `Compressor` | `\COMP` | Compressor |
| `Vessel` | `\VESSEL` | Pressure vessel |
| `Tee` | `\TEE` | Tee piece |
| `Junction` | `\JUNC` | Multi-pipe junction |

## Quick Reference

### Loading Models

```python
from pykorf import Model

model = Model("file.kdf")     # Load from file
model = Model()                # Create blank model
model.save()                   # Save changes
model.save_as("new.kdf")       # Save to new file
```

### Working with Elements

```python
# Access
elem = model.get_element("L1")   # By name
pipe = model.pipes[1]            # By index (collection)

# Modify
model.update_element("L1", {"LEN": 100})

# Add
model.add_element("PUMP", "P1")

# Delete
model.delete_element("L1")
```

### Multi-Case

```python
from pykorf import CaseSet

cases = CaseSet(model)
cases.names                    # ['NORMAL', 'RATED']
cases.count                    # 2
pipe.set_flow([50, 55])       # Set for all cases
```

### Querying Elements

```python
from pykorf import Model

model = Model("Pumpcases.kdf")

# Get elements by type
pipes = model.get_elements(etype="PIPE")

# Filter by name pattern
p_elements = model.get_elements(name="P*")

# Get/set parameters
value = model.get_param("L1", "LEN")
model.set_param("L1", "LEN", 200)
```

## Type Hints

pyKorf uses full type annotations:

```python
def load_model(path: str | Path) -> Model: ...
def update_element(self, name: str, params: dict[str, Any]) -> None: ...
```

## Documentation Sections

- [Model](model.md) - Core model class with service architecture
- [Elements](elements.md) - Element wrapper classes

Related:
- Cases - Multi-case utilities (`pykorf.core.cases`)
- Fluid - Fluid properties (`pykorf.core.fluid`)
- Types - Pydantic models (`pykorf.core.types`)
- Exceptions - Exception hierarchy (`pykorf.core.exceptions`)
