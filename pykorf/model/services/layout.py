"""Layout and positioning service for KORF models.

Handles element positions (XY records), auto-placement of new elements,
clash detection, alignment, and orthogonal pipe routing.

XY Record Format
----------------
Each element has an ``XY`` parameter with values like::

    [x1, y1, x2, y2, ...]

For most elements, ``(x1, y1)`` is the primary position.  Pipes may have
multiple coordinate pairs forming a polyline.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from pykorf.exceptions import LayoutError

if TYPE_CHECKING:
    from pykorf.elements.base import BaseElement
    from pykorf.model import Model

GRID_SIZE = 100.0
MIN_SPACING = GRID_SIZE * 10
COMFORT_SPACING_X = GRID_SIZE * 15
COMFORT_SPACING_Y = GRID_SIZE * 15

_PAGE_BOUNDARIES: dict[str, tuple[float, float, float, float]] = {
    "A4": (1000.0, 1000.0, 15500.0, 9000.0),
    "A3": (1000.0, 1000.0, 22500.0, 13000.0),
}
_DEFAULT_PAGE = "A4"


@dataclass(frozen=True, slots=True)
class LayoutService:
    """Service for managing element layout and positioning in KORF models.

    Provides functionality for:
    - Getting and setting element positions
    - Auto-placement of elements
    - Layout validation and clash detection
    - Alignment, distribution, grid snapping, and centering
    - Pipe polyline (waypoint) management and orthogonal routing

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

    def _apply_position(self, elem: BaseElement, x: float, y: float) -> None:
        """Apply position to element's XY parameter."""
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
        target: str | BaseElement,
        x: float,
        y: float,
    ) -> None:
        """Set the primary (x, y) position.

        Can be called in two ways:
        - set_position(element, x, y)
        - set_position(name, x, y)
        """
        # Case 1: set_position(name, x, y)
        if isinstance(target, str):
            self._apply_position(self.model.get_element(target), float(x), float(y))
            return

        # Case 2: set_position(element, x, y)
        self._apply_position(cast("BaseElement", target), float(x), float(y))

    def __all_positions(self) -> dict[str, tuple[float, float]]:
        """Collect all element positions as ``{name: (x, y)}``."""
        positions: dict[str, tuple[float, float]] = {}
        for elem in self.model.elements:
            pos = self.get_position(elem)
            if pos is not None:
                positions[elem.name] = pos
        return positions

    @property
    def page_size(self) -> str:
        """Detected page size from GEN.DWGSTD (e.g. ``'A4'`` or ``'A3'``).

        Falls back to ``'A4'`` when the record is missing or unrecognised.
        """
        rec = self.model.general.get_param("DWGSTD")
        page_str = (rec.values[0] if rec and rec.values else "") or ""
        for key in _PAGE_BOUNDARIES:
            if key in page_str:
                return key
        return _DEFAULT_PAGE

    @property
    def boundary_coordinates(self) -> tuple[float, float, float, float]:
        """Return ``(x_min, y_min, x_max, y_max)`` for the model's page size."""
        return _PAGE_BOUNDARIES[self.page_size]

    def check_layout(self) -> list[str]:
        """Check for overlapping element positions."""
        x_min, y_min, x_max, y_max = self.boundary_coordinates
        issues: list[str] = []
        positions = self.__all_positions()

        placed: list[tuple[str, float, float]] = []

        pos_map: dict[tuple[float, float], list[str]] = {}
        for name, pos in positions.items():
            if pos == (0.0, 0.0):
                continue
            x, y = float(pos[0]), float(pos[1])
            placed.append((name, x, y))

            if not (x_min <= x <= x_max and y_min <= y <= y_max):
                issues.append(
                    f"Element {name} at ({x:.1f}, {y:.1f}) is outside layout bounds "
                    f"[{x_min:.0f},{y_min:.0f}]-[{x_max:.0f},{y_max:.0f}]"
                )

            if round(x) % int(GRID_SIZE) != 0 or round(y) % int(GRID_SIZE) != 0:
                issues.append(
                    f"Element {name} at ({x:.1f}, {y:.1f}) is not aligned to "
                    f"{GRID_SIZE:.0f}-unit grid"
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
        """Automatically place *elem* at the first non-overlapping grid position.

        Scans a comfort-spacing grid within the page boundary and places the
        element at the first candidate that respects :data:`MIN_SPACING` from
        every already-placed element.

        Args:
            elem: Element to position.

        Raises:
            LayoutError: When no valid position can be found.
        """
        x_min, y_min, x_max, y_max = self.boundary_coordinates
        existing = []
        for name, pos in self.__all_positions().items():
            if name == elem.name or pos == (0.0, 0.0):
                continue
            existing.append((float(pos[0]), float(pos[1])))

        def _fits(candidate: tuple[float, float]) -> bool:
            cx, cy = candidate
            if not (x_min <= cx <= x_max and y_min <= cy <= y_max):
                return False
            for ex, ey in existing:
                dx = cx - ex
                dy = cy - ey
                if (dx * dx + dy * dy) ** 0.5 < MIN_SPACING:
                    return False
            return True

        cols = int((x_max - x_min) // COMFORT_SPACING_X) + 1
        rows = int((y_max - y_min) // COMFORT_SPACING_Y) + 1
        for row in range(rows):
            for col in range(cols):
                candidate = (
                    x_min + col * COMFORT_SPACING_X,
                    y_min + row * COMFORT_SPACING_Y,
                )
                if _fits(candidate):
                    self._apply_position(elem, candidate[0], candidate[1])
                    return

        raise LayoutError(
            f"No available layout position within bounds "
            f"[{x_min:.0f},{y_min:.0f}]-[{x_max:.0f},{y_max:.0f}] "
            f"with minimum spacing {MIN_SPACING:.0f}."
        )

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

        pairs = self.model.connectivity.get_connected_pairs()
        for name1, name2 in pairs:
            try:
                elem1 = self.model.get_element(name1)
                elem2 = self.model.get_element(name2)
            except KeyError:
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
                self._apply_position(elem2, pos2[0], pos1[1])
            elif angle_deg > (90.0 - threshold_deg):
                # Almost vertical — align elem2's X to elem1's X
                self._apply_position(elem2, pos1[0], pos2[1])

    # ------------------------------------------------------------------
    # Orthogonal pipe routing
    # ------------------------------------------------------------------

    def route_pipe(self, pipe: BaseElement, bend: str = "auto") -> None:
        """Route a single pipe as an orthogonal polyline between its endpoints.

        Looks up the two elements connected by *pipe*, reads their positions,
        and writes a 2- or 3-point polyline:

        - Straight line (2 points) when the connection is already horizontal
          or vertical.
        - L-shape (3 points) otherwise, with one 90-degree corner.

        The corner direction is controlled by *bend*:

        - ``"h"`` - horizontal-first: ``start -> (x_end, y_start) -> end``
        - ``"v"`` - vertical-first:   ``start -> (x_start, y_end) -> end``
        - ``"auto"`` (default) - horizontal-first when ``|dx| >= |dy|``,
          vertical-first otherwise.

        Args:
            pipe: A PIPE element to route.
            bend: Corner direction. One of ``"h"``, ``"v"``, or ``"auto"``.
        """
        pipe_to_elems = self.model.connectivity.get_pipe_to_elems()
        endpoint_names = pipe_to_elems.get(pipe.index, [])
        if len(endpoint_names) != 2:
            return

        try:
            elem1 = self.model.get_element(endpoint_names[0])
            elem2 = self.model.get_element(endpoint_names[1])
        except Exception:
            return

        pos1 = self.get_position(elem1)
        pos2 = self.get_position(elem2)
        if pos1 is None or pos2 is None:
            return

        x1, y1 = pos1
        x2, y2 = pos2
        dx = x2 - x1
        dy = y2 - y1

        if dx == 0.0 or dy == 0.0:
            # Already orthogonal — straight two-point line
            points: list[tuple[float, float]] = [(x1, y1), (x2, y2)]
        else:
            if bend == "auto":
                effective = "h" if abs(dx) >= abs(dy) else "v"
            else:
                effective = bend

            if effective == "h":
                # Horizontal first: travel along X to align, then along Y
                points = [(x1, y1), (x2, y1), (x2, y2)]
            else:
                # Vertical first: travel along Y to align, then along X
                points = [(x1, y1), (x1, y2), (x2, y2)]

        # Update the pipe's primary position (icon anchor) to the start point
        self._apply_position(pipe, x1, y1)
        self.set_polyline(pipe, points)

    def route_all_pipes(self, bend: str = "auto") -> None:
        """Route every pipe with two connected elements as an orthogonal polyline.

        Iterates over all non-template pipes in the model and calls
        :meth:`route_pipe` on each one that connects exactly two elements.
        Pipes with zero or one connected element (stubs) are silently skipped.

        Args:
            bend: Corner direction applied to all pipes.
                ``"h"`` - horizontal-first, ``"v"`` - vertical-first,
                ``"auto"`` (default) - chosen per-pipe by dominant displacement.
        """
        for idx, pipe in self.model.pipes.items():
            if idx == 0 or not pipe.name:
                continue
            self.route_pipe(pipe, bend)

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

        target_y = (
            anchor_y if anchor_y is not None else sum(p[1] for _, p in positioned) / len(positioned)
        )
        for elem, pos in positioned:
            self._apply_position(elem, pos[0], target_y)

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

        target_x = (
            anchor_x if anchor_x is not None else sum(p[0] for _, p in positioned) / len(positioned)
        )
        for elem, pos in positioned:
            self._apply_position(elem, target_x, pos[1])

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
            self._apply_position(elem, x_min + i * step, pos[1])

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
            self._apply_position(elem, pos[0], y_min + i * step)

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
            self._apply_position(elem, snapped_x, snapped_y)

    def center_layout(self) -> None:
        """Translate all placed elements so the bounding box is centred on the page boundary.

        All elements are shifted by the same offset so that the mid-point of
        their collective bounding box coincides with the centre of the detected
        page boundary (A4 or A3 as read from ``GEN.DWGSTD``).
        """
        positioned = [
            (elem, pos)
            for elem in self.model.elements
            for pos in (self.get_position(elem),)
            if pos is not None and pos != (0.0, 0.0)
        ]
        if not positioned:
            return

        x_min, y_min, x_max, y_max = self.boundary_coordinates
        xs = [p[0] for _, p in positioned]
        ys = [p[1] for _, p in positioned]
        bbox_cx = (min(xs) + max(xs)) / 2
        bbox_cy = (min(ys) + max(ys)) / 2
        page_cx = (x_min + x_max) / 2
        page_cy = (y_min + y_max) / 2
        dx = page_cx - bbox_cx
        dy = page_cy - bbox_cy
        for elem, pos in positioned:
            self._apply_position(elem, pos[0] + dx, pos[1] + dy)

    def _symbol_in_top_margin(self, margin_height: float = 500.0) -> bool:
        """Check if any symbol exists in the top margin area.

        The top margin is defined as the absolute region from y=0 to y=margin_height,
        spanning the full page width. This area is typically above the drawing boundary.

        Args:
            margin_height: Height of the top margin from y=0. Defaults to 500.

        Returns:
            True if at least one symbol exists in the top margin, False otherwise.
        """
        x_min, y_min, x_max, y_max = self.boundary_coordinates

        for rec in self.model._parser.records:
            if rec.element_type != "SYMBOL" or rec.index is None:
                continue

            xy_rec = self.model._parser.get("SYMBOL", rec.index, "XY")
            if xy_rec is None or len(xy_rec.values) < 2:
                continue

            try:
                x = float(xy_rec.values[0])
                y = float(xy_rec.values[1])
            except (ValueError, TypeError):
                continue

            if x_min <= x <= x_max and 0 <= y <= margin_height:
                return True

        return False

    def ensure_title(
        self,
        title_text: str | None = None,
        margin_height: float = 500.0,
        color: str = "16711680",  # blue
        font_size: int = 2,
    ) -> None:
        """Ensure a title symbol exists in the top margin area.

        If no symbol is present in the top margin (region from y=0 to y=margin_height),
        creates a new title symbol with the specified text and positions it at:
        - X: 200
        - Y: center of page width (margin_height / 2)

        Args:
            title_text: Title text to display. If None, uses the model filename
                (without .kdf extension) as the title.
            margin_height: Height of the top margin from y=0. Defaults to 500.
            color: Color code for the title text. Defaults to blue.
            font_size: Font size for the title. Defaults to 2.

        Example:
            ```python
            model.layout.ensure_title("My Process Model")
            model.layout.ensure_title()
            ```
        """
        if self._symbol_in_top_margin(margin_height):
            return

        if title_text is None:
            title_text = self.model.path.stem

        from pykorf.elements import Symbol
        from pykorf.parser import KdfParser

        template_parser: KdfParser | None = None
        if self.model._parser.num_instances(Symbol.ETYPE) == 0:
            from pathlib import Path

            template_path = Path(__file__).resolve().parent.parent.parent / "library" / "New.kdf"
            template_parser = KdfParser(template_path)
            template_parser.load()

        new_idx = self.model._parser.next_index(Symbol.ETYPE)

        if template_parser is not None:
            source_records = template_parser.get_all(Symbol.ETYPE, 0)
        else:
            source_records = self.model._parser.get_all(Symbol.ETYPE, 0)

        for rec in source_records:
            if rec.param == "NUM":
                continue

            clone = rec
            if template_parser is not None:
                from pykorf.parser import KdfRecord

                clone = KdfRecord(
                    element_type=Symbol.ETYPE,
                    index=new_idx,
                    param=rec.param,
                    values=list(rec.values),
                    raw_line="",
                )
            else:
                clone.index = new_idx
                clone.raw_line = ""

            if rec.param == Symbol.TYPE:
                clone.values = ["Text"]
            elif rec.param == Symbol.TEXT:
                clone.values = [title_text]
            elif rec.param == Symbol.FSIZ:
                clone.values = [str(font_size)]
            elif rec.param == Symbol.COLOR:
                clone.values = [color]
            elif rec.param == Symbol.XY:
                x_min, y_min, x_max, y_max = self.boundary_coordinates
                clone.values = [str(x_min + 200.0), str(200.0), "0", "0"]

            self.model._parser.insert_records([clone])

        current_count = self.model._parser.num_instances(Symbol.ETYPE)
        self.model._parser.set_num_instances(Symbol.ETYPE, current_count + 1)

        self.model._build_collections()


__all__ = [
    "COMFORT_SPACING_X",
    "COMFORT_SPACING_Y",
    "GRID_SIZE",
    "MIN_SPACING",
    "LayoutService",
]
