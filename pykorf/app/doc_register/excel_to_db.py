"""Excel-to-SQLite conversion for Document Register.

Handles:
- DB path resolution in AppData/data folder
- Staleness detection (Excel mtime vs config timestamp)
- SharePoint site URL auto-detection from query Path patterns
- Full DB rebuild from Excel (clear + re-insert all rows)

Sheets consumed:
    - ``FE EDDR``  — Front-End Engineering Document Deliverable Register
      (columns: ``Document No``, ``Title``). Dynamic header detection.
    - ``DE EDDR``  — Detailed Engineering Document Deliverable Register
      (columns: ``COMPANY DOCUMENT NUMBER``, ``DESCRIPTION``,
      ``CONTRACTOR DOCUMENT NUMBER``). Dynamic header detection.
    - ``Process`` / ``Client`` / ``Mechanical`` — SharePoint file/folder
      listings (columns: ``Name``, ``Modified``, ``Modified By``, ``Path``,
      ``Item Type``). All three are written into a single ``sp_entries``
      table, stamped with their originating sheet name.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from pykorf.app.doc_register._cols import Cols
from pykorf.app.operation.config.paths import ensure_data_dir
from pykorf.app.operation.config.preferences import (
    get_doc_register_db_last_imported,
    get_doc_register_excel_path,
    get_doc_register_sp_site_url,
    set_doc_register_db_last_imported,
)
from pykorf.core.log import get_logger

logger = get_logger(__name__)

# Source SharePoint-extracted sheet names → ``sp_entries.sheet`` values.
SP_SHEETS: tuple[str, ...] = ("Process", "Client", "Mechanical")


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


def _find_header_row(df: pd.DataFrame, header_value: str, default: int = 2) -> int:
    """Find the row index containing a given column header.

    Scans the first 10 rows (read with ``header=None``) for a cell whose value
    matches ``header_value``.

    Args:
        df: DataFrame read without header (header=None).
        header_value: The header cell value to locate (e.g. ``"Document No"``).
        default: Row index to return if the header is not found.

    Returns:
        Row index to use as the header row.
    """
    for idx in range(min(len(df), 10)):
        row = df.iloc[idx]
        if header_value in row.values:
            return idx
    return default


def _read_fe_eddr(excel_path: Path) -> pd.DataFrame:
    """Read the ``FE EDDR`` sheet and return a cleaned DataFrame.

    Uses dynamic header detection (scans for the ``Document No`` cell) and
    extracts only the ``Document No`` and ``Title`` columns.
    """
    raw = pd.read_excel(excel_path, sheet_name="FE EDDR", header=None, nrows=20)
    header_row = _find_header_row(raw, Cols.FE_EDDR_DOC_NO, default=2)

    df = pd.read_excel(
        excel_path,
        sheet_name="FE EDDR",
        header=header_row,
        usecols=[Cols.FE_EDDR_DOC_NO, Cols.FE_EDDR_TITLE],
    )
    df = df.dropna(subset=[Cols.FE_EDDR_DOC_NO])
    df[Cols.FE_EDDR_DOC_NO] = df[Cols.FE_EDDR_DOC_NO].astype(str).str.strip()
    df = df[df[Cols.FE_EDDR_DOC_NO] != "nan"]
    df[Cols.FE_EDDR_TITLE] = df[Cols.FE_EDDR_TITLE].fillna("").astype(str).str.strip()  # type: ignore[union-attr]
    return df


def _read_de_eddr(excel_path: Path) -> pd.DataFrame:
    """Read the ``DE EDDR`` sheet and return a cleaned DataFrame.

    Uses dynamic header detection (scans for the ``COMPANY DOCUMENT NUMBER``
    cell) and extracts the company document number, description and contractor
    document number columns.
    """
    raw = pd.read_excel(excel_path, sheet_name="DE EDDR", header=None, nrows=20)
    header_row = _find_header_row(raw, Cols.DE_EDDR_COMPANY_DOC_NO, default=2)

    df = pd.read_excel(
        excel_path,
        sheet_name="DE EDDR",
        header=header_row,
        usecols=[
            Cols.DE_EDDR_COMPANY_DOC_NO,
            Cols.DE_EDDR_DESCRIPTION,
            Cols.DE_EDDR_CONTRACTOR_DOC_NO,
        ],
    )
    df = df.dropna(subset=[Cols.DE_EDDR_COMPANY_DOC_NO])
    df[Cols.DE_EDDR_COMPANY_DOC_NO] = df[Cols.DE_EDDR_COMPANY_DOC_NO].astype(str).str.strip()
    df = df[df[Cols.DE_EDDR_COMPANY_DOC_NO] != "nan"]
    df[Cols.DE_EDDR_DESCRIPTION] = df[Cols.DE_EDDR_DESCRIPTION].fillna("").astype(str).str.strip()  # type: ignore[union-attr]
    df[Cols.DE_EDDR_CONTRACTOR_DOC_NO] = (
        df[Cols.DE_EDDR_CONTRACTOR_DOC_NO].fillna("").astype(str).str.strip()
    )
    return df


def _read_sp_sheet(excel_path: Path, sheet_name: str) -> pd.DataFrame:
    """Read one SharePoint-extracted sheet (Process/Client/Mechanical).

    Extracts the ``Name``, ``Modified``, ``Modified By``, ``Path`` and
    ``Item Type`` columns. Does NOT include the sheet name — the caller is
    responsible for stamping it.
    """
    df = pd.read_excel(
        excel_path,
        sheet_name=sheet_name,
        usecols=[
            Cols.SP_NAME,
            Cols.SP_MODIFIED,
            Cols.SP_MODIFIED_BY,
            Cols.SP_PATH,
            Cols.SP_ITEM_TYPE,
        ],
    )
    df = df.dropna(subset=[Cols.SP_NAME])
    df[Cols.SP_NAME] = df[Cols.SP_NAME].astype(str).str.strip()
    df[Cols.SP_MODIFIED] = df[Cols.SP_MODIFIED].fillna("").astype(str).str.strip()
    df[Cols.SP_MODIFIED_BY] = df[Cols.SP_MODIFIED_BY].fillna("").astype(str).str.strip()
    df[Cols.SP_PATH] = df[Cols.SP_PATH].fillna("").astype(str).str.strip()
    df[Cols.SP_ITEM_TYPE] = df[Cols.SP_ITEM_TYPE].fillna("").astype(str).str.strip()
    return df


def build_db_from_excel(excel_path: Path, sp_site_url: str = "") -> Path:
    """Read the Document Register Excel file and build the SQLite database.

    Performs a full sync: drops existing tables and re-inserts all rows.

    Sheets read:
        - ``FE EDDR``  → ``fe_eddr``  (Document No, Title)
        - ``DE EDDR``  → ``de_eddr``  (Company / Description / Contractor doc no)
        - ``Process`` / ``Client`` / ``Mechanical`` → ``sp_entries``
          (single table, ``sheet`` column stamps the source)

    Args:
        excel_path: Path to the Document Register Excel file.
        sp_site_url: SharePoint site base URL (unused here, stored in config).

    Returns:
        Path to the created SQLite database.
    """
    from pykorf.app.doc_register.db_ops import Base, get_engine

    logger.info("doc_register.build_db_start", excel_path=str(excel_path))

    fe_eddr_df = _read_fe_eddr(excel_path)
    de_eddr_df = _read_de_eddr(excel_path)

    sp_frames: list[pd.DataFrame] = []
    for sheet_name in SP_SHEETS:
        try:
            sp_df = _read_sp_sheet(excel_path, sheet_name)
        except ValueError:
            # Sheet not present in this workbook — skip silently.
            logger.info("doc_register.sp_sheet_missing", sheet=sheet_name)
            continue
        sp_df["sheet"] = sheet_name
        sp_frames.append(sp_df)

    sp_df_all = (
        pd.concat(sp_frames, ignore_index=True)
        if sp_frames
        else pd.DataFrame(columns=["sheet", "name", "modified", "modified_by", "path", "item_type"])
    )

    # Build database
    db_path = get_db_path()
    engine = get_engine()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    fe_eddr_df.rename(
        columns={Cols.FE_EDDR_DOC_NO: "document_no", Cols.FE_EDDR_TITLE: "title"}
    ).to_sql(  # type: ignore[call-overload]
        "fe_eddr", con=engine, if_exists="append", index=False
    )
    de_eddr_df.rename(
        columns={
            Cols.DE_EDDR_COMPANY_DOC_NO: "company_document_no",
            Cols.DE_EDDR_DESCRIPTION: "description",
            Cols.DE_EDDR_CONTRACTOR_DOC_NO: "contractor_document_no",
        }
    ).to_sql(  # type: ignore[call-overload]
        "de_eddr", con=engine, if_exists="append", index=False
    )
    sp_df_all.rename(
        columns={
            Cols.SP_NAME: "name",
            Cols.SP_MODIFIED: "modified",
            Cols.SP_MODIFIED_BY: "modified_by",
            Cols.SP_PATH: "path",
            Cols.SP_ITEM_TYPE: "item_type",
        }
    ).to_sql(  # type: ignore[call-overload]
        "sp_entries", con=engine, if_exists="append", index=False
    )

    logger.info(
        "doc_register.build_db_complete",
        fe_eddr_count=len(fe_eddr_df),
        de_eddr_count=len(de_eddr_df),
        sp_count=len(sp_df_all),
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
