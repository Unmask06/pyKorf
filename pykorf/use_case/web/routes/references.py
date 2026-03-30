"""References routes: /model/references/*."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from flask import Blueprint, redirect, render_template, request, url_for

from pykorf.use_case.web import session as _sess
from pykorf.use_case.web.helpers import is_redirect, require_model

bp = Blueprint("references", __name__)


def _load_refs() -> Any:
    """Load the ReferencesStore for the active model.

    Returns:
        ReferencesStore instance (empty if no model or no sidecar yet).
    """
    from pykorf.use_case.web.references import ReferencesStore

    kdf_path = _sess.get_kdf_path()
    if kdf_path is None:
        return ReferencesStore()
    return ReferencesStore.load(kdf_path)


def _refs_context(kdf_path: Path, store: Any, **extra: Any) -> dict[str, Any]:
    """Build the common template context for the references page.

    Args:
        kdf_path: Active KDF path.
        store: Current ReferencesStore.
        **extra: Additional context variables.

    Returns:
        Template context dict.
    """
    from pykorf.use_case.web.references import CATEGORIES

    return {
        "kdf_path": str(kdf_path),
        "store": store,
        "categories": CATEGORIES,
        "ref_dir": str(kdf_path.parent / "reference"),
        "flash": None,
        "shortcut_result": None,
        **extra,
    }


@bp.route("/model/references")
def references_page() -> Any:
    """Render the References manager page."""
    model = require_model()
    if is_redirect(model):
        return model
    kdf_path = _sess.get_kdf_path()
    store = _load_refs()
    return render_template("references.html", **_refs_context(kdf_path, store))


@bp.route("/model/references/basis", methods=["POST"])
def references_save_basis() -> Any:
    """Save only the design basis text."""
    model = require_model()
    if is_redirect(model):
        return model
    kdf_path = _sess.get_kdf_path()
    store = _load_refs()
    store.basis = request.form.get("basis", "")
    store.save(kdf_path)
    return redirect(url_for("references.references_page"))


@bp.route("/model/references/add", methods=["POST"])
def references_add() -> Any:
    """Add a new reference entry and save."""
    model = require_model()
    if is_redirect(model):
        return model

    from pykorf.use_case.web.references import Reference

    kdf_path = _sess.get_kdf_path()
    store = _load_refs()

    name = (request.form.get("name") or "").strip()
    link = (request.form.get("link") or "").strip()
    description = (request.form.get("description") or "").strip()
    category = (request.form.get("category") or "Other").strip()

    if name and link:
        store.add(Reference.new(name=name, link=link, description=description, category=category))
        store.save(kdf_path)
        store.create_shortcuts(kdf_path)

    return redirect(url_for("references.references_page"))


@bp.route("/model/references/update", methods=["POST"])
def references_update() -> Any:
    """Update an existing reference by ID and save."""
    model = require_model()
    if is_redirect(model):
        return model

    kdf_path = _sess.get_kdf_path()
    store = _load_refs()

    ref_id = (request.form.get("ref_id") or "").strip()
    if ref_id:
        store.update(
            ref_id,
            name=(request.form.get("name") or "").strip(),
            link=(request.form.get("link") or "").strip(),
            description=(request.form.get("description") or "").strip(),
            category=(request.form.get("category") or "Other").strip(),
        )
        store.save(kdf_path)
        store.create_shortcuts(kdf_path)

    return redirect(url_for("references.references_page"))


@bp.route("/model/references/delete", methods=["POST"])
def references_delete() -> Any:
    """Delete a reference by ID and save."""
    model = require_model()
    if is_redirect(model):
        return model

    kdf_path = _sess.get_kdf_path()
    store = _load_refs()
    ref_id = (request.form.get("ref_id") or "").strip()
    if ref_id:
        store.delete(ref_id)
        store.save(kdf_path)

    return redirect(url_for("references.references_page"))


@bp.route("/model/references/shortcuts", methods=["POST"])
def references_create_shortcuts() -> Any:
    """Create .url shortcut files in the reference/ folder."""
    model = require_model()
    if is_redirect(model):
        return model

    kdf_path = _sess.get_kdf_path()
    store = _load_refs()
    shortcut_result: dict[str, Any] = {}

    try:
        count, ref_dir = store.create_shortcuts(kdf_path)
        shortcut_result = {"count": count, "path": str(ref_dir)}
    except Exception as exc:
        shortcut_result = {"error": str(exc)}

    return render_template(
        "references.html",
        **_refs_context(kdf_path, store, shortcut_result=shortcut_result),
    )
