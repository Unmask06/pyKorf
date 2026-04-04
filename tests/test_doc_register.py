"""Tests for the Document Register module.

Covers:
- Config functions (preferences)
- Excel-to-DB conversion (excel_to_db)
- SQLAlchemy operations (db_ops)
- API routes (routes/doc_register)

Run with: pytest tests/test_doc_register.py -v
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, UTC
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from pykorf.use_case.preferences import (
    get_doc_register_db_last_imported,
    get_doc_register_excel_path,
    get_doc_register_sp_site_url,
    set_doc_register_db_last_imported,
    set_doc_register_excel_path,
    set_doc_register_sp_site_url,
)


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def sample_eddr_df():
    """Create a sample EDDR DataFrame."""
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
def sample_query_df():
    """Create a sample query DataFrame."""
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
def sample_excel_path(sample_eddr_df, sample_query_df):
    """Create a temporary Excel file with EDDR and query sheets."""
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        path = Path(f.name)

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        # EDDR sheet: 2 header rows (title + column names), then data
        eddr_with_header = pd.DataFrame(
            [
                ["Project Title Row", None, None],
                ["Sr. No", "Document No", "Title"],
            ]
            + [[i + 1, row["Document No"], row["Title"]] for i, row in sample_eddr_df.iterrows()]
        )
        eddr_with_header.to_excel(writer, sheet_name="EDDR", index=False, header=False)

        # query sheet: single header row
        sample_query_df.to_excel(writer, sheet_name="query", index=False)

    yield path

    path.unlink(missing_ok=True)


@pytest.fixture
def mock_config(tmp_path):
    """Mock config.json in a temporary directory."""
    config_file = tmp_path / "config.json"
    config_file.write_text("{}", encoding="utf-8")

    with patch("pykorf.use_case.preferences.get_config_path", return_value=config_file):
        yield config_file


@pytest.fixture
def mock_data_dir(tmp_path):
    """Mock the data directory for DB storage."""
    from pykorf.use_case.web.doc_register.db_ops import reset_engine

    reset_engine()

    data_dir = tmp_path / "data"
    data_dir.mkdir()

    with patch("pykorf.use_case.paths.get_config_dir", return_value=tmp_path):
        with patch("pykorf.use_case.paths.ensure_data_dir", return_value=data_dir):
            yield data_dir

    reset_engine()


@pytest.fixture
def populated_db(mock_data_dir, sample_eddr_df, sample_query_df):
    """Create a pre-populated SQLite DB for testing queries."""
    from pykorf.use_case.web.doc_register.db_ops import (
        Base,
        EDDR,
        QueryEntry,
        get_engine,
        reset_engine,
    )

    reset_engine()

    db_path = mock_data_dir / "doc_register.db"
    engine = get_engine()
    Base.metadata.create_all(engine)

    with engine.begin() as conn:
        for _, row in sample_eddr_df.iterrows():
            conn.execute(
                EDDR.__table__.insert().values(
                    document_no=row["Document No"],
                    title=row["Title"],
                )
            )
        for _, row in sample_query_df.iterrows():
            conn.execute(
                QueryEntry.__table__.insert().values(
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
    """Tests for preference config functions."""

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
    """Tests for Excel-to-SQLite conversion."""

    def test_get_db_path(self, mock_data_dir):
        from pykorf.use_case.web.doc_register.excel_to_db import get_db_path

        db_path = get_db_path()
        assert db_path == mock_data_dir / "doc_register.db"

    def test_is_excel_stale_no_config(self, mock_config):
        from pykorf.use_case.web.doc_register.excel_to_db import is_excel_stale

        assert is_excel_stale() is False

    def test_is_excel_stale_no_excel(self, mock_config):
        from pykorf.use_case.web.doc_register.excel_to_db import is_excel_stale

        set_doc_register_excel_path(r"C:\nonexistent\file.xlsx")
        assert is_excel_stale() is False

    def test_is_excel_stale_no_db(self, mock_config, mock_data_dir, sample_excel_path):
        from pykorf.use_case.web.doc_register.excel_to_db import is_excel_stale

        set_doc_register_excel_path(str(sample_excel_path))
        assert is_excel_stale() is True

    def test_is_excel_stale_excel_newer(self, mock_config, mock_data_dir, sample_excel_path):
        from pykorf.use_case.web.doc_register.excel_to_db import is_excel_stale

        set_doc_register_excel_path(str(sample_excel_path))
        set_doc_register_db_last_imported("2020-01-01T00:00:00+00:00")
        assert is_excel_stale() is True

    def test_is_excel_stale_db_newer(self, mock_config, mock_data_dir, sample_excel_path):
        import time
        from pykorf.use_case.web.doc_register.excel_to_db import build_db_from_excel, is_excel_stale

        set_doc_register_excel_path(str(sample_excel_path))
        # Ensure Excel mtime is in the past
        old_time = time.time() - 10
        os.utime(sample_excel_path, (old_time, old_time))
        # Build the DB (sets timestamp to now)
        build_db_from_excel(sample_excel_path, "https://tenant.sharepoint.com")
        # Now the DB should NOT be stale (just built, Excel is older)
        assert is_excel_stale() is False

    def test_build_db_from_excel(self, mock_config, mock_data_dir, sample_excel_path):
        from pykorf.use_case.web.doc_register.excel_to_db import build_db_from_excel
        from pykorf.use_case.web.doc_register.db_ops import EDDR, QueryEntry, get_engine

        db_path = build_db_from_excel(sample_excel_path, "https://tenant.sharepoint.com")

        assert db_path.exists()

        engine = get_engine()
        with engine.connect() as conn:
            eddr_count = conn.execute(EDDR.__table__.select()).fetchall()
            query_count = conn.execute(QueryEntry.__table__.select()).fetchall()

        assert len(eddr_count) == 3
        assert len(query_count) == 4

    def test_build_db_updates_timestamp(self, mock_config, mock_data_dir, sample_excel_path):
        from pykorf.use_case.web.doc_register.excel_to_db import build_db_from_excel

        build_db_from_excel(sample_excel_path, "https://tenant.sharepoint.com")

        ts = get_doc_register_db_last_imported()
        assert ts is not None
        # Should be a valid ISO timestamp
        datetime.fromisoformat(ts)


# ── DB Operations Tests ─────────────────────────────────────────────────────


class TestDBOps:
    """Tests for SQLAlchemy database operations."""

    def test_search_eddr_by_title_match(self, populated_db):
        from pykorf.use_case.web.doc_register.db_ops import search_eddr_by_title

        results = search_eddr_by_title("Single Line")
        assert len(results) == 1
        assert results[0]["document_no"] == "DOC-002"
        assert "Single Line" in results[0]["title"]

    def test_search_eddr_by_title_no_match(self, populated_db):
        from pykorf.use_case.web.doc_register.db_ops import search_eddr_by_title

        results = search_eddr_by_title("NonExistent")
        assert len(results) == 0

    def test_search_eddr_by_title_empty(self, populated_db):
        from pykorf.use_case.web.doc_register.db_ops import search_eddr_by_title

        results = search_eddr_by_title("")
        assert len(results) == 0

    def test_search_eddr_case_insensitive(self, populated_db):
        from pykorf.use_case.web.doc_register.db_ops import search_eddr_by_title

        results = search_eddr_by_title("single line")
        assert len(results) == 1

    def test_search_eddr_unordered_words(self, populated_db):
        from pykorf.use_case.web.doc_register.db_ops import search_eddr_by_title

        # Words reversed — "Diagram Instrument Process" should still match
        # "Process and Instrument Diagram"
        results = search_eddr_by_title("Diagram Instrument Process")
        assert len(results) == 1
        assert results[0]["document_no"] == "DOC-001"

    def test_search_eddr_by_document_no(self, populated_db):
        from pykorf.use_case.web.doc_register.db_ops import search_eddr_by_title

        # Search by document number directly
        results = search_eddr_by_title("DOC-002")
        assert len(results) == 1
        assert results[0]["document_no"] == "DOC-002"

    def test_search_eddr_mixed_doc_no_and_title(self, populated_db):
        from pykorf.use_case.web.doc_register.db_ops import search_eddr_by_title

        # "DOC-001" matches document_no, "Instrument" matches title — both words
        # must appear across either field
        results = search_eddr_by_title("DOC-001 Instrument")
        assert len(results) == 1
        assert results[0]["document_no"] == "DOC-001"

    def test_search_eddr_unordered_partial_words_no_match(self, populated_db):
        from pykorf.use_case.web.doc_register.db_ops import search_eddr_by_title

        # All words must appear — this extra word should yield no results
        results = search_eddr_by_title("Single Line Nonexistent")
        assert len(results) == 0

    def test_search_query_by_name_match(self, populated_db):
        from pykorf.use_case.web.doc_register.db_ops import search_query_by_name

        results = search_query_by_name("DOC-001")
        assert len(results) == 2
        assert all(r["name"].startswith("DOC-001") for r in results)

    def test_search_query_by_name_no_match(self, populated_db):
        from pykorf.use_case.web.doc_register.db_ops import search_query_by_name

        results = search_query_by_name("NONEXISTENT")
        assert len(results) == 0

    def test_search_query_empty(self, populated_db):
        from pykorf.use_case.web.doc_register.db_ops import search_query_by_name

        results = search_query_by_name("")
        assert len(results) == 0

    def test_search_query_includes_folders(self, populated_db):
        from pykorf.use_case.web.doc_register.db_ops import search_query_by_name

        results = search_query_by_name("DOC-002")
        assert len(results) == 1
        assert results[0]["item_type"] == "Folder"

    def test_construct_sharepoint_url(self):
        from pykorf.use_case.web.doc_register.db_ops import construct_sharepoint_url

        url = construct_sharepoint_url(
            "sites/Project/Documents/folder",
            "file.pdf",
            "https://tenant.sharepoint.com",
        )
        assert url == "https://tenant.sharepoint.com/sites/Project/Documents/folder/file.pdf"

    def test_construct_sharepoint_url_strips_slashes(self):
        from pykorf.use_case.web.doc_register.db_ops import construct_sharepoint_url

        url = construct_sharepoint_url(
            "/sites/Project/Documents/",
            "/file.pdf",
            "https://tenant.sharepoint.com/",
        )
        assert url == "https://tenant.sharepoint.com/sites/Project/Documents/file.pdf"

    def test_get_db_stats(self, populated_db):
        from pykorf.use_case.web.doc_register.db_ops import get_db_stats

        stats = get_db_stats()
        assert stats["db_exists"] is True
        assert stats["eddr_count"] == 3
        assert stats["query_count"] == 4

    def test_get_db_stats_no_db(self, mock_data_dir):
        from pykorf.use_case.web.doc_register.db_ops import get_db_stats

        stats = get_db_stats()
        assert stats["db_exists"] is False
        assert stats["eddr_count"] == 0
        assert stats["query_count"] == 0


# ── API Routes Tests ────────────────────────────────────────────────────────


class TestDocRegisterAPI:
    """Tests for the Flask API routes."""

    @pytest.fixture
    def client(self, mock_config, mock_data_dir):
        """Create a Flask test client."""
        from pykorf.use_case.web.doc_register.db_ops import reset_engine

        reset_engine()

        from pykorf.use_case.web.app import create_app

        app = create_app()
        app.config["TESTING"] = True
        with app.test_client() as client:
            yield client

    def test_status_no_config(self, client):
        resp = client.get("/api/doc-register/status")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["excel_path"] is None
        assert data["db_exists"] is False
        assert data["is_stale"] is False

    def test_search_eddr_empty(self, client):
        resp = client.get("/api/doc-register/search-eddr?q=")
        assert resp.status_code == 200
        assert resp.get_json() == []

    def test_search_query_empty(self, client):
        resp = client.get("/api/doc-register/search-query?doc_no=")
        assert resp.status_code == 200
        assert resp.get_json() == []

    def test_rebuild_db_no_config(self, client):
        resp = client.post("/api/doc-register/rebuild-db")
        assert resp.status_code == 400
        data = resp.get_json()
        assert "error" in data

    def test_config_save(self, client):
        resp = client.post(
            "/api/doc-register/config",
            data=json.dumps(
                {
                    "excel_path": r"C:\test\Register.xlsx",
                    "sp_site_url": "https://test.sharepoint.com",
                }
            ),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["excel_path"] == r"C:\test\Register.xlsx"
        assert data["sp_site_url"] == "https://test.sharepoint.com"
