# Validation

Ensuring model integrity with pyKorf's layered validation system.

## Overview

pyKorf provides a three-layer validation architecture accessible through a single `model.validate()` call:

| Layer | Source | Checks |
|---|---|---|
| **Core** | `pykorf.core.model.summary` | Pipe sizing criteria (DP/DL, velocity, ρV²), title symbol presence |
| **App** | `pykorf.app.validation` | PMS spec compliance, line-number parsing, pipe property vs. PMS match |
| **Connectivity** | `pykorf.core.model.connectivity` | Dangling pipe references, unconnected equipment, invalid CON/NOZL indices |

Each layer runs independently and their results are combined into a single `list[str]` of human-readable issue descriptions.

## Running Validation

### All Checks at Once

```python
issues = model.validate()

if issues:
    print(f"Found {len(issues)} issues:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("Model is valid!")
```

`model.validate()` runs all three layers in sequence:
1. **Core** — sizing criteria from the KDF's SIZ records + title symbol check
2. **App** — PMS spec, line-number parsing, pipe properties (DIA/SCH/ID/MAT)
3. **Connectivity** — dangling pipe references, unconnected elements

### What Each Layer Checks

**Core checks** (pure KDF data, no external config needed):
- Pipe DP/DL vs. SIZ dP/dL criteria (skips if criteria is 0)
- Pipe velocity vs. SIZ max velocity criteria (skips if 0)
- Pipe ρV² vs. min/max bounds from sizing tables (skips if null or 0)
- Model has at least one title SYMBOL (TYPE='Text', FSIZ > 1.5)

**App checks** (requires PMS config file to be set in Preferences):
- Every pipe has a parseable line number in its NOTES field
- PMS code from line number exists in the PMS specification file
- Schedule or ID is defined for the PMS code at the given NPS
- Pipe DIA matches expected NPS from line number
- Pipe SCH/ID matches expected PMS specification
- Pipe MAT matches expected PMS material

**Connectivity checks** (pure structural integrity):
- Equipment CON/NOZL/NOZ/NOZI/NOZO records reference valid pipe indices
- Feed/Product NOZL/NOZ records reference valid pipe indices
- Tee CON records reference valid pipe indices on all three ports
- No dangling references to non-existent pipe indices

## Validation Results in Excel Reports

### Single-File Report (`Generate Report` on the Reports page)

The report Excel includes a **Validation** sheet as the first tab (when issues exist):

| Severity | Category | Element | Message |
|---|---|---|---|
| Error | Sizing | L1 | Pipe 'L1' fails sizing criteria: DP/DL(0.642 > 0.500). |
| Error | Connectivity | V1 | V1 (VALVE): inlet references pipe index 999 which does not exist |
| Info | Model Setup | — | Add Title (Text with font size > 1.5) |

Severity levels are color-coded: red for errors, yellow for warnings, blue for info.

### Batch Report (`Batch Report` on the Reports page)

The batch Excel workbook includes the same **Validation** sheet with an additional `source_file` column so you can trace each issue back to its KDF file:

| source_file | Severity | Category | Element | Message |
|---|---|---|---|---|
| model1.kdf | Error | Sizing | L1 | Pipe 'L1' fails sizing criteria... |
| model2.kdf | Error | Connectivity | V1 | V1 (VALVE): inlet references... |

## Validation Errors

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Missing line number | Pipe NOTES field is empty | Add line number in NOTES |
| PMS not found | PMS code in NOTES doesn't exist in PMS file | Fix PMS code or add it to the PMS specification |
| Sizing criteria failure | Calculated DP/DL, velocity, or ρV² exceeds limits | Resize pipe or adjust criteria |
| Invalid pipe reference | CON points to non-existent pipe index | Fix connection |
| Property mismatch | Pipe DIA/SCH/MAT doesn't match PMS spec | Update pipe properties or fix line number |
| Missing title | No SYMBOL with TYPE='Text' and FSIZ > 1.5 | Add title symbol in KORF GUI |

### Handling Validation Errors

```python
from pykorf.exceptions import ValidationError

issues = model.validate()
if issues:
    raise ValidationError(issues, file_path=str(model._parser.path))
```

## Best Practices

### 1. Validate After Loading

```python
model = Model("input.kdf")
issues = model.validate()
if issues:
    for issue in issues:
        logger.warning(issue)
```

### 2. Ensure Model Has Title

All KDF models should have at least one title symbol for identification. A title is defined as a SYMBOL element with:
- `TYPE` = "Text"
- `FSIZ` > 1.5

To add a title:
1. Open the model in KORF GUI
2. Insert a SYMBOL element
3. Set TYPE to "Text"
4. Set FSIZ to 2
5. Enter the title text in the TEXT field

### 3. Validate Before Saving

```python
issues = model.validate()
if issues:
    logger.warning(f"Model has {len(issues)} validation issue(s)")
model.save()
```

### 4. PMS Config Required for App-Level Checks

App-level validation (line numbers, PMS compliance, pipe properties) requires a PMS specification file to be configured in **Preferences → PMS Path**. Without it, app-level checks are silently skipped.

## Next Steps

- [Working with Elements](working-with-elements.md)
- [Export & Import](export-import.md)
