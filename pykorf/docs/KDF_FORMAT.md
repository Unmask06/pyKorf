# KDF File Format Reference

This document describes the KORF Data File (`.kdf`) format as understood by pyKorf.
It is derived from analysis of real KDF files across KORF versions 2.0, 3.0 and 3.6.
The focus is on **input parameters** (user-editable); calculated outputs are noted but
not exhaustively documented.

---

## 1. File Structure

A `.kdf` file is a plain-text CSV file encoded in **latin-1** with `\r\n` line endings.

1. **Version header** – first line: `"KORF_2.0"`, `"KORF_3.0"`, or `"KORF_3.6"`.
2. In v3.6 the second line is `"\GEN",0,"VERNO",3.66` (version number).
3. **Record lines** – one parameter per line:
   ```
   "\ELEMENT_TYPE", element_index, "PARAMETER", value1, value2, ..., "unit"
   ```
4. **String tokens** are wrapped in double-quotes.
5. **Numeric tokens** are unquoted and may use VB6-style scientific notation
   (e.g. `2.22736E-02`).
6. Element types always appear in a fixed order (see §3).

---

## 2. Record Format

```
"\PIPE", 1, "TFLOW", "50;55;20", 20, "t/h"
  │       │    │        │          │    │
  │       │    │        │          │    └── unit string
  │       │    │        │          └─────── calculated numeric (last run)
  │       │    │        └────────────────── user input (semicolon = multi-case)
  │       │    └─────────────────────────── parameter keyword
  │       └──────────────────────────────── element instance index (0=template)
  └──────────────────────────────────────── element type
```

### Multi-case values

Values that vary between simulation cases are packed into a single quoted string
with **semicolons** as delimiters:

| String       | Case 1 | Case 2 | Case 3 |
| ------------ | ------ | ------ | ------ |
| `"50;55;20"` | 50     | 55     | 20     |
| `"100"`      | 100    | 100    | 100    |

A single value without semicolons applies to **all** cases.

### Calculated values & input markers

| Pattern | Meaning |
| ------- | ------- |
| `""` (empty string) | No user input — KORF will calculate |
| `";C"` | Value was calculated by KORF |
| `"50"` followed by `50` | User input = 50, calculated = 50 (confirmed) |
| `"50;55;20"` followed by `20` | Multi-case input; `20` is the calc for active case |

After a run, KORF writes numeric results into the token(s) following the input string.
These calculated tokens are **overwritten** on each solve and can be left unchanged
when editing.

---

## 3. Element Order in File

Elements always appear in this fixed order. Each type starts with its
index-0 template, then instances 1 … N.

```
GEN → PIPE → FEED → PROD → VALVE → CHECK → FO → HX → PUMP → COMP →
MISC → EXPAND → JUNC → TEE → VESSEL → SYMBOL → TOOLS → PSEUDO → PIPEDATA
```

`PSEUDO` and `PIPEDATA` are present only in **v3.6+** files.

---

## 4. Index 0 – Default Template

Every element type has a **template record** at index 0. Its `NUM` parameter
stores the count of real instances:

```
"\PIPE", 0, "NUM", 9
```

Real instances start at index **1**. The template defines default values that new
instances inherit.

---

## 5. Version Differences

| Feature | v2.0 | v3.0 | v3.6 |
| ------- | ---- | ---- | ---- |
| Header | `"KORF_2.0"` | `"KORF_3.0"` | `"KORF_3.6"` + `VERNO` |
| Unit strings | `UNITS` only | `UNITS1-3` added | `UNITS4`, `UNITS6` added |
| Drawing params | `DWGSTD/SIZ` | + `DWGMAR/GRD/BOR` | + `DWGCON`, `PRTWID` |
| Solver settings | — | — | `MITER`, `MSOS`, `MXYDAMP` added |
| Model choices | `MFLASH`, `MCOMP`, `MTP` | + `MSONIC`, `MDUKF` | + `MFIT/MFT`, `MVAPK`, `MQLOSS`, `MCVFL`, `MKE`, `M3PHASE`, `MHVYCOMP` |
| Pipe fittings | `FITA/FITB/FITO` (packed) | same | `FIT1-FIT11` (individual records) |
| Pipe heat transfer | `U`, `TAMB`, `Q` | same | `UI`, `QFAC/QNTU/QAIR/QPIP/QINS`, `DAMB`, `TSUR` |
| Pipe thermal props | — | `LIQSUR` added | `LIQCON/LIQCP/LIQMW`, `VAPCON/VAPCP`, `TOTCON/TOTCP/TOTMW`, `PSAT`, `OMEGA` |
| Feed/Prod level | `LEVEL`, `NOZ` | same | `LEVELH`, `NOZL` (renamed + extra tokens) |
| Feed/Prod equation | — | — | `EQN` added |
| Element display | — | `FLIP`, `LBL` added | same |
| Valve params | basic | same | `TYPE2`, `FL`, `PCRIT`, `OPENCV`, `OMEGA`, `RS`, `XC`, `NDS`, `MDEN`, `DPP`, `PSAT` |
| Pump sizing | — | — | `PZPRES`, `PZRAT`, `PZVES`, `NPSHAF`, `NPSHVV`, `NPSHVT` |
| `\PSEUDO` | — | — | New element type |
| `\PIPEDATA` | — | — | New element type |

---

## 6. Element Types

| Keyword     | Description                               |
| ----------- | ----------------------------------------- |
| `\GEN`      | General / project settings                |
| `\PIPE`     | Pipe / process line                       |
| `\FEED`     | Feed (source boundary condition)          |
| `\PROD`     | Product (sink boundary condition)         |
| `\VALVE`    | Control valve                             |
| `\CHECK`    | Check valve                               |
| `\FO`       | Flow orifice / restriction plate          |
| `\HX`       | Heat exchanger                            |
| `\PUMP`     | Centrifugal or positive-displacement pump |
| `\COMP`     | Compressor                                |
| `\MISC`     | Miscellaneous equipment                   |
| `\EXPAND`   | Expander or reducer                       |
| `\JUNC`     | Junction (multi-pipe meeting point)       |
| `\TEE`      | Tee piece                                 |
| `\VESSEL`   | Pressure vessel / separator               |
| `\SYMBOL`   | Drawing annotation (v3.0+)                |
| `\TOOLS`    | Default new-element settings              |
| `\PSEUDO`   | Pseudo-component definition (v3.6+)       |
| `\PIPEDATA` | Pipe material / dimension database (v3.6+)|

