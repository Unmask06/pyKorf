"""Tests for the pykorf.app.operation and pykorf.app.api packages.

Covers:
- ReferencesStore persistence round-trip
- sharepoint.get_sharepoint_url with mocked registry data
- Session stale detection with pykorf.app.api.session_state

Run with:  pytest tests/test_web.py -v
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

SAMPLES_DIR = Path(__file__).parent.parent / "pykorf" / "library"
PUMP_KDF = SAMPLES_DIR / "Pumpcases.kdf"


# ── ReferencesStore ────────────────────────────────────────────────────────────


class TestReferencesStore:
    def test_empty_load_when_no_sidecar(self, tmp_path: Path) -> None:
        from pykorf.app.operation.project.references import ReferencesStore

        kdf = tmp_path / "model.kdf"
        kdf.write_text("", encoding="utf-8")
        store = ReferencesStore.load(kdf)
        assert store.basis == ""
        assert store.references == []

    def test_save_and_reload(self, tmp_path: Path) -> None:
        from pykorf.app.operation.project.references import Reference, ReferencesStore

        kdf = tmp_path / "model.kdf"
        kdf.write_text("", encoding="utf-8")

        store = ReferencesStore(basis="Design notes")
        store.add(Reference.new(name="P&ID-001", link="https://sp.example.com/pid"))
        store.save(kdf)

        sidecar = tmp_path / "model.pykorf"
        assert sidecar.is_file()

        loaded = ReferencesStore.load(kdf)
        assert loaded.basis == "Design notes"
        assert len(loaded.references) == 1
        assert loaded.references[0].name == "P&ID-001"

    def test_corrupt_sidecar_returns_empty(self, tmp_path: Path) -> None:
        from pykorf.app.operation.project.references import ReferencesStore

        kdf = tmp_path / "model.kdf"
        kdf.write_text("", encoding="utf-8")
        sidecar = tmp_path / "model.pykorf"
        sidecar.write_text("not valid json", encoding="utf-8")

        store = ReferencesStore.load(kdf)
        assert store.references == []

    def test_add_update_delete(self, tmp_path: Path) -> None:
        from pykorf.app.operation.project.references import Reference, ReferencesStore

        store = ReferencesStore()
        ref = Reference.new(name="Doc A", link="https://example.com")
        store.add(ref)
        assert len(store.references) == 1

        store.update(ref.id, name="Doc B")
        assert store.references[0].name == "Doc B"

        deleted = store.delete(ref.id)
        assert deleted is True
        assert store.references == []

    def test_delete_nonexistent_returns_false(self) -> None:
        from pykorf.app.operation.project.references import ReferencesStore

        store = ReferencesStore()
        assert store.delete("nonexistent-id") is False

    def test_to_dataframe_columns(self, tmp_path: Path) -> None:
        from pykorf.app.operation.project.references import Reference, ReferencesStore

        store = ReferencesStore()
        store.add(Reference.new(name="X", link="https://x.com", category="P&ID"))
        df = store.to_dataframe()
        assert list(df.columns) == ["Name", "Category", "Link", "Description"]
        assert len(df) == 1

    def test_safe_filename_strips_illegal_chars(self) -> None:
        from pykorf.app.operation.project.references import ReferencesStore

        assert ReferencesStore._safe_filename('P&ID: "Foo"') == "P&ID_ _Foo_"

    def test_sidecar_is_valid_json(self, tmp_path: Path) -> None:
        from pykorf.app.operation.project.references import Reference, ReferencesStore

        kdf = tmp_path / "model.kdf"
        kdf.write_text("", encoding="utf-8")
        store = ReferencesStore(basis="notes")
        store.add(Reference.new(name="R1", link="https://a.com"))
        store.save(kdf)

        raw = (tmp_path / "model.pykorf").read_text(encoding="utf-8")
        data = json.loads(raw)
        assert "basis" in data
        assert "references" in data


# ── sharepoint.get_sharepoint_url ──────────────────────────────────────────────


class TestSharepointUrl:
    def test_returns_none_when_no_sync_roots(self) -> None:
        from pykorf.app.operation.integration.sharepoint import get_sharepoint_url

        with patch("pykorf.app.operation.integration.sharepoint._read_sync_roots", return_value=[]):
            result = get_sharepoint_url(r"C:\Users\alice\Documents\model.kdf")
        assert result is None

    def test_maps_local_to_sharepoint_url(self) -> None:
        from pykorf.app.operation.integration.sharepoint import get_sharepoint_url

        roots = [
            (
                r"C:\Users\alice\Company\ProjectA\Documents",
                "https://company.sharepoint.com/sites/ProjectA/Documents",
            ),
        ]
        with patch(
            "pykorf.app.operation.integration.sharepoint._read_sync_roots", return_value=roots
        ):
            url = get_sharepoint_url(r"C:\Users\alice\Company\ProjectA\Documents\model.kdf")
        assert url == "https://company.sharepoint.com/sites/ProjectA/Documents/model.kdf"

    def test_special_chars_encoded_in_url(self) -> None:
        from pykorf.app.operation.integration.sharepoint import get_sharepoint_url

        roots = [
            (r"C:\Users\alice\SP", "https://company.sharepoint.com/sites/SP"),
        ]
        with patch(
            "pykorf.app.operation.integration.sharepoint._read_sync_roots", return_value=roots
        ):
            url = get_sharepoint_url(r"C:\Users\alice\SP\P&ID 001.pdf")
        assert url is not None
        assert "%26" in url  # & encoded
        assert "%20" in url  # space encoded

    def test_non_matching_path_returns_none(self) -> None:
        from pykorf.app.operation.integration.sharepoint import get_sharepoint_url

        roots = [
            (r"C:\Users\alice\OneDrive", "https://company.sharepoint.com/personal/alice"),
        ]
        with patch(
            "pykorf.app.operation.integration.sharepoint._read_sync_roots", return_value=roots
        ):
            result = get_sharepoint_url(r"D:\OtherDrive\model.kdf")
        assert result is None


# ── Session stale detection (FastAPI session_state) ────────────────────────────


class TestSessionStaleDetection:
    def test_is_stale_false_on_fresh_load(self, tmp_path: Path) -> None:
        from pykorf.app.api.session_state import load_sync, is_stale_sync, clear_sync
        from pykorf import Model

        kdf = tmp_path / "model.kdf"
        kdf.write_bytes(b"test content")
        model = Model(kdf)
        load_sync(model, kdf)

        assert is_stale_sync() is False

        clear_sync()

    def test_is_stale_true_after_file_modified(self, tmp_path: Path) -> None:
        from pykorf.app.api.session_state import load_sync, is_stale_sync, clear_sync
        from pykorf import Model

        kdf = tmp_path / "model.kdf"
        kdf.write_bytes(b"test content")
        model = Model(kdf)
        load_sync(model, kdf)

        import time

        time.sleep(0.01)
        kdf.write_bytes(b"modified content")

        assert is_stale_sync() is True

        clear_sync()

    def test_is_stale_false_after_reload(self, tmp_path: Path) -> None:
        from pykorf.app.api.session_state import load_sync, is_stale_sync, reload_sync, clear_sync
        from pykorf import Model

        kdf = tmp_path / "model.kdf"
        kdf.write_bytes(b"test content")
        model = Model(kdf)
        load_sync(model, kdf)

        import time

        time.sleep(0.01)
        kdf.write_bytes(b"modified content")

        reload_sync()
        assert is_stale_sync() is False

        clear_sync()

    def test_is_stale_false_when_no_model(self) -> None:
        from pykorf.app.api.session_state import clear_sync, is_stale_sync

        clear_sync()
        assert is_stale_sync() is False

    def test_is_stale_false_when_file_deleted(self, tmp_path: Path) -> None:
        from pykorf.app.api.session_state import load_sync, is_stale_sync, clear_sync
        from pykorf import Model

        kdf = tmp_path / "model.kdf"
        kdf.write_bytes(b"test content")
        model = Model(kdf)
        load_sync(model, kdf)

        kdf.unlink()

        assert is_stale_sync() is False

        clear_sync()
