"""Apply PMS/HMB Data route: /model/data."""

from __future__ import annotations

from datetime import datetime, UTC
from pathlib import Path

import structlog
from flask import Blueprint, render_template, request

from pykorf.use_case.web import session as _sess
from pykorf.use_case.web.helpers import is_redirect, require_model

logger = structlog.get_logger(__name__)
bp = Blueprint("data", __name__)


def _get_filename(path_str: str) -> str:
    """Extract filename from path using Pathlib."""
    if not path_str:
        return ""
    return Path(path_str).name


def _apply_pms_from_source(model, pms_source: Path) -> None:
    """Apply PMS from a given source (Excel or JSON) to the model.

    Args:
        model: The active model to apply PMS to.
        pms_source: Path to PMS Excel or JSON file.
    """
    from pykorf.use_case.config import set_pms_excel_last_imported
    from pykorf.use_case.pms import apply_pms as _apply_pms, import_pms_from_excel

    model.io.save()

    # Convert Excel → pms.json in the data dir, then apply from JSON
    if pms_source.suffix.lower() in (".xlsx", ".xls"):
        json_path = import_pms_from_excel(pms_source)
        _apply_pms(json_path, model, save=False)
    else:
        _apply_pms(pms_source, model, save=False)

    model.io.save()
    _sess.reload()
    set_pms_excel_last_imported(datetime.now(UTC).isoformat())
    logger.info("pms_applied", pms_source=str(pms_source))


def apply_pms_if_stale(model) -> bool:
    """Apply PMS from the configured Excel file if it has been updated since last import.

    Args:
        model: The active model to apply PMS to.

    Returns:
        True if PMS was applied, False otherwise.
    """
    from pykorf.use_case.config import get_pms_excel_path
    from pykorf.use_case.pms import is_pms_excel_stale

    if not is_pms_excel_stale():
        logger.info("pms_stale_check", stale=False)
        return False

    pms_path = get_pms_excel_path()
    if not pms_path:
        logger.warning("pms_stale_but_no_path")
        return False

    pms_source = Path(pms_path)
    if not pms_source.is_file():
        logger.warning("pms_stale_but_file_not_found", pms_path=pms_path)
        return False

    logger.info("auto_apply_pms_start", pms_source=str(pms_source))
    try:
        _apply_pms_from_source(model, pms_source)
        return True
    except Exception as exc:
        logger.warning("auto_apply_pms_failed", error=str(exc), exc_info=True)
        return False


@bp.route("/model/data", methods=["GET", "POST"])
def apply_data():
    """Render and handle the Apply PMS/HMB Data form."""
    model = require_model()
    if is_redirect(model):
        return model

    from pykorf.use_case.config import get_last_hmb_path, get_pms_excel_path

    kdf_path = _sess.get_kdf_path()
    pms_excel = get_pms_excel_path()
    default_pms = pms_excel or (
        str(kdf_path.with_name(f"{kdf_path.stem}_pms.xlsx")) if kdf_path else ""
    )

    hmb_excel = get_last_hmb_path()
    default_hmb = hmb_excel or (
        str(kdf_path.with_name(f"{kdf_path.stem}_hmb.xlsx")) if kdf_path else ""
    )

    active_tab = "pms"

    if request.method == "GET":
        return render_template(
            "apply_data.html",
            kdf_path=str(kdf_path or ""),
            pms_excel_path=default_pms,
            hmb_excel_path=default_hmb,
            pms_filename=_get_filename(default_pms),
            hmb_filename=_get_filename(default_hmb),
            active_tab=active_tab,
            result=None,
        )

    pms_source_str = (request.form.get("pms_source") or "").strip()
    hmb_source_str = (request.form.get("hmb_source") or "").strip()

    result_lines: list[tuple[str, str]] = []
    errors: list[str] = []

    if pms_source_str:
        active_tab = "pms"
        from pykorf.use_case.config import set_pms_excel_path

        if pms_source_str:
            pms_source = Path(pms_source_str)
        else:
            pms_path = get_pms_excel_path()
            pms_source = Path(pms_path) if pms_path else None

        if not pms_source or not pms_source.is_file():
            errors.append(f"PMS data file not found: {pms_source}")
        else:
            try:
                set_pms_excel_path(pms_source)
                _apply_pms_from_source(model, pms_source)
                result_lines.append(("success", "PMS data applied successfully."))
                result_lines.append(("success", "Model saved."))
            except Exception as exc:
                errors.append(f"Error applying PMS: {exc}")

        return render_template(
            "apply_data.html",
            kdf_path=str(kdf_path or ""),
            pms_excel_path=str(pms_source or ""),
            hmb_excel_path=default_hmb,
            pms_filename=_get_filename(str(pms_source or "")),
            hmb_filename=_get_filename(default_hmb),
            active_tab=active_tab,
            result={"lines": result_lines, "errors": errors},
        )

    elif hmb_source_str:
        active_tab = "hmb"
        from pykorf.use_case.config import set_last_hmb_path

        hmb_source = Path(hmb_source_str) if hmb_source_str else get_last_hmb_path()

        if not hmb_source or not Path(hmb_source).is_file():
            errors.append(f"HMB data file not found: {hmb_source}")
        else:
            try:
                model.io.save()
                from pykorf.use_case.hmb import apply_hmb as _apply_hmb, import_stream_from_excel

                # Convert Excel → stream_data.json in the data dir, then apply from JSON
                if Path(hmb_source).suffix.lower() in (".xlsx", ".xls"):
                    json_path = import_stream_from_excel(hmb_source)
                    result_lines.append(("info", f"Stream JSON saved: {json_path}"))
                    _apply_hmb(json_path, model, save=False)
                else:
                    _apply_hmb(hmb_source, model, save=False)

                set_last_hmb_path(hmb_source)
                result_lines.append(("success", "HMB data applied successfully."))
                model.io.save()
                _sess.reload()
                result_lines.append(("success", "Model saved."))
            except Exception as exc:
                errors.append(f"Error applying HMB: {exc}")

        return render_template(
            "apply_data.html",
            kdf_path=str(kdf_path or ""),
            pms_excel_path=default_pms,
            hmb_excel_path=str(hmb_source or ""),
            pms_filename=_get_filename(default_pms),
            hmb_filename=_get_filename(str(hmb_source or "")),
            active_tab=active_tab,
            result={"lines": result_lines, "errors": errors},
        )

    errors.append("Either PMS or HMB source file must be provided.")
    return render_template(
        "apply_data.html",
        kdf_path=str(kdf_path or ""),
        pms_excel_path=default_pms,
        hmb_excel_path=default_hmb,
        pms_filename=_get_filename(default_pms),
        hmb_filename=_get_filename(default_hmb),
        active_tab=active_tab,
        result={"lines": result_lines, "errors": errors},
    )
