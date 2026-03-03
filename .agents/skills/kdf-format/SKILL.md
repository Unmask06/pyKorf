---
name: kdf-format
description: KDF file format, parser internals, record structure, encoding, and round-trip rules
---

# KDF File Format Reference

## File Structure

- Encoding: `latin-1` (NOT UTF-8)
- Line endings: `\r\n` (Windows CRLF)
- Record format: `\ETYPE,index,PARAM,value1,value2,...`
- Header lines: verbatim text (version string, comments)
- Reference file : `pykorf/library/New.kdf` defines the template (index-0 records) for all element types and their parameters.

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

## KdfParser

```python
parser = KdfParser("model.kdf")   # encoding defaults to latin-1
records = parser.load()            # → list[KdfRecord]
parser.save(records)               # write back, preserving order
```

## Multi-case Values

- Semicolon-delimited: `"50;55;20"` → 3 cases
- Calculated marker: value ending with `";C"` means KORF-computed
- Split/join helpers: `split_cases(val)`, `join_cases(vals)`

## Version Awareness

| Version    | Differences                            |
| ---------- | -------------------------------------- |
| `KORF_2.0` | `NOZ` nozzle parameter                 |
| `KORF_3.0` | Transitional                           |
| `KORF_3.6` | `NOZL` replaces `NOZ`, fitting changes |

## Round-trip Rules

1. `raw_line` preserved on unmodified records → exact byte-for-byte fidelity
2. Only `record.update()` clears `raw_line` (marks dirty)
3. Dirty records rebuilt via `format_line()` in `pykorf.utils`
4. Record ORDER must be preserved — never sort or reorder

## Key Files

- `pykorf/parser.py` — `KdfParser`, `KdfRecord`
- `pykorf/utils.py` — `parse_line()`, `format_line()`, `split_cases()`, `join_cases()`
- `pykorf/library/New.kdf` — default template (index-0 records define param schemas)