---

## 7. Parameters by Element

In the tables below:

- **mc** = multi-case (semicolon-delimited string).
- **calc** = calculated by KORF (follows the input token).
- **v3.0+** / **v3.6+** = first version where the parameter appears.
- Tokens after the input that hold calculated results are not listed.

### 7.1 `\GEN` (General Settings)

`\GEN` always has index 0 (singleton). There is no `NUM` record.

#### Project / Company

| Param | Tokens | Description |
| ----- | ------ | ----------- |
| `VERNO` | `version_float` | KORF version number, e.g. `3.66` (v3.6+) |
| `COM` | `"company","location"` | Company name and location |
| `PRJ` | `"client","client_loc","project","project_no"` | Project details |
| `ENG` | `"name","title","date","chk","app","rev"` | Engineer details |

#### Units

| Param | Tokens | Description |
| ----- | ------ | ----------- |
| `UNITS` | `"system"` | `Metric`, `Imperial`, or `Custom` |
| `UNITS1` | 6 strings | Length, elev, mass-flow, liq-vol-flow, gas-vol-flow, molar-flow |
| `UNITS2` | 6 strings | Density, temp, pressure, head, DP/100, velocity |
| `UNITS3` | 5 strings | Power, enthalpy, heat-cap, heat-flow, UA |
| `UNITS4` | 2 strings | Heat-transfer-coeff (W/m²/K), thermal-conductivity (W/m/K) (v3.6+) |
| `UNITS6` | 5 strings | Normal-vol-flow (Nm³/h), spare slots (v3.6+) |
| `PATM` | `value,"unit"` | Atmospheric pressure (default 101 kPag) |

#### Drawing / Display

| Param | Tokens | Description |
| ----- | ------ | ----------- |
| `DWGSTD` | `"paper_size"` | Drawing standard, e.g. `"A4 Landscape"` |
| `DWGSIZ` | `width,height,"twip"` | Drawing size in twips |
| `DWGMAR` | `margin,"twip"` | Drawing margin (v3.0+) |
| `DWGGRD` | `visible,spacing` | Grid visibility (-1=on) and spacing (v3.0+) |
| `DWGCON` | `snap_dist` | Connection snap distance in drawing units (v3.6+) |
| `DWGBOR` | `visible` | Border visibility (-1=on) (v3.0+) |
| `RPTSIZ` | `"paper",margin,"twip",fontsize,"pt"` | Report page layout |
| `PRTWID` | `width,"pixel"` | Print line width (v3.6+) |
| `MCOL` | `bg,grid,element,text` | Color scheme (v3.6+) |

#### Solver

| Param | Tokens | Description |
| ----- | ------ | ----------- |
| `MITER` | `max_iterations` | Maximum solver iterations, e.g. 20 (v3.6+) |
| `MSOS` | `tolerance` | Convergence tolerance, e.g. 0.001 (v3.6+) |
| `MXYDAMP` | `factor` | XY damping factor, e.g. 0.9 (v3.6+) |
| `MHDAMP` | `factor` | Head damping factor (v3.6+) |

#### Fluid & Flow Models

| Param | Tokens | Description |
| ----- | ------ | ----------- |
| `MFLASH` | `"model"` | Flash calculation model: `Korf`, `Hysys` |
| `MFLASHK` | `"method"` | K-value method for flash: `Antoine` |
| `MFLASHH` | `"method"` | Enthalpy method for flash: `SRK` |
| `MFLASHR` | `flag` | Flash refinement: -1 = on |
| `MCOMP` | `"model"` | Compressibility: `Incompressible`, `Ideal`, `SRK`, etc. |
| `MTP` | `"model"` | Two-phase flow model: `Homogeneous`, `Lockhart-Martinelli`, etc. |
| `MDELEV` | `"model"` | Two-phase elevation model: `Homogeneous`, etc. |
| `MDUKHP` | `"model"` | Dukler holdup model: `Hughmark`, etc. |
| `MDUKF` | `flag` | Dukler–Flanigan friction flag: 0 = off |
| `MACCEL` | `"model"` | Acceleration model: `Log` |
| `MSONIC` | `"model"` | Sonic velocity model: `HEMOmega` (v3.6), blank (v2.0/3.0) |
| `MFIT` | `"method"` | Fitting K-value method: `Crane` (v3.6+) |
| `MFT` | `flag` | Fitting method flag (v3.6+) |
| `MVAPK` | `"method"` | Vapor K method: `SemiIdeal` (v3.6+) |
| `MQLOSS` | `"method"` | Heat loss method: `NTU` (v3.6+) |
| `MKE` | `flag` | Include kinetic energy: 0 = off (v3.6+) |
| `M3PHASE` | `flag` | Three-phase mode: 0 = off (v3.6+) |
| `MHVYCOMP` | `"component"` | Heavy component name: `WATER` (v3.6+) |
| `MHYSYS` | `"eos"` | Hysys equation of state: `SRK` |
| `MHVIEW` | `flag` | Hysys view flag: -1 = on (v3.6+) |
| `MPPP` | `flag` | Physical property package selector (v3.6+) |
| `MFODEN` | `"method"` | Flow orifice density method: `SumOfArea` (v3.6+) |
| `MCVDEN` | `"method"` | CV density method: `SumOfCv` (v3.6+) |
| `MCVFL` | `"method"` | CV flow model: `2Phase` (v3.6+) |
| `MPCURV` | `flag1,flag2` | Pump curve extrapolation flags (v3.6+) |
| `MSIM` | `"",""`  | Simulation link strings |

#### Pump / Compressor Curves (Defaults)

| Param | Tokens | Description |
| ----- | ------ | ----------- |
| `PCURQ` | 10 values, `"%"` | Default pump curve flow % points |
| `PCURH` | 10 values, `"%"` | Default pump curve head % points |
| `PCUREFF` | 10 values, `"%"` | Default pump curve efficiency % points |
| `PCURNPSH` | 10 values, `"%"` | Default pump NPSH curve % points |
| `CCURQ` | 10 values, `"%"` | Default compressor curve flow % points |
| `CCURH` | 10 values, `"%"` | Default compressor curve head % points |
| `CCUREFF` | 10 values, `"%"` | Default compressor curve efficiency % points |

#### Cases

