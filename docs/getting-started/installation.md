# Installation

This guide covers all installation options for pyKorf.

## Requirements

- **Python**: 3.10 or higher
- **Operating System**: Windows, macOS, or Linux
- **Optional**: Windows with KORF installed (for GUI automation)

## Basic Installation

Install pyKorf with uv (recommended):

```bash
uv pip install pykorf
```

Or with pip:

```bash
pip install pykorf
```

## Installation Options

pyKorf has optional dependencies for specific features.

### With All Features

```bash
uv pip install pykorf[all]
```

### Feature-Specific Installation

=== "Visualization"

    For network visualization with PyVis:

    ```bash
    uv pip install pykorf[visualization]
    ```

    Includes: `pyvis`, `networkx`

=== "DataFrames"

    For pandas DataFrame export:

    ```bash
    uv pip install pykorf[dataframe]
    ```

    Includes: `pandas`, `openpyxl`

=== "CLI"

    For command-line interface:

    ```bash
    uv pip install pykorf[cli]
    ```

    Includes: `click`, `rich`

=== "Export"

    For additional export formats:

    ```bash
    uv pip install pykorf[export]
    ```

    Includes: `pyyaml`, `orjson`

=== "Automation"

    For GUI automation (Windows only):

    ```bash
    uv pip install pykorf[automation]
    ```

    Includes: `pywinauto`, `pywin32`

=== "Development"

    For contributing to pyKorf:

    ```bash
    uv pip install pykorf[dev]
    ```

    Includes: `pytest`, `mypy`, `ruff`, `pre-commit`, `mkdocs`

## Development Installation

If you want to contribute to pyKorf or modify the source code:

1. Clone the repository:

```bash
git clone https://github.com/pykorf/pykorf.git
cd pykorf
```

2. Create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install in editable mode with all dependencies:

```bash
uv pip install -e ".[dev]"
```

Or with pip:

```bash
pip install -e ".[dev]"
```

## Verify Installation

Test your installation:

```python
import pykorf

print(f"pyKorf version: {pykorf.__version__}")

# Test basic functionality
from pykorf import Model
model = Model()  # Creates blank model from template
print(f"Default model version: {model.version}")
```

## Troubleshooting

### ImportError for optional dependencies

If you see errors about missing modules:

```python
# Error: "No module named 'pandas'"
# Solution: Install the dataframe extra
uv pip install pykorf[dataframe]
```

### Windows GUI automation not working

The automation module requires Windows and pywinauto:

```bash
uv pip install pykorf[automation]
```

### Encoding issues on Windows

pyKorf internally uses `latin-1` encoding for KDF files, which should work on all platforms.

## Next Steps

- [Quick Start Guide](quickstart.md) - Get started with pyKorf
- [Core Concepts](concepts.md) - Understand the pyKorf architecture
