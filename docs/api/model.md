# Model API

The `Model` class is the main entry point for working with KDF files.

## Model Class

::: pykorf.model.Model
    options:
      show_root_heading: true
      show_source: true
      members:
        - __init__
        - load
        - save
        - save_as
        - summary
        - validate
        - get_element
        - update_element
        - update_elements
        - add_element
        - add_elements
        - delete_element
        - delete_elements
        - copy_element
        - copy_elements
        - move_element
        - connect_elements
        - disconnect_elements
        - check_connectivity
        - get_connection
        - get_unconnected_elements
        - check_layout
        - visualize
        - visualize_network
        - get_elements_by_type
        - compact_indices

## Model Properties

| Property | Type | Description |
|----------|------|-------------|
| `path` | `Path` | Path to the loaded file |
| `version` | `str` | KDF version string |
| `num_pipes` | `int` | Number of pipes |
| `num_pumps` | `int` | Number of pumps |
| `num_cases` | `int` | Number of cases |
| `elements` | `list[BaseElement]` | All real elements |
| `general` | `General` | General settings |
| `pipes` | `dict[int, Pipe]` | Pipe collection |
| `pumps` | `dict[int, Pump]` | Pump collection |
| `valves` | `dict[int, Valve]` | Valve collection |
| `feeds` | `dict[int, Feed]` | Feed collection |
| `products` | `dict[int, Product]` | Product collection |
| `exchangers` | `dict[int, HeatExchanger]` | HX collection |
| `compressors` | `dict[int, Compressor]` | Compressor collection |
| `vessels` | `dict[int, Vessel]` | Vessel collection |
| `tees` | `dict[int, Tee]` | Tee collection |
| `junctions` | `dict[int, Junction]` | Junction collection |
| `check_valves` | `dict[int, CheckValve]` | Check valve collection |
| `orifices` | `dict[int, FlowOrifice]` | Orifice collection |
| `expanders` | `dict[int, Expander]` | Expander collection |
| `misc_equipment` | `dict[int, MiscEquipment]` | Misc equipment collection |

## Examples

### Loading and Inspecting

```python
from pykorf import Model

model = Model("Pumpcases.kdf")
print(model.summary())
```

### Modifying Elements

```python
from pykorf.definitions import Pipe

model.update_element("L1", {
    Pipe.LEN: 200,
    Pipe.TFLOW: "50;55;20"
})
model.save()
```

### Adding Elements

```python
from pykorf.definitions import Element, Pump

model.add_element(Element.PUMP, "P2")
model.connect_elements("L1", "P2")
model.save()
```

## KorfModel Alias

`KorfModel` is an alias for `Model` for backward compatibility:

```python
from pykorf import KorfModel

model = KorfModel.load("file.kdf")  # Same as Model()
```
