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


class TestPolyline:
    def test_get_polyline_pipe_with_bends(self):
        m = Model(CWC_KDF)
        # CWC has pipes with BEND=1 and waypoints in XY records
        pipe = m.pipes[1]
        pts = m.get_polyline(pipe)
        assert isinstance(pts, list)
        # CWC pipe 1 has two waypoints
        assert len(pts) >= 1
        for x, y in pts:
            assert isinstance(x, float)
            assert isinstance(y, float)

    def test_get_polyline_no_waypoints(self):
        m = Model(PUMP_KDF)
        # Pipe 1 in Pumpcases has duplicate start point then waypoints
        pipe = m.pipes[1]
        pts = m.get_polyline(pipe)
        assert isinstance(pts, list)

    def test_set_polyline_roundtrip(self):
        m = Model(CWC_KDF)
        pipe = m.pipes[1]
        new_pts = [(1500.0, 4700.0), (2000.0, 4700.0), (2000.0, 5200.0)]
        m.set_polyline(pipe, new_pts)
        got = m.get_polyline(pipe)
        assert got == new_pts

    def test_set_polyline_sets_bend_flag(self):
        m = Model(CWC_KDF)
        pipe = m.pipes[1]
        m.set_polyline(pipe, [(1000.0, 2000.0), (3000.0, 2000.0)])
        rec = pipe.get_param("BEND")
        if rec and rec.values:
            assert int(rec.values[0]) == 1

    def test_set_polyline_empty_clears_bend_flag(self):
        m = Model(CWC_KDF)
        pipe = m.pipes[1]
        m.set_polyline(pipe, [])
        rec = pipe.get_param("BEND")
        if rec and rec.values:
            assert int(rec.values[0]) == 0


class TestAddBend:
    def test_add_bend_creates_corner(self):
        m = Model(CWC_KDF)
        pipe = m.pipes[1]
        pts_before = m.get_polyline(pipe)
        m.add_bend(pipe, 9999.0, 1111.0)
        pts_after = m.get_polyline(pipe)
        # One more point than before (or at least one point)
        assert len(pts_after) >= max(1, len(pts_before))
        # The new waypoint must appear somewhere
        assert (9999.0, 1111.0) in pts_after

    def test_add_bend_index_zero_prepends(self):
        m = Model(CWC_KDF)
        pipe = m.pipes[1]
        m.set_polyline(pipe, [(1000.0, 2000.0), (3000.0, 2000.0)])
        m.add_bend(pipe, 500.0, 2000.0, index=0)
        pts = m.get_polyline(pipe)
        assert pts[0] == (500.0, 2000.0)

    def test_add_bend_l_shape(self):
        # Orthogonal L-shape: start (1000,2000) → corner (3000,2000) → end (3000,5000)
        m = Model(CWC_KDF)
        pipe = m.pipes[1]
        m.set_polyline(pipe, [(1000.0, 2000.0), (3000.0, 5000.0)])
        # Horizontal-first corner
        m.add_bend(pipe, 3000.0, 2000.0)
        pts = m.get_polyline(pipe)
        assert (3000.0, 2000.0) in pts


