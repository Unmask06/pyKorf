"""Document Register package.

Provides Excel-to-SQLite conversion and database operations for the
Document Register search-and-select feature in the References page.
"""

from __future__ import annotations

from pykorf.app.doc_register._cols import Cols
from pykorf.app.doc_register.db_ops import (
    DEEDDR,
    FEEDDR,
    SpEntry,
    construct_sharepoint_url,
    get_db_stats,
    search_eddr,
    search_sp_entries,
    search_sp_entries_by_term,
)
from pykorf.app.doc_register.excel_to_db import (
    SP_SHEETS,
    build_db_from_excel,
    ensure_db_ready,
    get_db_path,
    is_excel_stale,
)

__all__ = [
    "Cols",
    "DEEDDR",
    "FEEDDR",
    "SP_SHEETS",
    "SpEntry",
    "build_db_from_excel",
    "construct_sharepoint_url",
    "ensure_db_ready",
    "get_db_path",
    "get_db_stats",
    "is_excel_stale",
    "search_eddr",
    "search_sp_entries",
    "search_sp_entries_by_term",
]