| Param | Tokens | Description |
| ----- | ------ | ----------- |
| `CASENO` | `"1;2;3"` (mc) | Active case numbers |
| `CASEDSC` | `"NORMAL;RATED;MINIMUM"` (mc) | Case descriptions |
| `CASERPT` | `"1;1;1"` (mc) | Include case in report: 1 = yes |
| `CASEDLG` | `flag` | Show case dialog on open: 0 = no (v3.0+) |

#### Directories

| Param | Tokens | Description |
| ----- | ------ | ----------- |
| `DIRLIC` | `"path"` | License file directory (v3.6+) |
| `DIRLIB` | `"path"` | Library directory (v3.0+) |
| `DIRINI` | `"path"` | INI / settings directory (v3.0+) |
| `DIRDAT` | `"path"` | Data directory (v3.0+) |

---

### 7.2 `\PIPE`

#### Common properties (all elements share these)

| Param | Tokens | Description |
| ----- | ------ | ----------- |
| `NUM` | `count` | Instance count (template only) |
| `NAME` | `"tag","description"` | Element name and description |
| `XY` | 26 integers | Graphic segment coordinates (13 x,y pairs) |
| `ROT` | `angle` | Rotation angle (0, 90, 180, 270) |
| `FLIP` | `h,v` | Horizontal, vertical flip (1=normal) (v3.0+) |
| `LBL` | `pos,x_offset,y_offset` | Label position & offset (v3.0+) |
| `COLOR` | `rgb_int` | Display colour (0=default, 16711680=red, 255=blue) |
| `BEND` | `flag` | Bend mode (v3.0+) |

#### Flow & Fluid Input

| Param | Tokens | Description |
| ----- | ------ | ----------- |
| `STRM` | `"stream_id"` | Stream identifier |
| `LOCK` | `flag` | Lock flag: 0 = unlocked |
| `TFLOW` | `"input"`,calc,`"unit"` | Total mass flow (mc) |
| `TEMP` | val,val,val,`"unit"` | Temperature per case (3 values for 3 cases) |
| `PRES` | val,val,val,`"unit"` | Pressure per case |
| `LF` | val,val,val | Liquid fraction per case |
| `H` | calc,calc,`"unit"` | Enthalpy (calculated) |
| `HAMB` | val,`"unit"` | Ambient enthalpy (v3.6+) |
| `S` | calc,calc,`"unit"` | Entropy (calculated) |
| `FT` | val,val | Flow type flags |

#### Liquid Properties (per case – typically 3 values)

| Param | Tokens | Description |
| ----- | ------ | ----------- |
| `LIQDEN` | val,val,val,`"unit"` | Liquid density [kg/m³] |
| `LIQVISC` | val,val,val,`"unit"` | Liquid viscosity [cP] |
| `LIQSUR` | val,val,val,`"unit"` | Liquid surface tension [dyne/cm] (v3.0+) |
| `LIQCON` | val,val,val,`"unit"` | Liquid thermal conductivity [W/m/K] (v3.6+) |
| `LIQCP` | val,val,val,`"unit"` | Liquid heat capacity [kJ/kg/K] (v3.6+) |
| `LIQMW` | val,val,val | Liquid molecular weight (v3.6+) |

#### Vapor Properties (per case – typically 3 values)

| Param | Tokens | Description |
| ----- | ------ | ----------- |
| `VAPDEN` | val,val,val,`"unit"` | Vapor density [kg/m³] |
| `VAPVISC` | val,val,val,`"unit"` | Vapor viscosity [cP] |
| `VAPMW` | val,val,val | Vapor molecular weight (v3.0+) |
| `VAPZ` | val,val,val | Vapor compressibility factor (v3.0+) |
| `VAPK` | val,val,val | Vapor Cp/Cv ratio (v3.0+) |
| `VAPCON` | val,val,val,`"unit"` | Vapor thermal conductivity [W/m/K] (v3.6+) |
| `VAPCP` | val,val,val,`"unit"` | Vapor heat capacity [kJ/kg/K] (v3.6+) |

#### Total (Mixture) Properties

| Param | Tokens | Description |
| ----- | ------ | ----------- |
| `TPROP` | calc,calc,calc,calc,`"unit"`,calc,`"unit"` | Total mixture properties (calculated) |
| `TOTCON` | `"in1"`,`"in2"`,calc,`"unit"` | Total thermal conductivity (v3.6+) |
| `TOTCP` | `"in1"`,`"in2"`,calc,`"unit"` | Total heat capacity (v3.6+) |
| `TOTMW` | val | Total molecular weight (v3.6+) |
| `PSAT` | `"input"`,calc,`"unit"` | Saturation pressure (v3.6+) |
| `OMEGA` | `"input"`,calc | Acentric factor (v3.6+) |
| `RS` | flag | Sonic flag: 0 = off (v3.6+) |
| `YW` | val | Y-factor for water: default 1 (v3.6+) |

#### Geometry & Material

| Param | Tokens | Description |
| ----- | ------ | ----------- |
| `MAT` | `"material"` | Pipe material: `Steel`, `Ductile Iron`, `PVC`, etc. |
| `DIA` | `"nominal"`,`"actual"`,`"unit"` | Nominal pipe diameter, e.g. `"4","","inch"` |
| `SCH` | `"schedule"` | Schedule: `40`, `80`, `STD`, `XS`, `XXS`, `ID` |
| `ID` | `"input"`,calc,`"unit"` | Internal diameter [m] (used when SCH = `ID`) |
| `IDH` | `"input"`,calc,`"unit"` | Hydraulic internal diameter [m] |
| `ODF` | `"input"`,calc,`"unit"` | Outer diameter [m] (v3.6+) |
| `LEN` | val,`"unit"` | Physical length [m] |
| `EQLEN` | val,`"unit"` | Equivalent length [m] (for fittings) |
| `EPS` | `"input"`,calc,`"unit"` | Roughness [m] |
| `SELEV` | val,`"unit"` | Start elevation [m] |
| `ELEV` | val,val,`"unit"` | Start, end elevation [m] |
| `FAC` | val | Length correction factor (default 1) |

#### Heat Transfer (v3.6+)

