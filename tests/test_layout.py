"""Tests for layout and positioning module.

Run with:  PYTHONPATH=. python -m pytest tests/test_layout.py -v
"""

from pathlib import Path

from pykorf.model import Model

SAMPLES_DIR = Path(__file__).parent.parent / "pykorf" / "library"
PUMP_KDF = SAMPLES_DIR / "Pumpcases.kdf"
CWC_KDF = SAMPLES_DIR / "Cooling Water Circuit.kdf"


# ---------------------------------------------------------------------------
# Core shortcuts that live directly on Model (pre-existing API)
# ---------------------------------------------------------------------------


class TestGetSetPosition:
    def test_get_position(self):
        m = Model(PUMP_KDF)
        pipe = m.pipes[1]
        pos = m.get_position(pipe)
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


# ---------------------------------------------------------------------------
# LayoutService — accessed via model.layout
# ---------------------------------------------------------------------------


class TestPolyline:
    def test_get_polyline_pipe_with_bends(self):
        m = Model(CWC_KDF)
        pipe = m.pipes[1]
        pts = m.layout.get_polyline(pipe)
        assert isinstance(pts, list)
        assert len(pts) >= 1
        for x, y in pts:
            assert isinstance(x, float)
            assert isinstance(y, float)

    def test_get_polyline_no_waypoints(self):
        m = Model(PUMP_KDF)
        pipe = m.pipes[1]
        pts = m.layout.get_polyline(pipe)
        assert isinstance(pts, list)

    def test_set_polyline_roundtrip(self):
        m = Model(CWC_KDF)
        pipe = m.pipes[1]
        new_pts = [(1500.0, 4700.0), (2000.0, 4700.0), (2000.0, 5200.0)]
        m.layout.set_polyline(pipe, new_pts)
        got = m.layout.get_polyline(pipe)
        assert got == new_pts

    def test_set_polyline_sets_bend_flag(self):
        m = Model(CWC_KDF)
        pipe = m.pipes[1]
        m.layout.set_polyline(pipe, [(1000.0, 2000.0), (3000.0, 2000.0)])
        rec = pipe.get_param("BEND")
        if rec and rec.values:
            assert int(rec.values[0]) == 1

    def test_set_polyline_empty_clears_bend_flag(self):
        m = Model(CWC_KDF)
        pipe = m.pipes[1]
        m.layout.set_polyline(pipe, [])
        rec = pipe.get_param("BEND")
        if rec and rec.values:
            assert int(rec.values[0]) == 0


class TestAddBend:
    def test_add_bend_creates_corner(self):
        m = Model(CWC_KDF)
        pipe = m.pipes[1]
        pts_before = m.layout.get_polyline(pipe)
        m.layout.add_bend(pipe, 9999.0, 1111.0)
        pts_after = m.layout.get_polyline(pipe)
        assert len(pts_after) >= max(1, len(pts_before))
        assert (9999.0, 1111.0) in pts_after

    def test_add_bend_index_zero_prepends(self):
        m = Model(CWC_KDF)
        pipe = m.pipes[1]
        m.layout.set_polyline(pipe, [(1000.0, 2000.0), (3000.0, 2000.0)])
        m.layout.add_bend(pipe, 500.0, 2000.0, index=0)
        pts = m.layout.get_polyline(pipe)
        assert pts[0] == (500.0, 2000.0)

    def test_add_bend_l_shape(self):
        m = Model(CWC_KDF)
        pipe = m.pipes[1]
        m.layout.set_polyline(pipe, [(1000.0, 2000.0), (3000.0, 5000.0)])
        m.layout.add_bend(pipe, 3000.0, 2000.0)
        pts = m.layout.get_polyline(pipe)
        assert (3000.0, 2000.0) in pts


