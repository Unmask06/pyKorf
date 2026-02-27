"""Tests for the Model API — constructor, elements, name-based access, update, CRUD.

Run with:  PYTHONPATH=. python -m pytest tests/test_model_api.py -v
"""

import os
import tempfile
from pathlib import Path

import pytest

from pykorf.model import KorfModel, Model
from pykorf.exceptions import ElementNotFound

SAMPLES_DIR = Path(__file__).parent.parent / "pykorf" / "library"
PUMP_KDF = SAMPLES_DIR / "Pumpcases.kdf"
CRANE_KDF = SAMPLES_DIR / "crane10.kdf"
CWC_KDF = SAMPLES_DIR / "Cooling Water Circuit.kdf"


# ------------------------------------------------------------------
# Model constructor
# ------------------------------------------------------------------


class TestModelConstructor:
    def test_model_no_args_creates_default(self):
        """Model() should load from New.kdf template."""
        m = Model()
        assert m.version.startswith("KORF")
        # Template has 0 real instances
        assert m.num_pipes == 0
        assert m.num_pumps == 0

    def test_model_with_path(self):
        """Model(path) should load from that file."""
        m = Model(PUMP_KDF)
        assert m.num_pipes == 5
        assert m.num_pumps == 1

    def test_model_load_classmethod(self):
        """Backward compat: Model.load(path) still works."""
        m = Model.load(PUMP_KDF)
        assert m.num_pipes == 5

    def test_korf_model_alias(self):
        """KorfModel is an alias for Model."""
        assert KorfModel is Model

    def test_backward_compat_load(self):
        """KorfModel.load() still works."""
        m = KorfModel.load(PUMP_KDF)
        assert "NORMAL" in m.general.case_descriptions

    def test_repr(self):
        m = Model(PUMP_KDF)
        assert "KorfModel(" in repr(m)

    def test_load_v36(self):
        m = Model(CWC_KDF)
        assert m.version == "KORF_3.6"
        assert m.num_pipes == 9


# ------------------------------------------------------------------
# Name-based element access
# ------------------------------------------------------------------


class TestNameAccess:
    def test_get_element_by_name(self):
        m = Model(PUMP_KDF)
        pipe = m.get_element("L1")
        assert pipe.etype == "PIPE"
        assert pipe.index == 1

    def test_getitem_shorthand(self):
        m = Model(PUMP_KDF)
        pipe = m["L1"]
        assert pipe.name == "L1"

    def test_contains(self):
        m = Model(PUMP_KDF)
        assert "L1" in m
        assert "NONEXISTENT" not in m

    def test_element_not_found(self):
        m = Model(PUMP_KDF)
        with pytest.raises(ElementNotFound):
            m.get_element("DOES_NOT_EXIST")

    def test_get_pump_by_name(self):
        m = Model(PUMP_KDF)
        pump = m["P1"]
        assert pump.etype == "PUMP"


# ------------------------------------------------------------------
# Elements listing
# ------------------------------------------------------------------


class TestElementsListing:
    def test_elements_returns_list(self):
        m = Model(PUMP_KDF)
        elems = m.elements
        assert isinstance(elems, list)
        assert len(elems) > 0

    def test_elements_excludes_templates(self):
        m = Model(PUMP_KDF)
        for elem in m.elements:
            assert elem.index >= 1

    def test_get_elements_by_type(self):
        m = Model(PUMP_KDF)
        pipes = m.get_elements_by_type("PIPE")
        assert len(pipes) == 5
        for p in pipes:
            assert p.etype == "PIPE"

    def test_get_elements_by_type_empty(self):
        m = Model(PUMP_KDF)
        # No TEEs in Pumpcases
        tees = m.get_elements_by_type("TEE")
        assert len(tees) == 0

    def test_get_elements_by_type_unknown(self):
        m = Model(PUMP_KDF)
        result = m.get_elements_by_type("UNKNOWN_TYPE")
        assert result == []


# ------------------------------------------------------------------
# Update element
# ------------------------------------------------------------------


class TestUpdateElement:
    def test_update_single_param(self):
        m = Model(PUMP_KDF)
        m.update_element("L1", {"LEN": 200})
        pipe = m["L1"]
        rec = pipe._get("LEN")
        assert rec.values[0] == "200"

    def test_update_multiple_params(self):
        m = Model(PUMP_KDF)
        m.update_element("L1", {"LEN": 200, "TFLOW": "80;90;60"})
        pipe = m["L1"]
        assert pipe._get("LEN").values[0] == "200"
        assert pipe._get("TFLOW").values[0] == "80;90;60"

    def test_update_elements_batch(self):
        m = Model(PUMP_KDF)
        m.update_elements({
            "L1": {"LEN": 200},
            "P1": {"EFFP": "0.75"},
        })
        assert m["L1"]._get("LEN").values[0] == "200"
        assert m["P1"]._get("EFFP").values[0] == "0.75"

    def test_update_nonexistent_raises(self):
        m = Model(PUMP_KDF)
        with pytest.raises(ElementNotFound):
            m.update_element("FAKE", {"LEN": 100})


