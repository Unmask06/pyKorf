"""Tests for the Document Register module.

Covers:
- Config functions (preferences)
- Excel-to-DB conversion (excel_to_db) — FE EDDR, DE EDDR, Process/Client/Mechanical
- SQLAlchemy operations (db_ops)
- FastAPI routes (routers/doc_register)
"""

from __future__ import annotations

import os
import tempfile
from datetime import datetime, UTC
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from pykorf.app.operation.config.preferences import (
    get_doc_register_db_last_imported,
    get_doc_register_excel_path,
    get_doc_register_sp_site_url,
    set_doc_register_db_last_imported,
    set_doc_register_excel_path,
    set_doc_register_sp_site_url,
)


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def sample_fe_eddr_df():
    return pd.DataFrame(
        {
            "Document No": ["DOC-001", "DOC-002", "DOC-003"],
            "Title": [
                "Process and Instrument Diagram",
                "Single Line Diagram",
                "Equipment Datasheet",
            ],
        }
    )


@pytest.fixture
def sample_de_eddr_df():
    return pd.DataFrame(
        {
            "COMPANY DOCUMENT NUMBER": ["DOC-004", "DOC-005"],
            "DESCRIPTION": [
                "Detailed Engineering P&ID",
                "Detailed Engineering Datasheet",
            ],
            "CONTRACTOR DOCUMENT NUMBER": ["CTR-001", "CTR-002"],
        }
    )


@pytest.fixture
def sample_sp_df():
    """SharePoint-extracted sheet content (Process/Client/Mechanical share this layout)."""
    return pd.DataFrame(
        {
            "Name": ["DOC-001 Rev A.pdf", "DOC-001 Rev B.pdf", "DOC-002 Folder", "OTHER.docx"],
            "Modified": ["2025-01-15", "2025-02-20", "2025-01-10", "2025-03-01"],
            "Modified By": ["Alice", "Bob", "Alice", "Charlie"],
            "Path": [
                "sites/Project/Documents/folder1",
                "sites/Project/Documents/folder1",
                "sites/Project/Documents",
                "sites/Project/Other",
            ],
            "Item Type": ["Item", "Item", "Folder", "Item"],
        }
    )


@pytest.fixture
def sample_excel_path(sample_fe_eddr_df, sample_de_eddr_df, sample_sp_df):
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        path = Path(f.name)

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        # FE EDDR: title row + header row + data
        fe_with_header = pd.DataFrame(
            [
                ["Project Title Row", None, None],
                ["Sr. No", "Document No", "Title"],
            ]
            + [[i + 1, row["Document No"], row["Title"]] for i, row in sample_fe_eddr_df.iterrows()]
        )
        fe_with_header.to_excel(writer, sheet_name="FE EDDR", index=False, header=False)

        # DE EDDR: title row + header row + data
        de_with_header = pd.DataFrame(
            [
                ["Detailed Engineering Register", None, None],
                ["COMPANY DOCUMENT NUMBER", "DESCRIPTION", "CONTRACTOR DOCUMENT NUMBER"],
            ]
            + [
                [
                    row["COMPANY DOCUMENT NUMBER"],
                    row["DESCRIPTION"],
                    row["CONTRACTOR DOCUMENT NUMBER"],
                ]
                for _, row in sample_de_eddr_df.iterrows()
            ]
        )
        de_with_header.to_excel(writer, sheet_name="DE EDDR", index=False, header=False)

        # SharePoint-extracted sheets (Process/Client/Mechanical) — single header row
        sample_sp_df.to_excel(writer, sheet_name="Process", index=False)
        sample_sp_df.to_excel(writer, sheet_name="Client", index=False)
        sample_sp_df.to_excel(writer, sheet_name="Mechanical", index=False)

    yield path

    path.unlink(missing_ok=True)


@pytest.fixture
def mock_config(tmp_path):
    from pykorf.app.operation.config._core import clear_config_cache

    clear_config_cache()
    config_file = tmp_path / "config.json"
    config_file.write_text("{}", encoding="utf-8")

    with patch("pykorf.app.operation.config._core.get_config_path", return_value=config_file):
        yield config_file


@pytest.fixture
def mock_data_dir(tmp_path):
    from pykorf.app.doc_register.db_ops import reset_engine

    reset_engine()

    data_dir = tmp_path / "data"
    data_dir.mkdir()

    with patch("pykorf.app.doc_register.excel_to_db.ensure_data_dir", return_value=data_dir):
        yield data_dir

    reset_engine()


