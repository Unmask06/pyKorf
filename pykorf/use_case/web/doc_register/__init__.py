"""Document Register package.

Provides Excel-to-SQLite conversion and database operations for the
Document Register search-and-select feature in the References page.
"""

from __future__ import annotations


class Cols:
    """Column names used across EDDR and query sheets.

    Single source of truth — change here if the Excel layout changes.
    """

    # EDDR sheet columns
    EDDR_DOC_NO = "Document No"
    EDDR_TITLE = "Title"

    # Query sheet columns
    QUERY_NAME = "Name"
    QUERY_MODIFIED = "Modified"
    QUERY_MODIFIED_BY = "Modified By"
    QUERY_PATH = "Path"
    QUERY_ITEM_TYPE = "Item Type"


from pykorf.use_case.web.doc_register.db_ops import (
    EDDR,
    QueryEntry,
    construct_sharepoint_url,
    get_db_stats,
    search_eddr_by_title,
    search_query_by_name,
)
from pykorf.use_case.web.doc_register.excel_to_db import (
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