# ------------------------------------------------------------------
# Add element
# ------------------------------------------------------------------


class TestAddElement:
    def test_add_pipe(self):
        m = Model(PUMP_KDF)
        original_count = m.num_pipes
        new_pipe = m.add_element("PIPE", "L_NEW")
        assert new_pipe.name == "L_NEW"
        assert new_pipe.etype == "PIPE"
        assert m.num_pipes == original_count + 1
        assert "L_NEW" in m

    def test_add_pipe_with_params(self):
        m = Model(PUMP_KDF)
        new_pipe = m.add_element("PIPE", "L_P", {"LEN": "50"})
        assert new_pipe._get("LEN").values[0] == "50"

    def test_add_elements_batch(self):
        m = Model(PUMP_KDF)
        orig_pipes = m.num_pipes
        orig_pumps = m.num_pumps
        results = m.add_elements([
            ("PIPE", "L_B1", {"LEN": "10"}),
            ("PUMP", "P_B1", None),
        ])
        assert len(results) == 2
        assert m.num_pipes == orig_pipes + 1
        assert m.num_pumps == orig_pumps + 1

    def test_add_unknown_type_raises(self):
        m = Model(PUMP_KDF)
        with pytest.raises(ValueError, match="Unknown element type"):
            m.add_element("FOOBAR", "X1")

    def test_add_then_save_reload(self):
        m = Model(PUMP_KDF)
        m.add_element("PIPE", "L_SAVE")
        with tempfile.NamedTemporaryFile(suffix=".kdf", delete=False) as f:
            tmp = f.name
        try:
            m.save(tmp)
            m2 = Model(tmp)
            assert "L_SAVE" in m2
            assert m2.num_pipes == 6  # was 5
        finally:
            os.unlink(tmp)


# ------------------------------------------------------------------
# Delete element
# ------------------------------------------------------------------


class TestDeleteElement:
    def test_delete_pipe(self):
        m = Model(PUMP_KDF)
        assert "L1" in m
        original = m.num_pipes
        m.delete_element("L1")
        assert "L1" not in m
        assert m.num_pipes == original - 1

    def test_delete_nonexistent_raises(self):
        m = Model(PUMP_KDF)
        with pytest.raises(ElementNotFound):
            m.delete_element("NOPE")

    def test_delete_elements_batch(self):
        m = Model(PUMP_KDF)
        original = m.num_pipes
        # Get first two pipe names
        pipe_names = [p.name for p in m.get_elements_by_type("PIPE")[:2]]
        m.delete_elements(pipe_names)
        assert m.num_pipes == original - 2


# ------------------------------------------------------------------
# Copy element
# ------------------------------------------------------------------


class TestCopyElement:
    def test_copy_pipe(self):
        m = Model(PUMP_KDF)
        original = m.num_pipes
        new_elem = m.copy_element("L1", "L_COPY")
        assert new_elem.name == "L_COPY"
        assert new_elem.etype == "PIPE"
        assert m.num_pipes == original + 1

    def test_copy_preserves_params(self):
        m = Model(PUMP_KDF)
        src = m["L1"]
        src_len = src._get("LEN").values[0]
        new_elem = m.copy_element("L1", "L_COPY2")
        assert new_elem._get("LEN").values[0] == src_len

    def test_copy_clears_connectivity(self):
        m = Model(PUMP_KDF)
        new_pump = m.copy_element("P1", "P_COPY")
        con_rec = new_pump._get("CON")
        if con_rec and con_rec.values:
            # All values should be "0"
            for v in con_rec.values[:2]:
                assert str(v) == "0"


# ------------------------------------------------------------------
# Move element
# ------------------------------------------------------------------


class TestMoveElement:
    def test_move_to_empty_index(self):
        m = Model(PUMP_KDF)
        # Move pipe at index 1 to index 100
        m.move_element("L1", 100)
        # Should still be findable by name
        assert "L1" in m
        assert m["L1"].index == 100

    def test_move_swap(self):
        m = Model(PUMP_KDF)
        name1 = m.pipes[1].name
        name2 = m.pipes[2].name
        m.move_element(name1, 2)
        assert m[name1].index == 2
        assert m[name2].index == 1

    def test_move_invalid_index_raises(self):
        m = Model(PUMP_KDF)
        with pytest.raises(ValueError, match="Target index must be >= 1"):
            m.move_element("L1", 0)