@pytest.fixture
def populated_db(mock_data_dir, sample_fe_eddr_df, sample_de_eddr_df, sample_sp_df):
    from pykorf.app.doc_register.db_ops import (
        Base,
        DEEDDR,
        FEEDDR,
        SpEntry,
        get_engine,
        reset_engine,
    )

    reset_engine()

    db_path = mock_data_dir / "doc_register.db"
    engine = get_engine()
    Base.metadata.create_all(engine)

    with engine.begin() as conn:
        for _, row in sample_fe_eddr_df.iterrows():
            conn.execute(
                FEEDDR.__table__.insert().values(
                    document_no=row["Document No"],
                    title=row["Title"],
                )
            )
        for _, row in sample_de_eddr_df.iterrows():
            conn.execute(
                DEEDDR.__table__.insert().values(
                    company_document_no=row["COMPANY DOCUMENT NUMBER"],
                    description=row["DESCRIPTION"],
                    contractor_document_no=row["CONTRACTOR DOCUMENT NUMBER"],
                )
            )
        # Insert SP rows for each sheet
        for sheet_name in ("Process", "Client", "Mechanical"):
            for _, row in sample_sp_df.iterrows():
                conn.execute(
                    SpEntry.__table__.insert().values(
                        sheet=sheet_name,
                        name=row["Name"],
                        modified=row["Modified"],
                        modified_by=row["Modified By"],
                        path=row["Path"],
                        item_type=row["Item Type"],
                    )
                )

    yield db_path


# ── Config Function Tests ───────────────────────────────────────────────────


class TestDocRegisterConfig:
    def test_set_and_get_excel_path(self, mock_config):
        set_doc_register_excel_path(r"C:\path\to\Register.xlsx")
        assert get_doc_register_excel_path() == r"C:\path\to\Register.xlsx"

    def test_get_excel_path_not_set(self, mock_config):
        assert get_doc_register_excel_path() is None

    def test_set_and_get_sp_site_url(self, mock_config):
        set_doc_register_sp_site_url("https://tenant.sharepoint.com")
        assert get_doc_register_sp_site_url() == "https://tenant.sharepoint.com"

    def test_sp_site_url_trailing_slash_stripped(self, mock_config):
        set_doc_register_sp_site_url("https://tenant.sharepoint.com/")
        assert get_doc_register_sp_site_url() == "https://tenant.sharepoint.com"

    def test_get_sp_site_url_not_set(self, mock_config):
        assert get_doc_register_sp_site_url() is None

    def test_set_and_get_db_last_imported(self, mock_config):
        ts = datetime.now(UTC).isoformat()
        set_doc_register_db_last_imported(ts)
        assert get_doc_register_db_last_imported() == ts

    def test_get_db_last_imported_not_set(self, mock_config):
        assert get_doc_register_db_last_imported() is None


# ── Excel-to-DB Tests ───────────────────────────────────────────────────────


