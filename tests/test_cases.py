"""
Tests for CaseSet and Results helpers.
Run with:  pytest tests/
"""

import os
import tempfile
from pathlib import Path

from pykorf.model import KorfModel
from pykorf.cases import CaseSet
from pykorf.results import Results

SAMPLES_DIR = Path(__file__).parent.parent / "pykorf" / "library"
PUMP_KDF = SAMPLES_DIR / "Pumpcases.kdf"


class TestCaseSet:
    def _cs(self):
        return CaseSet(KorfModel.load(PUMP_KDF))  # type: ignore[arg-type]

    def test_names(self):
        cs = self._cs()
        assert cs.names == ["NORMAL", "RATED", "MINIMUM"]

    def test_count(self):
        cs = self._cs()
        assert cs.count == 3

    def test_get_case_value(self):
        cs = self._cs()
        assert cs.get_case_value("50;55;20", 1) == "50"
        assert cs.get_case_value("50;55;20", 3) == "20"

    def test_set_case_value(self):
        cs = self._cs()
        result = cs.set_case_value("50;55;20", 2, "99")
        assert result == "50;99;20"

    def test_invalid_case_raises(self):
        import pytest
        from pykorf.exceptions import CaseError
        cs = self._cs()
        with pytest.raises(CaseError):
            cs.get_case_value("50;55;20", 5)

    def test_pipe_flows_table(self):
        cs = self._cs()
        table = cs.pipe_flows_table()
        assert isinstance(table, list)
        assert len(table) > 0
        assert "NORMAL" in table[0]


class TestResults:
    def _res(self):
        return Results(KorfModel.load(PUMP_KDF))

    def test_pump_summary(self):
        r = self._res()
        s = r.pump_summary(1)
        assert "power_kW" in s
        assert s["power_kW"] > 0

    def test_all_pump_results(self):
        r = self._res()
        results = r.all_pump_results()
        assert len(results) == 1

    def test_pipe_velocities(self):
        r = self._res()
        vels = r.pipe_velocities()
        assert 1 in vels
        assert isinstance(vels[1], list)

    def test_pipe_pressures(self):
        r = self._res()
        p = r.pipe_pressures()
        assert 1 in p

    def test_valve_dp(self):
        r = self._res()
        dp = r.valve_dp()
        assert 1 in dp
