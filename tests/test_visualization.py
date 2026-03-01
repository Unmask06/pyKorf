"""Tests for the visualization module.

Run with:  set PYTHONPATH=. && python -m pytest tests/test_visualization.py -v
"""

import json
import os
from pathlib import Path

import pytest

from pykorf.model import Model
from pykorf.visualization import Visualizer
from pykorf.visualization.models import EdgeData, NetworkData, NodeData

SAMPLES_DIR = Path(__file__).parent.parent / "pykorf" / "library"
CWC_KDF = SAMPLES_DIR / "Cooling Water Circuit.kdf"
PUMP_KDF = SAMPLES_DIR / "Pumpcases.kdf"
TRAIL_KDF = (
    Path(__file__).parent.parent
    / "pykorf"
    / "trail_files"
    / "Cooling Water Circuit-EES-IT-LT-00141.kdf"
)


class TestNodeData:
    def test_create(self):
        node = NodeData(
            id="P1", label="P1", x=100.0, y=200.0, element_type="PUMP"
        )
        assert node.id == "P1"
        assert node.element_type == "PUMP"

    def test_serialization(self):
        node = NodeData(
            id="L1", label="L1", x=50.0, y=75.0, element_type="PIPE"
        )
        data = node.model_dump()
        assert data["id"] == "L1"
        assert data["x"] == 50.0


class TestEdgeData:
    def test_create(self):
        edge = EdgeData(source="F1", target="L1")
        assert edge.source == "F1"
        assert edge.target == "L1"


class TestNetworkData:
    def test_create(self):
        nd = NetworkData(
            nodes=[
                NodeData(id="A", label="A", x=0, y=0, element_type="FEED"),
            ],
            edges=[EdgeData(source="A", target="B")],
        )
        assert len(nd.nodes) == 1
        assert len(nd.edges) == 1

    def test_json_round_trip(self):
        nd = NetworkData(
            nodes=[
                NodeData(id="X", label="X", x=1.5, y=2.5, element_type="PUMP"),
            ],
            edges=[],
        )
        text = nd.model_dump_json()
        restored = NetworkData.model_validate_json(text)
        assert restored.nodes[0].id == "X"


class TestVisualizer:
    def test_network_data_cwc(self):
        m = Model(CWC_KDF)
        viz = Visualizer(m)
        nd = viz.network_data
        assert isinstance(nd, NetworkData)
        assert len(nd.nodes) > 0
        assert len(nd.edges) > 0

    def test_network_data_pump(self):
        m = Model(PUMP_KDF)
        viz = Visualizer(m)
        nd = viz.network_data
        assert isinstance(nd, NetworkData)
        assert len(nd.nodes) > 0

    def test_node_types_present(self):
        m = Model(CWC_KDF)
        viz = Visualizer(m)
        types = {n.element_type for n in viz.network_data.nodes}
        # CWC has FEED, PROD, PUMP, HX, TEE
        assert "FEED" in types
        assert "PROD" in types

    def test_nodes_have_scaled_coordinates(self):
        m = Model(CWC_KDF)
        viz = Visualizer(m)
        for node in viz.network_data.nodes:
            assert isinstance(node.x, float)
            assert isinstance(node.y, float)

    def test_to_json(self, tmp_path):
        m = Model(CWC_KDF)
        viz = Visualizer(m)
        out = tmp_path / "network_data.json"
        viz.to_json(out)
        assert out.exists()
        data = json.loads(out.read_text(encoding="utf-8"))
        assert "nodes" in data
        assert "edges" in data
        assert len(data["nodes"]) > 0

    def test_json_node_structure(self, tmp_path):
        m = Model(CWC_KDF)
        viz = Visualizer(m)
        out = tmp_path / "network_data.json"
        viz.to_json(out)
        data = json.loads(out.read_text(encoding="utf-8"))
        node = data["nodes"][0]
        assert "id" in node
        assert "label" in node
        assert "x" in node
        assert "y" in node
        assert "element_type" in node

    def test_json_edge_structure(self, tmp_path):
        m = Model(CWC_KDF)
        viz = Visualizer(m)
        out = tmp_path / "network_data.json"
        viz.to_json(out)
        data = json.loads(out.read_text(encoding="utf-8"))
        if data["edges"]:
            edge = data["edges"][0]
            assert "source" in edge
            assert "target" in edge

    def test_to_html(self, tmp_path):
        m = Model(CWC_KDF)
        viz = Visualizer(m)
        out = tmp_path / "network.html"
        viz.to_html(out)
        assert out.exists()
        content = out.read_text(encoding="utf-8")
        assert "<html>" in content.lower()

    def test_to_html_pump(self, tmp_path):
        m = Model(PUMP_KDF)
        viz = Visualizer(m)
        out = tmp_path / "network.html"
        viz.to_html(out)
        assert out.exists()
        assert out.stat().st_size > 0

    def test_trail_hx_edges_present(self):
        m = Model(TRAIL_KDF)
        viz = Visualizer(m)
        edge_pairs = {(edge.source, edge.target) for edge in viz.network_data.edges}
        assert any("HP-001" in pair for pair in edge_pairs)

    def test_to_html_includes_layout_boundary_and_legend(self, tmp_path):
        m = Model(CWC_KDF)
        viz = Visualizer(m)
        out = tmp_path / "network.html"
        viz.to_html(out)
        content = out.read_text(encoding="utf-8")
        assert "__layout_tl" in content
        assert "pykorf-legend" in content


class TestModelConvenience:
    def test_visualize_network(self, tmp_path):
        m = Model(CWC_KDF)
        out = tmp_path / "test_model.html"
        m.visualize_network(out)
        assert out.exists()
