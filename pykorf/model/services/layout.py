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
        rec = elem.get_param("XY")
        if rec is None or len(rec.values) < 2:
            return None
        try:
            return (float(rec.values[0]), float(rec.values[1]))
        except (ValueError, TypeError):
            return None

    def __set_position_on_element(self, elem: BaseElement, x: float, y: float) -> None:
        """Set the primary (x, y) position on a concrete element object."""
        rec = elem.get_param("XY")
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
                rec = elem.get_param("CON")
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
                    rec = elem.get_param(noz_param)
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

    # ------------------------------------------------------------------
    # Pipe polyline (waypoint) access
    # ------------------------------------------------------------------

    def get_polyline(self, pipe: BaseElement) -> list[tuple[float, float]]:
        """Get the drawn waypoints from a pipe's XY record.

        Pair 0 of the XY record is the element icon anchor (managed by
        :meth:`get_position`).  Waypoints begin at pair 1 (index 2) and
        continue until the first ``(0, 0)`` padding pair.

        Args:
            pipe: A PIPE element.

        Returns:
            Ordered list of ``(x, y)`` waypoint tuples.  Empty list if none
            are set.
        """
        rec = pipe.get_param("XY")
        if rec is None or len(rec.values) < 4:
            return []
        vals = rec.values
        points: list[tuple[float, float]] = []
        i = 2  # skip pair 0 (primary / icon-anchor position)
        while i + 1 < len(vals):
            try:
                x, y = float(vals[i]), float(vals[i + 1])
            except (ValueError, TypeError):
                break
            if x == 0.0 and y == 0.0:
                break
            points.append((x, y))
            i += 2
        return points

    def __set_bend_flag(self, pipe: BaseElement, value: int) -> None:
        """Write the BEND flag on a pipe (0 = no bends, 1 = has bends)."""
        rec = pipe.get_param("BEND")
        if rec is None:
            return
        vals = list(rec.values)
        if vals:
            vals[0] = str(value)
            rec.values = vals
            rec.raw_line = ""

    def set_polyline(self, pipe: BaseElement, points: list[tuple[float, float]]) -> None:
        """Write waypoints into a pipe's XY record.

        Pair 0 (the element icon anchor) is left unchanged.  Pair 1 onward
        is overwritten with *points*, followed by zeros.  The ``BEND`` flag
        is set to ``1`` if waypoints are present, ``0`` otherwise.

        Args:
            pipe: A PIPE element.
            points: Ordered list of ``(x, y)`` waypoints.
        """
        rec = pipe.get_param("XY")
        if rec is None:
            return
        vals = list(rec.values)
        write_idx = 2  # start after pair 0 (primary position)
        for x, y in points:
            if write_idx + 1 >= len(vals):
                break
            vals[write_idx] = str(x)
            vals[write_idx + 1] = str(y)
            write_idx += 2
        for i in range(write_idx, len(vals)):
            vals[i] = "0"
        rec.values = vals
        rec.raw_line = ""
        self.__set_bend_flag(pipe, 1 if points else 0)

    def add_bend(
        self,
        pipe: BaseElement,
        x: float,
        y: float,
        index: int | None = None,
    ) -> None:
        """Insert a bend waypoint into a pipe's polyline.

        A bend waypoint creates an angular corner in the pipe drawing.
        The most common use-case is converting a straight pipe into an
        L-shape by inserting one corner point between start and end::

            start ──► corner ──► end   (two orthogonal segments)

        To build an orthogonal L-shape from ``(x1, y1)`` to ``(x2, y2)``:

        - horizontal-first corner: ``add_bend(pipe, x2, y1)``
        - vertical-first corner:   ``add_bend(pipe, x1, y2)``

        Args:
            pipe: A PIPE element.
            x: X coordinate of the new waypoint.
            y: Y coordinate of the new waypoint.
            index: Position in the waypoints list to insert at.
                ``None`` (default) inserts *before* the last waypoint so
                the point becomes the corner of a start → corner → end
                L-shape.  Pass ``0`` to prepend or
                ``len(get_polyline(pipe))`` to append.
        """
        points = self.get_polyline(pipe)
        if not points:
            pos = self.get_position(pipe)
            if pos is not None and pos != (0.0, 0.0):
                points = [pos]

        insert_at = max(0, len(points) - 1) if index is None else index
        points.insert(insert_at, (x, y))
        self.set_polyline(pipe, points)

    # ------------------------------------------------------------------
    # Flow connectivity helpers
    # ------------------------------------------------------------------

    def _build_flow_graph(self) -> dict[str, list[str]]:
        """Build a directed element-to-element adjacency from flow connectivity.

        Uses ``CON`` records (equipment outlet pipe) and ``NOZL``/``NOZ``
        records (FEED outgoing pipe) to establish direction.

        Returns:
            Dict mapping each element name to downstream element names.
        """
        from collections import defaultdict

        pipe_to_elems: dict[int, list[str]] = defaultdict(list)
        elem_out_pipe: dict[str, int] = {}

        equip_attrs = (
            "pumps",
            "valves",
            "check_valves",
            "orifices",
            "exchangers",
            "compressors",
            "misc_equipment",
            "expanders",
        )
        for attr in equip_attrs:
            for idx, elem in getattr(self.model, attr, {}).items():
                if idx == 0:
                    continue
                rec = elem.get_param("CON")
                if rec and len(rec.values) >= 2:
                    try:
                        in_p = int(rec.values[0])
                        out_p = int(rec.values[1])
                        if in_p:
                            pipe_to_elems[in_p].append(elem.name)
                        if out_p:
                            pipe_to_elems[out_p].append(elem.name)
                            elem_out_pipe[elem.name] = out_p
                    except (ValueError, TypeError):
                        pass

        for attr in ("feeds", "products"):
            for idx, elem in getattr(self.model, attr, {}).items():
                if idx == 0:
                    continue
                for noz in ("NOZL", "NOZ"):
                    rec = elem.get_param(noz)
                    if rec and rec.values:
                        try:
                            pipe_idx = int(rec.values[0])
                            if pipe_idx:
                                pipe_to_elems[pipe_idx].append(elem.name)
                                if attr == "feeds":
                                    elem_out_pipe[elem.name] = pipe_idx
                        except (ValueError, TypeError):
                            pass
                        break

        graph: dict[str, list[str]] = defaultdict(list)
        for elem_name, out_p in elem_out_pipe.items():
            for other in pipe_to_elems.get(out_p, []):
                if other != elem_name:
                    graph[elem_name].append(other)

        return dict(graph)

    def _assign_flow_levels(self, graph: dict[str, list[str]]) -> dict[str, int]:
        """Assign a column depth to each element via BFS from source nodes.

        Depth is the length of the *longest* path from any source (in-degree 0)
        node, so that elements always appear to the right of all their
        predecessors.

        Returns:
            Dict mapping element name to column index (0 = leftmost).
        """
        from collections import defaultdict, deque

        all_nodes: set[str] = set(graph.keys())
        for dests in graph.values():
            all_nodes.update(dests)

        in_degree: dict[str, int] = defaultdict(int)
        for node in all_nodes:
            in_degree[node] += 0  # ensure every node is present
        for dests in graph.values():
            for d in dests:
                in_degree[d] += 1

        levels: dict[str, int] = {}
        queue: deque[str] = deque()
        for node in all_nodes:
            if in_degree[node] == 0:
                levels[node] = 0
                queue.append(node)

        while queue:
            node = queue.popleft()
            for neighbor in graph.get(node, []):
                new_lvl = levels[node] + 1
                if neighbor not in levels or levels[neighbor] < new_lvl:
                    levels[neighbor] = new_lvl
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return levels

    def _auto_layout_grid(
        self,
        unplaced: list[BaseElement],
        existing: list[tuple[float, float]],
        spacing: float,
    ) -> None:
        """Place elements in a simple square-root grid (default strategy)."""
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

    def _auto_layout_flow(
        self,
        unplaced: list[BaseElement],
        existing: list[tuple[float, float]],
        spacing: float,
    ) -> None:
        """Place elements left-to-right in topological flow order.

        Elements connected to FEEDs are placed in column 0, their
        downstream neighbours in column 1, and so on.  Elements with no
        connectivity are placed in a grid after the flow columns.
        """
        import math
        from collections import defaultdict

        graph = self._build_flow_graph()
        levels = self._assign_flow_levels(graph)

        level_groups: dict[int, list[BaseElement]] = defaultdict(list)
        no_level: list[BaseElement] = []
        for elem in unplaced:
            if elem.name in levels:
                level_groups[levels[elem.name]].append(elem)
            else:
                no_level.append(elem)

        for level in sorted(level_groups.keys()):
            group = level_groups[level]
            x = X_MIN + level * spacing
            for i, elem in enumerate(group):
                y = Y_MIN + i * spacing
                self.set_position(self.model, elem.name, x, y)
                existing.append((x, y))

        if no_level:
            max_level = max(level_groups.keys(), default=-1)
            start_x = X_MIN + (max_level + 2) * spacing
            cols = max(1, int(math.sqrt(len(no_level))))
            for i, elem in enumerate(no_level):
                row = i // cols
                col = i % cols
                x = start_x + col * spacing
                y = Y_MIN + row * spacing
                self.set_position(self.model, elem.name, x, y)
                existing.append((x, y))

    def _get_connected_pairs(self) -> list[tuple[str, str]]:
        """Return connected element pairs via pipe indices.

        Builds a map of pipe index -> elements using that pipe (from CON /
        NOZL / NOZ records) and returns unique pairs of elements that share
        a common pipe.
        """
        from collections import defaultdict

        pipe_to_elems: dict[int, list[str]] = defaultdict(list)

        equip_attrs = (
            "pumps",
            "valves",
            "check_valves",
            "orifices",
            "exchangers",
            "compressors",
            "misc_equipment",
            "expanders",
        )
        for attr in equip_attrs:
            for idx, elem in getattr(self.model, attr, {}).items():
                if idx == 0:
                    continue
                rec = elem.get_param("CON")
                if rec and len(rec.values) >= 2:
                    for raw in rec.values[:2]:
                        try:
                            pipe_idx = int(raw)
                            if pipe_idx:
                                pipe_to_elems[pipe_idx].append(elem.name)
                        except (ValueError, TypeError):
                            pass

        for attr in ("feeds", "products"):
            for idx, elem in getattr(self.model, attr, {}).items():
                if idx == 0:
                    continue
                for noz in ("NOZL", "NOZ"):
                    rec = elem.get_param(noz)
                    if rec and rec.values:
                        try:
                            pipe_idx = int(rec.values[0])
                            if pipe_idx:
                                pipe_to_elems[pipe_idx].append(elem.name)
                        except (ValueError, TypeError):
                            pass
                        break

        pairs: list[tuple[str, str]] = []
        seen: set[frozenset[str]] = set()
        for elems in pipe_to_elems.values():
            if len(elems) == 2:
                key: frozenset[str] = frozenset(elems)
                if key not in seen:
                    seen.add(key)
                    pairs.append((elems[0], elems[1]))
        return pairs

    def snap_orthogonal(self, threshold_deg: float = 10.0) -> None:
        """Snap near-orthogonal connections to be exactly horizontal or vertical.

        For each connected element pair, if the angle between their positions
        deviates less than *threshold_deg* from horizontal (0°) or vertical
        (90°), the second element's Y (horizontal snap) or X (vertical snap)
        is adjusted to make the connection exactly orthogonal.

        Args:
            threshold_deg: Maximum deviation in degrees to trigger snapping.
                Defaults to 10.
        """
        import math

        pairs = self._get_connected_pairs()
        for name1, name2 in pairs:
            try:
                elem1 = self.model.get_element(name1)
                elem2 = self.model.get_element(name2)
            except Exception:
                continue
            pos1 = self.get_position(elem1)
            pos2 = self.get_position(elem2)
            if pos1 is None or pos2 is None:
                continue
            dx = pos2[0] - pos1[0]
            dy = pos2[1] - pos1[1]
            if dx == 0 and dy == 0:
                continue
            # angle_deg in [0, 90]: deviation from the nearest cardinal axis
            angle_deg = math.degrees(math.atan2(abs(dy), abs(dx)))
            if angle_deg < threshold_deg:
                # Almost horizontal — align elem2's Y to elem1's Y
                self.__set_position_on_element(elem2, pos2[0], pos1[1])
            elif angle_deg > (90.0 - threshold_deg):
                # Almost vertical — align elem2's X to elem1's X
                self.__set_position_on_element(elem2, pos1[0], pos2[1])

    # ------------------------------------------------------------------
    # Alignment helpers
    # ------------------------------------------------------------------

    def align_horizontal(self, names: list[str], anchor_y: float | None = None) -> None:
        """Align all named elements to the same Y coordinate.

        Elements are moved vertically so they share a common Y.  If
        *anchor_y* is not given the average Y of the named elements is used.

        Args:
            names: Element names to align.
            anchor_y: Target Y coordinate. Defaults to the mean Y of the group.
        """
        positioned = []
        for name in names:
            try:
                elem = self.model.get_element(name)
            except Exception:
                continue
            pos = self.get_position(elem)
            if pos is not None:
                positioned.append((elem, pos))

        if not positioned:
            return

        target_y = anchor_y if anchor_y is not None else sum(p[1] for _, p in positioned) / len(positioned)
        for elem, pos in positioned:
            self.__set_position_on_element(elem, pos[0], target_y)

    def align_vertical(self, names: list[str], anchor_x: float | None = None) -> None:
        """Align all named elements to the same X coordinate.

        Elements are moved horizontally so they share a common X.  If
        *anchor_x* is not given the average X of the named elements is used.

        Args:
            names: Element names to align.
            anchor_x: Target X coordinate. Defaults to the mean X of the group.
        """
        positioned = []
        for name in names:
            try:
                elem = self.model.get_element(name)
            except Exception:
                continue
            pos = self.get_position(elem)
            if pos is not None:
                positioned.append((elem, pos))

        if not positioned:
            return

        target_x = anchor_x if anchor_x is not None else sum(p[0] for _, p in positioned) / len(positioned)
        for elem, pos in positioned:
            self.__set_position_on_element(elem, target_x, pos[1])

    # ------------------------------------------------------------------
    # Distribution helpers
    # ------------------------------------------------------------------

    def distribute_horizontal(self, names: list[str]) -> None:
        """Space named elements evenly along the X axis.

        The leftmost and rightmost elements stay fixed; everything in between
        is repositioned with equal gaps.  At least three elements are needed
        for the distribution to have any effect.

        Args:
            names: Element names to distribute (order does not matter).
        """
        positioned = []
        for name in names:
            try:
                elem = self.model.get_element(name)
            except Exception:
                continue
            pos = self.get_position(elem)
            if pos is not None:
                positioned.append((elem, pos))

        if len(positioned) < 3:
            return

        positioned.sort(key=lambda ep: ep[1][0])
        x_min = positioned[0][1][0]
        x_max = positioned[-1][1][0]
        step = (x_max - x_min) / (len(positioned) - 1)
        for i, (elem, pos) in enumerate(positioned):
            self.__set_position_on_element(elem, x_min + i * step, pos[1])

    def distribute_vertical(self, names: list[str]) -> None:
        """Space named elements evenly along the Y axis.

        The topmost and bottommost elements stay fixed; everything in between
        is repositioned with equal gaps.  At least three elements are needed
        for the distribution to have any effect.

        Args:
            names: Element names to distribute (order does not matter).
        """
        positioned = []
        for name in names:
            try:
                elem = self.model.get_element(name)
            except Exception:
                continue
            pos = self.get_position(elem)
            if pos is not None:
                positioned.append((elem, pos))

        if len(positioned) < 3:
            return

        positioned.sort(key=lambda ep: ep[1][1])
        y_min = positioned[0][1][1]
        y_max = positioned[-1][1][1]
        step = (y_max - y_min) / (len(positioned) - 1)
        for i, (elem, pos) in enumerate(positioned):
            self.__set_position_on_element(elem, pos[0], y_min + i * step)

    # ------------------------------------------------------------------
    # Grid snapping and centering
    # ------------------------------------------------------------------

    def snap_to_grid(self, grid_size: float = 500.0) -> None:
        """Round every placed element's position to the nearest grid point.

        Args:
            grid_size: Grid cell size in model units. Defaults to 500.
        """
        if grid_size <= 0:
            raise ValueError(f"grid_size must be positive, got {grid_size}")
        for elem in self.model.elements:
            pos = self.get_position(elem)
            if pos is None or pos == (0.0, 0.0):
                continue
            snapped_x = round(pos[0] / grid_size) * grid_size
            snapped_y = round(pos[1] / grid_size) * grid_size
            self.__set_position_on_element(elem, snapped_x, snapped_y)

    def center_layout(self) -> None:
        """Translate all placed elements so the bounding box is centred on the canvas.

        The canvas centre is ``((X_MIN + X_MAX) / 2, (Y_MIN + Y_MAX) / 2)``.
        All elements are shifted by the same offset so that the mid-point of
        their collective bounding box coincides with the canvas centre.
        """
        positioned = [
            (elem, pos)
            for elem in self.model.elements
            for pos in (self.get_position(elem),)
            if pos is not None and pos != (0.0, 0.0)
        ]
        if not positioned:
            return

        xs = [p[0] for _, p in positioned]
        ys = [p[1] for _, p in positioned]
        bbox_cx = (min(xs) + max(xs)) / 2
        bbox_cy = (min(ys) + max(ys)) / 2
        canvas_cx = (X_MIN + X_MAX) / 2
        canvas_cy = (Y_MIN + Y_MAX) / 2
        dx = canvas_cx - bbox_cx
        dy = canvas_cy - bbox_cy
        for elem, pos in positioned:
            self.__set_position_on_element(elem, pos[0] + dx, pos[1] + dy)

    def auto_layout(self, spacing: float | None = None, strategy: str = "grid") -> None:
        """Automatically arrange all unplaced elements.

        Args:
            spacing: Spacing between elements. Defaults to
                :data:`COMFORT_SPACING_X`.
            strategy: Layout algorithm.

                ``"grid"`` (default) - simple rectangular grid.

                ``"flow"`` - topological left-to-right placement ordered by
                element connectivity (FEED → equipment → PROD).
        """
        spacing = spacing or COMFORT_SPACING_X

        unplaced = [
            elem for elem in self.model.elements
            if elem.name and ((p := self.get_position(elem)) is None or p == (0.0, 0.0))
        ]
        if not unplaced:
            return

        existing = [
            pos
            for pos in (self.get_position(e) for e in self.model.elements)
            if pos is not None and pos != (0.0, 0.0)
        ]

        if strategy == "flow":
            self._auto_layout_flow(unplaced, existing, spacing)
        else:
            self._auto_layout_grid(unplaced, existing, spacing)

        self.snap_orthogonal()

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
