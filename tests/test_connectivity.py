"""Tests for the connectivity module.

Run with:  PYTHONPATH=. python -m pytest tests/test_connectivity.py -v
"""

from pathlib import Path

import pytest

from pykorf.model import Model
from pykorf.exceptions import ConnectivityError

SAMPLES_DIR = Path(__file__).parent.parent / "pykorf" / "library"
PUMP_KDF = SAMPLES_DIR / "Pumpcases.kdf"
CWC_KDF = SAMPLES_DIR / "Cooling Water Circuit.kdf"


class TestConnectDisconnect:
    def test_connect_pipe_to_pump(self):
        m = Model(PUMP_KDF)
        # First add a new pipe and pump, both unconnected
        m.add_element("PIPE", "L_CON")
        m.add_element("PUMP", "P_CON")
        m.connect_elements("L_CON", "P_CON")
        pump = m["P_CON"]
        con_rec = pump._get("CON")
        pipe_idx = m["L_CON"].index
        assert str(con_rec.values[0]) == str(pipe_idx)

    def test_disconnect_pipe_from_pump(self):
        m = Model(PUMP_KDF)
        m.add_element("PIPE", "L_DC")
        m.add_element("PUMP", "P_DC")
        m.connect_elements("L_DC", "P_DC")
        m.disconnect_elements("L_DC", "P_DC")
        con_rec = m["P_DC"]._get("CON")
        assert str(con_rec.values[0]) == "0"

    def test_connect_two_pipes_raises(self):
        m = Model(PUMP_KDF)
        m.add_element("PIPE", "L_A")
        m.add_element("PIPE", "L_B")
        with pytest.raises(ConnectivityError, match="Cannot directly connect two pipes"):
            m.connect_elements("L_A", "L_B")

    def test_connect_no_pipe_raises(self):
        m = Model(PUMP_KDF)
        m.add_element("PUMP", "P_A")
        m.add_element("VALVE", "V_A")
        with pytest.raises(ConnectivityError, match="must be a PIPE"):
            m.connect_elements("P_A", "V_A")

    def test_disconnect_not_connected_raises(self):
        m = Model(PUMP_KDF)
        m.add_element("PIPE", "L_NC")
        m.add_element("PUMP", "P_NC")
        with pytest.raises(ConnectivityError, match="not connected"):
            m.disconnect_elements("L_NC", "P_NC")

    def test_connect_multiple_pairs(self):
        m = Model(PUMP_KDF)
        m.add_element("PIPE", "L_M1")
        m.add_element("PIPE", "L_M2")
        m.add_element("PUMP", "P_M1")
        m.connect_elements([("L_M1", "P_M1"), ("L_M2", "P_M1")])
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
