# CLI Overview

pyKorf provides a command-line interface for common operations.

## Installation

The CLI requires additional dependencies:

```bash
pip install pykorf[cli]
```

## Usage

```bash
pykorf --help
```

## Available Commands

| Command | Description |
|---------|-------------|
| `validate` | Validate a KDF file |
| `convert` | Convert to JSON/YAML |
| `query` | Query elements |
| `export` | Export to various formats |
| `summary` | Display model summary |

## Global Options

```bash
pykorf [OPTIONS] COMMAND [ARGS]...

Options:
  -v, --verbose  Enable verbose output
  --version      Show version
  --help         Show help
```

## Next Steps

- [Commands Reference](commands.md)