class TestExcelToDB:
    def test_get_db_path(self, mock_data_dir):
        from pykorf.app.doc_register.excel_to_db import get_db_path

        db_path = get_db_path()
        assert db_path == mock_data_dir / "doc_register.db"

    def test_is_excel_stale_no_config(self, mock_config):
        from pykorf.app.doc_register.excel_to_db import is_excel_stale

        assert is_excel_stale() is False

    def test_is_excel_stale_no_excel(self, mock_config):
        from pykorf.app.doc_register.excel_to_db import is_excel_stale

        set_doc_register_excel_path(r"C:\nonexistent\file.xlsx")
        assert is_excel_stale() is False

    def test_is_excel_stale_no_db(self, mock_config, mock_data_dir, sample_excel_path):
        from pykorf.app.doc_register.excel_to_db import is_excel_stale

        set_doc_register_excel_path(str(sample_excel_path))
        assert is_excel_stale() is True

    def test_is_excel_stale_excel_newer(self, mock_config, mock_data_dir, sample_excel_path):
        from pykorf.app.doc_register.excel_to_db import is_excel_stale

        set_doc_register_excel_path(str(sample_excel_path))
        set_doc_register_db_last_imported("2020-01-01T00:00:00+00:00")
        assert is_excel_stale() is True

    def test_is_excel_stale_db_newer(self, mock_config, mock_data_dir, sample_excel_path):
        import time
        from pykorf.app.doc_register.excel_to_db import build_db_from_excel, is_excel_stale

        set_doc_register_excel_path(str(sample_excel_path))
        old_time = time.time() - 10
        os.utime(sample_excel_path, (old_time, old_time))
        build_db_from_excel(sample_excel_path, "https://tenant.sharepoint.com")
        assert is_excel_stale() is False

    def test_build_db_from_excel(self, mock_config, mock_data_dir, sample_excel_path):
        from pykorf.app.doc_register.excel_to_db import build_db_from_excel
        from pykorf.app.doc_register.db_ops import DEEDDR, FEEDDR, SpEntry, get_engine

        db_path = build_db_from_excel(sample_excel_path, "https://tenant.sharepoint.com")

        assert db_path.exists()

        engine = get_engine()
        with engine.connect() as conn:
            fe_count = conn.execute(FEEDDR.__table__.select()).fetchall()
            de_count = conn.execute(DEEDDR.__table__.select()).fetchall()
            sp_count = conn.execute(SpEntry.__table__.select()).fetchall()

        assert len(fe_count) == 3
        assert len(de_count) == 2
        # 3 sheets x 4 rows each = 12 SP entries
        assert len(sp_count) == 12

    def test_build_db_stamps_sheet_name(self, mock_config, mock_data_dir, sample_excel_path):
        from pykorf.app.doc_register.excel_to_db import build_db_from_excel
        from pykorf.app.doc_register.db_ops import SpEntry, get_engine

        build_db_from_excel(sample_excel_path, "https://tenant.sharepoint.com")

        engine = get_engine()
        with engine.connect() as conn:
            sheets = {
                row[0]
                for row in conn.execute(SpEntry.__table__.select().with_only_columns(SpEntry.sheet))
            }
        assert sheets == {"Process", "Client", "Mechanical"}

    def test_build_db_updates_timestamp(self, mock_config, mock_data_dir, sample_excel_path):
        from pykorf.app.doc_register.excel_to_db import build_db_from_excel

        build_db_from_excel(sample_excel_path, "https://tenant.sharepoint.com")

        ts = get_doc_register_db_last_imported()
        assert ts is not None
        datetime.fromisoformat(ts)

    def test_build_db_skips_missing_sp_sheet(self, mock_config, mock_data_dir, sample_sp_df):
        """If an SP sheet is absent the build should still succeed for the others."""
        from pykorf.app.doc_register.excel_to_db import build_db_from_excel
        from pykorf.app.doc_register.db_ops import SpEntry, get_engine

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            path = Path(f.name)
        try:
            with pd.ExcelWriter(path, engine="openpyxl") as writer:
                fe = pd.DataFrame(
                    [
                        ["Project Title", None, None],
                        ["Sr. No", "Document No", "Title"],
                        [1, "DOC-001", "Title"],
                    ]
                )
                fe.to_excel(writer, sheet_name="FE EDDR", index=False, header=False)
                de = pd.DataFrame(
                    [
                        ["DE Register", None, None],
                        ["COMPANY DOCUMENT NUMBER", "DESCRIPTION", "CONTRACTOR DOCUMENT NUMBER"],
                        [1, "DOC-DE", "Desc", "CTR-1"],
                    ]
                )
                de.to_excel(writer, sheet_name="DE EDDR", index=False, header=False)
                # Only Process + Client — Mechanical intentionally omitted
                sample_sp_df.to_excel(writer, sheet_name="Process", index=False)
                sample_sp_df.to_excel(writer, sheet_name="Client", index=False)

            build_db_from_excel(path, "")

            engine = get_engine()
            with engine.connect() as conn:
                sheets = {
                    row[0]
                    for row in conn.execute(
                        SpEntry.__table__.select().with_only_columns(SpEntry.sheet)
                    )
                }
            assert sheets == {"Process", "Client"}
        finally:
            path.unlink(missing_ok=True)


# ── DB Operations Tests ─────────────────────────────────────────────────────


