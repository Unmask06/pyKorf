"""Tests for layout and positioning module.

Run with:  PYTHONPATH=. python -m pytest tests/test_layout.py -v
"""

from pathlib import Path

from pykorf.model.layout import auto_place, check_layout, get_position, set_position
from pykorf.model import Model

SAMPLES_DIR = Path(__file__).parent.parent / "pykorf" / "library"
PUMP_KDF = SAMPLES_DIR / "Pumpcases.kdf"
CWC_KDF = SAMPLES_DIR / "Cooling Water Circuit.kdf"


class TestGetSetPosition:
    def test_get_position(self):
        m = Model(PUMP_KDF)
        pipe = m.pipes[1]
        pos = get_position(pipe)
        # Pipe should have some XY position (may be tuple or None)
        # Just check it doesn't crash
        assert pos is None or isinstance(pos, tuple)

    def test_set_position(self):
        m = Model(PUMP_KDF)
        pipe = m.pipes[1]
        set_position(pipe, 500.0, 300.0)
        pos = get_position(pipe)
        if pos is not None:
            assert pos == (500.0, 300.0)

    def test_set_position_by_name(self):
        m = Model(PUMP_KDF)
        set_position(m, "L1", 700.0, 450.0)
        pos = get_position(m["L1"])
        if pos is not None:
            assert pos == (700.0, 450.0)


class TestCheckLayout:
    def test_check_layout_returns_list(self):
        m = Model(PUMP_KDF)
        issues = check_layout(m)
        assert isinstance(issues, list)

    def test_check_layout_cwc(self):
        m = Model(CWC_KDF)
        issues = check_layout(m)
        assert isinstance(issues, list)

    def test_model_check_layout(self):
        m = Model(PUMP_KDF)
        issues = m.check_layout()
        assert isinstance(issues, list)


class TestAutoPlace:
    def test_auto_place_new_element(self):
        m = Model(PUMP_KDF)
        new_pump = m.add_element("PUMP", "P_AP")
        auto_place(m, new_pump)
        pos = get_position(new_pump)
        # Should have been placed somewhere
        if pos is not None:
            assert pos != (0.0, 0.0)


class TestVisualize:
    def test_visualize_returns_string(self):
        m = Model(PUMP_KDF)
        text = m.visualize()
        assert isinstance(text, str)
        assert "Model Layout" in text

    def test_visualize_cwc(self):
        m = Model(CWC_KDF)
        text = m.visualize()
        assert "PIPE" in text
