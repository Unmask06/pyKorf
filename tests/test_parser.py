"""
Tests for KdfParser and KorfModel loading/saving.
Run with:  pytest tests/
"""

import os
import shutil
import tempfile
from pathlib import Path

import pytest

from pykorf.parser import KdfParser
from pykorf.model import KorfModel

# ------------------------------------------------------------------
# Resolve path to the sample .kdf files in the library folder
# ------------------------------------------------------------------
SAMPLES_DIR = Path(__file__).parent.parent / "pykorf" / "library"
PUMP_KDF = SAMPLES_DIR / "Pumpcases.kdf"
CRANE_KDF = SAMPLES_DIR / "crane10.kdf"


# ------------------------------------------------------------------
# Parser tests
# ------------------------------------------------------------------

class TestKdfParser:
    def test_load_pumpcases(self):
        p = KdfParser(PUMP_KDF)
        records = p.load()
        assert len(records) > 0

    def test_version_detected(self):
        p = KdfParser(PUMP_KDF)
        p.load()
        assert p.version().startswith("KORF")

    def test_num_pipes(self):
        p = KdfParser(PUMP_KDF)
        p.load()
        assert p.num_instances("PIPE") == 5

    def test_get_record(self):
        p = KdfParser(PUMP_KDF)
        p.load()
        rec = p.get("PIPE", 1, "TFLOW")
        assert rec is not None
        assert "50" in rec.values[0]   # "50;55;20"

    def test_set_value(self):
        p = KdfParser(PUMP_KDF)
        p.load()
        ok = p.set_value("PIPE", 1, "TFLOW", ["60;65;25", 20, "t/h"])
        assert ok
        rec = p.get("PIPE", 1, "TFLOW")
        assert "60" in rec.values[0]

    def test_round_trip(self):
        """Load, do nothing, save, reload – records count must match."""
        p = KdfParser(PUMP_KDF)
        p.load()
        original_count = len(p.records)

        with tempfile.NamedTemporaryFile(suffix=".kdf", delete=False) as f:
            tmp = f.name
        try:
            p.save(tmp)
            p2 = KdfParser(tmp)
            p2.load()
            assert len(p2.records) == original_count
        finally:
            os.unlink(tmp)

    def test_load_crane(self):
        p = KdfParser(CRANE_KDF)
        records = p.load()
        assert len(records) > 0

    def test_num_instances_crane(self):
        p = KdfParser(CRANE_KDF)
        p.load()
        assert p.num_instances("PIPE") >= 1


# ------------------------------------------------------------------
# Model tests
# ------------------------------------------------------------------

class TestKorfModel:
    def test_load(self):
        m = KorfModel.load(PUMP_KDF)
        assert m is not None

    def test_repr(self):
        m = KorfModel.load(PUMP_KDF)
        assert "KorfModel" in repr(m)

    def test_general_cases(self):
        m = KorfModel.load(PUMP_KDF)
        assert "NORMAL" in m.general.case_descriptions
        assert m.general.num_cases == 3

    def test_pipes_loaded(self):
        m = KorfModel.load(PUMP_KDF)
        assert len(m.pipes) > 1    # 0 (template) + 5 real pipes

    def test_pipe_1_flow(self):
        m = KorfModel.load(PUMP_KDF)
        flows = m.pipes[1].get_flow()
        assert flows[0] == "50"

    def test_pump_results(self):
        m = KorfModel.load(PUMP_KDF)
        pump = m.pumps[1]
        assert pump.head_m > 0
        assert pump.power_kW > 0
        assert 0 < pump.efficiency <= 1

    def test_set_flow_string(self):
        m = KorfModel.load(PUMP_KDF)
        m.pipes[1].set_flow("60;65;25")
        assert m.pipes[1].get_flow()[0] == "60"

    def test_set_flow_list(self):
        m = KorfModel.load(PUMP_KDF)
        m.pipes[1].set_flow([70, 75, 30])
        flows = m.pipes[1].get_flow()
        assert flows[0] == "70"
        assert flows[1] == "75"

    def test_save_modified(self):
        m = KorfModel.load(PUMP_KDF)
        m.pipes[1].set_flow("99;99;99")
        with tempfile.NamedTemporaryFile(suffix=".kdf", delete=False) as f:
            tmp = f.name
        try:
            m.save(tmp)
            m2 = KorfModel.load(tmp)
            assert m2.pipes[1].get_flow()[0] == "99"
        finally:
            os.unlink(tmp)

    def test_edits_are_in_memory_until_save(self):
        with tempfile.NamedTemporaryFile(suffix=".kdf", delete=False) as f:
            tmp = f.name
        try:
            shutil.copyfile(PUMP_KDF, tmp)
            original = Path(tmp).read_bytes()

            m = KorfModel.load(tmp)
            m.pipes[1].set_flow("88;88;88")
            m.add_element("PIPE", "L_MEM", {"LEN": "10"})

            # No direct file edits before save()
            assert Path(tmp).read_bytes() == original

            m.save()

            # After save() changes must be persisted
            assert Path(tmp).read_bytes() != original
            m2 = KorfModel.load(tmp)
            assert m2.pipes[1].get_flow()[0] == "88"
            assert "L_MEM" in m2
        finally:
            os.unlink(tmp)

    def test_save_as_keeps_source_file_unchanged(self):
        with tempfile.NamedTemporaryFile(suffix=".kdf", delete=False) as src_f:
            src_tmp = src_f.name
        with tempfile.NamedTemporaryFile(suffix=".kdf", delete=False) as dst_f:
            dst_tmp = dst_f.name
        try:
            shutil.copyfile(PUMP_KDF, src_tmp)
            source_before = Path(src_tmp).read_bytes()

            m = KorfModel.load(src_tmp)
            m.pipes[1].set_flow("77;77;77")
            m.save_as(dst_tmp)

            # save_as() writes to destination, not source
            assert Path(src_tmp).read_bytes() == source_before
            reloaded = KorfModel.load(dst_tmp)
            assert reloaded.pipes[1].get_flow()[0] == "77"
        finally:
            os.unlink(src_tmp)
            os.unlink(dst_tmp)

    def test_summary(self):
        m = KorfModel.load(PUMP_KDF)
        s = m.summary()
        assert s["num_pipes"] == 5
        assert s["num_pumps"] == 1

    def test_element_not_found(self):
        from pykorf.exceptions import ElementNotFound
        m = KorfModel.load(PUMP_KDF)
        with pytest.raises(ElementNotFound):
            m.pipe(999)
