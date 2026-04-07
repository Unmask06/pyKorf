"""
Tests for CaseSet and element summary helpers.
Run with:  pytest tests/
"""

from pathlib import Path

from pykorf.core.cases import CaseSet
from pykorf.core.model import Model

SAMPLES_DIR = Path(__file__).parent.parent / "pykorf" / "library"
PUMP_KDF = SAMPLES_DIR / "Pumpcases.kdf"


class TestCaseSet:
    def _cs(self):
        return CaseSet(Model.load(PUMP_KDF))  # type: ignore[arg-type]

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

        from pykorf.core.exceptions import CaseError

        cs = self._cs()
        with pytest.raises(CaseError):
            cs.get_case_value("50;55;20", 5)

    def test_pipe_flows_table(self):
        cs = self._cs()
        table = cs.pipe_flows_table()
        assert isinstance(table, list)
        assert len(table) > 0
        assert "NORMAL" in table[0]


class TestElementSummary:
    """Test direct element summary() methods (replaces old Results class)."""

    def _model(self):
        return Model.load(PUMP_KDF)

    def test_pump_summary(self):
        model = self._model()
        pump = model.pump(1)
        s = pump.summary(export=True)
        assert "Hydraulic Power [kW]" in s
        assert s["Hydraulic Power [kW]"] > 0

    def test_all_pumps(self):
        model = self._model()
        pumps = [p.summary(export=True) for idx, p in model.pumps.items() if idx > 0]
        assert len(pumps) == 1

    def test_pipe_velocities(self):
        model = self._model()
        vels = {idx: pipe.velocity for idx, pipe in model.pipes.items() if idx > 0}
        assert 1 in vels
        assert isinstance(vels[1], list)

    def test_pipe_pressures(self):
        model = self._model()
        p = {idx: pipe.pressure for idx, pipe in model.pipes.items() if idx > 0}
        assert 1 in p

    def test_valve_dp(self):
        model = self._model()
        dp = {idx: v.dp_kPag for idx, v in model.valves.items() if idx > 0}
        assert 1 in dp
