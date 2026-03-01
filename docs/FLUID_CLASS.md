# Fluid Class

Direct fluid properties management for KORF pipes. No text file imports needed.

## Quick Start

```python
from pykorf import Model, Fluid

model = Model("model.kdf")
pipe = model.get_element("L1")

# Use metric units - KORF auto-converts to your display units
fluid = Fluid(
    temp_inlet=52.25,       # °C
    pres_inlet=398.7,       # kPag
    liquid_density=570.24,  # kg/m³
    liquid_viscosity=0.153, # cP
)

pipe.set_fluid(fluid)
model.save()
```

## Units

**Always use metric in Python.** KORF converts automatically:

| Input | KORF Display |
|-------|--------------|
| 398.7 kPag | 3.987 barg (or 57.9 psig) |
| 52.25 °C | 52.25 °C (or 126.1 °F) |
| 570.24 kg/m³ | 570.24 kg/m³ (or 35.6 lb/ft³) |

## Creating Fluids

```python
# Basic
fluid = Fluid(temp_inlet=52.25, pres_inlet=398.7, liquid_density=570.24)

# Single-phase liquid helper
fluid = Fluid.single_phase_liquid(temp=25.0, pres=100.0, density=1000.0, viscosity=1.0)

# From HYSYS (handles barg → kPag)
fluid = Fluid.from_hysys_export(temp=52.25, pres=3.987, liqden=570.24, liqvisc=0.153)

# Multi-case
fluid = Fluid(
    temp_inlet=[52.25, 55.0, 50.0],
    pres_inlet=[398.7, 420.0, 380.0],
    liquid_density=[570.24, 565.0, 575.0],
)
```

## API

### Fluid Class

```python
Fluid(
    temp_inlet=25.0,           # °C
    temp_outlet=25.0,          # °C
    temp_average=25.0,         # °C
    pres_inlet=100.0,          # kPag
    pres_outlet=100.0,         # kPag
    pres_average=100.0,        # kPag
    liquid_fraction=1.0,       # 0-1
    liquid_density=1000.0,     # kg/m³
    liquid_viscosity=1.0,      # cP
    liquid_surface_tension=62.4,  # dyne/cm
    vapor_density=0.0,         # kg/m³
    vapor_viscosity=0.0,       # cP
)
```

### Pipe Methods

```python
pipe.set_fluid(fluid)   # Apply fluid to pipe
fluid = pipe.get_fluid()  # Get fluid from pipe
```

## Excel Import

```python
import pandas as pd
from pykorf import Model, Fluid

model = Model("model.kdf")
df = pd.read_excel("fluids.xlsx")  # Columns: Line_Name, Temp, Pres, LiqDen, LiqVisc

for _, row in df.iterrows():
    pipe = model.get_element(row["Line_Name"])
    fluid = Fluid.from_excel_row(row.to_dict())
    pipe.set_fluid(fluid)

model.save()
```

That's it. No text files. No manual unit conversion. KORF handles it.
