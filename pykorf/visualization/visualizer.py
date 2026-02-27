"""Visualizer – PyVis-based interactive network visualization for KORF models.

Generates an interactive HTML file with nodes placed at their scaled XY
coordinates (static layout, no physics) and a ``network_data.json`` for
future Vue.js consumption.

Example::

    from pykorf import Model
    from pykorf.visualization import Visualizer

    model = Model("Cooling Water Circuit.kdf")
    viz = Visualizer(model)
    viz.to_json("network_data.json")
    viz.to_html("network.html")
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from pykorf.definitions import Element
from pykorf.layout import _all_positions, _X_MAX, _X_MIN, _Y_MAX, _Y_MIN
from pykorf.visualization.models import EdgeData, NetworkData, NodeData

if TYPE_CHECKING:
    from pykorf.model import Model

# ---------------------------------------------------------------------------
# Node styling per element type: (shape, color, symbol_char)
# ---------------------------------------------------------------------------
_STYLE: dict[str, dict] = {
    Element.FEED: {"shape": "triangle", "color": "#2ECC71", "symbol": "▶"},
    Element.PROD: {"shape": "triangleDown", "color": "#E74C3C", "symbol": "▼"},
    Element.PUMP: {"shape": "box", "color": "#3498DB", "symbol": "⊳"},
    Element.VALVE: {"shape": "box", "color": "#2980B9", "symbol": "⊠"},
    Element.CHECK: {"shape": "box", "color": "#1ABC9C", "symbol": "⊳"},
    Element.HX: {"shape": "box", "color": "#E67E22", "symbol": "⊞"},
    Element.TEE: {"shape": "diamond", "color": "#9B59B6", "symbol": "◇"},
    Element.JUNC: {"shape": "diamond", "color": "#8E44AD", "symbol": "◆"},
    Element.COMP: {"shape": "box", "color": "#F39C12", "symbol": "⊳"},
    Element.MISC: {"shape": "box", "color": "#95A5A6", "symbol": "□"},
    Element.EXPAND: {"shape": "box", "color": "#D35400", "symbol": "⊲"},
    Element.VESSEL: {"shape": "ellipse", "color": "#16A085", "symbol": "⬭"},
    Element.ORIFICE: {"shape": "box", "color": "#7F8C8D", "symbol": "⊗"},
    Element.PIPE: {"shape": "dot", "color": "#BDC3C7", "symbol": "─"},
}

_DEFAULT_STYLE: dict = {"shape": "dot", "color": "#BDC3C7", "symbol": "·"}

# PyVis canvas size (pixels)
_CANVAS_W = 1200
_CANVAS_H = 700


def _scale_x(x: float) -> float:
    """Scale a KDF X coordinate to PyVis canvas pixels."""
    return (x - _X_MIN) / (_X_MAX - _X_MIN) * _CANVAS_W


def _scale_y(y: float) -> float:
    """Scale a KDF Y coordinate to PyVis canvas pixels."""
    return (y - _Y_MIN) / (_Y_MAX - _Y_MIN) * _CANVAS_H


class Visualizer:
    """Interactive network visualization for a KORF :class:`~pykorf.model.Model`.

    The visualizer extracts nodes and edges from the model, respecting the
    original XY layout.  Nodes are styled by element type and edges
    represent pipe connections.

    Args:
        model: A loaded :class:`~pykorf.model.Model`.
    """

    def __init__(self, model: Model) -> None:
        self._model = model
        self._network_data = self._build_network_data()

    # ------------------------------------------------------------------
    # Data extraction
    # ------------------------------------------------------------------

    def _build_network_data(self) -> NetworkData:
        """Extract nodes and edges from the model."""
        nodes = self._extract_nodes()
        edges = self._extract_edges()
        return NetworkData(nodes=nodes, edges=edges)

    def _extract_nodes(self) -> list[NodeData]:
        """Build the node list from model elements with positions."""
        positions = _all_positions(self._model)
        nodes: list[NodeData] = []
        for elem in self._model.elements:
            pos = positions.get(elem.name)
            if pos is None or pos == (0.0, 0.0):
                continue
            nodes.append(
                NodeData(
                    id=elem.name,
                    label=elem.name,
                    x=_scale_x(pos[0]),
                    y=_scale_y(pos[1]),
                    element_type=elem.etype,
                )
            )
        return nodes

    def _extract_edges(self) -> list[EdgeData]:
        """Build the edge list from pipe connections.

        For each pipe, find the two endpoint elements and create an edge
        between them.  If a pipe has fewer than two endpoints it is
        skipped.
        """
        from pykorf.connectivity import _is_element_connected_to_pipe

        edges: list[EdgeData] = []
        positions = _all_positions(self._model)
        node_ids = {
            name for name, pos in positions.items() if pos != (0.0, 0.0)
        }

        for idx, pipe_elem in self._model.pipes.items():
            if idx == 0:
                continue
            endpoints: list[str] = []
            for elem in self._model.elements:
                if elem.etype == Element.PIPE:
                    continue
                if _is_element_connected_to_pipe(elem, idx):
                    if elem.name in node_ids:
                        endpoints.append(elem.name)
            if len(endpoints) >= 2:
                edges.append(
                    EdgeData(source=endpoints[0], target=endpoints[1])
                )
            elif len(endpoints) == 1:
                # Pipe connected on only one end — still show it
                edges.append(
                    EdgeData(source=endpoints[0], target=endpoints[0])
                )
        return edges

    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------

    @property
    def network_data(self) -> NetworkData:
        """The extracted :class:`NetworkData` (nodes + edges)."""
        return self._network_data

    # ------------------------------------------------------------------
    # JSON export
    # ------------------------------------------------------------------

    def to_json(self, path: str | Path) -> None:
        """Write the network data to a JSON file.

        The JSON contains ``"nodes"`` and ``"edges"`` arrays ready
        for consumption by vue-vis-network or other front-end frameworks.

        Args:
            path: Output file path (e.g. ``"network_data.json"``).
        """
        data = self._network_data.model_dump()
        Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")

    # ------------------------------------------------------------------
    # HTML export (PyVis)
    # ------------------------------------------------------------------

    def to_html(self, path: str | Path = "network.html") -> None:
        """Generate an interactive HTML visualization using PyVis.

        The layout uses the exact scaled XY coordinates from the KDF
        file with the physics engine disabled.

        Args:
            path: Output HTML file path.
        """
        try:
            from pyvis.network import Network
        except ImportError as exc:
            raise ImportError(
                "pyvis is required for HTML visualization. "
                "Install it with: pip install pyvis"
            ) from exc

        net = Network(
            height=f"{_CANVAS_H}px",
            width=f"{_CANVAS_W}px",
            directed=True,
            notebook=False,
        )
        net.toggle_physics(False)

        # Add nodes
        for node in self._network_data.nodes:
            style = _STYLE.get(node.element_type, _DEFAULT_STYLE)
            net.add_node(
                node.id,
                label=node.label,
                x=node.x,
                y=node.y,
                shape=style["shape"],
                color=style["color"],
                title=f"{node.element_type}: {node.label}",
                size=20,
                fixed=True,
            )

        # Add edges
        for edge in self._network_data.edges:
            if edge.source != edge.target:
                net.add_edge(edge.source, edge.target)

        net.write_html(str(path))
