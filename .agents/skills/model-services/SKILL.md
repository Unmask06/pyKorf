---
name: model-services
description: Model class facade, service-oriented architecture, delegation patterns, and standalone helpers
---

# Model Services Architecture

## The Model Facade
The `Model` class in `pykorf/model/__init__.py` acts as a facade. It delegates specialized operations to specific service classes located in `pykorf/model/services/`.

## Service Domains
When adding new functionality to the `Model`, place the logic in the appropriate service, NOT directly in `core.py` or `__init__.py`.

| Service | Domain | Key Methods |
| :--- | :--- | :--- |
| `ElementService` | CRUD operations for elements | `add_element`, `update_element`, `delete_element`, `copy_element`, `move_element` |
| `QueryService` | Element querying and parameter access | `get_elements`, `get_elements_by_type`, `get_params`, `set_params` |
| `ConnectivityService` | Element connections and validation | `connect_elements`, `disconnect_elements`, `check_connectivity` |
| `LayoutService` | Element positioning and visualization | `set_position`, `auto_place`, `auto_layout`, `visualize_network` |
| `IOService` | File I/O and export operations | `save`, `to_dataframes`, `to_excel` |
| `SummaryService` | Validation and model statistics | `validate`, `summary`, `pipe()`, `pump()` |

## Standalone Helpers
Some advanced operations are handled by standalone helper classes that take a `Model` as an argument.

| Class | Source | Purpose |
| :--- | :--- | :--- |
| `CaseSet` | `pykorf.cases` | Manage multi-case (scenarios) logic. |
| `Results` | `pykorf.results` | Extract calculated results (power, head, velocity). |
| `Visualizer` | `pykorf.visualization` | Generate interactive PyVis HTML networks. |

## Internal Access
- Services have a `self.model` reference to the main `Model` instance.
- To access low-level parser operations, use `self.model._parser`.
- To access raw element collections, use `self.model.pipes`, `self.model.pumps`, etc.
- When creating a new Model method, define it in the relevant service and map it in `pykorf/model/__init__.py`.

## Parameter Setting & Validation

### Strict Schema Validation
The library enforces strict validation on the number of elements provided when setting parameters via `set_params` or `update_element`. This is based on the schema defined in `pykorf/library/New.kdf` (index-0 records).

If the input list length does not match the expected count, a `ParameterError` is raised.

### Common Parameter Formats
Most KDF parameters are stored as lists containing raw input, calculated results, and unit strings.

| Parameter Type | Typical Format | Example |
| :--- | :--- | :--- |
| **Simple Property** | `[value, "unit"]` | `Pipe.LEN: [100, "m"]` |
| **Multi-case Value** | `[case1, case2, case3, "unit"]` | `Pipe.TEMP: [50, 55, 20, "C"]` |
| **Input String** | `["val1;val2", calc, "unit"]` | `Pipe.TFLOW: ["50;60", 0, "t/h"]` |
| **Coordinate** | `[x, y]` | `Feed.XY: [1200, 4300]` |

### Best Practices
1. **Prefer Scalar Overrides:** `Model.update_element` allows passing a scalar which it will internally convert if simple.
2. **Consult Template:** Use `model.get_params(name, param).values` to see the current structure.
3. **Use Constants:** Always use parameter constants (e.g., `Pipe.TFLOW`) to ensure correct lookup and validation.
