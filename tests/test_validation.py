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
        """Pumpcases.kdf has DPL values well within criteria — no DPL violations."""
        m = Model(PUMP_KDF)
        issues = m.validate()
        dpl_violations = [i for i in issues if "fails sizing criteria:" in i and "DP/DL" in i]
        assert len(dpl_violations) == 0

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

    def test_pipe_missing_criteria_code_detected(self):
        """A pipe without a criteria code must be flagged in validation issues."""
        m = Model(PUMP_KDF)
        pipe = m.pipes[1]
        original_code = pipe.criteria_code
        pipe.criteria_code = ""
        issues = m.validate()
        pipe_issues = [i for i in issues if pipe.name in i and "missing criteria code" in i]
        assert len(pipe_issues) >= 1
        pipe.criteria_code = original_code

    def test_pipe_with_criteria_code_passes(self):
        """A pipe with a criteria code should not be flagged."""
        m = Model(PUMP_KDF)
        pipe = m.pipes[1]
        pipe.criteria_code = "P-DIS"
        issues = m.validate()
        pipe_issues = [i for i in issues if pipe.name in i and "missing criteria code" in i]
        assert len(pipe_issues) == 0

    def test_dummy_pipes_skipped_for_criteria_code(self):
        """Dummy pipes (names starting with 'd') should not be checked for criteria codes."""
        m = Model(PUMP_KDF)
        dummy_pipe = None
        for pipe in m.pipes.values():
            if pipe.name and pipe.name.lower().startswith("d"):
                dummy_pipe = pipe
                break
        if dummy_pipe is None:
            pytest.skip("No dummy pipes found in test model")
        original_code = dummy_pipe.criteria_code
        dummy_pipe.criteria_code = ""
        issues = m.validate()
        pipe_issues = [i for i in issues if dummy_pipe.name in i and "missing criteria code" in i]
        assert len(pipe_issues) == 0
        dummy_pipe.criteria_code = original_code
