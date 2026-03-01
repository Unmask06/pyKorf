# Excel Templates for pyKorf Workflows

This directory contains Excel templates and examples for the two main enterprise workflows:

## 1. PMS_Master Sheet

Used for: **Pipe Schedule Update Based on PMS Code**

### Required Columns:

| Column | Data Type | Description | Example |
|--------|-----------|-------------|---------|
| `PMS_Code` | String | Unique PMS identifier | PMS-A11-CS2 |
| `Nominal_Size` | Number | Nominal pipe size (inch) | 2 |
| `OD_inch` | Number | Outer diameter (inch) | 2.375 |
| `Schedule` | String | Pipe schedule | 40, 80, 160, STD, XS, XXS |
| `ID_inch` | Number | Inner diameter (inch) | 2.067 |
| `Material` | String | Pipe material | Carbon Steel, Stainless Steel |
| `Wall_Thickness_mm` | Number | Wall thickness (mm) | 3.91 |
| `Description` | String | Optional description | 2" Sch 40 CS |

### Sample Data:

```
PMS_Code        Nominal_Size  OD_inch  Schedule  ID_inch  Material         Wall_Thickness_mm
PMS-A11-CS2     2             2.375    40        2.067    Carbon Steel     3.91
PMS-A11-CS4     2             2.375    80        1.939    Carbon Steel     6.02
PMS-A22-CS2     4             4.500    40        4.026    Carbon Steel     6.02
PMS-B22-SS2     4             4.500    40S       4.026    Stainless Steel  6.02
```

## 2. Fluid_Properties Sheet

Used for: **Fluid Properties Import from Excel**

### Required Columns:

| Column | Data Type | Unit | Description |
|--------|-----------|------|-------------|
| `Line_Name` | String | - | Pipe name in KDF model |
| `Case` | Integer | - | Case number (1, 2, 3, ...) |
| `Temp_In` | Number | °C | Inlet temperature |
| `Temp_Out` | Number | °C | Outlet temperature |
| `Temp_Avg` | Number | °C | Average temperature |
| `Pres_In` | Number | kPag | Inlet pressure |
| `Pres_Out` | Number | kPag | Outlet pressure |
| `Pres_Avg` | Number | kPag | Average pressure |
| `LF_In` | Number | - | Inlet liquid fraction (0-1) |
| `LF_Out` | Number | - | Outlet liquid fraction (0-1) |
| `LF_Avg` | Number | - | Average liquid fraction (0-1) |
| `LiqDen` | Number | kg/m³ | Liquid density |
| `LiqVisc` | Number | cP | Liquid viscosity |
| `LiqSur` | Number | dyne/cm | Liquid surface tension |
| `LiqCon` | Number | W/m/K | Liquid thermal conductivity |
| `LiqCp` | Number | kJ/kg/K | Liquid specific heat |
| `LiqMW` | Number | - | Liquid molecular weight |

### Optional Columns (for two-phase flow):

| Column | Data Type | Unit | Description |
|--------|-----------|------|-------------|
| `VapDen` | Number | kg/m³ | Vapor density |
| `VapVisc` | Number | cP | Vapor viscosity |
| `VapCon` | Number | W/m/K | Vapor thermal conductivity |
| `VapCp` | Number | kJ/kg/K | Vapor specific heat |
| `VapMW` | Number | - | Vapor molecular weight |
| `VapZ` | Number | - | Vapor compressibility factor |
| `VapK` | Number | - | Vapor K-value |

### Sample Data:

```
Line_Name  Case  Temp_In  Temp_Out  Temp_Avg  Pres_In  Pres_Out  Pres_Avg  LiqDen  LiqVisc  ...
L1         1     52.25    52.25     52.25     398.7    398.7     398.7     570.24  0.153    ...
L1         2     55.0     55.0      55.0      420.0    420.0     420.0     565.0   0.145    ...
L2         1     50.0     48.0      49.0      350.0    340.0     345.0     600.0   0.2      ...
```

## How to Create the Excel File

### Option 1: Using Excel

