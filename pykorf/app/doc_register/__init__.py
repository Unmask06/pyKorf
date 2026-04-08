"""Document Register package.

Provides Excel-to-SQLite conversion and database operations for the
Document Register search-and-select feature in the References page.
"""

from __future__ import annotations

from pykorf.app.doc_register._cols import Cols
from pykorf.app.doc_register.db_ops import (
    EDDR,
    QueryEntry,
    construct_sharepoint_url,
    get_db_stats,
    search_eddr_by_title,
    search_query_by_name,
)
from pykorf.app.doc_register.excel_to_db import (
    build_db_from_excel,
    ensure_db_ready,
    get_db_path,
    is_excel_stale,
)

__all__ = [
    "Cols",
    "EDDR",
    "QueryEntry",
    "build_db_from_excel",
    "construct_sharepoint_url",
    "ensure_db_ready",
    "get_db_path",
    "get_db_stats",
    "is_excel_stale",
    "search_eddr_by_title",
    "search_query_by_name",
]
