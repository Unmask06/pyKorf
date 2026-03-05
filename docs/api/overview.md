# API Overview

pyKorf provides a comprehensive Python API for working with KORF hydraulic models.

## Package Structure

```
pykorf/
├── __init__.py          # Public API exports
├── model.py             # Model, KorfModel
├── parser.py            # KdfParser, KdfRecord
├── elements/            # Element wrapper classes
│   ├── base.py          # BaseElement
│   ├── pipe.py          # Pipe
│   ├── pump.py          # Pump
│   └── ...
├── definitions/         # Constants
│   ├── element.py       # Element types
│   ├── pipe.py          # Pipe parameters
│   └── ...
├── cases.py             # CaseSet
├── results.py           # Results
├── connectivity.py      # Connection management
├── layout.py            # Positioning
├── validation.py        # Validation
├── export.py            # Export functions
├── query.py             # Query DSL
├── types.py             # Pydantic models
├── config.py            # Configuration
├── log.py               # Logging
├── cli.py               # CLI
└── exceptions.py        # Exceptions
```

## Main Classes

| Class | Description |
|-------|-------------|
| `Model` | Top-level container for KDF files |
| `KdfParser` | Low-level file tokenizer |
| `CaseSet` | Multi-case scenario management |
| `Results` | Extract calculated results |
| `Query` | Fluent query DSL |

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
elem = model["name"]          # By name
pipe = model.pipes[1]          # By index

# Modify
model.update_element("L1", {Pipe.LEN: 100})

# Add
model.add_element(Element.PUMP, "P1")

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
params = model.get_params("L1")
model.set_params("L1", {"LEN": 200})
```

## Type Hints

pyKorf uses full type annotations:

```python
def load_model(path: str | Path) -> Model: ...
def update_element(self, name: str, params: dict[str, Any]) -> None: ...
```

## Documentation Sections

- [Model](model.md) - Core model class
- [Elements](elements.md) - Element wrapper classes

Coming soon:
- Parser - Low-level file parsing
- Cases - Multi-case utilities
- Results - Results extraction
- Export - Export functions
- Config - Configuration
- Logging - Structured logging
- Exceptions - Exception hierarchy
- Types - Pydantic models
