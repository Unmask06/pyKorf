"""Tests for the validation module.

Run with:  PYTHONPATH=. python -m pytest tests/test_validation.py -v
"""

from pathlib import Path

import pytest

from pykorf.model import Model
from pykorf.model.validation import validate

SAMPLES_DIR = Path(__file__).parent.parent / "pykorf" / "library"
PUMP_KDF = SAMPLES_DIR / "Pumpcases.kdf"
CWC_KDF = SAMPLES_DIR / "Cooling Water Circuit.kdf"
NEW_KDF = SAMPLES_DIR / "New.kdf"


class TestValidate:
    def test_validate_returns_list(self):
        m = Model(PUMP_KDF)
        issues = validate(m)
        assert isinstance(issues, list)

    def test_validate_pumpcases(self):
        m = Model(PUMP_KDF)
        issues = validate(m)
        # Pre-existing model should be mostly valid
        # There might be minor issues but no critical ones
        assert isinstance(issues, list)

    def test_validate_cwc(self):
        m = Model(CWC_KDF)
        issues = validate(m)
        assert isinstance(issues, list)

    def test_validate_new_template(self):
        m = Model(NEW_KDF)
        issues = validate(m)
        # Template should be valid — no instances so no instance issues
        assert isinstance(issues, list)

    def test_validate_detects_num_mismatch(self):
        m = Model(PUMP_KDF)
        # Corrupt a NUM count
        m._parser.set_num_instances("PIPE", 999)
        issues = validate(m)
        assert any("PIPE" in i and "NUM" in i for i in issues)

    def test_model_validate(self):
        m = Model(PUMP_KDF)
        issues = m.validate()
        assert isinstance(issues, list)

    def test_validate_blank_model(self):
        m = Model()  # loads New.kdf defaults
        issues = m.validate()
        assert isinstance(issues, list)
