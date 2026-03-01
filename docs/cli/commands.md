# CLI Commands

Complete reference for pyKorf CLI commands.

## validate

Validate a KDF file for errors.

```bash
pykorf validate [OPTIONS] INPUT_FILE
```

### Options

| Option | Description |
|--------|-------------|
| `--strict` | Enable strict validation mode |

### Examples

```bash
# Basic validation
pykorf validate model.kdf

# Strict mode
pykorf validate model.kdf --strict

# Verbose output
pykorf -v validate model.kdf
```

### Output

```
✓ Model is valid
```

Or if issues found:

```
Found 3 issue(s): 2 error(s), 1 warning(s)

#  Issue
1  ERROR Pipe L5: Missing NAME record
2  WARNING Pump P2: Unconnected outlet
3  WARNING General: Default units changed
```

## convert

Convert a KDF file to JSON or YAML.

```bash
pykorf convert [OPTIONS] INPUT_FILE
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `-o, --output` | Auto | Output file path |
| `--format` | `json` | Output format (json/yaml) |
| `--no-results` | False | Exclude calculated results |

### Examples

```bash
# Convert to JSON
pykorf convert model.kdf

# Convert to YAML
pykorf convert model.kdf --format yaml

# Custom output path
pykorf convert model.kdf -o output.json

# Exclude results
pykorf convert model.kdf --no-results
```

## query

Query elements in a KDF file.

```bash
pykorf query [OPTIONS] INPUT_FILE
```

### Options

| Option | Description |
|--------|-------------|
| `--type` | Filter by element type |
| `--name` | Filter by name pattern (glob) |
| `--where` | Filter condition |
| `--limit, -n` | Limit results |
| `--format` | Output format (table/json/csv) |

### Examples

```bash
# List all pipes
pykorf query model.kdf --type PIPE

# Find by name pattern
pykorf query model.kdf --name "P*"

# Complex query
pykorf query model.kdf --where "length_m > 100"

# Limit results
pykorf query model.kdf --type PUMP --limit 5

# JSON output
pykorf query model.kdf --type PIPE --format json

# CSV output
pykorf query model.kdf --format csv
```

### Output Formats

**Table (default):**

```
Query Results (5 elements)

Index  Name  Type  Description
1      L1    PIPE  Main suction
2      L2    PIPE  Main discharge
```

**JSON:**

```json
[
  {"name": "L1", "type": "PIPE", "index": 1},
  {"name": "L2", "type": "PIPE", "index": 2}
]
```

**CSV:**

```csv
name,type,index
L1,PIPE,1
L2,PIPE,2
```

## export

Export model data to various formats.

```bash
pykorf export [OPTIONS] INPUT_FILE OUTPUT_FILE
```

### Options

| Option | Description |
|--------|-------------|
| `--format` | Export format (required) |
| `--no-results` | Exclude calculated results |

### Formats

- `json` - JSON format
- `yaml` - YAML format
- `excel` - Excel workbook
- `csv` - CSV files

### Examples

```bash
# Export to JSON
pykorf export model.kdf output.json --format json

# Export to Excel
pykorf export model.kdf output.xlsx --format excel

# Export to CSV
pykorf export model.kdf ./csv/ --format csv

# Exclude results
pykorf export model.kdf output.json --format json --no-results
```

## summary

Display a summary of the model.

```bash
pykorf summary [OPTIONS] INPUT_FILE
```

### Examples

```bash
pykorf summary model.kdf
```

### Output

```
Model Summary: model.kdf

Property    Value
----------  ----------
File        model.kdf
Version     KORF_3.6
Cases       ['NORMAL', 'RATED']
Pipes       10
Pumps       2
Valves      3
Feeds       1
Products    1

Element Breakdown:

Type   Count
-----  -----
PIPE   10
PUMP   2
VALVE  3
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Validation failed |