| Param | Tokens | Description |
| ----- | ------ | ----------- |
| `Q` | `"input"`,calc,`"unit"` | Heat duty [kJ/h] |
| `UI` | `"input"`,calc,`"unit"` | Overall heat transfer coefficient [W/m²/K] (replaces `U` in v2.0) |
| `TAMB` | val,`"unit"` | Ambient temperature [C] |
| `DAMB` | val,`"unit"` | Ambient density [kg/m³] (v3.6+) |
| `TSUR` | val,`"unit"` | Surface temperature [C] (v3.6+) |
| `QFAC` | val | Heat loss factor (default 1) (v3.6+) |
| `QNTU` | val | NTU factor (default 1) (v3.6+) |
| `QAIR` | `"type"`,val,`"unit"` | Air type and velocity, e.g. `"AirL",0,"m/s"` (v3.6+) |
| `QPIP` | emissivity,conductivity,`"unit"` | Pipe emissivity & conductivity, e.g. `.8,43,"W/m/K"` (v3.6+) |
| `QINS` | thickness,`"unit"`,conductivity,`"unit"` | Insulation, e.g. `.05,"m",.06,"W/m/K"` (v3.6+) |
| `REFLINE` | flag | Reference line flag: 0 = off (v3.6+) |

#### Fittings – v3.6 format (FIT1–FIT11)

In **v3.6**, each fitting slot is a separate record with 7 tokens:

```
"\PIPE",0,"FIT1", "Entrance",  0,  0,  .5,  160,  .5,  0
                    │          │   │    │     │     │    │
                    Name     Count L/D   K    Cv    Kv  flag
```

| Param | Tokens | Description |
| ----- | ------ | ----------- |
| `FITK` | val | Total K from fittings (calculated sum) |
| `FITLD` | val | Total L/D from fittings (calculated sum) |
| `FITLR` | flag | Fitting L/R method flag: 1 = on (v3.6+) |
| `FIT1` – `FIT11` | `"name"`,count,L_D,K,Cv,Kv,flag | Individual fitting slots (v3.6+) |

Default fitting names: `Entrance`, `Exit`, `Gate valve`, `Globe valve`, `Check`,
`Stop-check`, `Elbow`, `180 Bend`, `T-Straight`, `T-Branch`, `Other`.

#### Fittings – v2.0 / v3.0 format (FITA/FITB/FITO)

In **v2.0** and **v3.0**, fittings are packed into three records:

```
"\PIPE",0,"FITA", "Entrance",0,0,.5,  "Exit",0,0,1,  "Gate",0,8,.15,  "Globe",0,340,6,  "Check",0,50,2
                   ─────── fitting 1 ──  ─── fitting 2 ── ── fitting 3 ──  ── fitting 4 ──  ── fitting 5 ──
"\PIPE",0,"FITB", "Stop-check",0,400,5, "Elbow",0,20,.45, "180 Bend",0,50,.7, "T-Str",0,20,0, "T-Brn",0,60,1
                   ─────── fitting 6 ──  ─── fitting 7 ──  ── fitting 8 ──── ── fitting 9 ──  ── fitting 10 ─
"\PIPE",0,"FITO", "Other",1,0
                   ── fitting 11 ──
```

Each fitting in FITA/FITB has 4 tokens: `"Name", count, L/D, K`.
FITO has 3 tokens: `"Name", count, K`.

#### Sizing & Calculated

| Param | Tokens | Description |
| ----- | ------ | ----------- |
| `SIZ` | `"input"`,DPmax,`"unit"`,len,velmin,velmax,fitLD,`"unit"` | Pipe sizing criteria |
| `OUTIN` | flag | Output-to-input direction flag |
| `LVFLOW` | val,calc,`"unit"` | Liquid volume flow |
| `MTP` | `"override"` | Two-phase model override (blank = use GEN default) |

#### Equation (v3.6+)

| Param | Tokens | Description |
| ----- | ------ | ----------- |
| `EQN` | type,`"expr"`,val,`"expr"`,val,val,val,val | User-defined equation constraints |

#### Other

| Param | Tokens | Description |
| ----- | ------ | ----------- |
| `NOTES` | `"text"` | User notes |
| `FILES` | 10 strings | Attached file references |

---

### 7.3 `\FEED` (Feed / Source Boundary)

| Param | Tokens | Description |
| ----- | ------ | ----------- |
| `NUM` | count | Instance count |
| `NAME` | `"tag","description"` | Element name |
| `XY` | x,y | Graphic position (2 values) |
| `ROT` | angle | Rotation |
| `FLIP` | h,v | Flip flags (v3.0+) |
| `LBL` | pos,x,y | Label position (v3.0+) |
| `COLOR` | rgb_int | Colour |
| `TYPE` | `"Pipe"` or `"Vessel"` | Feed type |
| `ELEV` | val,`"unit"` | Elevation [m] |
| `PRES` | `"input"`,calc,`"unit"` | Specified pressure (mc) |
| `POUT` | `"input"`,calc,`"unit"` | Outlet pressure (calculated) |
| `DP` | `"input"`,calc,`"unit"` | Pressure drop specification (mc) |
| `EQN` | type,`"expr"`,val,`"expr"`,val,val,val,val | Equation constraint (v3.6+) |
| `CHOKE` | flag | Choked-flow flag (v3.0+) |
| `NOTES` | `"text"` | Notes |

**Vessel-type feeds** have additional parameters:

| Param | Tokens | Description |
| ----- | ------ | ----------- |
| `LEVELH` | `"input"`,calc,`"unit"`,calc,`"unit"`,`"type"` | Liquid level + density (v3.6) |
| `NOZL` | pipe_idx,noz_elev,`"unit"`,calc,calc,calc,calc,`"unit"` | Nozzle connection (v3.6) |
| `LEVEL` | `"input"`,calc,`"unit"`,calc,`"unit"` | Liquid level (v2.0/v3.0 name) |
| `NOZ` | pipe_idx,noz_elev,`"unit"`,calc,calc,calc,`"unit"` | Nozzle connection (v2.0/v3.0 name) |

> **Version note:** `LEVEL` → `LEVELH` and `NOZ` → `NOZL` were renamed in v3.6
> with extra tokens added. The v3.6 `LEVELH` adds a 6th token (`"type"`: `"Line"`)
> and `NOZL` adds an extra calculated token.

---

### 7.4 `\PROD` (Product / Sink Boundary)

Identical structure to `\FEED` except:

| Param | Tokens | Description |
| ----- | ------ | ----------- |
| `PRES` | `"input"`,calc,`"unit"` | Specified back-pressure (mc) |
| `PIN` | `"input"`,calc,`"unit"` | Inlet pressure (calculated) |
| `DP` | `"input"`,calc,`"unit"` | Pressure drop (mc) |

