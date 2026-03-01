# PMS & Fluid Properties Workflow

Two enterprise workflows for updating KORF models from Excel data.

## 1. Pipe Schedule Update (PMS)

Update pipe ID/Schedule from PMS codes stored in Line Notes.

### Line Notes Format
```
PMS:PMS-A11-CS2; LINE-001;
```

### Excel: PMS_Master Sheet

| PMS_Code | Nominal_Size | OD_inch | Schedule | ID_inch | Material |
|----------|-------------|---------|----------|---------|----------|
| PMS-A11-CS2 | 2 | 2.375 | 40 | 2.067 | Carbon Steel |
| PMS-A22-CS2 | 4 | 4.500 | 40 | 4.026 | Carbon Steel |

### Code

```python
from pykorf import Model
from pykorf.definitions import Pipe
import pandas as pd

def extract_pms_code(notes):
    if "PMS:" not in notes:
        return None
    start = notes.find("PMS:") + 4
    end = notes.find(";", start)
    return notes[start:end].strip()

# Load data
model = Model("model.kdf")
pms_df = pd.read_excel("pms.xlsx", sheet_name="PMS_Master")
pms_data = {row["PMS_Code"]: row for _, row in pms_df.iterrows()}

# Update pipes
for pipe in model.pipes.values():
    if pipe.index == 0:
        continue
    
    notes = pipe.get_param(Pipe.NOTES, "")
    pms_code = extract_pms_code(notes)
    
    if pms_code and pms_code in pms_data:
        spec = pms_data[pms_code]
        pipe.set_param(Pipe.DIA, str(spec["Nominal_Size"]))
        pipe.set_param(Pipe.SCH, str(spec["Schedule"]))
        pipe.set_param(Pipe.ID, spec["ID_inch"] * 0.0254)  # inch to meter
        pipe.set_param(Pipe.ODF, spec["OD_inch"] * 0.0254)

model.save_as("model_updated.kdf")
```

## 2. Fluid Properties Import

Import fluid properties directly from Excel. No text file needed.

### Excel: Fluid_Properties Sheet

| Line_Name | Case | Temp_In | Temp_Out | Pres_In | Pres_Out | LiqDen | LiqVisc |
|-----------|------|---------|----------|---------|----------|--------|---------|
| L1 | 1 | 52.25 | 52.25 | 398.7 | 398.7 | 570.24 | 0.153 |
| L1 | 2 | 55.0 | 55.0 | 420.0 | 420.0 | 565.0 | 0.145 |

**Units:** Use metric (°C, kPag, kg/m³, cP). KORF auto-converts to your display units.

### Code

```python
from pykorf import Model, Fluid
import pandas as pd

model = Model("model.kdf")
df = pd.read_excel("fluids.xlsx", sheet_name="Fluid_Properties")

for _, row in df.iterrows():
    pipe = model.get_element(row["Line_Name"])
    
    fluid = Fluid(
        temp_inlet=row["Temp_In"],
        temp_outlet=row["Temp_Out"],
        pres_inlet=row["Pres_In"],
        pres_outlet=row["Pres_Out"],
        liquid_density=row["LiqDen"],
        liquid_viscosity=row["LiqVisc"],
    )
    
    pipe.set_fluid(fluid)

model.save_as("model_with_fluids.kdf")
```

## Combined Workflow

```python
from pykorf import Model, Fluid
import pandas as pd

model = Model("model.kdf")

# Update schedules
pms_df = pd.read_excel("data.xlsx", sheet_name="PMS_Master")
# ... PMS update code ...

# Update fluids
fluid_df = pd.read_excel("data.xlsx", sheet_name="Fluid_Properties")
for _, row in fluid_df.iterrows():
    pipe = model.get_element(row["Line_Name"])
    fluid = Fluid.from_excel_row(row.to_dict())
    pipe.set_fluid(fluid)

model.save_as("model_final.kdf")
```

## Key Points

1. **PMS codes** go in Line Notes as `PMS:CODE;`
2. **Fluid properties** use metric units - KORF converts automatically
3. **No text file imports** needed - direct KDF editing
4. **Multi-case** supported in both workflows

See `examples/enterprise_pms_and_fluid_workflow.py` for full working code.
