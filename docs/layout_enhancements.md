# Layout Enhancements — Session Recap

> Branch: `claude/enhance-auto-position-tJ66e`
> All implementations live in `LayoutService` (`pykorf/model/services/layout.py`).
> Every method is available both on the `Model` facade and directly via `model.layout.*`.

---

## Overview

This session added three tiers of layout functionality on top of the existing
grid-based `auto_layout` and basic `get_position`/`set_position` primitives.

| Tier | Theme | Methods added |
|------|-------|---------------|
| **0** | Orthogonal angle snapping | `snap_orthogonal` |
| **1** | Alignment & grid helpers | `align_horizontal`, `align_vertical`, `distribute_horizontal`, `distribute_vertical`, `snap_to_grid`, `center_layout` |
| **2** | Pipe polylines + flow layout | `get_polyline`, `set_polyline`, `add_bend`, `auto_layout(strategy='flow')` |
| **3** | Full orthogonal pipe routing | `route_pipe`, `route_all_pipes`, `auto_layout(route_pipes=True)` |

---

## Tier 0 — Orthogonal Angle Snapping

### `snap_orthogonal(threshold_deg=10.0)`

Scans every connected element pair and corrects "almost straight" connections
so they are exactly horizontal or vertical.

**Algorithm:**
- Builds connected pairs from `CON` / `NOZL` / `NOZ` records.
- Computes the angle between each pair: `atan2(|dy|, |dx|)` → value in [0°, 90°].
- If angle < `threshold_deg` → horizontal snap: moves the second element's Y to match the first.
- If angle > 90° − `threshold_deg` → vertical snap: moves the second element's X to match the first.

**Called automatically** at the end of every `auto_layout()` run.

```python
model.snap_orthogonal()           # default 10° threshold
model.snap_orthogonal(5.0)        # tighter — only correct angles < 5°
```

---

## Tier 1 — Alignment & Grid Helpers

### `align_horizontal(names, anchor_y=None)`

Moves all named elements to the same Y coordinate.
`anchor_y` defaults to the group's mean Y if not specified.

```python
model.align_horizontal(["P1", "V1", "HX1"])           # snap to mean Y
model.align_horizontal(["P1", "V1", "HX1"], anchor_y=4000.0)  # snap to 4000
```

### `align_vertical(names, anchor_x=None)`

Moves all named elements to the same X coordinate.
`anchor_x` defaults to the group's mean X if not specified.

```python
model.align_vertical(["F1", "P1", "Prod1"])
model.align_vertical(["F1", "P1"], anchor_x=2000.0)
```

### `distribute_horizontal(names)`

Spaces named elements evenly along X. The leftmost and rightmost elements
stay fixed; everything in between is repositioned with equal gaps.
Requires at least 3 elements.

```python
model.distribute_horizontal(["F1", "P1", "HX1", "V1", "Prod1"])
```

### `distribute_vertical(names)`

Same as `distribute_horizontal` but along Y.

```python
model.distribute_vertical(["T1", "P1", "T2"])
```

### `snap_to_grid(grid_size=500.0)`

Rounds every placed element's position to the nearest multiple of `grid_size`.

```python
model.snap_to_grid()          # 500-unit grid
model.snap_to_grid(1000.0)    # 1000-unit grid
```

### `center_layout()`

Translates all placed elements so their collective bounding box is centred
on the canvas (`X_MIN`=1000, `X_MAX`=15500, `Y_MIN`=1000, `Y_MAX`=8500).

```python
model.center_layout()
```

---

## Tier 2 — Pipe Polylines & Flow-Based Layout

### KDF Pipe XY Record Format

```
XY: [x0, y0,  x1, y1,  x2, y2, ...,  0, 0, 0, 0, ...]
     ^^^^^^^^^^^^  ^^^^^^^^^^^^^^^^^^  ^^^^^^^^^^^^^^^^^^^
     pair 0        pairs 1..N          zero padding
     (icon anchor) (drawn waypoints)
```

- **Pair 0** (`x0, y0`): primary position — the element icon anchor, managed by `get_position` / `set_position`.
- **Pairs 1..N**: the actual drawn polyline waypoints.
- **Trailing zeros**: padding up to 13 pairs (26 values).
- **`BEND` flag**: `0` = straight / no waypoints, `1` = has waypoints.

### `get_polyline(pipe)`

Returns the drawn waypoints (pairs 1..N) as a list of `(x, y)` tuples,
stopping at the first `(0, 0)` padding pair.

```python
pts = model.get_polyline(model.pipes[1])
# e.g. [(1500.0, 4700.0), (2600.0, 4700.0)]
```

### `set_polyline(pipe, points)`

Writes waypoints into the XY record starting at pair 1.
Automatically zeros out the remaining padding and sets the `BEND` flag.

```python
model.set_polyline(pipe, [(1000.0, 3000.0), (5000.0, 3000.0)])
```

### `add_bend(pipe, x, y, index=None)`

Inserts a single waypoint into the pipe's polyline at `index`
(default: before the last point, creating a corner in an existing
start → end line).