All other parameters (`TYPE`, `LEVELH`/`NOZL`, `EQN`, `CHOKE`, etc.) are the same
as `\FEED`.

---

### 7.5 `\VALVE` (Control Valve)

| Param | Tokens | Description |
| ----- | ------ | ----------- |
| `NUM` | count | Instance count |
| `NAME` | `"tag","description"` | Element name |
| `XY` | x1,y1,x2,y2 | Graphic position (4 values) |
| `ROT` | angle | Rotation |
| `FLIP` | h,v | Flip flags (v3.0+) |
| `LBL` | pos,x,y | Label position (v3.0+) |
| `COLOR` | rgb_int | Colour |
| `CON` | in_pipe,out_pipe | Connectivity |
| `ELEV` | val,`"unit"` | Elevation [m] |
| `DP` | `"input"`,calc,`"unit"` | Pressure drop (mc) |
| `DPP` | val,calc,`"unit"` | Differential pressure profile (v3.6+) |
| `PSAT` | `"input"`,calc,`"unit"` | Saturation pressure (v3.6+) |
| `PCRIT` | val,`"unit"` | Critical pressure, default 5000 kPag (v3.6+) |
| `THICK` | val,`"unit"` | Wall thickness, default 0.1 m (v3.6+) |
| `K` | `"input"` | K-factor (alternative to CV) |
| `CV` | `"input"`,calc | Valve CV (mc) |
| `DIA` | `"sizing"` | Valve diameter: `"Inlet line"` or specific size |
| `TYPE2` | `"subtype"` | Valve subtype: `"Control"`, `"Safety"` (v3.6+) |
| `TYPE` | `"characteristic"` | Valve type: `"Linear"`, `"Equal%"`, `"Quick"` |
| `OPEN` | `"input"`,calc | % open (mc) |
| `OPENCV` | val | Open CV value (v3.6+) |
| `XT` | val | Pressure recovery factor xT, default 0.72 |
| `FL` | val | Liquid pressure recovery factor FL, default 0.9 (v3.6+) |
| `YIN` | flag | Inlet expansion factor flag |
| `FP2` | flag | Pipe geometry factor flag |
| `CHOKE` | flag | Choked-flow flag (v3.6+) |
| `OMEGA` | `"input"`,calc | Acentric factor (v3.6+) |
| `RS` | flag | Sonic flag (v3.6+) |
| `XC` | val | Critical pressure ratio (v3.6+) |
| `NDS` | flag | Noise standard flag (v3.6+) |
| `MDEN` | `"method"` | Density method override (v3.6+) |
| `NOTES` | `"text"` | Notes |

---

### 7.6 `\CHECK` (Check Valve)

| Param | Tokens | Description |
| ----- | ------ | ----------- |
| `NUM` | count | Instance count |
| `NAME` | `"tag","description"` | Element name |
| `XY` | x1,y1,x2,y2 | Graphic position |
| `ROT` | angle | Rotation |
| `FLIP` | h,v | Flip flags (v3.0+) |
| `LBL` | pos,x,y | Label position (v3.0+) |
| `COLOR` | rgb_int | Colour |
| `CON` | in_pipe,out_pipe | Connectivity |
| `ELEV` | val,`"unit"` | Elevation [m] |
| `DP` | `"input"`,calc,`"unit"` | Pressure drop (mc) |
| `LD` | val | Equivalent L/D ratio, e.g. 100 or 600 |

---

### 7.7 `\FO` (Flow Orifice)

| Param | Tokens | Description |
| ----- | ------ | ----------- |
| `NUM` | count | Instance count |
| `NAME` | `"tag","description"` | Element name |
| `XY` | x1,y1,x2,y2 | Graphic position |
| `COLOR` | rgb_int | Colour |
| `TYPE` | `"type"` | Orifice type: `"Orifice"`, `"Venturi"`, `"Nozzle"` |
| `ROT` | angle | Rotation |
| `FLIP` | h,v | Flip flags (v3.0+) |
| `LBL` | pos,x,y | Label position (v3.0+) |
| `CON` | in_pipe,out_pipe | Connectivity |
| `ELEV` | val,`"unit"` | Elevation [m] |
| `DP` | `"input"`,calc,`"unit"` | Specified pressure drop (mc) |
| `DPF` | `"input"`,calc,`"unit"` | Friction pressure drop (calculated) |
| `PSAT` | `"input"`,calc,`"unit"` | Saturation pressure (v3.6+) |
| `HOLES` | count | Number of orifice holes, default 1 |
| `THICK` | val,`"unit"` | Plate thickness [m] |
| `BORE` | `"input"`,calc | Orifice bore [m] (mc) |
| `BETA` | `"input"`,calc | Beta ratio (mc) |
| `BETAO` | val | Original beta (v3.6+) |
| `CD` | `"input"`,calc | Discharge coefficient (v3.6+, replaces `C` in v2.0) |
| `C` | val | Discharge coefficient (v2.0/v3.0) |
| `YIN` | flag | Inlet Y-factor flag |
| `CHOKE` | flag | Choked-flow flag |
| `OMEGA` | `"input"`,calc | Acentric factor (v3.6+) |
| `RS` | flag | Sonic flag (v3.6+) |
| `RC` | val | Critical pressure ratio (v3.6+) |
| `NDS` | flag | Noise standard flag (v3.6+) |
| `MDEN` | `"method"` | Density method override (v3.6+) |
| `NOTES` | `"text"` | Notes |

---

### 7.8 `\HX` (Heat Exchanger)

| Param | Tokens | Description |
| ----- | ------ | ----------- |
| `NUM` | count | Instance count |
| `NAME` | `"tag","description"` | Element name |
| `XY` | x1,y1,x2,y2 | Graphic position |
| `ROT` | angle | Rotation |
| `FLIP` | h,v | Flip flags (v3.0+) |
| `LBL` | pos,x,y | Label position (v3.0+) |
| `COLOR` | rgb_int | Colour |
| `TYPE` | `"type"` | HX type: `"S-T"` (shell-tube), `"Plate"`, etc. |
| `SIDE` | `"side"` | Process side: `"Tube"`, `"Shell"` |
| `NOZI` | pipe_idx,noz_elev,`"unit"` | Inlet nozzle: pipe index & elevation |
| `NOZO` | pipe_idx,noz_elev,`"unit"` | Outlet nozzle: pipe index & elevation |
| `DP` | `"input"`,calc,`"unit"` | Pressure drop (mc) |
| `PRAT` | `"input"`,`"unit"`,flow,`"unit"`,density,`"unit"`,viscosity,`"unit"` | Rating data |
| `K` | `"input"` | K-factor |
| `DPELEV` | val,`"unit"` | Elevation pressure drop |
| `Q` | `"input"`,calc,`"unit"` | Heat duty [kJ/h] |
| `NOTES` | `"text"` | Notes |

