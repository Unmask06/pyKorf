"""Pydantic models for KORF network visualization data.

These models structure the node/edge data extracted from a
:class:`~pykorf.model.Model` so it can be serialized to JSON
(for future Vue.js consumption) or fed directly into PyVis.
"""

from __future__ import annotations

from pydantic import BaseModel


class NodeData(BaseModel):
    """A single node in the network graph.

    Attributes:
        id: Unique element name.
        label: Display label (element name).
        x: Scaled X coordinate.
        y: Scaled Y coordinate.
        element_type: KDF element type keyword (e.g. ``"PIPE"``, ``"PUMP"``).
    """

    id: str
    label: str
    x: float
    y: float
    element_type: str


class EdgeData(BaseModel):
    """A single edge in the network graph.

    Attributes:
        source: Name of the source node.
        target: Name of the target node.
    """

    source: str
    target: str


class NetworkData(BaseModel):
    """Complete network graph data for serialization.

    Attributes:
        nodes: List of network nodes.
        edges: List of network edges.
    """

    nodes: list[NodeData]
    edges: list[EdgeData]