**Orthogonal L-shape recipe:**
```
start (x1, y1) ──► corner ──► end (x2, y2)
```

```python
# Horizontal-first L:  (x1,y1) → (x2,y1) → (x2,y2)
model.add_bend(pipe, x2, y1)

# Vertical-first L:    (x1,y1) → (x1,y2) → (x2,y2)
model.add_bend(pipe, x1, y2)

# Prepend a point:
model.add_bend(pipe, 500.0, 3000.0, index=0)
```

### `auto_layout(strategy='flow')`

New `strategy` parameter:

| Value | Behaviour |
|-------|-----------|
| `"grid"` | (default, unchanged) Square-root rectangular grid. |
| `"flow"` | Topological left-to-right placement: FEEDs in column 0, their downstream neighbours in column 1, and so on. Unconnected elements fall back to a grid at the end. |

**How the flow strategy works:**
1. `_build_flow_graph()` — builds a directed adjacency list from `CON[1]` (equipment outlet pipes) and `NOZL` (FEED outgoing pipes).
2. `_assign_flow_levels()` — BFS from source nodes (in-degree 0) assigns the *longest-path* depth to each element so that every element appears to the right of all its predecessors.
3. Elements at the same depth share an X column and are distributed vertically.

```python
model.auto_layout(strategy="flow")
model.auto_layout(strategy="flow", spacing=2000.0)
```

---

## Tier 3 — Full Orthogonal Pipe Routing

### `route_pipe(pipe, bend='auto')`

Routes a single pipe between its two endpoint elements as an orthogonal polyline.

| Connection | Waypoints written |
|------------|------------------|
| Already horizontal or vertical | 2-point straight line |
| Diagonal | 3-point L-shape with one 90° corner |

**`bend` parameter:**

| Value | Corner position |
|-------|----------------|
| `"h"` | Horizontal-first: `(x_end, y_start)` |
| `"v"` | Vertical-first: `(x_start, y_end)` |
| `"auto"` | `"h"` when `|dx| >= |dy|`, `"v"` otherwise |

```python
model.route_pipe(model.pipes[2])               # auto
model.route_pipe(model.pipes[2], bend="h")     # force horizontal-first
model.route_pipe(model.pipes[2], bend="v")     # force vertical-first
```

### `route_all_pipes(bend='auto')`

Calls `route_pipe` on every non-template pipe that connects exactly two elements.
Pipes with zero or one endpoint (stubs) are silently skipped.

```python
model.route_all_pipes()
model.route_all_pipes(bend="h")   # all horizontal-first
```

### `auto_layout(route_pipes=True)`

Combines placement, orthogonal snapping, and routing in a single call:

```python
# Full pipeline — place, snap, then draw all pipe polylines
model.auto_layout(strategy="flow", route_pipes=True)
```

Internal sequence:
1. Topological placement (`_auto_layout_flow`)
2. `snap_orthogonal()` — corrects near-axis element positions
3. `route_all_pipes()` — generates orthogonal polylines for every connected pipe

---

## Internal Helpers (LayoutService only)

| Helper | Purpose |
|--------|---------|
| `_build_pipe_to_elems()` | Builds `{pipe_idx: [elem_names]}` from all CON / NOZL / NOZ records. Shared by connected-pair detection, flow graph, and routing. |
| `_build_flow_graph()` | Returns a directed adjacency dict using outlet pipe direction to establish upstream → downstream edges. |
| `_assign_flow_levels()` | BFS longest-path assignment from source nodes; returns `{elem_name: column_depth}`. |
| `_get_connected_pairs()` | Returns unique `(name_a, name_b)` pairs that share a pipe (undirected). Used by `snap_orthogonal`. |
| `_auto_layout_grid()` | The original square-root grid placement, extracted into a private method. |
| `_auto_layout_flow()` | Flow-based column placement, delegated to by `auto_layout(strategy='flow')`. |

---

## Complete API Reference

```python
# ----- Orthogonal snapping -----
model.snap_orthogonal(threshold_deg=10.0)

# ----- Alignment -----
model.align_horizontal(names, anchor_y=None)
model.align_vertical(names, anchor_x=None)
model.distribute_horizontal(names)
model.distribute_vertical(names)
model.snap_to_grid(grid_size=500.0)
model.center_layout()

# ----- Pipe polylines -----
model.get_polyline(pipe)                     # → list[tuple[float, float]]
model.set_polyline(pipe, points)
model.add_bend(pipe, x, y, index=None)

# ----- Layout with flow strategy -----
model.auto_layout(strategy="flow")
model.auto_layout(strategy="flow", spacing=2000.0)

# ----- Routing -----
model.route_pipe(pipe, bend="auto")          # "h" | "v" | "auto"
model.route_all_pipes(bend="auto")

# ----- Combined pipeline -----
model.auto_layout(strategy="flow", route_pipes=True)

# ----- All above also accessible via model.layout.* -----
model.layout.snap_orthogonal()
model.layout.route_all_pipes(bend="h")
model.layout.auto_layout(strategy="flow", route_pipes=True)
# etc.
```
