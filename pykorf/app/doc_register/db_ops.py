"""SQLAlchemy models and database operations for Document Register.

Provides:
- ORM models for FE EDDR, DE EDDR and SP-entries (Process/Client/Mechanical) tables
- Search functions for EDDR titles (FE + DE union) and SP entries
- SharePoint URL construction helper
- Database statistics
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    create_engine,
    event,
    literal,
    or_,
)
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from pykorf.app.doc_register.excel_to_db import get_db_path

Base = declarative_base()  # type: ignore[misc]


class FEEDDR(Base):  # type: ignore[valid-type]
    """FE EDDR (Front-End Engineering Document Deliverable Register) entry.

    Attributes:
        id: Auto-incrementing primary key.
        document_no: Unique document number (e.g., '1060-2304-EV000-EL-SLD-001').
        title: Document title/description.
    """

    __tablename__ = "fe_eddr"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_no = Column(String(200), nullable=False, index=True)
    title = Column(Text, nullable=False, index=True)


class DEEDDR(Base):  # type: ignore[valid-type]
    """DE EDDR (Detailed Engineering Document Deliverable Register) entry.

    Attributes:
        id: Auto-incrementing primary key.
        company_document_no: Company-issued document number (used as the primary
            doc number for SharePoint lookups).
        description: Document description / title.
        contractor_document_no: Contractor-issued document number (extra info).
    """

    __tablename__ = "de_eddr"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_document_no = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=False, index=True)
    contractor_document_no = Column(String(200), nullable=True, index=True)


class SpEntry(Base):  # type: ignore[valid-type]
    """SharePoint file/folder entry from one of the Process/Client/Mechanical sheets.

    Attributes:
        id: Auto-incrementing primary key.
        sheet: Source sheet name — one of 'Process', 'Client', 'Mechanical'.
        name: File or folder name.
        modified: ISO datetime string of last modification.
        modified_by: Username of last modifier.
        path: Server-relative SharePoint path (e.g., 'sites/.../Documents/folder').
        item_type: 'Item' for files, 'Folder' for folders.
    """

    __tablename__ = "sp_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sheet = Column(String(50), nullable=False, index=True)
    name = Column(String(300), nullable=False, index=True)
    modified = Column(String(50))
    modified_by = Column(String(200))
    path = Column(Text, nullable=False, index=True)
    item_type = Column(String(20), nullable=False)


_engine = None
_SessionFactory = None


def reset_engine():
    """Reset the engine singleton (useful for testing)."""
    global _engine, _SessionFactory
    _engine = None
    _SessionFactory = None


def get_engine():
    """Get or create the SQLAlchemy engine (lazy singleton).

    Returns:
        SQLAlchemy Engine instance pointed at the DB path.
    """
    global _engine, _SessionFactory
    if _engine is None:
        db_path = get_db_path()
        _engine = create_engine(
            f"sqlite:///{db_path}",
            pool_pre_ping=True,
            connect_args={"check_same_thread": False},
        )

        @event.listens_for(_engine, "connect")
        def _set_pragmas(dbapi_conn, _record):
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA journal_mode=WAL")  # faster concurrent reads
            cur.execute("PRAGMA synchronous=NORMAL")  # safe but not fsync on every write
            cur.execute("PRAGMA cache_size=-4000")  # 4 MB page cache
            cur.execute("PRAGMA mmap_size=16777216")  # 16 MB memory-mapped I/O
            cur.execute("PRAGMA temp_store=MEMORY")  # temp tables in RAM
            cur.close()

        _SessionFactory = sessionmaker(bind=_engine)
    return _engine


def get_session() -> Session:
    """Create a new database session.

    Returns:
        SQLAlchemy Session instance.
    """
    if _SessionFactory is None:
        get_engine()
    if _SessionFactory is None:  # pragma: no cover
        raise RuntimeError("SessionFactory not initialised — call get_engine() first")
    return _SessionFactory()


def search_eddr(query: str, limit: int = 50) -> list[dict[str, str | None]]:
    """Search FE EDDR + DE EDDR entries by Document No or Title/description.

    Each whitespace-separated word must appear in at least one of the searchable
    fields (AND across words, OR across fields). Results from both registers are
    merged and tagged with a ``source`` field (``"FE"`` or ``"DE"``).

    - FE rows are searched against ``document_no`` and ``title``.
    - DE rows are searched against ``company_document_no`` and ``description``.

    Args:
        query: Search term — words may appear in any order across either field.
        limit: Maximum number of results to return (applied per register).

    Returns:
        List of dicts with keys ``source`` ("FE"/"DE"), ``document_no``,
        ``title``, ``contractor_doc_no`` (None for FE rows).
    """
    words = query.strip().split()
    if not words:
        return []

    session = get_session()
    try:
        # --- FE EDDR rows ---
        fe_q = session.query(
            literal("FE").label("source"),
            FEEDDR.document_no.label("document_no"),
            FEEDDR.title.label("title"),
            literal(None).label("contractor_doc_no"),
        )
        for word in words:
            fe_q = fe_q.filter(
                or_(
                    FEEDDR.title.ilike(f"%{word}%"),
                    FEEDDR.document_no.ilike(f"%{word}%"),
                )
            )

        # --- DE EDDR rows ---
        de_q = session.query(
            literal("DE").label("source"),
            DEEDDR.company_document_no.label("document_no"),
            DEEDDR.description.label("title"),
            DEEDDR.contractor_document_no.label("contractor_doc_no"),
        )
        for word in words:
            de_q = de_q.filter(
                or_(
                    DEEDDR.description.ilike(f"%{word}%"),
                    DEEDDR.company_document_no.ilike(f"%{word}%"),
                )
            )

        # UNION ALL + per-branch limit. We apply the limit on each branch so that
        # neither register can starve the other (e.g. all FE rows matching first).
        fe_rows = fe_q.limit(limit).all()
        de_rows = de_q.limit(limit).all()

        results: list[dict[str, str | None]] = []
        for row in fe_rows:
            results.append(
                {
                    "source": row.source,
                    "document_no": row.document_no,
                    "title": row.title,
                    "contractor_doc_no": None,
                }
            )
        for row in de_rows:
            results.append(
                {
                    "source": row.source,
                    "document_no": row.document_no,
                    "title": row.title,
                    "contractor_doc_no": row.contractor_doc_no,
                }
            )
        return results
    except OperationalError:
        # DB has a stale/legacy schema — return empty until the user rebuilds.
        return []
    finally:
        session.close()


def search_sp_entries(
    doc_no: str, sheet: str | None = None, limit: int = 500
) -> list[dict[str, str | None]]:
    """Search SharePoint entries (Process/Client/Mechanical) by document number.

    Filters ``sp_entries`` where ``name`` contains the document number. Results
    are ordered by item type (files before folders) then by modified time
    descending (latest first). Each result includes the originating ``sheet``
    so callers can tag/filter results by source.

    Args:
        doc_no: Document number to search for in the name field.
        sheet: Optional sheet filter — one of ``"Process"``, ``"Client"``,
            ``"Mechanical"``. When ``None`` all three sheets are searched.
        limit: Maximum number of results to return.

    Returns:
        List of dicts with keys ``sheet``, ``name``, ``modified``,
        ``modified_by``, ``path``, ``item_type``.
    """
    if not doc_no.strip():
        return []

    term = f"%{doc_no.strip()}%"
    session = get_session()
    try:
        q = (
            session.query(
                SpEntry.sheet,
                SpEntry.name,
                SpEntry.modified,
                SpEntry.modified_by,
                SpEntry.path,
                SpEntry.item_type,
            )
            .filter(SpEntry.name.ilike(term))
            .order_by(
                SpEntry.item_type.desc(),
                SpEntry.modified.desc(),
            )
        )
        if sheet:
            q = q.filter(SpEntry.sheet == sheet)
        results = q.limit(limit).all()
        return [
            {
                "sheet": row.sheet,
                "name": row.name,
                "modified": row.modified,
                "modified_by": row.modified_by,
                "path": row.path,
                "item_type": row.item_type,
            }
            for row in results
        ]
    except OperationalError:
        # DB has a stale/legacy schema — return empty until the user rebuilds.
        return []
    finally:
        session.close()


def _score_match(query: str, target: str) -> int:
    """Score how well a query matches a target string.

    Uses multi-factor scoring:
    - Exact match: 1000 pts
    - Starts with query: 500 pts
    - Word boundary match (after -, _, space, .): 200 pts
    - Position-based: 100 * (1 - position/len)
    - Length bonus: 50 * (1 - target_len/query_len)

    Args:
        query: Search query string.
        target: Target string to match against.

    Returns:
        Score (higher = better match).
    """
    if not query or not target:
        return 0

    query_lower = query.lower()
    target_lower = target.lower()
    query_len = len(query_lower)
    target_len = len(target_lower)

    # Exact match (case-insensitive)
    if query_lower == target_lower:
        return 1000

    # Starts with query
    if target_lower.startswith(query_lower):
        # Bonus for shorter targets (more specific)
        length_bonus = (
            int(50 * (1 - target_len / (query_len * 3))) if target_len > query_len else 50
        )
        return 500 + max(0, length_bonus)

    # Find all match positions
    position = target_lower.find(query_lower)
    if position == -1:
        return 0

    score = 0

    # Check if match is at word boundary (after -, _, space, ., or digit-letter transition)
    if position > 0:
        prev_char = target[position - 1]
        if prev_char in "-_ .":
            score += 200  # Word boundary match
        elif prev_char.isdigit() and query[0].isalpha():
            score += 150  # Digit-letter transition (e.g., "001P" in "DWG-001-PID")
    else:
        # Match at start but not exact (already handled above for starts-with)
        score += 100

    # Position score (earlier = better)
    if position > 0:
        position_score = int(100 * (1 - position / target_len))
        score += max(0, position_score)

    # Length bonus (shorter targets that contain the query are more specific)
    if target_len > query_len:
        length_bonus = int(50 * (1 - (target_len - query_len) / target_len))
        score += max(0, length_bonus)

    return score


def search_sp_entries_by_term(term: str, limit: int = 50) -> list[dict[str, str | None]]:
    """Search SharePoint entries by name or path (fuzzy, score-sorted).

    Returns both Items (files) and Folders, sorted by match score (best first),
    then by modified time descending. Each result includes the originating
    ``sheet`` (Process/Client/Mechanical).

    Args:
        term: Search term (matched against name and path).
        limit: Maximum number of results to return.

    Returns:
        List of dicts with keys ``sheet``, ``name``, ``modified``,
        ``modified_by``, ``path``, ``item_type``.
    """
    if not term or len(term.strip()) < 2:
        return []

    search_term = f"%{term.strip()}%"
    session = get_session()
    try:
        # Fetch at most limit*4 rows from SQLite — never pull the whole table
        results = (
            session.query(
                SpEntry.sheet,
                SpEntry.name,
                SpEntry.modified,
                SpEntry.modified_by,
                SpEntry.path,
                SpEntry.item_type,
            )
            .filter(
                or_(
                    SpEntry.name.ilike(search_term),
                    SpEntry.path.ilike(search_term),
                )
            )
            .limit(limit * 4)
            .all()
        )

        # Score and sort results
        scored_results = []
        for row in results:
            # Score based on name match (primary) and path match (secondary)
            name_score = _score_match(term, row.name)
            path_score = _score_match(term, row.path) if row.path else 0
            # Use the higher of name or path score, with name getting priority
            final_score = name_score * 2 + path_score

            scored_results.append(
                {
                    "sheet": row.sheet,
                    "name": row.name,
                    "modified": row.modified,
                    "modified_by": row.modified_by,
                    "path": row.path,
                    "item_type": row.item_type,
                    "_score": final_score,
                    "_modified_ts": row.modified,
                }
            )

        # Sort by score (descending), then by modified time (descending)
        scored_results.sort(key=lambda x: (-x["_score"], x["_modified_ts"] or ""), reverse=False)

        # Remove internal scoring fields and apply limit
        return [
            {
                "sheet": r["sheet"],
                "name": r["name"],
                "modified": r["modified"],
                "modified_by": r["modified_by"],
                "path": r["path"],
                "item_type": r["item_type"],
            }
            for r in scored_results[:limit]
        ]
    except OperationalError:
        # DB has a stale/legacy schema — return empty until the user rebuilds.
        return []
    finally:
        session.close()


def construct_sharepoint_url(path: str, name: str, sp_site_url: str) -> str:
    """Construct a full SharePoint URL from server-relative components.

    Args:
        path: Server-relative path (e.g., 'sites/Project/Documents/folder').
        name: File or folder name.
        sp_site_url: SharePoint site base URL (e.g., 'https://tenant.sharepoint.com').

    Returns:
        Full SharePoint URL string.
    """
    base = sp_site_url.rstrip("/")
    clean_path = path.strip("/")
    clean_name = name.strip("/")
    return f"{base}/{clean_path}/{clean_name}"


def get_db_stats() -> dict[str, Any]:
    """Return statistics about the Document Register database.

    Returns:
        Dict with keys ``fe_eddr_count``, ``de_eddr_count``, ``sp_count``,
        ``db_path``, ``db_exists``.
    """
    db_path = get_db_path()
    if not db_path.is_file():
        return {
            "fe_eddr_count": 0,
            "de_eddr_count": 0,
            "sp_count": 0,
            "db_path": str(db_path),
            "db_exists": False,
        }

    session = get_session()
    try:
        fe_eddr_count = session.query(FEEDDR).count()
        de_eddr_count = session.query(DEEDDR).count()
        sp_count = session.query(SpEntry).count()
        return {
            "fe_eddr_count": fe_eddr_count,
            "de_eddr_count": de_eddr_count,
            "sp_count": sp_count,
            "db_path": str(db_path),
            "db_exists": True,
        }
    except OperationalError:
        # DB file exists but has a stale/legacy schema — treat as absent so the
        # UI prompts the user to rebuild from the current Excel workbook.
        return {
            "fe_eddr_count": 0,
            "de_eddr_count": 0,
            "sp_count": 0,
            "db_path": str(db_path),
            "db_exists": False,
        }
    finally:
        session.close()