class TestRoutePipe:
    def _first_two_endpoint_pipe(self, m: Model):
        pipe_to_elems = m.connectivity.get_pipe_to_elems()
        idx = next((i for i, ns in pipe_to_elems.items() if len(ns) == 2), None)
        if idx is None:
            return None, None
        return m.pipes[idx], pipe_to_elems[idx]

    def test_route_pipe_straight_horizontal(self):
        m = Model(CWC_KDF)
        pipe, _ = self._first_two_endpoint_pipe(m)
        if pipe is None:
            return
        m.layout.route_pipe(pipe, bend="h")
        pts = m.layout.get_polyline(pipe)
        assert len(pts) >= 2

    def test_route_pipe_h_bend(self):
        m = Model(CWC_KDF)
        pipe, names = self._first_two_endpoint_pipe(m)
        if pipe is None:
            return
        m.set_position(m[names[0]], 2000.0, 2000.0)
        m.set_position(m[names[1]], 5000.0, 5000.0)
        m.layout.route_pipe(pipe, bend="h")
        pts = m.layout.get_polyline(pipe)
        assert len(pts) == 3
        assert pts[1] == (5000.0, 2000.0)

    def test_route_pipe_v_bend(self):
        m = Model(CWC_KDF)
        pipe, names = self._first_two_endpoint_pipe(m)
        if pipe is None:
            return
        m.set_position(m[names[0]], 2000.0, 2000.0)
        m.set_position(m[names[1]], 5000.0, 5000.0)
        m.layout.route_pipe(pipe, bend="v")
        pts = m.layout.get_polyline(pipe)
        assert len(pts) == 3
        assert pts[1] == (2000.0, 5000.0)

    def test_route_pipe_auto_h_when_dx_dominant(self):
        m = Model(CWC_KDF)
        pipe, names = self._first_two_endpoint_pipe(m)
        if pipe is None:
            return
        m.set_position(m[names[0]], 1000.0, 2000.0)
        m.set_position(m[names[1]], 6000.0, 2100.0)
        m.layout.route_pipe(pipe, bend="auto")
        pts = m.layout.get_polyline(pipe)
        if len(pts) == 3:
            assert pts[1][1] == 2000.0  # horizontal-first: corner keeps start Y

    def test_route_all_pipes_smoke(self):
        m = Model(CWC_KDF)
        m.layout.route_all_pipes()
        pipe_to_elems = m.connectivity.get_pipe_to_elems()
        for idx, pipe in m.pipes.items():
            if idx == 0 or not pipe.name:
                continue
            if len(pipe_to_elems.get(idx, [])) == 2:
                pts = m.layout.get_polyline(pipe)
                assert len(pts) >= 2, f"Pipe {pipe.name} should have a polyline"

    def test_route_all_pipes_pump(self):
        m = Model(PUMP_KDF)
        m.layout.route_all_pipes()  # should not raise


class TestSnapOrthogonal:
    def test_snap_orthogonal_does_not_crash(self):
        m = Model(PUMP_KDF)
        m.layout.snap_orthogonal()

    def test_snap_orthogonal_cwc(self):
        m = Model(CWC_KDF)
        m.layout.snap_orthogonal()

    def test_snap_orthogonal_custom_threshold(self):
        m = Model(PUMP_KDF)
        m.layout.snap_orthogonal(threshold_deg=5.0)

    def test_snap_orthogonal_positions_remain_valid(self):
        m = Model(CWC_KDF)
        m.layout.snap_orthogonal()
        for elem in m.elements:
            pos = m.get_position(elem)
            if pos is not None:
                assert isinstance(pos[0], float)
                assert isinstance(pos[1], float)


class TestAlignElements:
    def test_align_horizontal_smoke(self):
        m = Model(CWC_KDF)
        names = [e.name for e in m.elements if m.get_position(e) is not None][:4]
        m.layout.align_horizontal(names)
        ys = {m.get_position(m[n])[1] for n in names if m.get_position(m[n]) is not None}
        assert len(ys) == 1

    def test_align_horizontal_anchor(self):
        m = Model(CWC_KDF)
        names = [e.name for e in m.elements if m.get_position(e) is not None][:3]
        m.layout.align_horizontal(names, anchor_y=3000.0)
        for n in names:
            pos = m.get_position(m[n])
            if pos is not None:
                assert pos[1] == 3000.0

    def test_align_vertical_smoke(self):
        m = Model(CWC_KDF)
        names = [e.name for e in m.elements if m.get_position(e) is not None][:4]
        m.layout.align_vertical(names)
        xs = {m.get_position(m[n])[0] for n in names if m.get_position(m[n]) is not None}
        assert len(xs) == 1

    def test_align_vertical_anchor(self):
        m = Model(CWC_KDF)
        names = [e.name for e in m.elements if m.get_position(e) is not None][:3]
        m.layout.align_vertical(names, anchor_x=5000.0)
        for n in names:
            pos = m.get_position(m[n])
            if pos is not None:
                assert pos[0] == 5000.0

    def test_align_empty_list_no_crash(self):
        m = Model(PUMP_KDF)
        m.layout.align_horizontal([])
        m.layout.align_vertical([])


class TestDistributeElements:
    def test_distribute_horizontal_even_spacing(self):
        m = Model(CWC_KDF)
        positioned = [e for e in m.elements if m.get_position(e) is not None]
        if len(positioned) < 3:
            return
        names = [e.name for e in positioned[:5]]
        m.layout.distribute_horizontal(names)
        xs = sorted(m.get_position(m[n])[0] for n in names if m.get_position(m[n]))
        gaps = [xs[i + 1] - xs[i] for i in range(len(xs) - 1)]
        assert all(abs(g - gaps[0]) < 0.01 for g in gaps)

    def test_distribute_vertical_even_spacing(self):
        m = Model(CWC_KDF)
        positioned = [e for e in m.elements if m.get_position(e) is not None]
        if len(positioned) < 3:
            return
        names = [e.name for e in positioned[:5]]
        m.layout.distribute_vertical(names)
        ys = sorted(m.get_position(m[n])[1] for n in names if m.get_position(m[n]))
        gaps = [ys[i + 1] - ys[i] for i in range(len(ys) - 1)]
        assert all(abs(g - gaps[0]) < 0.01 for g in gaps)

    def test_distribute_two_elements_no_change(self):
        m = Model(PUMP_KDF)
        positioned = [e for e in m.elements if m.get_position(e) is not None]
        names = [e.name for e in positioned[:2]]
        before = [m.get_position(m[n]) for n in names]
        m.layout.distribute_horizontal(names)
        after = [m.get_position(m[n]) for n in names]
        assert before == after


