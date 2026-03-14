# Connectivity

Managing connections between elements in your hydraulic model.

## Connectivity Model

In KORF, **pipes** are the edges and **equipment** are the nodes:

```
Feed → Pipe1 → Pump → Pipe2 → Valve → Pipe3 → Product
```

- **Pipes** don't have explicit connections; they're referenced by equipment
- **Equipment** has `CON` records: `[inlet_pipe, outlet_pipe]`
- **Boundaries** (Feed/Product) have `NOZL` records: `[pipe_index]`

## Connecting Elements

### Connect Two Elements

```python
# Connect two elements (creates pipe if needed)
model.connect_elements("Feed1", "Pump1")

# Specify pipe name
model.connect_elements("Pump1", "Product1", pipe_name="Discharge")
```

### Connect Multiple Pairs

```python
# Connect multiple pairs at once
model.connect_elements([
    ("Feed1", "Pump1"),
    ("Pump1", "Valve1"),
    ("Valve1", "Product1"),
])

# With custom pipe names
model.connect_elements([
    ("Feed1", "Pump1", "Suction"),
    ("Pump1", "Product1", "Discharge"),
])
```

### Connecting Pipes Directly

```python
# If both elements are pipes, you need an intermediate element
# This will fail:
# model.connect_elements("L1", "L2")  # Error!

# Instead, use a Tee or Junction
model.add_element(Element.TEE, "T1")
model.connect_elements("L1", "T1")
model.connect_elements("L2", "T1")
model.connect_elements("L3", "T1")  # Third leg
```

## Disconnecting Elements

### Disconnect Two Elements

```python
# Remove connection between elements
model.disconnect_elements("Pump1", "Pipe1")
```

### Disconnect Multiple

```python
model.disconnect_elements([
    ("Pump1", "Pipe1"),
    ("Valve1", "Pipe2"),
])
```

## Querying Connections

### Get Connections

```python
# Get all elements connected to a pipe
connected = model.get_connection("L1")
print(connected)  # ['Pump1', 'Valve1']

# Get connections for equipment
# (returns connected pipe names)
connected = model.get_connection("Pump1")
print(connected)  # ['Suction', 'Discharge']
```

### Check Connectivity

```python
# Validate all connections
issues = model.check_connectivity()
if issues:
    for issue in issues:
        print(issue)
else:
    print("All connections valid")
```

### Find Unconnected Elements

```python
# Find elements with open connections
unconnected = model.get_unconnected_elements()
print(f"Unconnected: {unconnected}")
```

## Connection Types

### Equipment with CON

```python
# Pump, Valve, Compressor, etc.
# CON = [inlet_pipe, outlet_pipe]

pump = model["P1"]
rec = pump.get_param(Common.CON)
print(rec.values)  # [1, 2] - pipe indices
```

### Feed/Product with NOZL

```python
# Feed and Product boundaries
# NOZL = [pipe_index]

feed = model["Source"]
rec = feed.get_param(Common.NOZL)  # or Common.NOZ for older versions
print(rec.values)  # [1] - single pipe index
```

### Tee with CON

```python
# Tee has 6 values in CON:
# [C_in, C_out, M_in, M_out, B_in, B_out]
# (Combined, Main, Branch)

tee = model["T1"]
rec = tee.get_param(Common.CON)
print(rec.values)  # [1, 0, 2, 0, 3, 0]
```

### Junction with NOZI/NOZO

```python
# Junction has multiple NOZI/NOZO records
# NOZI = inlet nozzles
# NOZO = outlet nozzles

junc = model["J1"]
for rec in junc.records():
    if rec.param in (Common.NOZI, Common.NOZO):
        print(f"{rec.param}: {rec.values}")
```

## Advanced Connectivity

### Update Pipe References

When you delete or move a pipe, references are automatically updated:

```python
# Delete a pipe
model.delete_element("L1")

# P1's CON record is automatically updated
# (L1's index is replaced with 0)
```

### Manual Reference Updates

```python
from pykorf.connectivity import update_pipe_references

# Manually update references (rarely needed)
update_pipe_references(model, old_pipe_index=5, new_pipe_index=10)
```

## Visualization

### Text Visualization

```python
# Get text representation of connectivity
viz = model.visualize()
print(viz)

# Output:
# === Model Layout ===
# [PIPE]
#   L1          idx=1   (1000, 2000)
# [PUMP]
#   P1          idx=1   (1500, 2000)
# [Connections]
#   L1 --> [P1] --> L2
```

### Network Graph

```python
# Generate interactive HTML
model.visualize_network("network.html")
```

## Best Practices

### 1. Connect in Logical Order

```python
# Build the model in flow direction
model.connect_elements("Feed", "Pump")
model.connect_elements("Pump", "Valve")
model.connect_elements("Valve", "Product")
```

### 2. Name Pipes Meaningfully

```python
# Good names
model.connect_elements("P1", "V1", pipe_name="P1_to_V1")
model.connect_elements("V1", "Prod", pipe_name="V1_Discharge")
```

### 3. Validate After Changes

```python
# After modifying connectivity
model.connect_elements(...)
issues = model.check_connectivity()
if issues:
    raise ValueError(f"Connectivity issues: {issues}")
```

### 4. Check for Orphans

```python
# Before saving
unconnected = model.get_unconnected_elements()
if unconnected:
    logger.warning(f"Unconnected elements: {unconnected}")
```

## Troubleshooting

### Common Issues

```python
# Issue: Cannot connect two pipes
try:
    model.connect_elements("L1", "L2")
except ConnectivityError as e:
    print("Use a Tee or Junction between pipes")

# Issue: Element already connected
try:
    model.connect_elements("Pump1", "L3")
except ConnectivityError as e:
    print("Pump1 may already have both connections filled")
```

## Next Steps

- [Validation](validation.md)
- [Working with Elements](working-with-elements.md)
