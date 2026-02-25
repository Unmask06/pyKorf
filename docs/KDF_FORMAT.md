# KDF File Format Reference

This document describes the KORF Data File (`.kdf`) format as understood by pyKorf.

---

## File Structure

A `.kdf` file is a plain-text CSV file with the following conventions:

1. **Version header** – first line, e.g. `"KORF_2.0"` or `"KORF_3.0"`.
2. **Record lines** – one parameter per line:
   ```
   "\ELEMENT_TYPE", element_index, "PARAMETER", value1, value2, ..., "unit"
   ```
3. **String tokens** are wrapped in double-quotes.
4. **Numeric tokens** are unquoted and may use VB6-style scientific notation (e.g. `2.22736E-02`).

---

## Record Format

```
"\PIPE", 1, "TFLOW", "50;55;20", 20, "t/h"
  │       │    │        │          │    │
  │       │    │        │          │    └── unit string
  │       │    │        │          └─────── calculated numeric (last run)
  │       │    │        └────────────────── user input (semicolon = multi-case)
  │       │    └─────────────────────────── parameter keyword
  │       └──────────────────────────────── element instance index (0=template, 1+=real)
  └──────────────────────────────────────── element type
```

### Multi-case values

Values that vary between simulation cases are packed into a single quoted string with **semicolons** as delimiters:

| String       | Case 1 | Case 2 | Case 3 |
| ------------ | ------ | ------ | ------ |
| `"50;55;20"` | 50     | 55     | 20     |
| `"100"`      | 100    | 100    | 100    |

### Calculated values

The marker `";C"` means the value was **calculated** by KORF (not user-specified).
After a run, numeric results are written to the second value position. Example:

```
"\PUMP", 1, "DP", ";C", 1526.52, "kPag"
            spec=calc  ↑ calculated result
```

---

## Index 0 – Default Template

Every element type has a **template record** at index 0. Its `NUM` parameter stores the count of real instances:

```
"\PIPE", 0, "NUM", 5
```

Real instances start at index **1**.

---

## Element Types

| Keyword   | Description                               |
| --------- | ----------------------------------------- |
| `\GEN`    | General / project settings                |
| `\PIPE`   | Pipe / process line                       |
| `\FEED`   | Feed (source boundary condition)          |
| `\PROD`   | Product (sink boundary condition)         |
| `\PUMP`   | Centrifugal or positive-displacement pump |
| `\VALVE`  | Control valve                             |
| `\CHECK`  | Check valve                               |
| `\FO`     | Flow orifice / restriction plate          |
| `\HX`     | Heat exchanger                            |
| `\COMP`   | Compressor                                |
| `\MISC`   | Miscellaneous equipment                   |
| `\EXPAND` | Expander or reducer                       |
| `\JUNC`   | Junction (multi-pipe meeting point)       |
| `\TEE`    | Tee piece                                 |
| `\VESSEL` | Pressure vessel / separator               |
| `\SYMBOL` | Drawing annotation                        |
| `\TOOLS`  | Default new-element settings              |

---

## Key Parameters by Element

### `\GEN` (General)

| Param         | Description                         |
| ------------- | ----------------------------------- |
| `COM`         | Company name                        |
| `PRJ`         | Project details                     |
| `UNITS`       | Unit system (`Metric` / `Imperial`) |
| `PATM`        | Atmospheric pressure [kPa]          |
| `CASENO`      | Active cases (semicolon list)       |
| `CASEDSC`     | Case descriptions (semicolon list)  |
| `CASERPT`     | Report flags per case (1/0)         |
| `MCOMP`       | Compressibility model               |
| `MTP`         | Two-phase flow model                |
| `PCURQ/H/EFF` | Default pump curve points           |

### `\PIPE`

| Param      | Description                                   |
| ---------- | --------------------------------------------- |
| `NAME`     | Tag name, description                         |
| `TFLOW`    | Total flow input + calculated [t/h]           |
| `DIA`      | Nominal diameter [inch string]                |
| `SCH`      | Schedule (`40`, `80`, etc.)                   |
| `ID`       | Internal diameter [m]                         |
| `LEN`      | Length [m]                                    |
| `EQLEN`    | Equivalent length with fittings [m]           |
| `MAT`      | Material (`Steel`, etc.)                      |
| `EPS`      | Roughness [m]                                 |
| `LIQDEN`   | Liquid density per case [kg/m³]               |
| `LIQVISC`  | Liquid viscosity per case [cP]                |
| `PRES`     | Pressure per case (calculated) [kPag]         |
| `VEL`      | Velocity per case (calculated) [m/s]          |
| `DPL`      | Pressure drop / 100 m (calculated) [kPa/100m] |
| `RE`       | Reynolds number (calculated)                  |
| `ELEV`     | Inlet/outlet elevation [m]                    |
| `FITA/B/O` | Fittings table                                |

### `\PUMP`

| Param             | Description                                    |
| ----------------- | ---------------------------------------------- |
| `CON`             | Connected pipe indices (inlet, outlet)         |
| `TYPE`            | `Centrifugal` / `Reciprocating`                |
| `DP`              | Differential pressure spec / calculated [kPag] |
| `EFFP`            | Hydraulic efficiency spec / calculated         |
| `POW`             | Absorbed power (calculated) [kW]               |
| `HQACT`           | Head [m] and flow [m³/h] at operating point    |
| `CURQ/H/EFF/NPSH` | Performance curve data                         |
| `NPSHA13/NPSHR13` | NPSH available / required [m]                  |

### `\FEED`

| Param   | Description                            |
| ------- | -------------------------------------- |
| `TYPE`  | `Pipe` / `Vessel`                      |
| `PRES`  | Specified pressure + calculated [kPag] |
| `POUT`  | Calculated outlet pressure [kPag]      |
| `NOZ`   | Connected pipe index                   |
| `LEVEL` | Liquid level for vessel feeds          |

### `\PROD`

| Param  | Description                        |
| ------ | ---------------------------------- |
| `TYPE` | `Pipe` / `Vessel`                  |
| `PRES` | Back-pressure specification [kPag] |
| `PIN`  | Calculated inlet pressure [kPag]   |
| `NOZ`  | Connected pipe index               |

---

## Editing Guidelines

1. **Never change element-type or index tokens** – these define the file structure.
2. **Update only the `values` list** of a record (after the 3rd token).
3. Multi-case inputs must be updated as semicolon strings.
4. Calculated result fields (position 1 in the values list) will be overwritten by KORF on the next run – you may leave them unchanged.
5. Always call `model.save()` before asking KORF to reload.
