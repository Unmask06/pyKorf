---
hide:
  - navigation
  - toc
---

# pyKorf

**Enterprise Python toolkit for reading, editing, validating, and writing KORF hydraulic model files (.kdf).**

<div class="hero" markdown>

## Build, analyze, and automate hydraulic simulations with Python

</div>

<div class="grid cards" markdown>

-   :material-rocket-launch:{ .lg .middle } __Quick Start__

    ---

    Get up and running in minutes with our quick start guide.

    [:octicons-arrow-right-24: Getting Started](getting-started/quickstart.md)

-   :material-book-open-variant:{ .lg .middle } __User Guide__

    ---

    Learn how to use pyKorf for your hydraulic modeling workflows.

    [:octicons-arrow-right-24: User Guide](user-guide/loading-models.md)

-   :material-code-braces:{ .lg .middle } __API Reference__

    ---

    Comprehensive API documentation with examples.

    [:octicons-arrow-right-24: API Reference](api/overview.md)

-   :material-console:{ .lg .middle } __CLI Tools__

    ---

    Command-line interface for automation and scripting.

    [:octicons-arrow-right-24: CLI Reference](cli/overview.md)

</div>

---

## What is pyKorf?

pyKorf is a comprehensive Python library that enables programmatic manipulation of [KORF](https://www.korf.co.uk/) hydraulic simulation models. KORF is widely used in the oil & gas, chemical, and process industries for pipeline hydraulic calculations.

### Key Features

| Feature | Description |
|---------|-------------|
| **Load & Save** | Read and write `.kdf` files with full fidelity |
| **Edit Models** | Modify element parameters, add/remove elements, update connectivity |
| **Multi-Case** | Handle multiple simulation scenarios in a single file |
| **Validate** | Check model integrity and KDF format compliance |
| **Export** | Export to JSON, YAML, Excel, and CSV formats |
| **Visualize** | Generate interactive network diagrams with PyVis |
| **Automate** | Control the KORF GUI programmatically (Windows) |
| **Type Safe** | Full Pydantic models for data validation |

---

## Installation

```bash
# Basic installation
pip install pykorf

# With all features
pip install pykorf[all]

# Development installation
git clone https://github.com/pykorf/pykorf.git
cd pykorf
pip install -e ".[dev]"
```

---

## Quick Example

```python
from pykorf import Model, Query, attr

# Load a model
model = Model("Pumpcases.kdf")

# Inspect the model
print(f"Version: {model.version}")
print(f"Cases: {model.general.case_descriptions}")
print(f"Pipes: {model.num_pipes}")

# Modify a pipe
model.update_element("L1", {"LEN": 200, "TFLOW": "80;90;60"})

# Query elements
large_pipes = Query(model).pipes.where(attr("diameter_inch") == "8").all()

# Save changes
model.save("Pumpcases_modified.kdf")
```

---

## Project Information

- **License**: MIT
- **Python**: 3.10+
- **Repository**: [github.com/pykorf/pykorf](https://github.com/pykorf/pykorf)
- **Issues**: [GitHub Issues](https://github.com/pykorf/pykorf/issues)

---

## Support

If you encounter any issues or have questions:

1. Search [existing issues](https://github.com/pykorf/pykorf/issues)
3. Create a [new issue](https://github.com/pykorf/pykorf/issues/new)

