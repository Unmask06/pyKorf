"""Tests for the use_case module.

Covers: line_number, pms, hmb, settings, processor.
Run with:  pytest tests/test_use_case.py -v
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from pykorf import Model
from pykorf.elements import Pipe
from pykorf.use_case import (
    FluidProperties,
    HmbReader,
    LineNumber,
    PipedataProcessor,
    UseCaseSettings,
    apply_hmb,
    apply_pms,
    load_hmb,
    load_pms,
    lookup_schedule,
    lookup_stream,
    parse_stream_from_notes,
)
from pykorf.use_case.exceptions import ProcessError
from pykorf.use_case.hmb import get_stream_path, import_stream_from_excel
from pykorf.use_case.pms import get_pms_path, import_pms_from_excel

SAMPLES_DIR = Path(__file__).parent.parent / "pykorf" / "library"
PUMP_KDF = SAMPLES_DIR / "Pumpcases.kdf"
INPUT_DIR = Path(__file__).parent.parent / "pykorf" / "use_case" / "Input"

# Ensure test files exist in the user config dir
PMS_JSON = get_pms_path("pms.json")
if not PMS_JSON.exists():
    import_pms_from_excel(INPUT_DIR / "pms.xlsx", "pms.json")

HMB_JSON = get_stream_path("stream_data.json")
if not HMB_JSON.exists():
    import_stream_from_excel(INPUT_DIR / "stream.xlsx", "stream_data.json")


# =========================================================================
# LineNumber parsing
# =========================================================================


class TestLineNumber:
    """Tests for LineNumber.parse() and validate()."""

    def test_parse_basic(self):
        """Parse a standard 5-segment line number."""
        ln = LineNumber.parse("6-10U01-WATR-001-BC1A1B")
        assert ln is not None
        assert ln.nominal_pipe_size == 6
        assert ln.unit_number == "10U01"
        assert ln.fluid_code == "WATR"
        assert ln.serial_number == 1
        assert ln.piping_class == "BC1A1B"
        assert ln.coating_code == ""
        assert ln.insulation_thickness is None
        assert ln.tracing_temp is None

    def test_parse_with_coating_and_insulation(self):
        """Parse line number with optional coating and insulation fields."""
        ln = LineNumber.parse("14-CA020-BRL1-020-AP7A0F-FX2-50")
        assert ln is not None
        assert ln.nominal_pipe_size == 14
        assert ln.unit_number == "CA020"
        assert ln.fluid_code == "BRL1"
        assert ln.serial_number == 20
        assert ln.piping_class == "AP7A0F"
        assert ln.coating_code == "FX2"
        assert ln.insulation_thickness == 50

    def test_parse_with_all_segments(self):
        """Parse line number with all optional segments."""
        ln = LineNumber.parse("8-20U02-STEA-003-BC1A1B-HTR-75-150-XX")
        assert ln is not None
        assert ln.nominal_pipe_size == 8
        assert ln.fluid_code == "STEA"
        assert ln.coating_code == "HTR"
        assert ln.insulation_thickness == 75
        assert ln.tracing_temp == 150

    def test_parse_non_numeric_optional_fields(self):
        """Non-numeric optional fields (like 'N', 'F') should yield None for int fields."""
        ln = LineNumber.parse("14-CA020-BRL1-020-AP7A0F-FX2-N")
        assert ln is not None
        assert ln.coating_code == "FX2"
        assert ln.insulation_thickness is None  # 'N' is not a digit

    def test_parse_from_notes_with_delimiter(self):
        """Parse line number from NOTES field with stream number after delimiter."""
        ln = LineNumber.parse("6-10U01-WATR-001-BC1A1B;S-101;")
        assert ln is not None
        assert ln.nominal_pipe_size == 6
        assert ln.piping_class == "BC1A1B"

    def test_parse_returns_none_for_invalid(self):
        """parse() returns None for unparseable strings."""
        assert LineNumber.parse("") is None
        assert LineNumber.parse("not-a-line-number") is None
        assert LineNumber.parse("abc") is None

    def test_parse_fluid_code_with_digits(self):
        """Fluid code can contain digits (e.g., BRL1, WCOR)."""
        ln = LineNumber.parse("10-20U03-BRL1-005-AP7A0F")
        assert ln is not None
        assert ln.fluid_code == "BRL1"

    def test_validate_valid(self):
        result = LineNumber.validate("6-10U01-WATR-001-BC1A1B;S-101;")
        assert result.is_valid is True

    def test_validate_empty(self):
        result = LineNumber.validate("")
        assert result.is_valid is False

    def test_validate_invalid_format(self):
        result = LineNumber.validate("invalid-stuff")
        assert result.is_valid is False
        assert result.error_message is not None

    def test_raw_line_number_stored(self):
        """raw_line_number should store the line portion only (before delimiter)."""
        ln = LineNumber.parse("6-10U01-WATR-001-BC1A1B;S-101;")
        assert ln is not None
        assert ln.raw_line_number == "6-10U01-WATR-001-BC1A1B"


class TestParseStreamFromNotes:
    """Tests for the parse_stream_from_notes helper."""

    def test_parse_stream(self):
        assert parse_stream_from_notes("6-10U01-WATR-001-BC1A1B;S-101;") == "S-101"

    def test_no_stream(self):
        assert parse_stream_from_notes("6-10U01-WATR-001-BC1A1B") is None

    def test_empty_stream(self):
        """Empty second field after delimiter should return None."""
        assert parse_stream_from_notes("6-10U01-WATR-001-BC1A1B;;") is None

    def test_empty_notes(self):
        assert parse_stream_from_notes("") is None
        assert parse_stream_from_notes("  ") is None


# =========================================================================
# PMS Functions (simplified API)
# =========================================================================


class TestPmsFunctions:
    """Tests for the simplified PMS function API."""

    def test_load_pms(self):
        """load_pms() returns (material, pms_data, od_data). Roughness is in pms_data[pms_code]["roughness"]."""
        material, pms_data, od_data = load_pms(PMS_JSON, "Steel")
        assert material == "Steel"
        assert "BC1A1B-FDA" in pms_data
        # Check that 6.0 inch has schedule "STD" or value "STD"
        spec = pms_data["BC1A1B-FDA"][6.0]
        assert spec.get("value") == "SCH STD" or spec.get("schedule") == "STD"

    def test_load_pms_roughness_in_pms_data(self):
        """Roughness is stored in pms_data[pms_code][\"roughness\"] as float."""
        import json
        import tempfile
        from pathlib import Path

        # Create test JSON with roughness
        test_data = {
            "Steel": {
                "specifications": {"TEST-PMS": {"roughness": 46.5, "6": "SCH 80", "8": "SCH 40"}}
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            temp_path = Path(f.name)

        try:
            material, pms_data, od_data = load_pms(temp_path, "Steel")
            # Roughness should be accessible directly in pms_data
            assert "TEST-PMS" in pms_data
            assert pms_data["TEST-PMS"]["roughness"] == 46.5
            # Schedule data should also be present
            assert pms_data["TEST-PMS"][6.0]["value"] == "SCH 80"
        finally:
            temp_path.unlink()

    def test_lookup_schedule_exact(self):
        """lookup_schedule() finds exact size matches."""
        material, pms_data, od_data = load_pms(PMS_JSON, "Steel")
        spec = lookup_schedule(pms_data, "BC1A1B-FDA", 6.0)
        assert spec.get("value") == "SCH STD" or spec.get("schedule") == "STD"

    def test_lookup_schedule_exact_required(self):
        """lookup_schedule() requires exact NPS match - no fallback to closest."""
        material, pms_data, od_data = load_pms(PMS_JSON, "Steel")
        from pykorf.use_case.exceptions import PmsLookupError

        # 5.5 is not in the table - should raise error
        with pytest.raises(PmsLookupError, match="not defined"):
            lookup_schedule(pms_data, "BC1A1B-FDA", 5.5)

        # Exact match should still work
        spec = lookup_schedule(pms_data, "BC1A1B-FDA", 6.0)
        assert spec.get("value") == "SCH STD" or spec.get("schedule") == "STD"

    def test_lookup_schedule_unknown_class(self):
        """lookup_schedule() raises for unknown PMS class."""
        material, pms_data, od_data = load_pms(PMS_JSON, "Steel")
        from pykorf.use_case.exceptions import PmsLookupError

        with pytest.raises(PmsLookupError, match="PMS class not found"):
            lookup_schedule(pms_data, "UNKNOWN-CLASS", 6.0)

    def test_apply_pms(self):
        """apply_pms() applies PMS specs directly to pipes and returns list of updated pipes."""
        model = Model(PUMP_KDF)
        # Set NOTES on pipe L1
        model.pipes[1].notes = "6-10U01-WATR-001-BC1A1B-FDA;S-101;"

        updated_pipes = apply_pms(PMS_JSON, model, save=False)

        assert "L1" in updated_pipes
        # Verify params were applied directly
        dia_values = model.pipes[1]._values(Pipe.DIA)
        assert dia_values[0] == "6"
        assert dia_values[1] == "6"
        assert dia_values[2] == "inch"
        sch_values = model.pipes[1]._values(Pipe.SCH)
        assert sch_values == ["STD"]
        mat_values = model.pipes[1]._values(Pipe.MAT)
        assert mat_values == ["Steel"]


# =========================================================================
# HMB Functions (simplified API)
# =========================================================================


class TestHmbFunctions:
    """Tests for the simplified HMB function API."""

    def test_load_hmb(self):
        """load_hmb() returns {stream_no: {property: value}}."""
        hmb_data = load_hmb(HMB_JSON)
        assert "S-101" in hmb_data
        assert hmb_data["S-101"]["temp"] == 55.0
        assert hmb_data["S-101"]["pres"] == 101.0

    def test_lookup_stream(self):
        """lookup_stream() finds stream properties."""
        hmb_data = load_hmb(HMB_JSON)
        props = lookup_stream(hmb_data, "S-101")
        assert props["temp"] == 55.0
        assert props["pres"] == 101.0

    def test_lookup_stream_not_found(self):
        """lookup_stream() raises for unknown stream."""
        hmb_data = load_hmb(HMB_JSON)
        from pykorf.use_case.exceptions import StreamNotFoundError

        with pytest.raises(StreamNotFoundError, match="Stream not found"):
            lookup_stream(hmb_data, "S-999")

    def test_apply_hmb(self):
        """apply_hmb() applies fluid props directly to pipes and returns list of updated pipes."""
        model = Model(PUMP_KDF)
        # Set NOTES on pipe L1
        model.pipes[1].notes = "6-10U01-WATR-001-BC1A1B-FDA;S-101;"

        updated_pipes = apply_hmb(HMB_JSON, model, save=False)

        assert "L1" in updated_pipes
        # Verify fluid was applied directly
        temp_values = model.pipes[1]._values(Pipe.TEMP)
        assert float(temp_values[0]) == 55.0
        pres_values = model.pipes[1]._values(Pipe.PRES)
        assert float(pres_values[0]) == 101.0
        liqden_values = model.pipes[1]._values(Pipe.LIQDEN)
        assert float(liqden_values[0]) == 1010.0


# =========================================================================
# HMB Reader (legacy class API)
# =========================================================================


class TestHmbReader:
    """Tests for HmbReader loading and lookup."""

    @pytest.fixture()
    def hmb(self) -> HmbReader:
        reader = HmbReader(INPUT_DIR)
        reader.load_json(HMB_JSON)
        return reader

    def test_load_json(self, hmb: HmbReader):
        streams = hmb.get_all_streams()
        assert "S-101" in streams

    def test_lookup_stream(self, hmb: HmbReader):
        props = hmb.lookup("S-101")
        assert props is not None
        assert props.temp == 55.0
        assert props.pres == 101.0
        assert props.lf == 1.0
        assert props.liqden == 1010.0

    def test_lookup_unknown_stream(self, hmb: HmbReader):
        assert hmb.lookup("S-999") is None

    def test_fluid_properties_defaults(self):
        fp = FluidProperties(stream_no="X")
        assert fp.temp is None
        assert fp.liqvisc is None
        assert fp.vapden is None


# =========================================================================
# UseCaseSettings
# =========================================================================


class TestUseCaseSettings:
    """Tests for UseCaseSettings defaults."""

    def test_defaults(self):
        s = UseCaseSettings()
        assert s.notes_delimiter == ";"
        assert s.default_material == "Carbon Steel"
        assert s.pms_file is None
        assert s.hmb_file is None


# =========================================================================
# PipedataProcessor
# =========================================================================


class TestPipedataProcessor:
    """Tests for the main PipedataProcessor class."""

    @pytest.fixture()
    def processor(self) -> PipedataProcessor:
        """Create a processor with PMS and HMB data loaded."""
        proc = PipedataProcessor()
        proc.load_pms(PMS_JSON)
        proc.load_hmb(HMB_JSON)
        return proc

    # ------------------------------------------------------------------
    # Model-based processing (in-memory)
    # ------------------------------------------------------------------

    def test_process_model_in_memory(self, processor: PipedataProcessor):
        """Process an in-memory Model — pipes with valid NOTES get updated."""
        model = Model(PUMP_KDF)
        # Set NOTES on pipe L1 with a valid line number + stream
        pipe = model.pipes[1]
        pipe.notes = "6-10U01-WATR-001-BC1A1B-FDA;S-101;"

        result = processor.process_kdf(model, save=False)

        assert result.pipes_processed == model.num_pipes
        # L1 should succeed
        l1_result = next(r for r in result.pipe_results if r.pipe_name == "L1")
        assert l1_result.success is True
        assert l1_result.line_number == "6-10U01-WATR-001-BC1A1B-FDA"
        assert l1_result.stream_no == "S-101"
        assert l1_result.pms_schedule == "STD"
        assert l1_result.pms_material == "Steel"
        assert l1_result.fluid_temp == 55.0
        assert l1_result.fluid_pres == 101.0

    def test_pipe_dia_updated_correctly(self, processor: PipedataProcessor):
        """DIA should be set to [nominal, nominal, 'inch']."""
        model = Model(PUMP_KDF)
        model.pipes[1].notes = "6-10U01-WATR-001-BC1A1B-FDA;S-101;"

        processor.process_kdf(model, save=False)

        dia_values = model.pipes[1]._values(Pipe.DIA)
        assert dia_values[0] == "6"
        assert dia_values[1] == "6"
        assert dia_values[2] == "inch"

    def test_pipe_sch_updated_correctly(self, processor: PipedataProcessor):
        """SCH should be set to the PMS schedule value."""
        model = Model(PUMP_KDF)
        model.pipes[1].notes = "6-10U01-WATR-001-BC1A1B-FDA;S-101;"

        processor.process_kdf(model, save=False)

        sch_values = model.pipes[1]._values(Pipe.SCH)
        assert sch_values == ["STD"]  # 6-inch BC1A1B-FDA is SCH STD

    def test_pipe_mat_updated_correctly(self, processor: PipedataProcessor):
        """MAT should be set to the PMS material."""
        model = Model(PUMP_KDF)
        model.pipes[1].notes = "6-10U01-WATR-001-BC1A1B-FDA;S-101;"

        processor.process_kdf(model, save=False)

        mat_values = model.pipes[1]._values(Pipe.MAT)
        assert mat_values == ["Steel"]

    def test_pipe_roughness_updated(self, processor: PipedataProcessor):
        """EPS should be set from PMS roughness (mm → m)."""
        model = Model(PUMP_KDF)
        model.pipes[1].notes = "6-10U01-WATR-001-BC1A1B-FDA;S-101;"

        processor.process_kdf(model, save=False)

        eps_values = model.pipes[1]._values(Pipe.ROUGHNESS)
        assert eps_values[0] == str(0.000046)
        assert float(eps_values[1]) == pytest.approx(0.000046, abs=1e-7)
        assert eps_values[2] == "m"

    def test_pipe_fluid_updated(self, processor: PipedataProcessor):
        """Fluid properties from HMB should be applied to the pipe."""
        model = Model(PUMP_KDF)
        model.pipes[1].notes = "6-10U01-WATR-001-BC1A1B-FDA;S-101;"

        processor.process_kdf(model, save=False)

        # Check that TEMP, PRES, LIQDEN are set
        temp_values = model.pipes[1]._values(Pipe.TEMP)
        assert float(temp_values[0]) == 55.0
        pres_values = model.pipes[1]._values(Pipe.PRES)
        assert float(pres_values[0]) == 101.0
        liqden_values = model.pipes[1]._values(Pipe.LIQDEN)
        assert float(liqden_values[0]) == 1010.0

    def test_pipes_without_notes_fail_gracefully(self):
        """Pipes with empty NOTES should not raise — just report failure."""
        # Create processor WITHOUT PMS/HMB loaded
        proc = PipedataProcessor()
        model = Model(PUMP_KDF)
        # Clear any existing NOTES from previous test runs
        for idx in range(1, model.num_pipes + 1):
            model.pipes[idx].notes = ""
        # Now all pipes have empty NOTES → all should fail gracefully
        result = proc.process_kdf(model, save=False)

        assert result.pipes_processed == model.num_pipes
        assert result.pipes_updated == 0
        assert len(result.errors) == model.num_pipes

    def test_invalid_line_number_fails_gracefully(self, processor: PipedataProcessor):
        """Invalid line number format in NOTES should fail gracefully."""
        model = Model(PUMP_KDF)
        model.pipes[1].notes = "invalid-stuff;S-101;"

        result = processor.process_kdf(model, save=False)

        l1_result = next(r for r in result.pipe_results if r.pipe_name == "L1")
        assert l1_result.success is False
        assert "parse" in l1_result.error.lower()

    def test_unknown_pms_class_fails_gracefully(self, processor: PipedataProcessor):
        """Unknown piping class should fail gracefully."""
        model = Model(PUMP_KDF)
        # Use a piping class + coating code that doesn't exist in PMS data
        model.pipes[1].notes = "6-10U01-WATR-001-XXXXXX-ZZZ;S-101;"

        result = processor.process_kdf(model, save=False)

        l1_result = next(r for r in result.pipe_results if r.pipe_name == "L1")
        assert l1_result.success is False
        assert l1_result.error is not None and "PMS" in l1_result.error

    def test_unknown_stream_fails_gracefully(self, processor: PipedataProcessor):
        """Unknown stream number should fail gracefully."""
        model = Model(PUMP_KDF)
        # Use valid PMS code (BC1A1B-FDA) but unknown stream
        model.pipes[1].notes = "6-10U01-WATR-001-BC1A1B-FDA;S-999;"

        result = processor.process_kdf(model, save=False)

        l1_result = next(r for r in result.pipe_results if r.pipe_name == "L1")
        assert l1_result.success is False
        assert l1_result.error is not None and "Stream" in l1_result.error

    # ------------------------------------------------------------------
    # File-based processing
    # ------------------------------------------------------------------

    def test_process_kdf_file(self, processor: PipedataProcessor, tmp_path: Path):
        """Process a KDF file from disk — should save automatically."""
        kdf_copy = tmp_path / "test.kdf"
        shutil.copy(PUMP_KDF, kdf_copy)

        # Pre-modify the copied file to add NOTES
        model = Model(kdf_copy)
        model.pipes[1].notes = "6-10U01-WATR-001-BC1A1B-FDA;S-101;"
        model.save(kdf_copy)

        result = processor.process_kdf(kdf_copy)

        assert result.pipes_processed > 0
        assert result.file_path == kdf_copy

        # Verify changes persisted to disk
        reloaded = Model(kdf_copy)
        assert reloaded.pipes[1].diameter_inch == "6"

    def test_process_kdf_file_not_found(self, processor: PipedataProcessor):
        """Processing a non-existent file should raise ProcessError."""
        with pytest.raises(ProcessError, match="File not found"):
            processor.process_kdf(Path("nonexistent.kdf"))

    def test_process_model_no_save_by_default(self, processor: PipedataProcessor):
        """When passing a Model, save=False by default."""
        model = Model(PUMP_KDF)
        result = processor.process_kdf(model)
        # Should not raise — no save attempted on the read-only sample file
        assert result.pipes_processed == model.num_pipes

    def test_process_model_with_explicit_save(self, processor: PipedataProcessor, tmp_path: Path):
        """Passing save=True with save_path should write to disk."""
        model = Model(PUMP_KDF)
        model.pipes[1].notes = "6-10U01-WATR-001-BC1A1B-FDA;S-101;"

        out_path = tmp_path / "output.kdf"
        result = processor.process_kdf(model, save=True, save_path=out_path)

        assert out_path.exists()
        reloaded = Model(out_path)
        assert reloaded.pipes[1].diameter_inch == "6"

    # ------------------------------------------------------------------
    # Processor without PMS / HMB
    # ------------------------------------------------------------------

    def test_processor_without_pms(self):
        """Processor without PMS loaded should still parse line numbers."""
        proc = PipedataProcessor()
        proc.load_hmb(HMB_JSON)
        # No PMS loaded

        model = Model(PUMP_KDF)
        model.pipes[1].notes = "6-10U01-WATR-001-BC1A1B-FDA;S-101;"

        result = proc.process_kdf(model, save=False)

        l1_result = next(r for r in result.pipe_results if r.pipe_name == "L1")
        # Should succeed — PMS is skipped when not loaded
        assert l1_result.success is True
        assert l1_result.pms_schedule is None
        assert l1_result.fluid_temp is not None

    def test_processor_without_hmb(self):
        """Processor without HMB loaded should still apply PMS data."""
        proc = PipedataProcessor()
        proc.load_pms(PMS_JSON)
        # No HMB loaded

        model = Model(PUMP_KDF)
        model.pipes[1].notes = "6-10U01-WATR-001-BC1A1B-FDA;S-101;"

        result = proc.process_kdf(model, save=False)

        l1_result = next(r for r in result.pipe_results if r.pipe_name == "L1")
        assert l1_result.success is True
        assert l1_result.pms_schedule is not None
        assert l1_result.fluid_temp is None

    # ------------------------------------------------------------------
    # Validate helper
    # ------------------------------------------------------------------

    def test_validate_method(self):
        proc = PipedataProcessor()
        result = proc.validate("6-10U01-WATR-001-BC1A1B;S-101;")
        assert result.is_valid is True

        result = proc.validate("bad-string")
        assert result.is_valid is False

    # ------------------------------------------------------------------
    # Process folder
    # ------------------------------------------------------------------

    def test_process_folder(self, processor: PipedataProcessor, tmp_path: Path):
        """process_folder should process all *.kdf files in a directory."""
        # Create two KDF files with NOTES
        for name in ("a.kdf", "b.kdf"):
            dest = tmp_path / name
            shutil.copy(PUMP_KDF, dest)
            m = Model(dest)
            m.pipes[1].notes = "6-10U01-WATR-001-BC1A1B-FDA;S-101;"
            m.save(dest)

        results = processor.process_folder(tmp_path)

        assert len(results) == 2
        for r in results:
            assert r.pipes_processed > 0

    def test_process_folder_empty(self, processor: PipedataProcessor, tmp_path: Path):
        """Empty folder should return empty results."""
        results = processor.process_folder(tmp_path)
        assert results == []
