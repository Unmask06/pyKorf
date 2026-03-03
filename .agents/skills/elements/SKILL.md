---
name: elements
description: Element types, parameter constants, registry, BaseElement API, and adding new elements
---

# Element Types, Constants & Registry

## STRICT RULE: Always Use Constants

```python
# CORRECT
from pykorf.elements import Element, Pipe, Feed, BaseElement
model.add_element(Element.PIPE, "L1", {Pipe.LEN: 100, Pipe.DIA: 50})

# WRONG — never hardcode strings
model.add_element("PIPE", "L1", {"LEN": 100})
```

## Element Class Hierarchy

All element classes inherit from `BaseElement` in `pykorf/elements/base.py`.

### BaseElement Common Constants

```
NAME, NUM, XY, NOTES, CON, NOZI, NOZO, NOZL, ETYPE, ENAME
```

### Element Type Tokens (`Element` class)

```
PIPE, FEED, PROD, PUMP, VALVE, CHECK, ORIFICE, HX, COMP, MISC,
EXPAND, JUNC, TEE, VESSEL, GEN, SYMBOL, TOOLS, PSEUDO, PIPEDATA
```

### Concrete Classes → Key Parameters

| Class           | ETYPE       | Key params                                        |
| --------------- | ----------- | ------------------------------------------------- |
| `Pipe`          | `"PIPE"`    | `LEN, DIA, ID, SCH, MAT, TFLOW, TEMP, PRES, BEND` |
| `Feed`          | `"FEED"`    | `NAME, PRES, TEMP, TFLOW`                         |
| `Product`       | `"PROD"`    | `NAME, PRES`                                      |
| `Pump`          | `"PUMP"`    | `NAME, HEAD, EFF, SPEED`                          |
| `Valve`         | `"VALVE"`   | `NAME, CV, TYPE`                                  |
| `CheckValve`    | `"CHECK"`   | `NAME, CV`                                        |
| `FlowOrifice`   | `"ORIFICE"` | `NAME, DIA`                                       |
| `HeatExchanger` | `"HX"`      | `NAME, DP, DUTY`                                  |
| `Compressor`    | `"COMP"`    | `NAME, HEAD, EFF`                                 |
| `MiscEquipment` | `"MISC"`    | `NAME, DP`                                        |
| `Expander`      | `"EXPAND"`  | `NAME`                                            |
| `Junction`      | `"JUNC"`    | `NAME`                                            |
| `Tee`           | `"TEE"`     | `NAME`                                            |
| `Vessel`        | `"VESSEL"`  | `NAME, VOL`                                       |

### Backward-compat Aliases

`Gen=General, Hx=HeatExchanger, Comp=Compressor, Misc=MiscEquipment, Expand=Expander, Junc=Junction, Prod=Product, Check=CheckValve, Orifice=FlowOrifice, Common=BaseElement`

## ELEMENT_REGISTRY

Maps KDF keyword → class: `ELEMENT_REGISTRY["PIPE"] → Pipe`

## PROPERTIES_BY_ELEMENT

Maps KDF keyword → tuple of ALL parameter constants for that type.

## Element Indexing

- Index `0` = KORF default template (schema reference)
- Real instances start at index `1`
- `model.pipes[1]` = first real pipe

## Adding a New Element Type

1. Create `pykorf/elements/<name>.py` with class inheriting `BaseElement`
2. Define `ETYPE`, `ENAME`, parameter constants, `ALL` tuple
3. Register in `pykorf/elements/__init__.py` (imports, `ELEMENT_REGISTRY`, `PROPERTIES_BY_ELEMENT`)
4. Add collection property to `Model` class in `pykorf/model.py`
5. Add tests in `tests/test_elements.py`

## Key Files

- `pykorf/elements/__init__.py` — registry, `Element` class, exports
- `pykorf/elements/base.py` — `BaseElement`, param validation
- `pykorf/elements/pipe.py` — largest element (90+ constants)
- `pykorf/elements/*.py` — one file per element type
