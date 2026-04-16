"""Tests for the validation module."""

from pathlib import Path

import pytest

from pykorf.core.model import Model

SAMPLES_DIR = Path(__file__).parent.parent / "pykorf" / "library"
PUMP_KDF = SAMPLES_DIR / "Pumpcases.kdf"
CWC_KDF = SAMPLES_DIR / "Cooling Water Circuit.kdf"


class TestValidate:
    def test_validate_returns_list(self):
        issues = Model(PUMP_KDF).validate()
        assert isinstance(issues, list)

    def test_dpl_violation_caught(self):
        """A pipe with DPL far above its sizing criteria must appear in issues."""
        m = Model(PUMP_KDF)
        m.update_element("L1", {"DPL": "9999"})
        issues = m.validate()
        pipe_issues = [i for i in issues if "L1" in i and "fails sizing" in i]
        assert len(pipe_issues) >= 1

    def test_no_false_positive_on_valid_model(self):
        """Pumpcases.kdf has DPL values well within criteria — no DPL/VEL violations."""
        m = Model(PUMP_KDF)
        issues = m.validate()
        violations = [
            i for i in issues
            if "fails sizing criteria:" in i
        ]
        assert len(violations) == 0

    def test_multiple_pipe_violations_all_reported(self):
        """Setting all pipes to extreme DPL must generate one issue per pipe."""
        m = Model(PUMP_KDF)
        for pipe in m.get_elements_by_type("PIPE"):
            m.update_element(pipe.name, {"DPL": "9999"})
        issues = m.validate()
        violating_pipes = {i.split("'")[1] for i in issues if "fails sizing criteria:" in i}
        all_pipe_names = {p.name for p in m.get_elements_by_type("PIPE")}
        assert violating_pipes == all_pipe_names

    def test_connectivity_issue_detected(self):
        """Deleting a pipe that a pump references must appear as connectivity issue."""
        m = Model(PUMP_KDF)
        pump = m.pumps[1]
        con_rec = pump.get_param("CON")
        if not (con_rec and con_rec.values):
            pytest.skip("Pump has no CON record")
        try:
            pipe_idx = int(con_rec.values[0])
        except (ValueError, TypeError):
            pytest.skip("CON value is not an integer index")
        if pipe_idx <= 0 or pipe_idx not in m.pipes:
            pytest.skip("No connected pipe to delete")
        m._parser.delete_records("PIPE", pipe_idx)
        m._build_collections()
        issues = m.validate()
        assert any("does not exist" in i or "dangling" in i.lower() for i in issues)

    def test_cwc_validates_without_crash(self):
        issues = Model(CWC_KDF).validate()
        assert isinstance(issues, list)