class TestRoutePipe:
    def test_route_pipe_straight_horizontal(self):
        m = Model(CWC_KDF)
        # Find a pipe with exactly 2 connected elements
        pipe_to_elems = m._layout_service._build_pipe_to_elems()
        target_idx = next((idx for idx, names in pipe_to_elems.items() if len(names) == 2), None)
        if target_idx is None:
            return
        pipe = m.pipes[target_idx]
        m.route_pipe(pipe, bend="h")
        pts = m.get_polyline(pipe)
        assert len(pts) >= 2

    def test_route_pipe_h_bend(self):
        m = Model(CWC_KDF)
        # Place two elements at a diagonal and route between them
        pipe_to_elems = m._layout_service._build_pipe_to_elems()
        target_idx = next((idx for idx, names in pipe_to_elems.items() if len(names) == 2), None)
        if target_idx is None:
            return
        pipe = m.pipes[target_idx]
        names = pipe_to_elems[target_idx]
        # Force a diagonal position
        m.set_position(m[names[0]], 2000.0, 2000.0)
        m.set_position(m[names[1]], 5000.0, 5000.0)
        m.route_pipe(pipe, bend="h")
        pts = m.get_polyline(pipe)
        # Should have 3 points for the L-shape
        assert len(pts) == 3
        # Corner should be at (5000, 2000) for horizontal-first
        assert pts[1] == (5000.0, 2000.0)

    def test_route_pipe_v_bend(self):
        m = Model(CWC_KDF)
        pipe_to_elems = m._layout_service._build_pipe_to_elems()
        target_idx = next((idx for idx, names in pipe_to_elems.items() if len(names) == 2), None)
        if target_idx is None:
            return
        pipe = m.pipes[target_idx]
        names = pipe_to_elems[target_idx]
        m.set_position(m[names[0]], 2000.0, 2000.0)
        m.set_position(m[names[1]], 5000.0, 5000.0)
        m.route_pipe(pipe, bend="v")
        pts = m.get_polyline(pipe)
        assert len(pts) == 3
        # Corner should be at (2000, 5000) for vertical-first
        assert pts[1] == (2000.0, 5000.0)

    def test_route_pipe_auto_chooses_h_when_dx_dominant(self):
        m = Model(CWC_KDF)
        pipe_to_elems = m._layout_service._build_pipe_to_elems()
        target_idx = next((idx for idx, names in pipe_to_elems.items() if len(names) == 2), None)
        if target_idx is None:
            return
        pipe = m.pipes[target_idx]
        names = pipe_to_elems[target_idx]
        # dx >> dy  => horizontal-first
        m.set_position(m[names[0]], 1000.0, 2000.0)
        m.set_position(m[names[1]], 6000.0, 2100.0)
        m.route_pipe(pipe, bend="auto")
        pts = m.get_polyline(pipe)
        # Since dy is small but nonzero, we get 3 points; corner Y == start Y
        if len(pts) == 3:
            assert pts[1][1] == 2000.0  # horizontal-first: corner keeps start Y

    def test_route_all_pipes_smoke(self):
        m = Model(CWC_KDF)
        m.route_all_pipes()
        # All connected pipes should now have polylines
        pipe_to_elems = m._layout_service._build_pipe_to_elems()
        for idx, pipe in m.pipes.items():
            if idx == 0 or not pipe.name:
                continue
            if len(pipe_to_elems.get(idx, [])) == 2:
                pts = m.get_polyline(pipe)
                assert len(pts) >= 2, f"Pipe {pipe.name} should have polyline"

    def test_route_all_pipes_pump(self):
        m = Model(PUMP_KDF)
        m.route_all_pipes()  # should not raise

    def test_auto_layout_with_route_pipes(self):
        m = Model(PUMP_KDF)
        for elem in m.elements:
            m.set_position(elem, 0.0, 0.0)
        m.auto_layout(strategy="flow", route_pipes=True)
        # Pipes should have polylines
        pipe_to_elems = m._layout_service._build_pipe_to_elems()
        routed = 0
        for idx, pipe in m.pipes.items():
            if idx == 0 or not pipe.name:
                continue
            if len(pipe_to_elems.get(idx, [])) == 2:
                pts = m.get_polyline(pipe)
                if pts:
                    routed += 1
        assert routed > 0


class TestAutoLayoutFlow:
    def test_auto_layout_flow_does_not_crash(self):
        m = Model(CWC_KDF)
        # Reset all positions to unplaced
        for elem in m.elements:
            pos = m.get_position(elem)
            if pos is not None:
                m.set_position(elem, 0.0, 0.0)
        m.auto_layout(strategy="flow")

    def test_auto_layout_flow_places_elements(self):
        m = Model(PUMP_KDF)
        for elem in m.elements:
            m.set_position(elem, 0.0, 0.0)
        m.auto_layout(strategy="flow")
        placed = [e for e in m.elements if m.get_position(e) not in (None, (0.0, 0.0))]
        assert len(placed) > 0

    def test_auto_layout_grid_still_works(self):
        m = Model(PUMP_KDF)
        for elem in m.elements:
            m.set_position(elem, 0.0, 0.0)
        m.auto_layout(strategy="grid")
        placed = [e for e in m.elements if m.get_position(e) not in (None, (0.0, 0.0))]
        assert len(placed) > 0


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
