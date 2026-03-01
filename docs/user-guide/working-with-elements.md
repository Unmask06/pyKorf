# Working with Elements

Comprehensive guide to manipulating KORF elements.

## Accessing Elements

### By Name (Recommended)

```python
# Access elements by their NAME tag
pipe = model["L1"]
pump = model["P1"]
valve = model["CV1"]
```

### By Index

```python
# Access by element index
# Index 0 is the template, 1+ are real instances
pipe = model.pipes[1]      # First real pipe
pump = model.pumps[1]      # First real pump
```

### Checking Existence

```python
# Check if element exists
if "L1" in model:
    print("L1 exists")

# Or use try/except
try:
    elem = model["NONEXISTENT"]
except ElementNotFound:
    print("Not found")
```

## Element Properties

### Common Properties

All elements have these properties:

```python
elem = model["L1"]

print(elem.index)        # Element index (1, 2, 3, ...)
print(elem.etype)        # Element type ("PIPE", "PUMP", etc.)
print(elem.name)         # Element name tag ("L1")
print(elem.description)  # Description from NAME record
print(elem.notes)        # User notes
```

### Element-Specific Properties

#### Pipes

```python
pipe = model["L1"]

# Geometry
print(pipe.diameter_inch)      # Nominal diameter
print(pipe.schedule)           # Pipe schedule
print(pipe.length_m)           # Length in meters
print(pipe.material)           # Material ("Steel", etc.)

# Flow
print(pipe.flow_string)        # Raw flow string (e.g., "50;55;20")
print(pipe.get_flow())         # List of flow values
print(pipe.flow_unit)          # Flow unit ("t/h")

# Results (after KORF calculation)
print(pipe.velocity)           # Velocities per case
print(pipe.pressure)           # Pressures per case
print(pipe.reynolds_number)    # Reynolds number
print(pipe.pressure_drop_per_100m)  # dP/100m
```

#### Pumps

```python
pump = model["P1"]

print(pump.pump_type)          # "Centrifugal" or "Reciprocating"
print(pump.efficiency)         # Pump efficiency
print(pump.power_kW)           # Calculated power
print(pump.head_m)             # Calculated head
print(pump.flow_m3h)           # Calculated flow
```

## Modifying Elements

### Update Parameters

```python
from pykorf.definitions import Pipe, Pump

# Update single parameter
model.update_element("L1", {Pipe.LEN: 200})

# Update multiple parameters
model.update_element("L1", {
    Pipe.LEN: 200,
    Pipe.MAT: "Stainless Steel",
    Pipe.SCH: "40"
})

# Update multi-case values
model.update_element("L1", {
    Pipe.TFLOW: "50;55;20"  # 3 cases
})
```

### Setting Position

```python
from pykorf.layout import set_position

# Set element position
set_position(model, "L1", 1000.0, 2000.0)

# Or on the element directly
from pykorf.layout import set_position as set_pos
pipe = model["L1"]
set_pos(pipe, 1000.0, 2000.0)
```

## Adding Elements

### Add Equipment

```python
from pykorf.definitions import Element, Pump, Valve

# Add a pump
model.add_element(Element.PUMP, "P2", {
    Pump.TYPE: "Centrifugal"
})

# Add a valve
model.add_element(Element.VALVE, "CV2", {
    Valve.TYPE: "Linear",
    Valve.CV: "50"
})
```

### Add Pipes with Connectivity

```python
# Pipes must be created via connect_elements
model.connect_elements("P1", "V1", pipe_name="L10")
```

### Batch Add

```python
from pykorf.definitions import Element, Feed, Prod

# Add multiple elements at once
elements = model.add_elements([
    (Element.FEED, "S2", {Feed.PRES: "100"}),
    (Element.FEED, "S3", {Feed.PRES: "120"}),
    (Element.PROD, "D2", {Prod.PRES: "50"}),
])
```

## Copying Elements

### Copy Single Element

```python
# Copy element with new name
copy = model.copy_element("L1", "L1_copy")

# Connectivity is cleared on the copy
print(copy.name)  # "L1_copy"
```

### Copy Multiple

```python
# Copy multiple elements
copies = model.copy_elements([
    ("L1", "L1_copy"),
    ("P1", "P1_copy"),
])
```

## Deleting Elements

### Delete Single

```python
# Delete by name
model.delete_element("L10")
```

### Delete Multiple

```python
# Delete multiple elements
model.delete_elements(["L10", "L11", "L12"])
```

### Delete with Connectivity Update

When you delete a pipe, pyKorf automatically updates references:

```python
# If L1 is connected to P1 and V1
model.delete_element("L1")

# P1 and V1 will have their CON records updated
# (pipe index set to 0)
```

## Moving Elements

### Reorder Indices

```python
# Move element to different index
model.move_element("L5", target_index=10)
```

### Compact Indices

```python
# Reorder all indices to be continuous (1, 2, 3, ...)
model.compact_indices()  # All element types
model.compact_indices("PIPE")  # Just pipes
```

## Working with Collections

### Iterate Elements

```python
# All real elements (index >= 1)
for elem in model.elements:
    print(f"{elem.name}: {elem.etype}")

# Specific type
for idx, pipe in model.pipes.items():
    if idx == 0:
        continue  # Skip template
    print(f"Pipe {idx}: {pipe.name}")
```

### Filter by Type

```python
# Get all elements of a type
pipes = model.get_elements_by_type("PIPE")
pumps = model.get_elements_by_type("PUMP")
```

## Best Practices

### 1. Use Constants

```python
# Always use constants from definitions
from pykorf.definitions import Element, Pipe, Common

model.update_element("L1", {Pipe.LEN: 100})  # Good
model.update_element("L1", {"LEN": 100})     # Bad
```

### 2. Handle Missing Elements

```python
try:
    elem = model[name]
except ElementNotFound:
    logger.warning(f"Element {name} not found")
    return
```

### 3. Validate After Bulk Changes

```python
# After many changes
model.update_elements({...})
issues = model.validate()
if issues:
    logger.warning(f"Validation issues: {issues}")
```

### 4. Use Descriptive Names

```python
# Good names
cooling_water_feed
main_process_line
product_transfer_pump

# Avoid single letters
L1  # OK if following existing convention
P1  # OK if following existing convention
```

## Next Steps

- [Connectivity](connectivity.md)
- [Multi-Case Analysis](multi-case-analysis.md)