---

### 7.9 `\PUMP`

| Param | Tokens | Description |
| ----- | ------ | ----------- |
| `NUM` | count | Instance count |
| `NAME` | `"tag","description"` | Element name |
| `XY` | x1,y1,x2,y2 | Graphic position |
| `ROT` | angle | Rotation |
| `FLIP` | h,v | Flip flags (v3.0+) |
| `LBL` | pos,x,y | Label position (v3.0+) |
| `COLOR` | rgb_int | Colour |
| `CON` | in_pipe,out_pipe | Connectivity |
| `ELEV` | val,`"unit"` | Elevation [m] |
| `DP` | `"input"`,calc,`"unit"` | Differential pressure (mc) |
| `TYPE` | `"type"` | `"Centrifugal"`, `"Reciprocating"` |
| `EFFP` | `"input"`,calc | Pump efficiency (fraction) |
| `EFFS` | `"input"`,calc | System efficiency (fraction) |
| `POW` | calc,`"unit"` | Power (calculated) |
| `HQACT` | calc,`"unit"`,calc,`"unit"` | Head and actual flow (calculated) |

#### Pump Curves

| Param | Tokens | Description |
| ----- | ------ | ----------- |
| `CURRPM` | rated,actual,`"unit"` | RPM (rated and actual) |
| `CURDIA` | rated,actual,`"unit"` | Impeller diameter |
| `CURVSD` | flag | Curve SD flag (v3.6+) |
| `CURC1` | flag | Curve type flag |
| `CURNP` | count | Number of curve points |
| `CURQ` | v1,v2,...,v10,`"unit"` | Curve flow points [m³/h] |
| `CURH` | v1,v2,...,v10,`"unit"` | Curve head points [m] |
| `CUREFF` | v1,v2,...,v10,`"unit"` | Curve efficiency points [fraction] |
| `CURNPSH` | v1,v2,...,v10,`"unit"` | Curve NPSH points [m] |

#### NPSH

| Param | Tokens | Description |
| ----- | ------ | ----------- |
| `NPSHA13` | `"input"`,calc,`"unit"` | NPSH available at 1.3× (calculated) |
| `NPSHR13` | `"input"`,calc,`"unit"` | NPSH required at 1.3× (calculated) |
| `NPSHAF` | v1,v2,v3,v4,`"unit"`,v5,`"unit"` | NPSH available factors (v3.6+) |
| `NPSHRE` | suction_specific_speed,rpm,`"unit"`,Ns | NPSH required estimate |
| `NPSHVV` | val | NPSH vapor velocity flag (v3.6+) |
| `NPSHVT` | `"method"` | NPSH vapor type: `"Credit"` (v3.6+) |

#### Pump Sizing (v3.6+)

| Param | Tokens | Description |
| ----- | ------ | ----------- |
| `PZPRES` | v1,v2,v3,`"unit"` | Pump zone pressure [kPag] |
| `PZRAT` | `"method"`,factor,flag | Rating method, e.g. `"dPcalc",1.25,1` |
| `PZVES` | val,`"unit"`,val,`"unit"` | Pump zone vessel data |
| `NOTES` | `"text"` | Notes |

---

### 7.10 `\COMP` (Compressor)

| Param | Tokens | Description |
| ----- | ------ | ----------- |
| `NUM` | count | Instance count |
| `NAME` | `"tag","description"` | Element name |
| `XY` | x1,y1,x2,y2 | Graphic position |
| `ROT` | angle | Rotation |
| `FLIP` | h,v | Flip flags (v3.0+) |
| `LBL` | pos,x,y | Label position (v3.0+) |
| `COLOR` | rgb_int | Colour |
| `CON` | in_pipe,out_pipe | Connectivity |
| `ELEV` | val,`"unit"` | Elevation [m] |
| `DP` | `"input"`,calc,`"unit"` | Differential pressure (mc) |
| `PRAT` | `"input"`,calc,`"unit"` | Pressure ratio (v3.6+) |
| `QACT` | `"input"`,calc,`"unit"` | Actual volume flow (v3.6+) |
| `TYPE` | `"type"` | `"Centrifugal"`, `"Reciprocating"` |
| `EFFC` | `"input"`,calc | Compressor efficiency |
| `EFFS` | `"input"`,calc | System efficiency |
| `POW` | calc,`"unit"` | Power (calculated) |
| `FHAD` | `"input"`,calc | Adiabatic head factor (v3.6+) |
| `HQACT` | calc,`"unit"`,calc,`"unit"` | Head and actual flow (calculated) |
| `CURRPM` | rated,actual,`"unit"` | RPM |
| `CURDIA` | rated,actual,`"unit"` | Impeller diameter |
| `CURNP` | count | Number of curve points |
| `CURQ` | 10 values,`"unit"` | Curve flow points |
| `CURH` | 10 values,`"unit"` | Curve head points |
| `CUREFF` | 10 values,`"unit"` | Curve efficiency points |
| `NOTES` | `"text"` | Notes |

---

### 7.11 `\MISC` (Miscellaneous Equipment)

| Param | Tokens | Description |
| ----- | ------ | ----------- |
| `NUM` | count | Instance count |
| `NAME` | `"tag","description"` | Element name |
| `XY` | x1,y1,x2,y2 | Graphic position |
| `ROT` | angle | Rotation |
| `FLIP` | h,v | Flip flags (v3.0+) |
| `LBL` | pos,x,y | Label position (v3.0+) |
| `COLOR` | rgb_int | Colour |
| `NOZI` | pipe_idx,noz_elev,`"unit"` | Inlet nozzle connection |
| `NOZO` | pipe_idx,noz_elev,`"unit"` | Outlet nozzle connection |
| `DP` | `"input"`,calc,`"unit"` | Pressure drop (mc) |
| `PRAT` | `"input"`,`"unit"`,flow,`"unit"`,density,`"unit"`,viscosity,`"unit"` | Rating data |
| `K` | `"input"` | K-factor |
| `LD` | `"input"` | Equivalent L/D ratio |
| `DPELEV` | val,`"unit"` | Elevation pressure drop |
| `VOLBAL` | flag | Volume balance: 0 = off (v3.6+) |
| `MASBAL` | flag | Mass balance: 1 = on (v3.6+) |
| `NOTES` | `"text"` | Notes |

