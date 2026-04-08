"""Column name constants for Document Register Excel sheets."""

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
