"""SQLAlchemy models and database operations for Document Register.

Provides:
- ORM models for EDDR and query_entries tables
- Search functions for EDDR titles and query entries
- SharePoint URL construction helper
- Database statistics
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import Column, Integer, String, Text, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from pykorf.use_case.web.doc_register.excel_to_db import get_db_path

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
        db_path = get_db_path()
        _engine = create_engine(f"sqlite:///{db_path}", pool_pre_ping=True)
        _SessionFactory = sessionmaker(bind=_engine)
    return _engine


def get_session() -> Session:
    """Create a new database session.

    Returns:
        SQLAlchemy Session instance.
    """
    if _SessionFactory is None:
        get_engine()
    assert _SessionFactory is not None
    return _SessionFactory()


def search_eddr_by_title(query: str, limit: int = 50) -> list[dict[str, str]]:
    """Search EDDR entries by title using case-insensitive containment.

    Args:
        query: Search term (matched with ILIKE %term%).
        limit: Maximum number of results to return.

    Returns:
        List of dicts with keys 'document_no' and 'title'.
    """
    if not query.strip():
        return []

    term = f"%{query.strip()}%"
    session = get_session()
    try:
        results = (
            session.query(EDDR.document_no, EDDR.title)
            .filter(EDDR.title.ilike(term))
            .limit(limit)
            .all()
        )
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
            .order_by(QueryEntry.modified.desc())
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