1. Open Microsoft Excel
2. Create Sheet1 and rename to `PMS_Master`
3. Add the column headers from above
4. Fill in your PMS data
5. Create Sheet2 and rename to `Fluid_Properties`
6. Add the column headers and fluid property data
7. Save as `your_data.xlsx`

### Option 2: Using Python (pandas)

```python
import pandas as pd

# Create PMS Master data
pms_data = {
    "PMS_Code": ["PMS-A11-CS2", "PMS-A11-CS4", "PMS-A22-CS2"],
    "Nominal_Size": [2, 2, 4],
    "OD_inch": [2.375, 2.375, 4.500],
    "Schedule": ["40", "80", "40"],
    "ID_inch": [2.067, 1.939, 4.026],
    "Material": ["Carbon Steel", "Carbon Steel", "Carbon Steel"],
    "Wall_Thickness_mm": [3.91, 6.02, 6.02],
}

# Create Fluid Properties data
fluid_data = {
    "Line_Name": ["L1", "L1", "L2"],
    "Case": [1, 2, 1],
    "Temp_In": [52.25, 55.0, 50.0],
    "Temp_Out": [52.25, 55.0, 48.0],
    "Temp_Avg": [52.25, 55.0, 49.0],
    "Pres_In": [398.7, 420.0, 350.0],
    "Pres_Out": [398.7, 420.0, 340.0],
    "Pres_Avg": [398.7, 420.0, 345.0],
    "LF_In": [1.0, 1.0, 1.0],
    "LF_Out": [1.0, 1.0, 1.0],
    "LF_Avg": [1.0, 1.0, 1.0],
    "LiqDen": [570.24, 565.0, 600.0],
    "LiqVisc": [0.153, 0.145, 0.2],
    "LiqSur": [20.0, 19.5, 25.0],
}

# Write to Excel with multiple sheets
with pd.ExcelWriter("pms_and_fluid_data.xlsx") as writer:
    pd.DataFrame(pms_data).to_excel(writer, sheet_name="PMS_Master", index=False)
    pd.DataFrame(fluid_data).to_excel(writer, sheet_name="Fluid_Properties", index=False)

print("Excel file created: pms_and_fluid_data.xlsx")
```

## Line Notes Format

When using the PMS feature, add PMS codes to pipe Line Notes in this format:

```
PMS:PMS-A11-CS2; LINE-001; INSTALLED:2024-01;
```

The parser looks for `PMS:` followed by the code and terminated by `;`.

### Examples:

| Line Notes Content | Extracted PMS Code |
|-------------------|-------------------|
| `PMS:PMS-A11-CS2;` | PMS-A11-CS2 |
| `PMS:PMS-B22-SS4; LINE-014;` | PMS-B22-SS4 |
| `PMS:PMS-C10-CS2; SERVICE:COOLING;` | PMS-C10-CS2 |
| `LINE-001;` | (none - no PMS tag) |

## Common Pipe Dimensions Reference

### Carbon Steel (ASME B36.10M)

| NPS | OD (in) | Sch 40 ID (in) | Sch 80 ID (in) | Sch 160 ID (in) |
|-----|---------|----------------|----------------|-----------------|
| 2" | 2.375 | 2.067 | 1.939 | 1.689 |
| 3" | 3.500 | 3.068 | 2.900 | 2.624 |
| 4" | 4.500 | 4.026 | 3.826 | 3.438 |
| 6" | 6.625 | 6.065 | 5.761 | 5.189 |
| 8" | 8.625 | 7.981 | 7.625 | 6.813 |

### Stainless Steel (ASME B36.19M)

| NPS | OD (in) | Sch 40S ID (in) | Sch 80S ID (in) |
|-----|---------|-----------------|-----------------|
| 2" | 2.375 | 2.157 | 1.771 |
| 4" | 4.500 | 4.026 | 3.826 |
| 6" | 6.625 | 6.065 | 5.761 |

---

*Template Version: 1.0*
*Compatible with pyKorf Enterprise Workflows*
