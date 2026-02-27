"""Layout and positioning management for KORF models.

Handles element positions (XY records), auto-placement of new elements,
clash detection, and simple visualization.

XY Record Format
----------------
Each element has an ``XY`` parameter with values like::

    [x1, y1, x2, y2, ...]

For most elements, ``(x1, y1)`` is the primary position.  Pipes may have
multiple coordinate pairs forming a polyline.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pykorf.exceptions import LayoutError

if TYPE_CHECKING:
    from pykorf.elements.base import BaseElement
    from pykorf.model import Model

# KORF drawing coordinate bounds
_X_MIN = 1000.0
_Y_MIN = 1000.0
_X_MAX = 15500.0
_Y_MAX = 8500.0

# Spacing rules
_MIN_SPACING = 1000.0
_COMFORT_SPACING_X = 1500.0
_COMFORT_SPACING_Y = 1500.0


def get_position(elem: BaseElement) -> tuple[float, float] | None:
    """Extract the primary (x, y) position from an element's XY record.

    Returns *None* if the element has no XY record or it's empty.
    """
    rec = elem._get("XY")
    if rec is None or len(rec.values) < 2:
        return None
    try:
        return (float(rec.values[0]), float(rec.values[1]))
    except (ValueError, TypeError):
        return None


def _set_position_on_element(elem: BaseElement, x: float, y: float) -> None:
    """Set the primary (x, y) position on a concrete element object."""
    rec = elem._get("XY")
    if rec is None:
        return
    vals = list(rec.values)
    if len(vals) >= 2:
        vals[0] = str(x)
        vals[1] = str(y)
        rec.values = vals
        rec.raw_line = ""


def set_position(
    target: Model | BaseElement,
    name_or_x: str | float,
    x_or_y: float,
    y: float | None = None,
) -> None:
    """Set the primary (x, y) position.

    Supports two call styles:

    - ``set_position(model, element_name, x, y)``
    - ``set_position(element, x, y)`` (backward-compatible)
    """
    if hasattr(target, "get_element"):
        if not isinstance(name_or_x, str) or y is None:
            raise ValueError("Use set_position(model, element_name, x, y)")
        elem = target.get_element(name_or_x)
        _set_position_on_element(elem, float(x_or_y), float(y))
        return

    if y is not None:
        raise ValueError("Use set_position(element, x, y) for element objects")
    _set_position_on_element(target, float(name_or_x), float(x_or_y))


def _all_positions(model: Model) -> dict[str, tuple[float, float]]:
    """Collect all element positions as ``{name: (x, y)}``."""
    positions: dict[str, tuple[float, float]] = {}
    for elem in model.elements:
        pos = get_position(elem)
        if pos is not None:
            positions[elem.name] = pos
    return positions


def check_layout(model: Model) -> list[str]:
    """Check for overlapping element positions.

    Returns a list of clash descriptions (empty = no clashes).
    Elements at position (0, 0) are ignored as they are unplaced.
    """
    issues: list[str] = []
    positions = _all_positions(model)

    placed: list[tuple[str, float, float]] = []

    # Bounds + exact overlap checks
    pos_map: dict[tuple[float, float], list[str]] = {}
    for name, pos in positions.items():
        if pos == (0.0, 0.0):
            continue
        x, y = float(pos[0]), float(pos[1])
        placed.append((name, x, y))

        if not (_X_MIN <= x <= _X_MAX and _Y_MIN <= y <= _Y_MAX):
            issues.append(
                f"Element {name} at ({x:.1f}, {y:.1f}) is outside layout bounds "
                f"[{_X_MIN:.0f},{_Y_MIN:.0f}]–[{_X_MAX:.0f},{_Y_MAX:.0f}]"
            )

        key = (round(x, 1), round(y, 1))
        pos_map.setdefault(key, []).append(name)

    for pos, names in pos_map.items():
        if len(names) > 1:
            issues.append(
                f"Overlapping elements at ({pos[0]}, {pos[1]}): " + ", ".join(names)
            )

    # Minimum spacing checks (Euclidean)
    for i in range(len(placed)):
        n1, x1, y1 = placed[i]
        for j in range(i + 1, len(placed)):
            n2, x2, y2 = placed[j]
            dx = x2 - x1
            dy = y2 - y1
            dist = (dx * dx + dy * dy) ** 0.5
            if dist < _MIN_SPACING:
                issues.append(
                    f"Elements {n1} and {n2} are too close ({dist:.1f} < {_MIN_SPACING:.0f})"
                )

    return issues


def auto_place(model: Model, elem: BaseElement) -> None:
    """Automatically place an element at a non-overlapping position.

    Finds an empty grid position and sets the element's XY accordingly.
    """
    existing = []
    for name, pos in _all_positions(model).items():
        if name == elem.name or pos == (0.0, 0.0):
            continue
        existing.append((float(pos[0]), float(pos[1])))

    def _fits(candidate: tuple[float, float]) -> bool:
        cx, cy = candidate
        if not (_X_MIN <= cx <= _X_MAX and _Y_MIN <= cy <= _Y_MAX):
            return False
        for ex, ey in existing:
            dx = cx - ex
            dy = cy - ey
            dist = (dx * dx + dy * dy) ** 0.5
            if dist < _MIN_SPACING:
                return False
        return True

    cols = int((_X_MAX - _X_MIN) // _COMFORT_SPACING_X) + 1
    rows = int((_Y_MAX - _Y_MIN) // _COMFORT_SPACING_Y) + 1

    for row in range(rows):
        for col in range(cols):
            candidate = (
                _X_MIN + col * _COMFORT_SPACING_X,
                _Y_MIN + row * _COMFORT_SPACING_Y,
            )
            if _fits(candidate):
                _set_position_on_element(elem, candidate[0], candidate[1])
                return

    raise LayoutError(
        "No available layout position within bounds "
        f"[{_X_MIN:.0f},{_Y_MIN:.0f}]–[{_X_MAX:.0f},{_Y_MAX:.0f}] "
        f"with minimum spacing {_MIN_SPACING:.0f}."
    )


def visualize(model: Model, **kwargs) -> str:
    """Create a simple text representation of the model layout.

    Returns a multi-line string showing element names at their grid
    positions with connection lines indicated by ``-->``.
    """
    lines: list[str] = []
    lines.append(f"=== Model Layout: {model.path.name} ===")
    lines.append(f"Version: {model.version}  |  Elements: {len(model.elements)}")
    lines.append("")

    # List elements by type with position
    from collections import defaultdict

    by_type: dict[str, list] = defaultdict(list)
    for elem in model.elements:
        pos = get_position(elem)
        pos_str = f"({pos[0]:.0f}, {pos[1]:.0f})" if pos else "(unplaced)"
        by_type[elem.etype].append(f"  {elem.name:12s} idx={elem.index:<3d} {pos_str}")

    for etype in sorted(by_type.keys()):
        lines.append(f"[{etype}]")
        lines.extend(by_type[etype])
        lines.append("")

    # Show connections
    lines.append("[Connections]")
    conn_lines = _format_connections(model)
    if conn_lines:
        lines.extend(conn_lines)
    else:
        lines.append("  (no connections)")
    lines.append("")

    return "\n".join(lines)


def _format_connections(model: Model) -> list[str]:
    """Format connection information for visualization."""
    conn_lines: list[str] = []
    pipe_names = {idx: elem.name for idx, elem in model.pipes.items() if idx >= 1}

    # Equipment connections (CON records)
    for attr in (
        "pumps",
        "valves",
        "check_valves",
        "orifices",
        "exchangers",
        "compressors",
        "misc_equipment",
        "expanders",
    ):
        collection = getattr(model, attr, {})
        for idx, elem in collection.items():
            if idx == 0:
                continue
            rec = elem._get("CON")
            if rec and len(rec.values) >= 2:
                try:
                    in_idx, out_idx = int(rec.values[0]), int(rec.values[1])
                    in_name = pipe_names.get(in_idx, f"?{in_idx}")
                    out_name = pipe_names.get(out_idx, f"?{out_idx}")
                    if in_idx != 0 or out_idx != 0:
                        conn_lines.append(
                            f"  {in_name} --> [{elem.name}] --> {out_name}"
                        )
                except (ValueError, TypeError):
                    pass

    # FEED/PROD nozzle connections
    for attr in ("feeds", "products"):
        collection = getattr(model, attr, {})
        for idx, elem in collection.items():
            if idx == 0:
                continue
            for noz_param in ("NOZL", "NOZ"):
                rec = elem._get(noz_param)
                if rec and rec.values:
                    try:
                        pipe_ref = int(rec.values[0])
                        if pipe_ref != 0:
                            p_name = pipe_names.get(pipe_ref, f"?{pipe_ref}")
                            arrow = "-->" if elem.etype == "FEED" else "<--"
                            conn_lines.append(f"  [{elem.name}] {arrow} {p_name}")
                    except (ValueError, TypeError):
                        pass
                    break

    return conn_lines
