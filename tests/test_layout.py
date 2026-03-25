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


class TestAlignElements:
    def test_align_horizontal_smoke(self):
        m = Model(CWC_KDF)
        names = [e.name for e in m.elements if m.get_position(e) is not None][:4]
        m.align_horizontal(names)
        ys = {m.get_position(m[n])[1] for n in names if m.get_position(m[n]) is not None}
        assert len(ys) == 1

    def test_align_horizontal_anchor(self):
        m = Model(CWC_KDF)
        names = [e.name for e in m.elements if m.get_position(e) is not None][:3]
        m.align_horizontal(names, anchor_y=3000.0)
        for n in names:
            pos = m.get_position(m[n])
            if pos is not None:
                assert pos[1] == 3000.0

    def test_align_vertical_smoke(self):
        m = Model(CWC_KDF)
        names = [e.name for e in m.elements if m.get_position(e) is not None][:4]
        m.align_vertical(names)
        xs = {m.get_position(m[n])[0] for n in names if m.get_position(m[n]) is not None}
        assert len(xs) == 1

    def test_align_vertical_anchor(self):
        m = Model(CWC_KDF)
        names = [e.name for e in m.elements if m.get_position(e) is not None][:3]
        m.align_vertical(names, anchor_x=5000.0)
        for n in names:
            pos = m.get_position(m[n])
            if pos is not None:
                assert pos[0] == 5000.0

    def test_align_empty_list_no_crash(self):
        m = Model(PUMP_KDF)
        m.align_horizontal([])
        m.align_vertical([])


class TestDistributeElements:
    def test_distribute_horizontal_even_spacing(self):
        m = Model(CWC_KDF)
        positioned = [e for e in m.elements if m.get_position(e) is not None]
        if len(positioned) < 3:
            return
        names = [e.name for e in positioned[:5]]
        m.distribute_horizontal(names)
        xs = sorted(m.get_position(m[n])[0] for n in names if m.get_position(m[n]))
        gaps = [xs[i + 1] - xs[i] for i in range(len(xs) - 1)]
        assert all(abs(g - gaps[0]) < 0.01 for g in gaps)

    def test_distribute_vertical_even_spacing(self):
        m = Model(CWC_KDF)
        positioned = [e for e in m.elements if m.get_position(e) is not None]
        if len(positioned) < 3:
            return
        names = [e.name for e in positioned[:5]]
        m.distribute_vertical(names)
        ys = sorted(m.get_position(m[n])[1] for n in names if m.get_position(m[n]))
        gaps = [ys[i + 1] - ys[i] for i in range(len(ys) - 1)]
        assert all(abs(g - gaps[0]) < 0.01 for g in gaps)

    def test_distribute_two_elements_no_change(self):
        m = Model(PUMP_KDF)
        positioned = [e for e in m.elements if m.get_position(e) is not None]
        names = [e.name for e in positioned[:2]]
        before = [m.get_position(m[n]) for n in names]
        m.distribute_horizontal(names)
        after = [m.get_position(m[n]) for n in names]
        assert before == after


class TestSnapToGrid:
    def test_snap_to_grid_smoke(self):
        m = Model(CWC_KDF)
        m.snap_to_grid(500.0)
        for elem in m.elements:
            pos = m.get_position(elem)
            if pos is not None and pos != (0.0, 0.0):
                assert pos[0] % 500.0 == 0.0
                assert pos[1] % 500.0 == 0.0

    def test_snap_to_grid_invalid(self):
        m = Model(PUMP_KDF)
        import pytest
        with pytest.raises(ValueError):
            m.snap_to_grid(0)


class TestCenterLayout:
    def test_center_layout_smoke(self):
        m = Model(CWC_KDF)
        m.center_layout()
        positioned = [m.get_position(e) for e in m.elements if m.get_position(e) is not None and m.get_position(e) != (0.0, 0.0)]
        if not positioned:
            return
        xs = [p[0] for p in positioned]
        ys = [p[1] for p in positioned]
        from pykorf.model.services.layout import X_MAX, X_MIN, Y_MAX, Y_MIN
        canvas_cx = (X_MIN + X_MAX) / 2
        canvas_cy = (Y_MIN + Y_MAX) / 2
        bbox_cx = (min(xs) + max(xs)) / 2
        bbox_cy = (min(ys) + max(ys)) / 2
        assert abs(bbox_cx - canvas_cx) < 1.0
        assert abs(bbox_cy - canvas_cy) < 1.0

    def test_center_layout_pump(self):
        m = Model(PUMP_KDF)
        m.center_layout()  # should not raise


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
