"""Document Register API routes: /api/doc-register/*."""

from __future__ import annotations

from pathlib import Path

from flask import Blueprint, jsonify, request

from pykorf.log import get_logger
from pykorf.use_case.config import (
    get_doc_register_excel_path,
    get_doc_register_sp_site_url,
    set_doc_register_excel_path,
    set_doc_register_sp_site_url,
)
from pykorf.use_case.web.doc_register.excel_to_db import (
    build_db_from_excel,
    get_db_path,
    is_excel_stale,
)
from pykorf.use_case.web.doc_register.db_ops import (
    get_db_stats,
    search_eddr_by_title,
    search_query_by_name,
    search_query_entries,
)

logger = get_logger(__name__)

bp = Blueprint("doc_register", __name__)


@bp.route("/api/doc-register/status")
def api_status():
    """Return Document Register configuration and DB status.

    Returns:
        JSON with excel_path, sp_site_url, db_exists, is_stale, db_stats.
    """
    excel_path = get_doc_register_excel_path()
    sp_site_url = get_doc_register_sp_site_url()
    db_path = get_db_path()
    db_exists = db_path.is_file()
    stale = is_excel_stale() if excel_path else False
    stats = get_db_stats() if db_exists else {"eddr_count": 0, "query_count": 0, "db_exists": False}

    return jsonify(
        {
            "excel_path": excel_path,
            "sp_site_url": sp_site_url,
            "db_exists": db_exists,
            "is_stale": stale,
            "db_stats": stats,
        }
    )


@bp.route("/api/doc-register/search-eddr")
def api_search_eddr():
    """Search EDDR entries by title.

    Query params:
        q (str): Search term (case-insensitive containment).

    Returns:
        JSON list of {document_no, title}.
    """
    q = (request.args.get("q") or "").strip()
    if not q:
        return jsonify([])

    results = search_eddr_by_title(q)
    return jsonify(results)


@bp.route("/api/doc-register/search-query")
def api_search_query():
    """Search query entries by document number.

    Query params:
        doc_no (str): Document number to match in name field.

    Returns:
        JSON list of {name, modified, modified_by, path, item_type}.
    """
    doc_no = (request.args.get("doc_no") or "").strip()
    if not doc_no:
        return jsonify([])

    results = search_query_by_name(doc_no)
    return jsonify(results)


@bp.route("/api/doc-register/search-files")
def api_search_files():
    """Search query entries by name or path.

    Query params:
        q (str): Search term (min 2 chars, matched against name and path).

    Returns:
        JSON list of {name, modified, modified_by, path, item_type}.
    """
    q = (request.args.get("q") or "").strip()
    if len(q) < 2:
        return jsonify([])

    results = search_query_entries(q)
    return jsonify(results)


@bp.route("/api/doc-register/rebuild-db", methods=["POST"])
def api_rebuild_db():
    """Force rebuild the Document Register database from Excel.

    Returns:
        JSON with success status and stats, or error message.
    """
    excel_path_str = get_doc_register_excel_path()
    if not excel_path_str:
        return jsonify({"error": "No Excel path configured. Set it in Preferences."}), 400

    excel_path = Path(excel_path_str)
    if not excel_path.is_file():
        return jsonify({"error": f"Excel file not found: {excel_path_str}"}), 400

    sp_site_url = get_doc_register_sp_site_url() or ""

    try:
        build_db_from_excel(excel_path, sp_site_url)
        stats = get_db_stats()
        logger.info("doc_register.rebuild_complete", stats=stats)
        return jsonify(
            {
                "success": True,
                "message": f"DB rebuilt: {stats['eddr_count']} EDDR entries, {stats['query_count']} query entries",
                "stats": stats,
            }
        )
    except Exception as exc:
        logger.error("doc_register.rebuild_failed", error=str(exc))
        return jsonify({"error": str(exc)}), 500


@bp.route("/api/doc-register/config", methods=["POST"])
def api_config():
    """Save Document Register configuration (Excel path and/or SP site URL).

    JSON body:
        excel_path (str, optional): Path to Document Register Excel file.
        sp_site_url (str, optional): SharePoint site base URL.

    Returns:
        JSON with updated config values.
    """
    data = request.get_json(silent=True) or {}

    excel_path = data.get("excel_path")
    if excel_path:
        set_doc_register_excel_path(excel_path.strip())

    sp_site_url = data.get("sp_site_url")
    if sp_site_url:
        set_doc_register_sp_site_url(sp_site_url.strip())

    return jsonify(
        {
            "excel_path": get_doc_register_excel_path(),
            "sp_site_url": get_doc_register_sp_site_url(),
        }
    )