class TestSnapToGrid:
    def test_snap_to_grid_smoke(self):
        m = Model(CWC_KDF)
        m.layout.snap_to_grid(500.0)
        for elem in m.elements:
            pos = m.get_position(elem)
            if pos is not None and pos != (0.0, 0.0):
                assert pos[0] % 500.0 == 0.0
                assert pos[1] % 500.0 == 0.0

    def test_snap_to_grid_invalid(self):
        import pytest

        m = Model(PUMP_KDF)
        with pytest.raises(ValueError):
            m.layout.snap_to_grid(0)


class TestPageSize:
    def test_page_size_a4(self):
        m = Model(PUMP_KDF)
        assert m.page_size == "A4"

    def test_boundary_coordinates_a4(self):
        m = Model(PUMP_KDF)
        x_min, y_min, x_max, y_max = m.boundary_coordinates
        assert x_min == 1000.0
        assert y_min == 1000.0
        assert x_max == 15500.0
        assert y_max == 9000.0

    def test_grid_size(self):
        m = Model(PUMP_KDF)
        assert m.grid_size == 100.0

    def test_layout_service_boundary_coordinates(self):
        m = Model(CWC_KDF)
        coords = m.layout.boundary_coordinates
        assert len(coords) == 4
        assert coords == m.boundary_coordinates


class TestCenterLayout:
    def test_center_layout_smoke(self):
        m = Model(CWC_KDF)
        m.layout.center_layout()
        positioned = [
            m.get_position(e) for e in m.elements if m.get_position(e) not in (None, (0.0, 0.0))
        ]
        if not positioned:
            return
        x_min, y_min, x_max, y_max = m.layout.boundary_coordinates
        xs = [p[0] for p in positioned]
        ys = [p[1] for p in positioned]
        page_cx = (x_min + x_max) / 2
        page_cy = (y_min + y_max) / 2
        bbox_cx = (min(xs) + max(xs)) / 2
        bbox_cy = (min(ys) + max(ys)) / 2
        assert abs(bbox_cx - page_cx) < 1.0
        assert abs(bbox_cy - page_cy) < 1.0

    def test_center_layout_pump(self):
        m = Model(PUMP_KDF)
        m.layout.center_layout()

    def test_ensure_title_no_existing_title(self):
        """Test that ensure_title creates a title symbol when none exists."""
        m = Model(PUMP_KDF)
        m.layout.ensure_title("Test Title")

        title_found = False
        for rec in m._parser.records:
            if rec.element_type == "SYMBOL" and rec.index is not None:
                type_rec = m._parser.get("SYMBOL", rec.index, "TYPE")
                text_rec = m._parser.get("SYMBOL", rec.index, "TEXT")
                color_rec = m._parser.get("SYMBOL", rec.index, "COLOR")
                if type_rec and type_rec.values and type_rec.values[0] == "Text":
                    if text_rec and text_rec.values and text_rec.values[0] == "Test Title":
                        xy_rec = m._parser.get("SYMBOL", rec.index, "XY")
                        if xy_rec and len(xy_rec.values) >= 2:
                            x = float(xy_rec.values[0])
                            y = float(xy_rec.values[1])
                            assert x == 1200.0
                            assert y == 200.0
                            assert (
                                color_rec and color_rec.values and color_rec.values[0] == "16711680"
                            )
                            title_found = True
                            break

        assert title_found, "Title symbol was not created"

    def test_ensure_title_with_existing_in_margin(self):
        """Test that ensure_title does nothing when symbol already exists in top margin."""
        m = Model(PUMP_KDF)
        m.layout.ensure_title("First Title")

        initial_symbol_count = sum(
            1 for rec in m._parser.records if rec.element_type == "SYMBOL" and rec.index is not None
        )

        m.layout.ensure_title("Second Title")

        new_symbol_count = sum(
            1 for rec in m._parser.records if rec.element_type == "SYMBOL" and rec.index is not None
        )

        assert new_symbol_count == initial_symbol_count

    def test_ensure_title_default_name(self):
        """Test that ensure_title uses filename as default title."""
        m = Model(PUMP_KDF)
        m.layout.ensure_title()

        title_found = False
        for rec in m._parser.records:
            if rec.element_type == "SYMBOL" and rec.index is not None:
                type_rec = m._parser.get("SYMBOL", rec.index, "TYPE")
                text_rec = m._parser.get("SYMBOL", rec.index, "TEXT")
                if type_rec and type_rec.values and type_rec.values[0] == "Text":
                    if text_rec and text_rec.values and text_rec.values[0] == "Pumpcases":
                        title_found = True
                        break

        assert title_found

    def test_symbol_in_top_margin_empty(self):
        """Test _symbol_in_top_margin with no symbols in margin."""
        m = Model(PUMP_KDF)
        assert not m.layout._symbol_in_top_margin(margin_height=500.0)
