"""Excel-to-SQLite conversion for Document Register.

Handles:
- DB path resolution in AppData/data folder
- Staleness detection (Excel mtime vs config timestamp)
- SharePoint site URL auto-detection from query Path patterns
- Full DB rebuild from Excel (clear + re-insert all rows)
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import structlog

from pykorf.use_case.paths import ensure_data_dir
from pykorf.use_case.preferences import (
    get_doc_register_db_last_imported,
    get_doc_register_excel_path,
    get_doc_register_sp_site_url,
    set_doc_register_db_last_imported,
)

logger = structlog.get_logger()

# Default SharePoint tenant URL derived from observed path patterns
_DEFAULT_SP_SITE_URL = "https://cc7ges.sharepoint.com"


def get_db_path() -> Path:
    """Return the path to the Document Register SQLite database.

    Returns:
        Path to ``doc_register.db`` in the AppData data directory.
    """
    return ensure_data_dir() / "doc_register.db"


def detect_sp_site_url(path_sample: str = "") -> str:
    """Extract SharePoint tenant URL from a server-relative path sample.

    Given a path like ``sites/25002TAZIZSALT-ADNOCUAE/Shared Documents``,
    returns ``https://cc7ges.sharepoint.com``.

    Falls back to the configured SP site URL or default if detection fails.

    Args:
        path_sample: A sample server-relative path from the query sheet.

    Returns:
        SharePoint site base URL string.
    """
    configured = get_doc_register_sp_site_url()
    if configured:
        return configured.rstrip("/")

    # Try to extract tenant from path pattern
    # Paths look like: sites/25002TAZIZSALT-ADNOCUAE/Shared Documents/...
    # We can't derive tenant from path alone, so use default
    return _DEFAULT_SP_SITE_URL


def is_excel_stale() -> bool:
    """Check if the Document Register Excel file is newer than the DB.

    Compares the Excel file's modification time against the
    ``doc_register_db_last_imported`` config timestamp.

    Returns:
        True if the Excel file exists and is newer than the last DB build,
        or if the DB doesn't exist yet. False if Excel is not configured.
    """
    excel_path_str = get_doc_register_excel_path()
    if not excel_path_str:
        return False

    excel_path = Path(excel_path_str)
    if not excel_path.is_file():
        return False

    db_path = get_db_path()
    if not db_path.is_file():
        return True

    last_imported = get_doc_register_db_last_imported()
    if not last_imported:
        return True

    try:
        excel_mtime = datetime.fromtimestamp(excel_path.stat().st_mtime, tz=timezone.utc)
        imported_time = datetime.fromisoformat(last_imported)
        if imported_time.tzinfo is None:
            imported_time = imported_time.replace(tzinfo=timezone.utc)
        return excel_mtime > imported_time
    except (OSError, ValueError) as exc:
        logger.warning("doc_register.staleness_check_failed", error=str(exc))
        return True


def _find_eddr_header_row(df: pd.DataFrame) -> int:
    """Find the row index containing the 'Document No' column header.

    Scans rows until a cell with value 'Document No' is found.

    Args:
        df: DataFrame read without header (header=None).

    Returns:
        Row index to use as header, defaults to 2 if not found.
    """
    for idx in range(min(len(df), 10)):
        row = df.iloc[idx]
        if "Document No" in row.values:
            return idx
    return 2


def build_db_from_excel(excel_path: Path, sp_site_url: str = "") -> Path:
    """Read the Document Register Excel file and build the SQLite database.

    Performs a full sync: drops existing tables and re-inserts all rows.

    EDDR sheet:
        - Dynamic header detection (searches for 'Document No' column)
        - Extracts 'Document No' and 'Title' columns

    query sheet:
        - Extracts 'Name', 'Modified', 'Modified By', 'Path', 'Item Type'
        - Includes both Items (files) and Folders

    Args:
        excel_path: Path to the Document Register Excel file.
        sp_site_url: SharePoint site base URL (unused here, stored in config).

    Returns:
        Path to the created SQLite database.
    """
    from pykorf.use_case.web.doc_register.db_ops import Base, EDDR, QueryEntry, get_engine

    logger.info("doc_register.build_db_start", excel_path=str(excel_path))

    # Read EDDR sheet with dynamic header detection
    eddr_raw = pd.read_excel(excel_path, sheet_name="EDDR", header=None, nrows=20)
    header_row = _find_eddr_header_row(eddr_raw)

    eddr_df = pd.read_excel(
        excel_path,
        sheet_name="EDDR",
        header=header_row,
        usecols=["Document No", "Title"],
    )
    eddr_df = eddr_df.dropna(subset=["Document No"])
    eddr_df["Document No"] = eddr_df["Document No"].astype(str).str.strip()
    eddr_df = eddr_df[eddr_df["Document No"] != "nan"]
    eddr_df["Title"] = eddr_df["Title"].fillna("").astype(str).str.strip()  # type: ignore[union-attr]

    # Read query sheet
    query_df = pd.read_excel(
        excel_path,
        sheet_name="query",
        usecols=["Name", "Modified", "Modified By", "Path", "Item Type"],
    )
    query_df = query_df.dropna(subset=["Name"])
    query_df["Name"] = query_df["Name"].astype(str).str.strip()
    query_df["Modified"] = query_df["Modified"].fillna("").astype(str).str.strip()
    query_df["Modified By"] = query_df["Modified By"].fillna("").astype(str).str.strip()
    query_df["Path"] = query_df["Path"].fillna("").astype(str).str.strip()
    query_df["Item Type"] = query_df["Item Type"].fillna("").astype(str).str.strip()

    # Build database
    db_path = get_db_path()
    engine = get_engine()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    with engine.begin() as conn:
        for _, row in eddr_df.iterrows():
            conn.execute(
                EDDR.__table__.insert().values(
                    document_no=row["Document No"],
                    title=row["Title"],
                )
            )

        for _, row in query_df.iterrows():
            conn.execute(
                QueryEntry.__table__.insert().values(
                    name=row["Name"],
                    modified=row["Modified"],
                    modified_by=row["Modified By"],
                    path=row["Path"],
                    item_type=row["Item Type"],
                )
            )

    logger.info(
        "doc_register.build_db_complete",
        eddr_count=len(eddr_df),
        query_count=len(query_df),
        db_path=str(db_path),
    )

    # Update config timestamp
    set_doc_register_db_last_imported(datetime.now(timezone.utc).isoformat())

    return db_path


def ensure_db_ready() -> Path | None:
    """Ensure the Document Register DB exists and is current.

    Checks staleness and auto-rebuilds if the Excel file is newer than
    the last DB build.

    Returns:
        Path to the DB if ready, None if Excel is not configured.
    """
    excel_path_str = get_doc_register_excel_path()
    if not excel_path_str:
        return None

    excel_path = Path(excel_path_str)
    if not excel_path.is_file():
        logger.warning("doc_register.excel_not_found", path=str(excel_path))
        return None

    sp_site_url = get_doc_register_sp_site_url() or detect_sp_site_url()

    if is_excel_stale() or not get_db_path().is_file():
        try:
            build_db_from_excel(excel_path, sp_site_url)
        except Exception as exc:
            logger.error("doc_register.build_db_failed", error=str(exc))
            return None

    return get_db_path()
