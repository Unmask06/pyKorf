"""Layout and positioning service for KORF models.

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

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from pykorf.exceptions import LayoutError

if TYPE_CHECKING:
    from pykorf.elements.base import BaseElement
    from pykorf.model import Model

X_MIN = 1000.0
Y_MIN = 1000.0
X_MAX = 15500.0
Y_MAX = 8500.0

MIN_SPACING = 1000.0
COMFORT_SPACING_X = 1500.0
COMFORT_SPACING_Y = 1500.0

_X_MIN = X_MIN
_Y_MIN = Y_MIN
_X_MAX = X_MAX
_Y_MAX = Y_MAX
_MIN_SPACING = MIN_SPACING
_COMFORT_SPACING_X = COMFORT_SPACING_X
_COMFORT_SPACING_Y = COMFORT_SPACING_Y


@dataclass(frozen=True, slots=True)
class LayoutService:
    """Service for managing element layout and positioning in KORF models.

    Provides functionality for:
    - Getting and setting element positions
    - Auto-placement of elements
    - Layout validation and clash detection
    - Text and HTML visualization

    Attributes:
        model: The Model instance to operate on.
    """

    model: Model

    def get_position(self, elem: BaseElement) -> tuple[float, float] | None:
        """Extract the primary (x, y) position from an element's XY record."""
        rec = elem._get("XY")
        if rec is None or len(rec.values) < 2:
            return None
        try:
            return (float(rec.values[0]), float(rec.values[1]))
        except (ValueError, TypeError):
            return None

    def __set_position_on_element(self, elem: BaseElement, x: float, y: float) -> None:
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
        self,
        target: str | BaseElement | Model,
        name_or_x: str | float,
        x_or_y: float,
        y: float | None = None,
    ) -> None:
        """Set the primary (x, y) position.

        Can be called in three ways:
        - set_position(element, x, y)
        - set_position(name, x, y)
        - set_position(model, name, x, y)
        """
        # Case 1: set_position(model, name, x, y)
        if hasattr(target, "get_element"):
            if not isinstance(name_or_x, str) or y is None:
                raise ValueError("Use set_position(model, element_name, x, y)")
            from pykorf.model import Model as KorfModel

            if isinstance(target, KorfModel):
                elem = target.get_element(name_or_x)
            self.__set_position_on_element(elem, float(x_or_y), float(y))
            return

        # Case 2: set_position(name, x, y)
        if isinstance(target, str):
            if y is not None:
                # If y is provided, assume Case 1 was intended but target was name
                # Actually Case 2 should only have 3 args (name, x, y)
                # But if called via model.set_position("L1", x, y), it arrives here
                # because model is not target.
                # Wait, if called via model.set_position, target is "L1".
                self.__set_position_on_element(
                    self.model.get_element(target), float(name_or_x), float(x_or_y)
                )
                return
            # If y is None, then Case 2: set_position(name, x, y)
            # but wait, the signature is (self, target, name_or_x, x_or_y, y=None)
            # So name_or_x is x, x_or_y is y.
            self.__set_position_on_element(
                self.model.get_element(target), float(name_or_x), float(x_or_y)
            )
            return

        # Case 3: set_position(element, x, y)
        if y is not None:
            raise ValueError("Use set_position(element, x, y) for element objects")
        self.__set_position_on_element(cast("BaseElement", target), float(name_or_x), float(x_or_y))

    def __all_positions(self) -> dict[str, tuple[float, float]]:
        """Collect all element positions as ``{name: (x, y)}``."""
        positions: dict[str, tuple[float, float]] = {}
        for elem in self.model.elements:
            pos = self.get_position(elem)
            if pos is not None:
                positions[elem.name] = pos
        return positions

    def check_layout(self) -> list[str]:
        """Check for overlapping element positions."""
        issues: list[str] = []
        positions = self.__all_positions()

        placed: list[tuple[str, float, float]] = []

        pos_map: dict[tuple[float, float], list[str]] = {}
        for name, pos in positions.items():
            if pos == (0.0, 0.0):
                continue
            x, y = float(pos[0]), float(pos[1])
            placed.append((name, x, y))

            if not (X_MIN <= x <= X_MAX and Y_MIN <= y <= Y_MAX):
                issues.append(
                    f"Element {name} at ({x:.1f}, {y:.1f}) is outside layout bounds "
                    f"[{X_MIN:.0f},{Y_MIN:.0f}]-[{X_MAX:.0f},{Y_MAX:.0f}]"
                )

            key = (round(x, 1), round(y, 1))
            pos_map.setdefault(key, []).append(name)

        for pos, names in pos_map.items():
            if len(names) > 1:
                issues.append(f"Overlapping elements at ({pos[0]}, {pos[1]}): " + ", ".join(names))

        for i in range(len(placed)):
            n1, x1, y1 = placed[i]
            for j in range(i + 1, len(placed)):
                n2, x2, y2 = placed[j]
                dx = x2 - x1
                dy = y2 - y1
                dist = (dx * dx + dy * dy) ** 0.5
                if dist < MIN_SPACING:
                    issues.append(
                        f"Elements {n1} and {n2} are too close ({dist:.1f} < {MIN_SPACING:.0f})"
                    )

        return issues

    def auto_place(self, elem: BaseElement) -> None:
        """Automatically place an element at a non-overlapping position."""
        existing = []
        for name, pos in self.__all_positions().items():
            if name == elem.name or pos == (0.0, 0.0):
                continue
            existing.append((float(pos[0]), float(pos[1])))

        def _fits(candidate: tuple[float, float]) -> bool:
            cx, cy = candidate
            if not (X_MIN <= cx <= X_MAX and Y_MIN <= cy <= Y_MAX):
                return False
            for ex, ey in existing:
                dx = cx - ex
                dy = cy - ey
                dist = (dx * dx + dy * dy) ** 0.5
                if dist < MIN_SPACING:
                    return False
            return True

        cols = int((X_MAX - X_MIN) // COMFORT_SPACING_X) + 1
        rows = int((Y_MAX - Y_MIN) // COMFORT_SPACING_Y) + 1

        for row in range(rows):
            for col in range(cols):
                candidate = (
                    X_MIN + col * COMFORT_SPACING_X,
                    Y_MIN + row * COMFORT_SPACING_Y,
                )
                if _fits(candidate):
                    self.__set_position_on_element(elem, candidate[0], candidate[1])
                    return

        raise LayoutError(
            "No available layout position within bounds "
            f"[{X_MIN:.0f},{Y_MIN:.0f}]-[{X_MAX:.0f},{Y_MAX:.0f}] "
            f"with minimum spacing {MIN_SPACING:.0f}."
        )

    def visualize(self, **kwargs: Any) -> str:
        """Create a simple text representation of the model layout."""
        lines: list[str] = []
        lines.append(f"=== Model Layout: {self.model.path.name} ===")
        lines.append(f"Version: {self.model.version}  |  Elements: {len(self.model.elements)}")
        lines.append("")

        from collections import defaultdict

        by_type: dict[str, list] = defaultdict(list)
        for elem in self.model.elements:
            pos = self.get_position(elem)
            pos_str = f"({pos[0]:.0f}, {pos[1]:.0f})" if pos else "(unplaced)"
            by_type[elem.etype].append(f"  {elem.name:12s} idx={elem.index:<3d} {pos_str}")

        for etype in sorted(by_type.keys()):
            lines.append(f"[{etype}]")
            lines.extend(by_type[etype])
            lines.append("")

        lines.append("[Connections]")
        conn_lines = self.__format_connections()
        if conn_lines:
            lines.extend(conn_lines)
        else:
            lines.append("  (no connections)")
        lines.append("")

        return "\n".join(lines)

    def __format_connections(self) -> list[str]:
        """Format connection information for visualization."""
        conn_lines: list[str] = []
        pipe_names = {idx: elem.name for idx, elem in self.model.pipes.items() if idx >= 1}

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
            collection = getattr(self.model, attr, {})
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
                            conn_lines.append(f"  {in_name} --> [{elem.name}] --> {out_name}")
                    except (ValueError, TypeError):
                        pass

        for attr in ("feeds", "products"):
            collection = getattr(self.model, attr, {})
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

    def auto_layout(self, spacing: float | None = None) -> None:
        """Automatically arrange all unplaced elements in a logical flow."""
        spacing = spacing or COMFORT_SPACING_X

        unplaced = []
        for elem in self.model.elements:
            pos = self.get_position(elem)
            if pos is None or pos == (0.0, 0.0):
                unplaced.append(elem)

        if not unplaced:
            return

        existing = [
            pos
            for pos in (self.get_position(e) for e in self.model.elements)
            if pos is not None and pos != (0.0, 0.0)
        ]

        import math

        cols = max(1, int(math.sqrt(len(unplaced))))

        for i, elem in enumerate(unplaced):
            row = i // cols
            col = i % cols

            x = X_MIN + col * spacing
            y = Y_MIN + row * spacing

            for ex, ey in existing:
                if abs(x - ex) < spacing / 2 and abs(y - ey) < spacing / 2:
                    x += spacing
                    break

            self.set_position(self.model, elem.name, x, y)
            existing.append((x, y))

    def visualize_network(self, path: str | Path = "network.html") -> None:
        """Generate an interactive PyVis HTML visualization."""
        from pykorf.visualization import Visualizer

        viz = Visualizer(self.model)
        viz.to_html(path)


__all__ = [
    "COMFORT_SPACING_X",
    "COMFORT_SPACING_Y",
    "MIN_SPACING",
    "X_MAX",
    "X_MIN",
    "Y_MAX",
    "Y_MIN",
    "LayoutService",
]
