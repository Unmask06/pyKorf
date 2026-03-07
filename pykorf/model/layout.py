"""Layout-related functionality for KORF models.

This module provides the :class:`LayoutMixin` which adds layout and visualization
capabilities to a model class. It assumes the following attributes exist in the
class that uses this mixin:

- ``self.elements``: Property returning list of all element instances
- ``self._parser``: KdfParser instance (for path access)
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class LayoutMixin:
    """Mixin providing layout and visualization functionality.

    This mixin assumes the host class provides:
    - ``elements``: Property returning list of all element instances
    - ``_parser``: KdfParser instance
    """

    def check_layout(self) -> list[str]:
        """Check for element position clashes.

        Returns a list of issue descriptions (empty = no clashes).
        """
        from pykorf.layout import check_layout

        return check_layout(self)  # type: ignore[arg-type]

    def visualize(self, **kwargs) -> str:
        """Create a text visualization of elements and connections.

        Returns:
        -------
        A multi-line string with element positions.
        """
        from pykorf.layout import visualize

        return visualize(self, **kwargs)  # type: ignore[arg-type]

    def auto_layout(self, spacing: float | None = None) -> None:
        """Automatically arrange all unplaced elements in a logical flow.

        Places elements that are at position (0, 0) in a grid pattern,
        preserving the positions of already-placed elements.

        Parameters
        ----------
        spacing:
            Grid spacing in drawing units. Default is 1500.

        Example:
        -------
        ```python
        model.auto_layout()  # Arrange all unplaced elements
        ```
        """
        from pykorf.layout import (
            COMFORT_SPACING_X,
            X_MIN,
            Y_MIN,
            get_position,
            set_position,
        )

        spacing = spacing or COMFORT_SPACING_X

        unplaced = []
        for elem in self.elements:  # type: ignore[attr-defined]
            pos = get_position(elem)
            if pos is None or pos == (0.0, 0.0):
                unplaced.append(elem)

        if not unplaced:
            return

        existing = [
            pos
            for pos in (get_position(e) for e in self.elements)  # type: ignore[attr-defined]
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

            set_position(self, elem.name, x, y)  # type: ignore[arg-type]
            existing.append((x, y))

    def visualize_network(self, path: str | Path = "network.html") -> None:
        """Generate an interactive PyVis HTML visualization.

        Requires ``pyvis`` and ``pydantic`` to be installed.

        Args:
            path: Output HTML file path.
        """
        from pykorf.visualization import Visualizer

        viz = Visualizer(self)  # type: ignore[arg-type]
        viz.to_html(path)
