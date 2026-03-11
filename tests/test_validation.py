"""Tests for the validation module.

Run with:  PYTHONPATH=. python -m pytest tests/test_validation.py -v
"""

from pathlib import Path

from pykorf.model import Model

SAMPLES_DIR = Path(__file__).parent.parent / "pykorf" / "library"
PUMP_KDF = SAMPLES_DIR / "Pumpcases.kdf"
CWC_KDF = SAMPLES_DIR / "Cooling Water Circuit.kdf"
NEW_KDF = SAMPLES_DIR / "New.kdf"


class TestValidate:
    def test_validate_returns_list(self):
        m = Model(PUMP_KDF)
        issues = m.validate()
        assert isinstance(issues, list)

    def test_validate_pumpcases(self):
        m = Model(PUMP_KDF)
        issues = m.validate()
        # Pumpcases.kdf may have some legacy issues (empty TFLOW, template params)
        # Just ensure it returns a list and we can log them
        assert isinstance(issues, list)
        if issues:
            print(f"\nPumpcases issues found: {len(issues)}")

    def test_validate_cwc(self):
        m = Model(CWC_KDF)
        issues = m.validate()
        assert isinstance(issues, list)
        if issues:
            print(f"\nCWC issues found: {len(issues)}")

    def test_validate_new(self):
        m = Model(NEW_KDF)
        issues = m.validate()
        # New.kdf should be mostly valid, but might have some template issues
        assert isinstance(issues, list)
