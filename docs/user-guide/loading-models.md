# Loading and Saving Models

Working with KDF files in pyKorf.

## Loading Models

### From File

```python
from pykorf import Model

# Load an existing KDF file
model = Model("path/to/model.kdf")
```

### Creating Blank Models

```python
# Create a blank model from the default template
model = Model()  # Uses pykorf/library/New.kdf

# The template includes default values for all element types
```

### From Template

```python
from pathlib import Path

# Load from a custom template
template_path = Path("my_template.kdf")
model = Model(template_path)
```

## Model Information

### Basic Properties

```python
# File information
print(model.path)        # Path to the loaded file
print(model.version)     # KDF version (e.g., "KORF_3.6")

# Element counts
print(model.num_pipes)
print(model.num_pumps)
print(model.num_cases)

# Summary
summary = model.summary()
print(summary)
# {
#     'file': 'model.kdf',
#     'version': 'KORF_3.6',
#     'cases': ['NORMAL', 'RATED', 'MINIMUM'],
#     'num_pipes': 10,
#     'num_pumps': 2,
#     ...
# }
```

### General Settings

```python
# Access general settings
print(model.general.case_descriptions)  # ['NORMAL', 'RATED', 'MINIMUM']
print(model.general.units)              # 'Metric'
print(model.general.project_name)       # Project name
```

## Saving Models

### Save Over Original

```python
# Overwrite the original file
model.save()
```

### Save As New File

```python
# Save to a new file
model.save("modified_model.kdf")

# Or use save_as (alias)
model.save_as("backup.kdf")
```

### Save With Validation

```python
# Validate before saving
issues = model.validate()
if issues:
    print("Validation issues found:")
    for issue in issues:
        print(f"  - {issue}")
    # Decide whether to save anyway
else:
    model.save()
```

## File Paths

### Working with Paths

```python
from pathlib import Path

# pyKorf uses pathlib.Path internally
model = Model(Path("models") / "pump.kdf")

# Get absolute path
abs_path = model.path.resolve()

# Check if file exists
if model.path.exists():
    print("File exists")
```

## Error Handling

### Common Errors

```python
from pykorf import Model
from pykorf.exceptions import ParseError, KorfError

try:
    model = Model("corrupted.kdf")
except ParseError as e:
    print(f"Failed to parse: {e}")
    # e.context may contain file_path, line_number
except FileNotFoundError:
    print("File not found")
except KorfError as e:
    print(f"Korf error: {e}")
```

### Validation on Load

```python
model = Model("model.kdf")

# Always validate after loading if file integrity is critical
issues = model.validate()
if issues:
    raise ValueError(f"Model has {len(issues)} validation issues")
```

## Best Practices

### 1. Always Save Explicitly

```python
# Changes are in-memory only until save()
model.update_element("L1", {Pipe.LEN: 200})
# ... more changes ...
model.save()  # Don't forget this!
```

### 2. Backup Before Modifying

```python
from shutil import copy

# Backup original
copy("model.kdf", "model_backup.kdf")

# Now modify
model = Model("model.kdf")
# ... changes ...
model.save()
```

### 3. Use Context Managers for Batch Operations

```python
from pykorf.log import log_operation

with log_operation("batch_update", file="model.kdf"):
    model = Model("model.kdf")
    
    # Multiple changes
    for i in range(1, model.num_pipes + 1):
        pipe = model.pipes[i]
        model.update_element(pipe.name, {Pipe.LEN: 100})
    
    model.save()
```

### 4. Handle Encoding Properly

pyKorf handles `latin-1` encoding automatically. Don't try to convert:

```python
# Don't do this
with open("model.kdf", "r", encoding="utf-8") as f:  # Wrong!
    ...

# pyKorf handles encoding internally
model = Model("model.kdf")  # Correct
```

## Next Steps

- [Working with Elements](working-with-elements.md)
- [Validation](validation.md)
- [Export & Import](export-import.md)