class TestDBOps:
    def test_search_eddr_fe_match(self, populated_db):
        from pykorf.app.doc_register.db_ops import search_eddr

        results = search_eddr("Single Line")
        assert len(results) == 1
        assert results[0]["document_no"] == "DOC-002"
        assert results[0]["source"] == "FE"
        assert results[0]["contractor_doc_no"] is None
        assert "Single Line" in results[0]["title"]

    def test_search_eddr_de_match(self, populated_db):
        from pykorf.app.doc_register.db_ops import search_eddr

        results = search_eddr("Detailed Engineering")
        assert len(results) == 2
        assert all(r["source"] == "DE" for r in results)
        assert {r["document_no"] for r in results} == {"DOC-004", "DOC-005"}
        # contractor doc no populated for DE rows
        assert {r["contractor_doc_no"] for r in results} == {"CTR-001", "CTR-002"}

    def test_search_eddr_union_fe_and_de(self, populated_db):
        from pykorf.app.doc_register.db_ops import search_eddr

        # "Datasheet" matches FE (DOC-003) and DE (DOC-005)
        results = search_eddr("Datasheet")
        sources = {r["source"] for r in results}
        assert sources == {"FE", "DE"}
        assert len(results) == 2

    def test_search_eddr_no_match(self, populated_db):
        from pykorf.app.doc_register.db_ops import search_eddr

        results = search_eddr("NonExistent")
        assert len(results) == 0

    def test_search_eddr_empty(self, populated_db):
        from pykorf.app.doc_register.db_ops import search_eddr

        results = search_eddr("")
        assert len(results) == 0

    def test_search_eddr_case_insensitive(self, populated_db):
        from pykorf.app.doc_register.db_ops import search_eddr

        results = search_eddr("single line")
        assert len(results) == 1
        assert results[0]["document_no"] == "DOC-002"

    def test_search_eddr_unordered_words(self, populated_db):
        from pykorf.app.doc_register.db_ops import search_eddr

        results = search_eddr("Diagram Instrument Process")
        assert len(results) == 1
        assert results[0]["document_no"] == "DOC-001"

    def test_search_eddr_by_document_no(self, populated_db):
        from pykorf.app.doc_register.db_ops import search_eddr

        results = search_eddr("DOC-002")
        assert len(results) == 1
        assert results[0]["document_no"] == "DOC-002"

    def test_search_eddr_mixed_doc_no_and_title(self, populated_db):
        from pykorf.app.doc_register.db_ops import search_eddr

        results = search_eddr("DOC-001 Instrument")
        assert len(results) == 1
        assert results[0]["document_no"] == "DOC-001"

    def test_search_eddr_unordered_partial_words_no_match(self, populated_db):
        from pykorf.app.doc_register.db_ops import search_eddr

        results = search_eddr("Single Line Nonexistent")
        assert len(results) == 0

    def test_search_eddr_de_by_company_doc_no(self, populated_db):
        from pykorf.app.doc_register.db_ops import search_eddr

        results = search_eddr("DOC-004")
        assert len(results) == 1
        assert results[0]["source"] == "DE"
        assert results[0]["document_no"] == "DOC-004"

    def test_search_sp_entries_match(self, populated_db):
        from pykorf.app.doc_register.db_ops import search_sp_entries

        results = search_sp_entries("DOC-001")
        # 2 matching names x 3 sheets = 6
        assert len(results) == 6
        assert all(r["name"].startswith("DOC-001") for r in results)
        assert all(r["sheet"] in {"Process", "Client", "Mechanical"} for r in results)

    def test_search_sp_entries_no_match(self, populated_db):
        from pykorf.app.doc_register.db_ops import search_sp_entries

        results = search_sp_entries("NONEXISTENT")
        assert len(results) == 0

    def test_search_sp_entries_empty(self, populated_db):
        from pykorf.app.doc_register.db_ops import search_sp_entries

        results = search_sp_entries("")
        assert len(results) == 0

    def test_search_sp_entries_includes_folders(self, populated_db):
        from pykorf.app.doc_register.db_ops import search_sp_entries

        results = search_sp_entries("DOC-002")
        # 1 matching name x 3 sheets = 3
        assert len(results) == 3

    def test_search_sp_entries_sheet_filter(self, populated_db):
        from pykorf.app.doc_register.db_ops import search_sp_entries

        results = search_sp_entries("DOC-001", sheet="Client")
        assert len(results) == 2
        assert all(r["sheet"] == "Client" for r in results)

    def test_search_sp_entries_by_term_scoring(self, populated_db):
        from pykorf.app.doc_register.db_ops import search_sp_entries_by_term

        results = search_sp_entries_by_term("DOC")
        assert len(results) > 0
        names = [r["name"] for r in results]
        assert any("DOC" in name for name in names)
        assert all(r["sheet"] in {"Process", "Client", "Mechanical"} for r in results)

    def test_search_sp_entries_by_term_exact_match_ranks_first(self, populated_db):
        from pykorf.app.doc_register.db_ops import (
            search_sp_entries_by_term,
            reset_engine,
            get_session,
            SpEntry,
        )

        reset_engine()
        session = get_session()
        try:
            session.query(SpEntry).delete()
            test_entries = [
                {
                    "sheet": "Process",
                    "name": "PID-001",
                    "modified": "2024-01-01",
                    "modified_by": "user",
                    "path": "docs",
                    "item_type": "File",
                },
                {
                    "sheet": "Process",
                    "name": "Main-PID-001",
                    "modified": "2024-01-01",
                    "modified_by": "user",
                    "path": "docs",
                    "item_type": "File",
                },
                {
                    "sheet": "Process",
                    "name": "COPY_OF_PID",
                    "modified": "2024-01-01",
                    "modified_by": "user",
                    "path": "docs",
                    "item_type": "File",
                },
            ]
            for entry in test_entries:
                session.add(SpEntry(**entry))
            session.commit()

            results = search_sp_entries_by_term("PID")
            assert len(results) == 3
            assert results[0]["name"] == "PID-001"
            assert results[1]["name"] == "Main-PID-001"
            assert results[2]["name"] == "COPY_OF_PID"
        finally:
            session.close()
            reset_engine()

    def test_construct_sharepoint_url(self):
        from pykorf.app.doc_register.db_ops import construct_sharepoint_url

        url = construct_sharepoint_url(
            "sites/Project/Documents/folder",
            "file.pdf",
            "https://tenant.sharepoint.com",
        )
        assert url == "https://tenant.sharepoint.com/sites/Project/Documents/folder/file.pdf"

    def test_construct_sharepoint_url_strips_slashes(self):
        from pykorf.app.doc_register.db_ops import construct_sharepoint_url

        url = construct_sharepoint_url(
            "/sites/Project/Documents/",
            "/file.pdf",
            "https://tenant.sharepoint.com/",
        )
        assert url == "https://tenant.sharepoint.com/sites/Project/Documents/file.pdf"

    def test_get_db_stats(self, populated_db):
        from pykorf.app.doc_register.db_ops import get_db_stats

        stats = get_db_stats()
        assert stats["db_exists"] is True
        assert stats["fe_eddr_count"] == 3
        assert stats["de_eddr_count"] == 2
        assert stats["sp_count"] == 12

    def test_get_db_stats_no_db(self, mock_data_dir):
        from pykorf.app.doc_register.db_ops import get_db_stats

        stats = get_db_stats()
        assert stats["db_exists"] is False
        assert stats["fe_eddr_count"] == 0
        assert stats["de_eddr_count"] == 0
        assert stats["sp_count"] == 0


