# Quick Start

Get up and running with pyKorf in minutes.

## Your First Model

### Loading an Existing Model

```python
from pykorf import Model

# Load an existing KDF file
model = Model("Pumpcases.kdf")

# Display basic information
print(f"Version: {model.version}")
print(f"Cases: {model.general.case_descriptions}")
print(f"Pipes: {model.num_pipes}")
print(f"Pumps: {model.num_pumps}")
```

### Creating a New Model

```python
from pykorf import Model
from pykorf.elements import Element, Pipe, Feed, Product

# Create a blank model from the default template
model = Model()

# Add elements
model.add_element(Element.FEED, "S1", {Feed.PRES: "100"})
model.add_element(Element.PROD, "D1", {Product.PRES: "50"})

# Connect them with a pipe
model.connect_elements("S1", "D1", pipe_name="L1")

# Configure the pipe
model.update_element("L1", {
    Pipe.LEN: 100,
    Pipe.DIA: "6",
    Pipe.TFLOW: "50"
})

# Save the model
model.save("new_model.kdf")
```

## Working with Elements

### Accessing Elements

```python
# By name (recommended)
pipe = model["L1"]
pump = model["P1"]

# By index
pipe = model.pipes[1]  # Index 1 is the first real pipe
pump = model.pumps[1]

# List all elements
for elem in model.elements:
    print(f"{elem.name}: {elem.etype}")
```

### Modifying Elements

```python
# Update parameters
model.update_element("L1", {
    Pipe.LEN: 200,
    Pipe.MAT: "Steel"
})

# Update multi-case values
model.update_element("L1", {
    Pipe.TFLOW: "50;55;20"  # 3 cases
})
```

## Multi-Case Analysis

```python
from pykorf import Model, CaseSet

model = Model("Pumpcases.kdf")
cases = CaseSet(model)

# List cases
print(f"Cases: {cases.names}")  # ['NORMAL', 'RATED', 'MINIMUM']

# Get flow table
flows = cases.pipe_flows_table()
for row in flows[:3]:
    print(row)

# Activate specific cases
cases.activate_cases([1, 2])  # Run only cases 1 and 2
model.save()
```

## Querying Elements

```python
from pykorf import Model

model = Model("Pumpcases.kdf")

# Find all pipes
pipes = model.get_elements(etype="PIPE")

# Find by name pattern
p_elements = model.get_elements(name="P*")

# Get element parameters
params = model.get_params("L1")
len_value = model.get_params("L1", param="LEN")

# Set element parameters
model.set_params("L1", {"LEN": 200, "DIAM": 50})
```

## Validation

```python
# Validate the model
issues = model.validate()

if issues:
    print(f"Found {len(issues)} issues:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("Model is valid!")

# Check connectivity
conn_issues = model.check_connectivity()
if conn_issues:
    print("Connectivity issues:", conn_issues)
```

## Export

```python
from pykorf.export import export_to_json, export_to_excel

# Export to JSON
export_to_json(model, "model.json")

# Export to Excel
export_to_excel(model, "model.xlsx")
```

## Next Steps

- Learn about [core concepts](concepts.md)
- Explore the [user guide](../user-guide/loading-models.md)
- Check out the [API reference](../api/overview.md)
