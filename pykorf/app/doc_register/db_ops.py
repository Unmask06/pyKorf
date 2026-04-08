"""SQLAlchemy models and database operations for Document Register.

Provides:
- ORM models for EDDR and query_entries tables
- Search functions for EDDR titles and query entries
- SharePoint URL construction helper
- Database statistics
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import Column, Integer, String, Text, create_engine, or_
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from pykorf.app.doc_register.excel_to_db import get_db_path

Base = declarative_base()  # type: ignore[misc]


class EDDR(Base):  # type: ignore[valid-type]
    """EDDR (Engineering Document Deliverable Register) entry.

    Attributes:
        id: Auto-incrementing primary key.
        document_no: Unique document number (e.g., '1060-2304-EV000-EL-SLD-001').
        title: Document title/description.
    """

    __tablename__ = "eddr"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_no = Column(String(200), nullable=False, index=True)
    title = Column(Text, nullable=False, index=True)


class QueryEntry(Base):  # type: ignore[valid-type]
    """Query table entry from SharePoint file listing.

    Attributes:
        id: Auto-incrementing primary key.
        name: File or folder name.
        modified: ISO datetime string of last modification.
        modified_by: Username of last modifier.
        path: Server-relative SharePoint path (e.g., 'sites/.../Documents/folder').
        item_type: 'Item' for files, 'Folder' for folders.
    """

    __tablename__ = "query_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
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
        from sqlalchemy import event

        db_path = get_db_path()
        _engine = create_engine(
            f"sqlite:///{db_path}",
            pool_pre_ping=True,
            connect_args={"check_same_thread": False},
        )

        @event.listens_for(_engine, "connect")
        def _set_pragmas(dbapi_conn, _record):
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA journal_mode=WAL")       # faster concurrent reads
            cur.execute("PRAGMA synchronous=NORMAL")     # safe but not fsync on every write
            cur.execute("PRAGMA cache_size=-4000")       # 4 MB page cache
            cur.execute("PRAGMA mmap_size=16777216")     # 16 MB memory-mapped I/O
            cur.execute("PRAGMA temp_store=MEMORY")      # temp tables in RAM
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


def search_eddr_by_title(query: str, limit: int = 50) -> list[dict[str, str]]:
    """Search EDDR entries by Document No or Title, with unordered word matching.

    Each whitespace-separated word must appear in either the document number
    or the title (AND across words, OR across fields). For example,
    "EV000 data sheet" matches any entry where every word is found in at
    least one of the two fields.

    Args:
        query: Search term — words may appear in any order across either field.
        limit: Maximum number of results to return.

    Returns:
        List of dicts with keys 'document_no' and 'title'.
    """
    words = query.strip().split()
    if not words:
        return []

    session = get_session()
    try:
        q = session.query(EDDR.document_no, EDDR.title)
        for word in words:
            q = q.filter(
                or_(
                    EDDR.title.ilike(f"%{word}%"),
                    EDDR.document_no.ilike(f"%{word}%"),
                )
            )
        results = q.limit(limit).all()
        return [{"document_no": row.document_no, "title": row.title} for row in results]
    finally:
        session.close()


def search_query_by_name(doc_no: str, limit: int = 20) -> list[dict[str, str]]:
    """Search query entries where name contains the document number.

    Returns both Items (files) and Folders, sorted by modified time
    descending (latest first).

    Args:
        doc_no: Document number to search for in the name field.
        limit: Maximum number of results to return.

    Returns:
        List of dicts with keys 'name', 'modified', 'modified_by',
        'path', 'item_type'.
    """
    if not doc_no.strip():
        return []

    term = f"%{doc_no.strip()}%"
    session = get_session()
    try:
        results = (
            session.query(
                QueryEntry.name,
                QueryEntry.modified,
                QueryEntry.modified_by,
                QueryEntry.path,
                QueryEntry.item_type,
            )
            .filter(QueryEntry.name.ilike(term))
            .order_by(QueryEntry.item_type.desc(), QueryEntry.modified.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "name": row.name,
                "modified": row.modified,
                "modified_by": row.modified_by,
                "path": row.path,
                "item_type": row.item_type,
            }
            for row in results
        ]
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


def search_query_entries(term: str, limit: int = 50) -> list[dict[str, str]]:
    """Search query entries by name or path.

    Returns both Items (files) and Folders, sorted by match score (best first),
    then by modified time descending.

    Args:
        term: Search term (matched against name and path).
        limit: Maximum number of results to return.

    Returns:
        List of dicts with keys 'name', 'modified', 'modified_by',
        'path', 'item_type'.
    """
    if not term or len(term.strip()) < 2:
        return []

    search_term = f"%{term.strip()}%"
    session = get_session()
    try:
        # Fetch at most limit*4 rows from SQLite — never pull the whole table
        results = (
            session.query(
                QueryEntry.name,
                QueryEntry.modified,
                QueryEntry.modified_by,
                QueryEntry.path,
                QueryEntry.item_type,
            )
            .filter(
                or_(
                    QueryEntry.name.ilike(search_term),
                    QueryEntry.path.ilike(search_term),
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
                "name": r["name"],
                "modified": r["modified"],
                "modified_by": r["modified_by"],
                "path": r["path"],
                "item_type": r["item_type"],
            }
            for r in scored_results[:limit]
        ]
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
        Dict with keys 'eddr_count', 'query_count', 'db_path', 'db_exists'.
    """
    db_path = get_db_path()
    if not db_path.is_file():
        return {
            "eddr_count": 0,
            "query_count": 0,
            "db_path": str(db_path),
            "db_exists": False,
        }

    session = get_session()
    try:
        eddr_count = session.query(EDDR).count()
        query_count = session.query(QueryEntry).count()
        return {
            "eddr_count": eddr_count,
            "query_count": query_count,
            "db_path": str(db_path),
            "db_exists": True,
        }
    finally:
        session.close()
