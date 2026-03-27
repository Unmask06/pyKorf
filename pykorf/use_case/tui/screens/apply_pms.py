"""Apply PMS screen."""

from __future__ import annotations

import datetime
from pathlib import Path

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Label, LoadingIndicator, RichLog, Static

from pykorf.log import get_log_file
from pykorf.use_case.config import (
    get_pms_excel_last_imported,
    get_pms_excel_path,
    get_pms_path,
)
from pykorf.use_case.tui.logging import (
    display_log_entries,
    log_error,
    log_info,
    log_success,
    reload_if_modified,
)


class ApplyPmsScreen(Screen):
    """Screen for applying PMS specifications to pipes."""

    CSS_PATH = []

    CSS = """
    ApplyPmsScreen {
        align: center middle;
    }
    #pms-container {
        width: 100%;
        height: 100%;
    }
    #pms-form {
        padding: 0 1;
    }
    #pms-form Label {
        margin-bottom: 0;
        height: 1;
    }
    #pms-buttons {
        height: auto;
        margin-top: 1;
    }
    #pms-buttons Button {
        margin-right: 1;
        height: 3;
        padding: 0 1;
    }
    #pms-results {
        width: 100%;
        height: 1fr;
        border: round $surface;
        margin-top: 1;
        overflow-x: hidden;
    }
    #pms-results RichLog {
        overflow-x: hidden;
    }
    #apply-loading {
        display: none;
        height: 1;
        margin-left: 1;
    }
    #apply-loading.active {
        display: block;
    }
    #right-panel-content {
        padding: 0 1;
    }
    .info-section {
        margin-bottom: 1;
    }
    .info-section Label {
        text-style: bold;
        color: $accent;
    }
    #stale-warning {
        color: $warning;
        text-style: bold;
        height: auto;
        display: none;
    }
    #stale-warning.visible {
        display: block;
    }
    """

    def compose(self) -> ComposeResult:
        pms_path = get_pms_path()

        with Vertical(id="pms-container"), Horizontal():
            with Vertical(id="left-panel"), Vertical(id="pms-form"):
                yield Label("Apply PMS Specifications", classes="info-section")
                yield Static("─" * 30)
                yield Label(f"PMS file: {pms_path}")
                yield Label("", id="stale-warning")
                yield RichLog(id="pms-results", wrap=True)
                with Horizontal(id="pms-buttons"):
                    yield Button("Apply", variant="primary", id="btn-apply")
                    yield LoadingIndicator(id="apply-loading")

            with Vertical(id="right-panel"):
                with Vertical(classes="info-section"):
                    yield Label("About PMS")
                    yield Static("─" * 15)
                    yield Static("PMS specifications")
                    yield Static("define pipe properties")
                    yield Static("based on pipe names.")
                    yield Static("")
                    yield Static("Matches pipes by NAME")
                    yield Static("attribute.")

                with Vertical(classes="info-section"):
                    yield Label("Note")
                    yield Static("─" * 15)
                    yield Static("Import PMS from Excel")
                    yield Static("via Configuration menu")
                    yield Static("if file not found.")
        yield Footer()

    def on_mount(self) -> None:
        excel_path_str = get_pms_excel_path()
        last_imported_str = get_pms_excel_last_imported()
        stale = False
        if excel_path_str and last_imported_str:
            p = Path(excel_path_str)
            try:
                if p.exists():
                    file_mtime = datetime.datetime.fromtimestamp(p.stat().st_mtime)
                    last_imported = datetime.datetime.fromisoformat(last_imported_str)
                    stale = file_mtime > last_imported
            except (OSError, ValueError):
                pass
        if stale:
            warning = self.query_one("#stale-warning", Label)
            warning.update("▲ PMS Excel updated since last import — re-import recommended")
            warning.add_class("visible")

    @on(Button.Pressed, "#btn-apply")
    def apply(self) -> None:
        self.query_one("#btn-apply", Button).disabled = True
        self.query_one("#apply-loading").add_class("active")
        self._run_apply()

    @work(thread=True)
    def _run_apply(self) -> None:
        from pykorf.use_case.tui.app import UseCaseTUI
        from pykorf.use_case.tui.screens.save_confirm import SaveConfirmScreen

        results = self.query_one("#pms-results", RichLog)
        try:
            self.app.call_from_thread(results.clear)

            pms_path = get_pms_path()
            if not pms_path.exists():
                self.app.call_from_thread(
                    lambda: log_error(
                        results,
                        f"PMS file not found: {pms_path}\n"
                        "Please import PMS data from Excel first (Configuration menu).",
                    )
                )
                return

            self.app.call_from_thread(lambda: log_info(results, f"Loading PMS from: {pms_path}"))

            from pykorf.use_case import apply_pms

            app = self.app
            assert isinstance(app, UseCaseTUI)
            model = app.model
            assert model is not None

            reload_if_modified(model, self.app.call_from_thread, results)

            updated = apply_pms(str(pms_path), model, save=False)

            display_log_entries(
                self.app.call_from_thread,
                results,
                get_log_file(),
                "pykorf.use_case.pms",
                "Warnings/Errors during PMS processing:",
            )

            self.app.call_from_thread(
                lambda: log_success(results, f"Applied PMS specs to {len(updated)} pipes."),
            )
            for name in updated:
                self.app.call_from_thread(lambda n=name: log_info(results, f"  - {n}"))

            app = self.app
            self.app.call_from_thread(
                app.show_notification, f"✅ Applied PMS to {len(updated)} pipes."
            )
            self.app.call_from_thread(self.app.push_screen, SaveConfirmScreen(model))
        except Exception as exc:
            self.app.call_from_thread(lambda e=exc: log_error(results, f"Error: {e}"))
        finally:

            def _finish_pms():
                self.query_one("#btn-apply", Button).disabled = False
                self.query_one("#apply-loading").remove_class("active")

            self.app.call_from_thread(_finish_pms)
