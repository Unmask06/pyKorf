"""Document Register package.

Provides Excel-to-SQLite conversion and database operations for the
Document Register search-and-select feature in the References page.
"""

from __future__ import annotations

from pykorf.use_case.web.doc_register.excel_to_db import (
    build_db_from_excel,
    ensure_db_ready,
    get_db_path,
    is_excel_stale,
)
from pykorf.use_case.web.doc_register.db_ops import (
    EDDR,
    QueryEntry,
    construct_sharepoint_url,
    search_eddr_by_title,
    search_query_by_name,
    get_db_stats,
)

__all__ = [
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