---

### 7.12 `\EXPAND` (Expander / Reducer)

| Param | Tokens | Description |
| ----- | ------ | ----------- |
| `NUM` | count | Instance count |
| `NAME` | `"tag","description"` | Element name |
| `XY` | x1,y1,x2,y2 | Graphic position |
| `ROT` | angle | Rotation |
| `FLIP` | h,v | Flip flags (v3.0+) |
| `LBL` | pos,x,y | Label position (v3.0+) |
| `COLOR` | rgb_int | Colour |
| `TYPE` | flag | 1 = expander (large→small), 2 = reducer (small→large) |
| `CON` | in_pipe,out_pipe | Connectivity |
| `ELEV` | val,`"unit"` | Elevation [m] |
| `DP` | `"input"`,calc,`"unit"` | Pressure drop (mc) |
| `DPP` | val,`"unit"` | DP profile (v3.6+) |
| `CHOKE` | flag | Choked-flow flag (v3.0+) |
| `K` | val | K-factor (calculated from geometry) |
| `ANGLE` | degrees | Half-angle, default 180 (sudden) |

---

### 7.13 `\JUNC` (Junction)

Multi-pipe meeting point with up to 4 inlet and 4 outlet nozzles.

| Param | Tokens | Description |
| ----- | ------ | ----------- |
| `NUM` | count | Instance count |
| `NAME` | `"tag","description"` | Element name |
| `XY` | 16 values | Graphic coordinates |
| `ROT` | angle | Rotation |
| `FLIP` | h,v | Flip flags (v3.0+) |
| `LBL` | pos,x,y | Label position (v3.0+) |
| `COLOR` | rgb_int | Colour |
| `PRES` | `"input"`,calc,`"unit"` | Junction pressure (mc) |
| `NOZI` | nozzle_num,pipe_idx,noz_elev,`"unit"` | Inlet nozzle (repeats 1–4) |
| `NOZO` | nozzle_num,pipe_idx,noz_elev,`"unit"` | Outlet nozzle (repeats 1–4) |

---

### 7.14 `\TEE` (Tee Piece)

A tee connects exactly 3 pipe legs: **C**ombined (main), **M**ain (straight-through),
and **B**ranch.

| Param | Tokens | Description |
| ----- | ------ | ----------- |
| `NUM` | count | Instance count |
| `NAME` | `"tag","description"` | Element name |
| `XY` | 12 values | Graphic coordinates (6 x,y pairs) |
| `ROT` | angle | Rotation |
| `FLIP` | h,v | Flip flags (v3.0+) |
| `LBL` | pos,x,y | Label position (v3.0+) |
| `COLOR` | rgb_int | Colour |
| `TYPE` | flag | Geometry: -3 = converging, 0 = none, 1 = diverging |
| `CON` | p1,p2,p3,p4,p5,p6 | 6 pipe indices (see connectivity below) |
| `ELEV` | val,`"unit"` | Elevation [m] |
| `PRES` | val,val,val,`"unit"` | Pressures at C, M, B legs (calculated) |
| `DPP` | val,val,val,`"unit"` | DP profile at C, M, B legs (v3.6+) |
| `KCM` | `"input"`,calc | K-factor combined→main |
| `KCB` | `"input"`,calc | K-factor combined→branch |
| `SPAC` | val | Spacer flag |
| `C` | leg_id,pipe_idx,density,`"unit"` | Combined leg pipe assignment |
| `M` | leg_id,pipe_idx,density,`"unit"` | Main leg pipe assignment |
| `B` | leg_id,pipe_idx,density,`"unit"` | Branch leg pipe assignment |
| `NOTES` | `"text"` | Notes |

**Tee connectivity (`CON`):** The 6 values in `CON` are pipe indices, arranged
as 3 pairs. Each pair corresponds to one leg (C, M, B), with the first value
being the upstream pipe and the second the downstream pipe. A value of 0 means
unconnected.

---

### 7.15 `\VESSEL` (Pressure Vessel / Separator)

| Param | Tokens | Description |
| ----- | ------ | ----------- |
| `NUM` | count | Instance count |
| `NAME` | `"tag","description"` | Element name |
| `XY` | 16 values | Graphic coordinates |
| `ROT` | angle | Rotation |
| `FLIP` | h,v | Flip flags (v3.0+) |
| `LBL` | pos,x,y | Label position (v3.0+) |
| `COLOR` | rgb_int | Colour |
| `TYPE` | `"orientation"` | `"Vertical"` or `"Horizontal"` |
| `PRES` | `"input"`,calc,`"unit"` | Operating pressure (mc) |
| `WSPEC` | flag | Weight specification flag (v3.6+) |
| `VF` | `"input"`,calc | Vapor fraction (v3.6+) |
| `LLF` | `"input"`,calc | Low liquid fraction (v3.6+) |
| `HLF` | `"input"`,calc | High liquid fraction (v3.6+) |
| `ELEV` | val,`"unit"` | Elevation [m] |
| `NOZN` | count | Number of active nozzles |

#### Vessel Levels (v3.6 names)

| Param | Tokens | Description |
| ----- | ------ | ----------- |
| `LEVELL` | `"input"`,calc,`"unit"`,calc,`"unit"`,`"type"` | Low liquid level |
| `LEVELM` | `"input"`,calc,`"unit"`,calc,`"unit"`,`"type"` | Mid liquid level |
| `LEVELH` | `"input"`,calc,`"unit"`,calc,`"unit"`,`"type"` | High liquid level |

> **v2.0/v3.0 names:** `LEVL`, `LEVM`, `LEVH` (fewer tokens).

#### Vessel Nozzles (v3.6 names)

| Param | Tokens | Description |
| ----- | ------ | ----------- |
| `NOZLI` | nozzle_num,pipe_idx,elev,`"unit"`,DP,`"unit"`,calc,calc,calc,calc,`"unit"` | Inlet nozzle (repeats 1–4) |
| `NOZLO` | nozzle_num,pipe_idx,elev,`"unit"`,DP,`"unit"`,calc,calc,calc,calc,`"unit"` | Outlet nozzle (repeats 1–4) |

