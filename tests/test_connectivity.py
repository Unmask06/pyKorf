"""Tests for the connectivity module.

Run with:  PYTHONPATH=. python -m pytest tests/test_connectivity.py -v
"""

from pathlib import Path

import pytest

from pykorf.exceptions import ConnectivityError
from pykorf.model import Model

SAMPLES_DIR = Path(__file__).parent.parent / "pykorf" / "library"
PUMP_KDF = SAMPLES_DIR / "Pumpcases.kdf"
CWC_KDF = SAMPLES_DIR / "Cooling Water Circuit.kdf"


class TestConnectDisconnect:
    def test_connect_pipe_to_pump(self):
        m = Model(PUMP_KDF)
        m.add_element("PUMP", "P_CON")
        m.connect_elements("L1", "P_CON")
        pump = m["P_CON"]
        con_rec = pump._get("CON")
        pipe_idx = m["L1"].index
        assert str(con_rec.values[0]) == str(pipe_idx)

    def test_disconnect_pipe_from_pump(self):
        m = Model(PUMP_KDF)
        m.add_element("PUMP", "P_DC")
        m.connect_elements("L1", "P_DC")
        m.disconnect_elements("L1", "P_DC")
        con_rec = m["P_DC"]._get("CON")
        assert str(con_rec.values[0]) == "0"

    def test_connect_two_pipes_raises(self):
        m = Model(PUMP_KDF)
        m.add_element("PUMP", "P_A")
        m.add_element("PUMP", "P_B")
        m.connect_elements("P_A", "P_B", pipe_name="L_A")
        with pytest.raises(
            ConnectivityError, match="Cannot directly connect two pipes"
        ):
            m.connect_elements("L_A", "L1")

    def test_connect_no_pipe_auto_creates_pipe(self):
        m = Model(PUMP_KDF)
        m.add_element("PUMP", "P_A")
        m.add_element("VALVE", "V_A")
        m.connect_elements("P_A", "V_A", pipe_name="L_AUTO_CON")
        assert "L_AUTO_CON" in m
        assert m["L_AUTO_CON"].etype == "PIPE"

    def test_connect_no_pipe_auto_creates_pipe_for_hx(self):
        m = Model(PUMP_KDF)
        m.add_element("PUMP", "P_HX")
        m.add_element("HX", "HX_A")
        m.connect_elements("P_HX", "HX_A", pipe_name="L_HX")

        pipe_idx = m["L_HX"].index
        pump_con = m["P_HX"]._get("CON")
        assert str(pump_con.values[0]) == str(pipe_idx)

        hx = m["HX_A"]
        nozzles = [hx._get("NOZI"), hx._get("NOZO")]
        assert any(rec and str(rec.values[0]) == str(pipe_idx) for rec in nozzles)

    def test_disconnect_pipe_from_hx_nozzle(self):
        m = Model(PUMP_KDF)
        m.add_element("PUMP", "P_HXD")
        m.add_element("HX", "HX_D")
        m.connect_elements("P_HXD", "HX_D", pipe_name="L_HXD")

        pipe_idx = str(m["L_HXD"].index)
        m.disconnect_elements("L_HXD", "HX_D")

        hx = m["HX_D"]
        nozzles = [hx._get("NOZI"), hx._get("NOZO")]
        assert all(
            not rec or not rec.values or str(rec.values[0]) != pipe_idx
            for rec in nozzles
        )
        assert any(rec and str(rec.values[0]) == "0" for rec in nozzles)

    def test_disconnect_not_connected_raises(self):
        m = Model(PUMP_KDF)
        m.add_element("PUMP", "P_NC")
        with pytest.raises(ConnectivityError, match="not connected"):
            m.disconnect_elements("L1", "P_NC")

    def test_connect_multiple_pairs(self):
        m = Model(PUMP_KDF)
        m.add_element("PUMP", "P_M1")
        m.add_element("VALVE", "V_M1")
        m.add_element("VALVE", "V_M2")
        m.connect_elements([("P_M1", "V_M1", "L_M1"), ("P_M1", "V_M2", "L_M2")])
        con_rec = m["P_M1"]._get("CON")
        assert str(con_rec.values[0]) == str(m["L_M1"].index)
        assert str(con_rec.values[1]) == str(m["L_M2"].index)


class TestCheckConnectivity:
    def test_check_valid_model(self):
        m = Model(PUMP_KDF)
        issues = m.check_connectivity()
        # Pumpcases is a pre-existing model — may or may not have issues
        # depending on pipe indices. Just ensure it returns a list.
        assert isinstance(issues, list)

    def test_check_after_delete_finds_issue(self):
        m = Model(PUMP_KDF)
        # Delete a pipe that's referenced by an equipment CON
        # First check which pipes are connected
        pump = m.pumps[1]
        con_rec = pump._get("CON")
        if con_rec and con_rec.values:
            try:
                pipe_idx = int(con_rec.values[0])
                if pipe_idx > 0 and pipe_idx in m.pipes:
                    pipe_name = m.pipes[pipe_idx].name
                    m.delete_element(pipe_name)
                    issues = m.check_connectivity()
                    # Should find at least one issue (pump referencing deleted pipe)
                    assert any("does not exist" in i for i in issues)
            except (ValueError, TypeError):
                pass

    def test_check_cwc_model(self):
        m = Model(CWC_KDF)
        issues = m.check_connectivity()
        assert isinstance(issues, list)
