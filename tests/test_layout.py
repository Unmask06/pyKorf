"""Tests for layout and positioning module.

Run with:  PYTHONPATH=. python -m pytest tests/test_layout.py -v
"""

from pathlib import Path

from pykorf.model import Model

SAMPLES_DIR = Path(__file__).parent.parent / "pykorf" / "library"
PUMP_KDF = SAMPLES_DIR / "Pumpcases.kdf"
CWC_KDF = SAMPLES_DIR / "Cooling Water Circuit.kdf"


class TestGetSetPosition:
    def test_get_position(self):
        m = Model(PUMP_KDF)
        pipe = m.pipes[1]
        pos = m.get_position(pipe)
        # Pipe should have some XY position (may be tuple or None)
        # Just check it doesn't crash
        assert pos is None or isinstance(pos, tuple)

    def test_set_position(self):
        m = Model(PUMP_KDF)
        pipe = m.pipes[1]
        m.set_position(pipe, 500.0, 300.0)
        pos = m.get_position(pipe)
        if pos is not None:
            assert pos == (500.0, 300.0)

    def test_set_position_by_name(self):
        m = Model(PUMP_KDF)
        m.set_position("L1", 700.0, 450.0)
        pos = m.get_position(m["L1"])
        if pos is not None:
            assert pos == (700.0, 450.0)


class TestCheckLayout:
    def test_check_layout_returns_list(self):
        m = Model(PUMP_KDF)
        issues = m.check_layout()
        assert isinstance(issues, list)

    def test_check_layout_cwc(self):
        m = Model(CWC_KDF)
        issues = m.check_layout()
        assert isinstance(issues, list)

    def test_model_check_layout(self):
        m = Model(PUMP_KDF)
        issues = m.check_layout()
        assert isinstance(issues, list)


class TestAutoPlace:
    def test_auto_place_new_element(self):
        m = Model(PUMP_KDF)
        new_pump = m.add_element("PUMP", "P_AP")
        m.auto_place(new_pump)
        pos = m.get_position(new_pump)
        # Should have been placed somewhere
        if pos is not None:
            assert pos != (0.0, 0.0)


class TestSnapOrthogonal:
    def test_snap_orthogonal_does_not_crash(self):
        m = Model(PUMP_KDF)
        m.snap_orthogonal()  # should not raise

    def test_snap_orthogonal_cwc(self):
        m = Model(CWC_KDF)
        m.snap_orthogonal()  # smoke test on more complex model

    def test_snap_orthogonal_custom_threshold(self):
        m = Model(PUMP_KDF)
        m.snap_orthogonal(threshold_deg=5.0)  # narrower threshold, should not raise

    def test_snap_orthogonal_positions_remain_valid(self):
        m = Model(CWC_KDF)
        m.snap_orthogonal()
        for elem in m.elements:
            pos = m.get_position(elem)
            if pos is not None:
                assert isinstance(pos[0], float)
                assert isinstance(pos[1], float)


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
