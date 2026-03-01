# pyKorf Enterprise API Guide

This guide covers the advanced features of pyKorf designed for enterprise use, including type safety, structured logging, configuration management, and export capabilities.

## Table of Contents

- [Type-Safe Data Models](#type-safe-data-models)
- [Configuration Management](#configuration-management)
- [Structured Logging](#structured-logging)
- [Advanced Querying](#advanced-querying)
- [Export/Import](#exportimport)
- [Error Handling](#error-handling)
- [CLI Usage](#cli-usage)

---

## Type-Safe Data Models

pyKorf provides Pydantic-based data models for type safety and validation:

```python
from pykorf.types import PipeData, PumpData, FlowParameters, Position

# Create a type-safe pipe definition
pipe = PipeData(
    name="L1",
    diameter_inch="6",
    schedule="40",
    length_m=100.0,
    material="Steel",
    position=Position(x=1000.0, y=2000.0),
    flow=FlowParameters(
        mass_flow_t_h=[50, 55, 20],
        temperature_c=[25, 30, 20],
        pressure_kpag=[100, 120, 80],
    )
)

# Automatic validation
pipe_dict = pipe.model_dump()  # Convert to dict for serialization
```

### Available Models

| Model | Description |
|-------|-------------|
| `PipeData` | Pipe/line element data |
| `PumpData` | Pump element data |
| `ValveData` | Control valve data |
| `FeedData` | Feed boundary condition |
| `ProductData` | Product boundary condition |
| `CompressorData` | Compressor element data |
| `HeatExchangerData` | Heat exchanger data |
| `VesselData` | Vessel element data |

---

## Configuration Management

Centralized configuration with environment variable and file support:

```python
from pykorf.config import get_config, Config, set_config

# Get global configuration
config = get_config()

# Access settings
print(config.io.default_encoding)  # "latin-1"
print(config.validation.strict_mode)  # False

# Override at runtime
config.io.default_encoding = "utf-8"
config.validation.strict_mode = True

# Load from file
config = Config.from_file("pykorf.toml")
set_config(config)

# Save configuration
config.save("pykorf.yaml")
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `PYKORF_ENCODING` | Default file encoding |
| `PYKORF_STRICT_VALIDATION` | Enable strict validation |
| `PYKORF_CACHE_SIZE` | LRU cache size |
| `PYKORF_LOG_LEVEL` | Logging level |

### Configuration File Example (TOML)

```toml
[io]
default_encoding = "latin-1"
backup_files = true

[validation]
strict_mode = false
check_connectivity_on_save = true

[performance]
cache_size = 256
enable_caching = true

[logging]
level = "INFO"
format = "structured"
```

---

## Structured Logging

pyKorf uses structured logging for observability:

```python
from pykorf.log import get_logger, bind_context, log_operation

logger = get_logger()

# Basic logging
logger.info("Loading model", file="Pumpcases.kdf")
logger.error("Validation failed", errors=5)

# Context binding
with bind_context(model="Pumpcases.kdf", operation="batch_process"):
    logger.info("Starting batch")  # Includes context
    # ... do work ...
    logger.info("Batch complete")

# Operation timing
with log_operation("validate_model", path="model.kdf"):
    model.validate()  # Logs start, success/failure, and duration
```

### Output Formats

**Structured (JSON)** for production:
```json
{
  "event": "model_loaded",
  "timestamp": "2024-01-15T10:30:00Z",
  "logger": "pykorf.model",
  "level": "info",
  "file": "Pumpcases.kdf",
  "elements": 42
}
```

**Console** for development (colored output with rich formatting)

---

## Advanced Querying

The Query DSL provides powerful filtering capabilities:

```python
from pykorf import Model, Query, attr

model = Model("Pumpcases.kdf")
q = Query(model)

# Simple queries
pipes = q.pipes.all()
pumps = q.pumps.limit(10).all()

# Attribute-based filtering
large_pipes = (
    q.pipes
    .where(attr("diameter_inch").in_(["8", "10", "12"]))
    .where(attr("length_m") > 100)
    .all()
)

# String matching
feed_lines = q.by_name("F*").all()
cv_valves = q.valves.where(attr("name").contains("CV")).all()

# Pattern matching
process_lines = q.pipes.where(attr("name").matches("L*[0-9]")).all()

# Range queries
medium_pipes = q.pipes.where(attr("length_m").between(50, 200)).all()

# Chaining conditions
results = (
    q.elements
    .where(attr("etype") == "PIPE")
    .where(attr("name").startswith("L"))
    .order_by("name")
    .limit(20)
    .all()
)

# Check existence
has_large_pipes = q.pipes.where(attr("diameter_inch") == "12").exists()

# Get single result
try:
    main_pump = q.pumps.where(attr("name") == "P1").one()
except ValueError as e:
    print("Not found or multiple matches")
```

### Query Result Methods

```python
results = q.pipes.all()

# Aggregation
first_pipe = results.first()
last_pipe = results.last()
count = results.count()

# Extraction
names = results.pluck("name")
by_type = results.group_by("etype")

# Transformation
summaries = results.map(lambda p: p.summary())
```

---

## Export/Import

Export models to various formats:

```python
from pykorf import Model
from pykorf.export import (
    export_to_json,
    export_to_yaml,
    export_to_excel,
    export_to_csv,
)
from pykorf.types import ExportOptions

model = Model("Pumpcases.kdf")

# JSON export
export_to_json(
    model,
    "output.json",
    options=ExportOptions(
        include_results=True,
        include_geometry=True,
        indent=2,
    )
)

# YAML export
export_to_yaml(model, "output.yaml")

# Excel export (multiple sheets)
export_to_excel(
    model,
    "output.xlsx",
    include_results=True,
)

# CSV export (directory of files)
export_to_csv(
    model,
    "./csv_export/",
    element_type="all",
    include_results=True,
)
```

---

## Error Handling

pyKorf provides structured exceptions with context:

```python
from pykorf.exceptions import (
    KorfError,
    ElementNotFound,
    ValidationError,
    ErrorContext,
)

# Basic error handling
try:
    elem = model["NonExistent"]
except ElementNotFound as e:
    print(f"Error: {e.message}")
    print(f"Context: {e.context.to_dict()}")
    if e.suggestion:
        print(f"Suggestion: {e.suggestion}")

# Validation with details
try:
    issues = model.validate()
    if issues:
        raise ValidationError(issues)
except ValidationError as e:
    print(f"Validation failed with {len(e.issues)} issues:")
    for issue in e.issues:
        print(f"  - {issue}")

# Rich error context
raise KorfError(
    "Invalid parameter value",
    context=ErrorContext(
        element_type="PIPE",
        element_name="L1",
        parameter="LEN",
        file_path="model.kdf",
    ),
    suggestion="Check that length is a positive number",
)
```

---

## CLI Usage

The pyKorf CLI provides convenient commands for common operations:

```bash
# Install CLI dependencies
pip install pykorf[cli]

# Validate a model
pykorf validate model.kdf

# Convert to JSON
pykorf convert model.kdf output.json --format json

# Query elements
pykorf query model.kdf --type PIPE --limit 10
pykorf query model.kdf --name "P*" --format table

# Export to Excel
pykorf export model.kdf output.xlsx --format excel

# Show summary
pykorf summary model.kdf

# Enable verbose output
pykorf -v validate model.kdf
```

### CLI Output Examples

**Validation:**
```
✓ Model is valid
```

**Summary:**
```
┌─────────────┬─────────────────────────┐
│ Property    │ Value                   │
├─────────────┼─────────────────────────┤
│ File        │ model.kdf               │
│ Version     │ KORF_3.6                │
│ Cases       │ ['NORMAL', 'RATED']     │
│ Pipes       │ 10                      │
│ Pumps       │ 2                       │
└─────────────┴─────────────────────────┘
```

---

## Best Practices

### 1. Use Context Managers for Logging

```python
from pykorf.log import log_operation

with log_operation("process_batch", batch_size=100):
    # Your code here
    pass
```

### 2. Validate Before Saving

```python
if config.validation.check_connectivity_on_save:
    issues = model.check_connectivity()
    if issues:
        logger.warning("Connectivity issues detected", count=len(issues))

model.save()
```

### 3. Use Type Hints

```python
from pykorf.types import PipeData
from pykorf.model import Model

def process_pipes(model: Model) -> list[PipeData]:
    return [pipe for pipe in model.pipes.values() if pipe.index > 0]
```

### 4. Handle Exceptions Gracefully

```python
from pykorf.exceptions import KorfError

try:
    model = Model(path)
except KorfError as e:
    logger.error("Failed to load model", error=e.to_dict())
    raise
```

---

## Performance Tips

1. **Enable caching** for repeated operations:
   ```python
   config = get_config()
   config.performance.enable_caching = True
   config.performance.cache_size = 256
   ```

2. **Use lazy loading** for large models:
   ```python
   config.performance.lazy_loading = True
   ```

3. **Query efficiently**:
   ```python
   # Good: Filter first, then access
   pipes = q.pipes.where(attr("diameter_inch") == "6").all()
   
   # Avoid: Loading all then filtering in Python
   pipes = [p for p in model.pipes.values() if p.diameter_inch == "6"]
   ```

4. **Export selectively**:
   ```python
   # Export only what you need
   options = ExportOptions(include_results=False)
   export_to_json(model, "output.json", options=options)
   ```
