---
name: kdf-format
description: KDF file format, parser internals, record structure, encoding, and round-trip rules
---

# KDF File Format Reference

## File Structure

- **Encoding:** `latin-1` (NOT UTF-8)
- **Line endings:** `\r\n` (Windows CRLF)
- **Record format:** `\ETYPE,index,PARAM,value1,value2,...`
- **Header lines:** Verbatim text (version string, comments)
- **Template:** `pykorf/library/New.kdf` defines index-0 records (schemas) for all types.

## KdfRecord

```python
from pykorf.parser import KdfParser, KdfRecord

# Each line → one KdfRecord
record.element_type  # "PIPE", "PUMP", etc. (None for verbatim lines)
record.index         # int (0 = template, 1+ = real instances)
record.param         # "LEN", "DIA", etc.
record.values        # list of value tokens
record.raw_line      # original text (preserved for unmodified records)

record.key()         # → (etype, index, param) or None
record.to_line()     # serialize back (uses raw_line if unmodified)
record.update(vals)  # replace values + mark dirty (clears raw_line)
```

## Multi-case Values
- Semicolon-delimited strings: `"50;55;20"` → 3 cases.
- Calculated marker: Value ending with `";C"` means KORF-computed.
- Use `split_cases(val)` and `join_cases(vals)` helpers in `pykorf.utils`.

## Round-trip Rules
1. **Fidelity:** `raw_line` is preserved for unmodified records.
2. **Dirty Marker:** Only `record.update()` clears `raw_line`.
3. **Ordering:** Never sort or reorder records; KORF is sensitive to sequence.

## PIPE Criteria Parameters (SIZ, DPL, VEL)

### SIZ (Sizing Criteria)
Format: `\PIPE,index,"SIZ","",dP_dL,unit,max_vel,min_vel,max_coeff,min_coeff,vel_unit`
- `dP_dL`: Pressure drop per length criteria (e.g., `22.6`).
- `max_vel`, `min_vel`: Velocity bounds.

### DPL (Calculated Pressure Drop)
Format: `\PIPE,index,"DPL",value,unit`
- `value`: Calculated pressure drop per 100m.
- **Validation:** Must be `<= SIZ.dP_dL`.

### VEL (Calculated Velocities)
Format: `\PIPE,index,"VEL",V_avg,V_in,V_out,V_sonic,unit`
- `V_avg`, `V_in`, `V_out`: Calculated velocities.
- **Validation:** Must be within `SIZ.min_vel` and `SIZ.max_vel`.

## Key Files
- `pykorf/parser.py`: `KdfParser`, `KdfRecord`.
- `pykorf/utils.py`: `parse_line()`, `format_line()`, `split_cases()`.
- `pykorf/library/New.kdf`: Schema reference.
