"""Generate Report route: /model/report."""

from __future__ import annotations

from pathlib import Path

from flask import Blueprint, render_template, request

from pykorf.use_case.web import session as _sess
from pykorf.use_case.web.helpers import is_redirect, require_model

bp = Blueprint("report", __name__)


@bp.route("/model/report", methods=["GET", "POST"])
def generate_report():
    """Render and handle the Generate Report page."""
    model = require_model()
    if is_redirect(model):
        return model

    from pykorf.use_case.config import get_last_excel_export_path

    if request.method == "GET":
        return render_template(
            "report.html",
            kdf_path=str(_sess.get_kdf_path() or ""),
            last_report_path=str(get_last_excel_export_path() or ""),
            result=None,
        )

    report_path_str = (request.form.get("report_path") or "").strip()

    result_lines: list[tuple[str, str]] = []
    errors: list[str] = []

    if not report_path_str:
        errors.append("Output file path is required.")
    else:
        report_path = Path(report_path_str)
        try:
            import pandas as pd

            from pykorf.use_case.web.references import ReferencesStore

            dfs = model.io.to_dataframes()

            kdf_path_for_refs = _sess.get_kdf_path()
            refs_store = (
                ReferencesStore.load(kdf_path_for_refs)
                if kdf_path_for_refs
                else ReferencesStore()
            )

            with pd.ExcelWriter(report_path, engine="openpyxl") as writer:
                refs_df = refs_store.to_dataframe()
                if not refs_df.empty:
                    refs_df.to_excel(writer, sheet_name="References", index=False)

                if refs_store.basis.strip():
                    basis_df = pd.DataFrame({"Design Basis": [refs_store.basis]})
                    basis_df.to_excel(writer, sheet_name="Basis", index=False)

                for sheet_name, df in dfs.items():
                    df.to_excel(writer, sheet_name=sheet_name[:31], index=False)

            n_refs = len(refs_store.references)
            ref_note = f" (+{n_refs} reference(s))" if n_refs else ""
            result_lines.append(("success", f"Report saved to: {report_path}{ref_note}"))
        except Exception as exc:
            errors.append(f"Error generating report: {exc}")

    return render_template(
        "report.html",
        kdf_path=str(_sess.get_kdf_path() or ""),
        last_report_path=report_path_str,
        result={"lines": result_lines, "errors": errors},
    )
