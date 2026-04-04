"""Excel-to-SQLite conversion for Document Register.

Handles:
- DB path resolution in AppData/data folder
- Staleness detection (Excel mtime vs config timestamp)
- SharePoint site URL auto-detection from query Path patterns
- Full DB rebuild from Excel (clear + re-insert all rows)
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import structlog

from pykorf.use_case.paths import ensure_data_dir
from pykorf.use_case.preferences import (
    get_doc_register_db_last_imported,
    get_doc_register_excel_path,
    get_doc_register_sp_site_url,
    set_doc_register_db_last_imported,
)
from pykorf.use_case.web.doc_register._cols import Cols

logger = structlog.get_logger()


def get_db_path() -> Path:
    """Return the path to the Document Register SQLite database.

    Returns:
        Path to ``doc_register.db`` in the AppData data directory.
    """
    return ensure_data_dir() / "doc_register.db"


def detect_sp_site_url() -> str:
    """Get the configured SharePoint site URL for document links.

    Returns:
        Configured SharePoint site base URL, or empty string if not set.
    """
    configured = get_doc_register_sp_site_url()
    return configured.rstrip("/") if configured else ""


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
        excel_mtime = datetime.fromtimestamp(excel_path.stat().st_mtime, tz=UTC)
        imported_time = datetime.fromisoformat(last_imported)
        if imported_time.tzinfo is None:
            imported_time = imported_time.replace(tzinfo=UTC)
        return excel_mtime > imported_time
    except (OSError, ValueError) as exc:
        logger.warning("doc_register.staleness_check_failed", error=str(exc))
        return True


def _find_eddr_header_row(df: pd.DataFrame) -> int:
    """Find the row index containing the document number column header.

    Scans rows until a cell with value matching Cols.EDDR_DOC_NO is found.

    Args:
        df: DataFrame read without header (header=None).

    Returns:
        Row index to use as header, defaults to 2 if not found.
    """
    for idx in range(min(len(df), 10)):
        row = df.iloc[idx]
        if Cols.EDDR_DOC_NO in row.values:
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
    from pykorf.use_case.web.doc_register.db_ops import Base, get_engine

    logger.info("doc_register.build_db_start", excel_path=str(excel_path))

    # Read EDDR sheet with dynamic header detection
    eddr_raw = pd.read_excel(excel_path, sheet_name="EDDR", header=None, nrows=20)
    header_row = _find_eddr_header_row(eddr_raw)

    eddr_df = pd.read_excel(
        excel_path,
        sheet_name="EDDR",
        header=header_row,
        usecols=[Cols.EDDR_DOC_NO, Cols.EDDR_TITLE],
    )
    eddr_df = eddr_df.dropna(subset=[Cols.EDDR_DOC_NO])
    eddr_df[Cols.EDDR_DOC_NO] = eddr_df[Cols.EDDR_DOC_NO].astype(str).str.strip()
    eddr_df = eddr_df[eddr_df[Cols.EDDR_DOC_NO] != "nan"]
    eddr_df[Cols.EDDR_TITLE] = eddr_df[Cols.EDDR_TITLE].fillna("").astype(str).str.strip()  # type: ignore[union-attr]

    # Read query sheet
    query_df = pd.read_excel(
        excel_path,
        sheet_name="query",
        usecols=[
            Cols.QUERY_NAME,
            Cols.QUERY_MODIFIED,
            Cols.QUERY_MODIFIED_BY,
            Cols.QUERY_PATH,
            Cols.QUERY_ITEM_TYPE,
        ],
    )
    query_df = query_df.dropna(subset=[Cols.QUERY_NAME])
    query_df[Cols.QUERY_NAME] = query_df[Cols.QUERY_NAME].astype(str).str.strip()
    query_df[Cols.QUERY_MODIFIED] = query_df[Cols.QUERY_MODIFIED].fillna("").astype(str).str.strip()
    query_df[Cols.QUERY_MODIFIED_BY] = (
        query_df[Cols.QUERY_MODIFIED_BY].fillna("").astype(str).str.strip()
    )
    query_df[Cols.QUERY_PATH] = query_df[Cols.QUERY_PATH].fillna("").astype(str).str.strip()
    query_df[Cols.QUERY_ITEM_TYPE] = (
        query_df[Cols.QUERY_ITEM_TYPE].fillna("").astype(str).str.strip()
    )

    # Build database
    db_path = get_db_path()
    engine = get_engine()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    eddr_df.rename(columns={Cols.EDDR_DOC_NO: "document_no", Cols.EDDR_TITLE: "title"}).to_sql(  # type: ignore[call-overload]
        "eddr", con=engine, if_exists="append", index=False
    )
    query_df.rename(
        columns={
            Cols.QUERY_NAME: "name",
            Cols.QUERY_MODIFIED: "modified",
            Cols.QUERY_MODIFIED_BY: "modified_by",
            Cols.QUERY_PATH: "path",
            Cols.QUERY_ITEM_TYPE: "item_type",
        }
    ).to_sql("query_entries", con=engine, if_exists="append", index=False)

    logger.info(
        "doc_register.build_db_complete",
        eddr_count=len(eddr_df),
        query_count=len(query_df),
        db_path=str(db_path),
    )

    # Update config timestamp
    set_doc_register_db_last_imported(datetime.now(UTC).isoformat())

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

    sp_site_url = get_doc_register_sp_site_url() or ""

    if is_excel_stale() or not get_db_path().is_file():
        try:
            build_db_from_excel(excel_path, sp_site_url)
        except Exception as exc:
            logger.error("doc_register.build_db_failed", error=str(exc))
            return None

    return get_db_path()