> **v2.0/v3.0 names:** `NOZI`, `NOZO` (fewer tokens).

| `NOTES` | `"text"` | Notes |

---

### 7.16 `\SYMBOL` (Drawing Annotation)

Symbols are drawing-only elements (text labels, lines, shapes). They have no
hydraulic effect.

| Param | Tokens | Description |
| ----- | ------ | ----------- |
| `NUM` | count | Instance count |
| `TYPE` | `"kind"` | `"Text"`, `"Line"`, `"Rectangle"`, etc. |
| `XY` | x1,y1,x2,y2 | Bounding box |
| `TEXT` | `"content"` | Text content |
| `COLOR` | rgb_int | Colour |
| `STYLL` | flag | Line style |
| `STYLA` | flag | Area style |
| `ANGL` | radians,flag | Rotation angle (in radians) |
| `FSIZ` | size | Font size multiplier |

---

### 7.17 `\TOOLS` (Default New-Element Settings)

Stores default parameters used when creating new elements in the KORF GUI.
Always index 0 (singleton). Each record packs many tokens into a single line.

| Param | Tokens | Description |
| ----- | ------ | ----------- |
| `PIPEI` | `"tag","desc"`,flow,`"unit"`,... | Default new-pipe input parameters |
| `PIPEOA` | ... | Default new-pipe output parameters (A) |
| `PIPEOB` | ... | Default new-pipe output parameters (B) |
| `VALVEI` | `"tag","desc"`,flow,`"unit"`,... | Default new-valve input parameters |
| `VALVEO` | ... | Default new-valve output parameters |
| `FOI` | `"tag","desc"`,flow,`"unit"`,... | Default new-orifice input parameters |
| `FOO` | ... | Default new-orifice output parameters |

---

### 7.18 `\PSEUDO` (Pseudo-Component Definition) — v3.6+

Defines custom pseudo-components for flash calculations when no built-in
component data is available.

| Param | Tokens | Description |
| ----- | ------ | ----------- |
| `NUM` | count | Number of pseudo-components |
| `NAME` | id1,id2,`"name1"`,`"name2"` | Component identifiers |
| `FOR` | `"formula1"`,`"formula2"` | Chemical formulas |
| `MW` | val1,val2 | Molecular weights |
| `TFP` | val1,val2,`"unit"` | Freezing point temperatures [K] |
| `TBP` | val1,val2,`"unit"` | Boiling point temperatures [K] |
| `TC` | val1,val2,`"unit"` | Critical temperatures [K] |
| `PC` | val1,val2,`"unit"` | Critical pressures [kPaa] |
| `VC` | val1,val2,`"unit"` | Critical volumes [m³/kmol] |
| `ZC` | val1,val2 | Critical compressibility factors |
| `ACC` | val1,val2 | Acentric factors |
| `DENS` | val1,val2,`"unit"` | Reference densities [kg/m³] |
| `DENT` | val1,val2,`"unit"`,val3,val4,`"unit"` | Density vs temperature correlation |
| `DIPM` | val1,val2 | Dipole moments |
| `CP` | 10 coefficients,`"unit"` | Heat capacity polynomial [kJ/kmol/K] |
| `VISC` | 10 coefficients,`"unit"` | Viscosity correlation [cP_K] |
| `HVAP` | val1,val2 | Heat of vaporisation |
| `HFOR` | val1,val2 | Heat of formation |
| `ANT` | 10 coefficients,`"unit"`,4 values,`"unit"` | Antoine equation coefficients |

---

### 7.19 `\PIPEDATA` (Pipe Material Database) — v3.6+

Stores pipe material dimension tables. The `NUM` record (at index 0) gives the
number of materials. Each material has its own index (1, 2, 3, …).

| Param | Tokens | Description |
| ----- | ------ | ----------- |
| `NUM` | count | Number of materials (e.g. 3) |
| `MAT` | `"name"` | Material name: `"Steel"`, `"Ductile Iron"`, `"PVC"` |
| `NOTES` | `"standard"` | Reference standard (e.g. ASME B36.10M) |
| `PROP` | val,`"unit"`,val,`"unit"` | Material properties |
| `E` | val,`"unit"` | Default roughness [m] |
| `NSS` | `"sizes"` | Nominal size string (semicolon-delimited) |
| `IDIA` | `"count"`,`"default_sch"` | Number of diameter rows and default schedule |
| `SDIA` | various | Schedule-to-diameter mapping thresholds |
| `UNITS` | `"unit"` | Diameter table units: `"mm"` |
| `SCH` | 20 strings | Schedule column names |
| `DIA` | row_num,`"nom_size"`,21 values | Inner diameters for each schedule |

The `DIA` records form a matrix: rows are nominal sizes, columns are schedules.
A value of 0 means that schedule is not available for that size.

---

## 8. Editing Guidelines

1. **Never change element-type or index tokens** – these define the file structure.
2. **Update only the `values` list** of a record (after the 3rd token).
3. **Multi-case inputs** must be updated as semicolon-delimited strings.
4. **Calculated result fields** will be overwritten by KORF on the next run — you
   may leave them unchanged or set to 0.
5. **In-memory editing contract:** all manipulations done through pyKorf's
   `Model` API are applied in memory; the `.kdf` file is written only when
   `model.save()` / `model.save_as()` is called.
6. Always call `model.save()` before asking KORF to reload.
7. **Version awareness:** Parameter names differ across versions. Check the version
   header before accessing parameters:
   - v2.0/v3.0: `LEVEL`, `NOZ`, `FITA/FITB/FITO`, `U`, `C` (for FO)
   - v3.6: `LEVELH`, `NOZL`, `FIT1–FIT11`, `UI`, `CD` (for FO)
8. **Fitting format:** When editing fittings, ensure you use the correct format for
   the file version. The v3.6 `FIT1–FIT11` format has 7 tokens per fitting
   (Name, Count, L/D, K, Cv, Kv, flag) while v2.0/v3.0 `FITA/FITB` packs
   5 fittings per record with 4 tokens each.
9. **Encoding:** Always read/write KDF files with `latin-1` encoding and `\r\n`
   line endings.
10. **Element order** must be preserved — see §3.
