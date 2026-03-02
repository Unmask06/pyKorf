# Multi-Case Analysis

Working with multiple simulation scenarios in KORF.

## Understanding Cases

KORF supports running multiple simulation scenarios (cases) in a single file. Each case can have different:

- Flow rates
- Pressures
- Temperatures
- Fluid properties

### Case Structure

```python
from pykorf import Model, CaseSet

model = Model("Pumpcases.kdf")
cases = CaseSet(model)

# Case information
print(cases.names)      # ['NORMAL', 'RATED', 'MINIMUM']
print(cases.count)      # 3
print(cases.numbers)    # ['1', '2', '3']
```

## Setting Case Values

### Setting Flows

```python
# Set pipe flow for all cases
model.pipes[1].set_flow([50, 55, 20])

# Or as semicolon-delimited string
model.update_element("L1", {Pipe.TFLOW: "50;55;20"})
```

### Setting Pressures

```python
# Set feed pressure for all cases
model.feeds[1].set_pressure([100, 120, 80])

# Set product back-pressure
model.products[1].set_pressure([50, 60, 40])
```

### Setting Temperatures

```python
# Set pipe temperature (per case)
model.update_element("L1", {
    Pipe.TEMP: "25;30;20"  # 3 cases
})
```

## Case Management

### Activating Cases

Control which cases are included in the KORF report:

```python
# Activate all cases
cases.activate_cases([1, 2, 3])

# Activate only specific cases
cases.activate_cases([1, 3])  # Run only cases 1 and 3

# Activate single case
cases.activate_cases([2])  # Run only case 2
```

### Getting Case Values

```python
# Get value for specific case
value = cases.get_case_value("50;55;20", case_index=2)
print(value)  # "55"

# Single value applies to all cases
value = cases.get_case_value("100", case_index=3)
print(value)  # "100"
```

### Setting Case Values

```python
# Update value for specific case
new_string = cases.set_case_value("50;55;20", case_index=2, new_value=60)
print(new_string)  # "50;60;20"
```

## Flow Tables

### Pipe Flow Table

```python
# Get table of pipe flows
flows = cases.pipe_flows_table()

for row in flows:
    print(row)
# {
#     'pipe': 'L1',
#     'index': 1,
#     'NORMAL': '50',
#     'RATED': '55',
#     'MINIMUM': '20'
# }
```

### Custom Tables

```python
# Create custom analysis table
table = []
for idx, pipe in model.pipes.items():
    if idx == 0:
        continue
    row = {
        'name': pipe.name,
        'diameter': pipe.diameter_inch,
    }
    # Add case values
    for i, case_name in enumerate(cases.names, 1):
        flow = cases.get_case_value(pipe.flow_string, i)
        row[case_name] = flow
    table.append(row)
```

## Case Utilities

### CaseSet Methods

```python
cases = CaseSet(model)

# Validate case index
cases._validate_case(1)  # OK
cases._validate_case(5)  # Raises CaseError

# Set bulk values
cases.set_pipe_flows(1, [50, 55, 20])
cases.set_feed_pressures(1, [100, 110, 90])
cases.set_product_pressures(1, [50, 55, 45])
```

## Best Practices

### 1. Always Use Lists for Multi-Case

```python
# Good - clear intent
pipe.set_flow([50, 55, 20])

# OK but less clear
pipe.set_flow("50;55;20")
```

### 2. Match List Length to Case Count

```python
# Ensure your values match the number of cases
if len(flows) != cases.count:
    raise ValueError(f"Expected {cases.count} values, got {len(flows)}")

pipe.set_flow(flows)
```

### 3. Document Case Meanings

```python
# Add comments explaining cases
CASE_DEFINITIONS = {
    1: "NORMAL - Standard operating conditions",
    2: "RATED - Maximum design capacity",
    3: "MINIMUM - Minimum operating flow"
}
```

### 4. Use Descriptive Case Names

```python
# Set meaningful case descriptions
model.general.case_descriptions = [
    "Summer Peak",
    "Winter Normal",
    "Startup",
    "Shutdown"
]
```

### 5. Validate Before Running

```python
# Check all required parameters are set for all cases
for case_idx in range(1, cases.count + 1):
    for pipe in model.pipes.values():
        if pipe.index == 0:
            continue
        flow = cases.get_case_value(pipe.flow_string, case_idx)
        if not flow or flow == "":
            logger.warning(f"Pipe {pipe.name} has no flow for case {case_idx}")
```

## Example: Complete Case Setup

```python
from pykorf import Model, CaseSet
from pykorf.elements import Element, Pipe, Feed, Product

# Create model
model = Model()
cases = CaseSet(model)

# Define cases
case_names = ["NORMAL", "RATED", "MINIMUM"]
model.general.case_descriptions = case_names

# Add elements
model.add_element(Element.FEED, "Source", {Feed.PRES: "100;110;90"})
model.add_element(Element.PROD, "Sink", {Product.PRES: "50"})
model.connect_elements("Source", "Sink", pipe_name="MainLine")

# Set flows for all cases
model.update_element("MainLine", {Pipe.TFLOW: "100;120;80"})

# Verify
print("Case setup:")
print(f"  Names: {cases.names}")
print(f"  Count: {cases.count}")

flows = cases.pipe_flows_table()
for row in flows:
    print(f"  {row['name']}: {row['NORMAL']} / {row['RATED']} / {row['MINIMUM']}")

# Save
model.save("multi_case_model.kdf")
```

## Next Steps

- [Export & Import](export-import.md)
- [Working with Elements](working-with-elements.md)
