"""Tests for KDF ↔ DataFrame ↔ Excel round-trip conversion.

Verifies that converting a .kdf file through DataFrames (and optionally
through an Excel workbook) produces an identical .kdf file.

Run with:  PYTHONPATH=. python -m pytest tests/test_dataframe.py -v
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from pykorf.model import Model

SAMPLES_DIR = Path(__file__).parent.parent / "pykorf" / "library"
PUMP_KDF = SAMPLES_DIR / "Pumpcases.kdf"
CRANE_KDF = SAMPLES_DIR / "crane10.kdf"
NEW_KDF = SAMPLES_DIR / "New.kdf"
CWC_KDF = SAMPLES_DIR / "Cooling Water Circuit.kdf"


# ---- helper ---------------------------------------------------------------


def _read_bytes(path: Path) -> bytes:
    """Read a file as raw bytes for binary comparison."""
    return path.read_bytes()


def _save_model_bytes(model: Model) -> bytes:
    """Save a model to a temp file and return the raw bytes."""
    with tempfile.NamedTemporaryFile(suffix=".kdf", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        model.save(tmp_path, check_layout=False)
        return Path(tmp_path).read_bytes()
    finally:
        Path(tmp_path).unlink(missing_ok=True)


# ---- to_dataframes / from_dataframes -------------------------------------


class TestToDataframes:
    """Tests for Model.to_dataframes()."""

    def test_returns_dict_of_dataframes(self):
        import pandas as pd

        model = Model(PUMP_KDF)
        dfs = model.to_dataframes()
        assert isinstance(dfs, dict)
        for key, df in dfs.items():
            assert isinstance(df, pd.DataFrame), f"Sheet {key!r} is not a DataFrame"

    def test_has_header_and_element_sheets(self):
        model = Model(PUMP_KDF)
        dfs = model.to_dataframes()
        assert "_HEADER" in dfs
        assert "GEN" in dfs
        assert "PIPE" in dfs

    def test_header_df_has_required_columns(self):
        model = Model(PUMP_KDF)
        dfs = model.to_dataframes()
        header_df = dfs["_HEADER"]
        assert "line_no" in header_df.columns
        assert "raw_line" in header_df.columns

    def test_element_df_has_required_columns(self):
        model = Model(PUMP_KDF)
        dfs = model.to_dataframes()
        pipe_df = dfs["PIPE"]
        for col in ("line_no", "element_type", "index", "param", "raw_line"):
            assert col in pipe_df.columns, f"Missing column {col!r} in PIPE DataFrame"

    def test_default_model(self):
        """Blank model (New.kdf) should also produce valid DataFrames."""
        model = Model()
        dfs = model.to_dataframes()
        assert "_HEADER" in dfs
        assert "GEN" in dfs


class TestDataframeRoundTrip:
    """KDF → DataFrame → KDF round-trip tests."""

    @pytest.mark.parametrize(
        "kdf_path",
        [PUMP_KDF, CRANE_KDF, NEW_KDF, CWC_KDF],
        ids=["Pumpcases", "crane10", "New", "CWC"],
    )
    def test_roundtrip_via_dataframes(self, kdf_path: Path):
        """Model → to_dataframes → from_dataframes → save must produce identical bytes."""
        original = Model(kdf_path)
        original_bytes = _save_model_bytes(original)

        dfs = original.to_dataframes()
        reconstructed = Model.from_dataframes(dfs)
        reconstructed_bytes = _save_model_bytes(reconstructed)

        assert original_bytes == reconstructed_bytes, (
            f"Round-trip mismatch for {kdf_path.name}"
        )


# ---- to_excel / from_excel ------------------------------------------------


class TestExcelRoundTrip:
    """KDF → DataFrame → Excel → DataFrame → KDF round-trip tests."""

    @pytest.mark.parametrize(
        "kdf_path",
        [PUMP_KDF, CRANE_KDF, NEW_KDF, CWC_KDF],
        ids=["Pumpcases", "crane10", "New", "CWC"],
    )
    def test_roundtrip_via_excel(self, kdf_path: Path):
        """Model → to_excel → from_excel → save must produce identical bytes."""
        original = Model(kdf_path)
        original_bytes = _save_model_bytes(original)

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            xlsx_path = tmp.name

        try:
            original.to_excel(xlsx_path)
            reconstructed = Model.from_excel(xlsx_path)
            reconstructed_bytes = _save_model_bytes(reconstructed)

            assert original_bytes == reconstructed_bytes, (
                f"Excel round-trip mismatch for {kdf_path.name}"
            )
        finally:
            Path(xlsx_path).unlink(missing_ok=True)

    def test_excel_sheets_match_dataframes(self):
        """Excel workbook should have the same sheets as to_dataframes()."""
        import pandas as pd

        model = Model(PUMP_KDF)
        dfs = model.to_dataframes()

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            xlsx_path = tmp.name

        try:
            model.to_excel(xlsx_path)
            xls = pd.ExcelFile(xlsx_path, engine="openpyxl")
            assert set(xls.sheet_names) == set(dfs.keys())
        finally:
            Path(xlsx_path).unlink(missing_ok=True)


# ---- functional-level tests -----------------------------------------------


class TestExportFunctions:
    """Tests for the standalone export functions."""

    def test_model_to_dataframes_function(self):
        from pykorf.export import model_to_dataframes

        model = Model(PUMP_KDF)
        dfs = model_to_dataframes(model)
        assert isinstance(dfs, dict)
        assert "_HEADER" in dfs

    def test_dataframes_to_kdf_function(self):
        from pykorf.export import dataframes_to_kdf, model_to_dataframes

        model = Model(PUMP_KDF)
        original_bytes = _save_model_bytes(model)

        dfs = model_to_dataframes(model)
        with tempfile.NamedTemporaryFile(suffix=".kdf", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            dataframes_to_kdf(dfs, tmp_path)
            assert Path(tmp_path).read_bytes() == original_bytes
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_dataframes_to_excel_and_back(self):
        from pykorf.export import (
            dataframes_to_excel,
            excel_to_dataframes,
            model_to_dataframes,
        )

        model = Model(PUMP_KDF)
        dfs = model_to_dataframes(model)

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            xlsx_path = tmp.name

        try:
            dataframes_to_excel(dfs, xlsx_path)
            dfs_back = excel_to_dataframes(xlsx_path)
            assert set(dfs_back.keys()) == set(dfs.keys())
            for key in dfs:
                assert len(dfs_back[key]) == len(dfs[key]), (
                    f"Row count mismatch for sheet {key!r}"
                )
        finally:
            Path(xlsx_path).unlink(missing_ok=True)


# ---- model property preservation ------------------------------------------


class TestModelPreservation:
    """Verify that reconstructed models have identical properties."""

    def test_version_preserved(self):
        model = Model(PUMP_KDF)
        dfs = model.to_dataframes()
        reconstructed = Model.from_dataframes(dfs)
        assert reconstructed.version == model.version

    def test_element_counts_preserved(self):
        model = Model(PUMP_KDF)
        dfs = model.to_dataframes()
        reconstructed = Model.from_dataframes(dfs)
        assert reconstructed.num_pipes == model.num_pipes
        assert reconstructed.num_pumps == model.num_pumps
        assert reconstructed.num_cases == model.num_cases

    def test_element_names_preserved(self):
        model = Model(PUMP_KDF)
        original_names = sorted(e.name for e in model.elements)
        dfs = model.to_dataframes()
        reconstructed = Model.from_dataframes(dfs)
        reconstructed_names = sorted(e.name for e in reconstructed.elements)
        assert reconstructed_names == original_names

    def test_summary_preserved(self):
        model = Model(CWC_KDF)
        dfs = model.to_dataframes()
        reconstructed = Model.from_dataframes(dfs)
        orig = model.summary()
        recon = reconstructed.summary()
        # File path will differ (temp file); compare everything else
        del orig["file"]
        del recon["file"]
        assert recon == orig
