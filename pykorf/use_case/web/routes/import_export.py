"""Import/Export route: /model/import-export."""

from __future__ import annotations

from pathlib import Path

from flask import Blueprint, render_template, request

from pykorf.use_case.web import session as _sess
from pykorf.use_case.web.helpers import is_redirect, require_model

bp = Blueprint("import_export", __name__)


@bp.route("/model/import-export", methods=["GET", "POST"])
def import_export():
    """Render and handle the Import/Export page."""
    model = require_model()
    if is_redirect(model):
        return model

    from pykorf.use_case.config import (
        get_last_excel_export_path,
        get_last_excel_import_path,
        set_last_excel_export_path,
        set_last_excel_import_path,
    )

    if request.method == "GET":
        return render_template(
            "import_export.html",
            kdf_path=str(_sess.get_kdf_path() or ""),
            last_export_path=str(get_last_excel_export_path() or ""),
            last_import_path=str(get_last_excel_import_path() or ""),
            result=None,
        )

    action = (request.form.get("action") or "export").strip()
    file_path_str = (request.form.get("file_path") or "").strip()

    result_lines: list[tuple[str, str]] = []
    errors: list[str] = []

    if not file_path_str:
        errors.append("File path is required.")
    else:
        file_path = Path(file_path_str)
        try:
            if action == "export":
                model.io.to_excel(file_path)
                set_last_excel_export_path(str(file_path))
                result_lines.append(("success", f"Exported to: {file_path}"))
            elif action == "import":
                if not file_path.is_file():
                    errors.append(f"File not found: {file_path}")
                else:
                    model.io.from_excel(file_path)
                    set_last_excel_import_path(str(file_path))
                    result_lines.append(("success", f"Imported from: {file_path}"))
            else:
                errors.append(f"Unknown action: {action}")
        except Exception as exc:
            errors.append(f"Error during {action}: {exc}")

    return render_template(
        "import_export.html",
        kdf_path=str(_sess.get_kdf_path() or ""),
        last_export_path=str(get_last_excel_export_path() or ""),
        last_import_path=str(get_last_excel_import_path() or ""),
        result={"lines": result_lines, "errors": errors},
    )
