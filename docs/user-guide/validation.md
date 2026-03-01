# Validation

Ensuring model integrity with pyKorf's validation system.

## Overview

pyKorf provides comprehensive validation to ensure your KDF files are:

- **Structurally valid** - Correct format and encoding
- **Semantically valid** - Meaningful data and relationships
- **Complete** - All required fields present

## Running Validation

### Basic Validation

```python
# Validate the entire model
issues = model.validate()

if issues:
    print(f"Found {len(issues)} issues:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("Model is valid!")
```

### Connectivity Validation

```python
# Check element connections
issues = model.check_connectivity()

for issue in issues:
    print(issue)
# "Pump P1: inlet references pipe index 99 which does not exist"
```

### Layout Validation

```python
# Check for layout issues
issues = model.check_layout()

for issue in issues:
    print(issue)
# "Element Pump1 at (1000.0, 2000.0) is outside layout bounds"
```

## Validation Levels

### 1. File Format Validation

- Valid encoding (latin-1)
- Correct line endings
- Valid CSV structure
- Supported version

### 2. Structure Validation

- Required parameters present
- Valid element indices
- NUM records match actual counts
- Element order correct

### 3. Content Validation

- Valid parameter values
- Consistent units
- Logical relationships
- Complete connectivity

### 4. Semantic Validation

- Positive lengths
- Valid diameters
- Consistent pressures
- Realistic temperatures

## Configuration

### Strict Mode

```python
from pykorf.config import get_config

config = get_config()
config.validation.strict_mode = True

# Now validation will be stricter
issues = model.validate()
```

### Environment Variable

```bash
export PYKORF_STRICT_VALIDATION=1
```

## Validation Errors

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Missing NAME record | Element has no name | Assign a name |
| Invalid pipe reference | CON points to non-existent pipe | Fix connection |
| NUM mismatch | NUM record doesn't match count | Regenerate indices |
| Outside layout bounds | XY coordinates invalid | Reposition element |
| Overlapping elements | Two elements at same position | Move one element |

### Handling Validation Errors

```python
from pykorf.exceptions import ValidationError

try:
    issues = model.validate()
    if issues:
        raise ValidationError(issues)
except ValidationError as e:
    print(f"Validation failed:")
    for issue in e.issues:
        print(f"  - {issue}")
```

## Best Practices

### 1. Validate After Loading

```python
model = Model("input.kdf")
issues = model.validate()
if issues:
    logger.warning(f"Loaded model has {len(issues)} issues")
```

### 2. Validate Before Saving

```python
# Before saving critical models
if config.validation.check_connectivity_on_save:
    issues = model.check_connectivity()
    if issues:
        raise ValueError(f"Cannot save: {issues}")

model.save()
```

### 3. Log Validation Issues

```python
from pykorf.log import get_logger

logger = get_logger()

issues = model.validate()
for issue in issues:
    if "ERROR" in issue:
        logger.error(issue)
    else:
        logger.warning(issue)
```

## Next Steps

- [Working with Elements](working-with-elements.md)
- [Export & Import](export-import.md)