# ── API Routes Tests (FastAPI) ──────────────────────────────────────────────


class TestDocRegisterAPI:
    """Tests for the FastAPI doc-register routes."""

    @pytest.fixture
    def client(self, mock_config, mock_data_dir):
        from fastapi.testclient import TestClient
        from pykorf.app.doc_register.db_ops import reset_engine
        from pykorf.app.api.app import create_app

        reset_engine()
        app = create_app()
        with TestClient(app, raise_server_exceptions=True) as c:
            yield c

    def test_status_no_config(self, client):
        resp = client.get("/api/doc-register/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["excel_path"] is None
        assert data["db_exists"] is False
        assert data["is_stale"] is False

    def test_search_eddr_empty(self, client):
        resp = client.get("/api/doc-register/search-eddr?q=")
        assert resp.status_code == 200
        assert resp.json()["results"] == []

    def test_search_query_empty(self, client):
        resp = client.get("/api/doc-register/search-query?doc_no=")
        assert resp.status_code == 200
        assert resp.json()["results"] == []

    def test_search_query_with_sheet_filter(self, client):
        # Sheet filter should be accepted even with empty doc_no
        resp = client.get("/api/doc-register/search-query?doc_no=&sheet=Client")
        assert resp.status_code == 200
        assert resp.json()["results"] == []

    def test_rebuild_db_no_config(self, client):
        resp = client.post("/api/doc-register/rebuild-db", json={})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("error") is not None
        assert data["success"] is False

    def test_config_save(self, client):
        resp = client.post(
            "/api/doc-register/config",
            json={
                "excel_path": r"C:\test\Register.xlsx",
                "sp_site_url": "https://test.sharepoint.com",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["excel_path"] == r"C:\test\Register.xlsx"
        assert data["sp_site_url"] == "https://test.sharepoint.com"
