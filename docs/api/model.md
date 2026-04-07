# Model API

The `Model` class is the main entry point for working with KDF files.

## Model Class

::: pykorf.core.model.Model
    options:
      show_root_heading: true
      show_source: true
      members:
        - __init__
        - load
        - save
        - to_dataframes
        - from_dataframes
        - to_excel
        - from_excel
        - get_summary
        - validate
        - get_element
        - get_elements
        - get_elements_by_type
        - update_element
        - update_elements
        - add_element
        - add_elements
        - delete_element
        - delete_elements
        - copy_element
        - move_element
        - connect_elements
        - disconnect_elements
        - set_param
        - get_param

## Model Properties

| Property | Type | Description |
|----------|------|-------------|
| `path` | `Path` | Path to the loaded file |
| `version` | `str` | KDF version string |
| `num_pipes` | `int` | Number of pipes |
| `num_pumps` | `int` | Number of pumps |
| `num_cases` | `int` | Number of cases |
| `general` | `General` | General settings |
| `pipes` | `dict[int, Pipe]` | Pipe collection (index 0 = default) |
| `pumps` | `dict[int, Pump]` | Pump collection (index 0 = default) |
| `valves` | `dict[int, Valve]` | Valve collection (index 0 = default) |
| `feeds` | `dict[int, Feed]` | Feed collection (index 0 = default) |
| `products` | `dict[int, Product]` | Product collection (index 0 = default) |
| `junctions` | `dict[int, Junction]` | Junction collection |
| `tees` | `dict[int, Tee]` | Tee collection |
| `check_valves` | `dict[int, CheckValve]` | Check valve collection |
| `orifices` | `dict[int, FlowOrifice]` | Orifice collection |
| `exchangers` | `dict[int, HeatExchanger]` | Heat exchanger collection |
| `compressors` | `dict[int, Compressor]` | Compressor collection |
| `vessels` | `dict[int, Vessel]` | Vessel collection |
| `expanders` | `dict[int, Expander]` | Expander collection |
| `misc_equipment` | `dict[int, MiscEquipment]` | Misc equipment collection |
| `pseudos` | `dict[int, Pseudo]` | Pseudo collection |
| `symbols` | `dict[int, Symbol]` | Symbol collection |

## Service Attributes (Internal)

| Service | Attribute | Purpose |
|---------|-----------|---------|
| `ElementService` | `model._element_service` | CRUD operations |
| `QueryService` | `model._query_service` | Filtering, get/set params |
| `ConnectivityService` | `model._connectivity_service` | Connect/disconnect |
| `LayoutService` | `model._layout_service` | Positioning, routing |
| `IOService` | `model._io_service` | Save, export, import |
| `SummaryService` | `model._summary_service` | Validate, summary |

## Examples

### Loading and Inspecting

```python
from pykorf import Model

model = Model("Pumpcases.kdf")
print(model.get_summary())
```

### Modifying Elements

```python
model.update_element("L1", {
    "LEN": 200,
    "TFLOW": "50;55;20"
})
model.save()
```

### Adding Elements

```python
model.add_element("PUMP", "P2")
model.connect_elements("L1", "P2")
model.save()
```

### Query and Parameters

```python
# Get all pipes
pipes = model.get_elements(etype="PIPE")

# Get/set parameter
flow = model.get_param("L1", "TFLOW")
model.set_param("L1", "TFLOW", "60;65;25")
```

## KorfModel Alias

`KorfModel` is an alias for `Model` for backward compatibility:

```python
from pykorf import KorfModel

model = KorfModel.load("file.kdf")  # Same as Model()
```
