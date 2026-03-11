"""Apply PMS screen."""

from __future__ import annotations

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, RichLog, Static

from pykorf.log import get_log_file
from pykorf.use_case.config import get_pms_path
from pykorf.use_case.tui.logging import (
    get_log_entries,
    log_error,
    log_info,
    log_success,
    log_warning,
)


class ApplyPmsScreen(Screen):
    """Screen for applying PMS specifications to pipes."""

    BINDINGS = [("escape", "go_back", "Back")]

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
    """

    def compose(self) -> ComposeResult:
        pms_path = get_pms_path()
        
        with Vertical(id="pms-container"):
            with Horizontal():
                with Vertical(id="left-panel"):
                    with Vertical(id="pms-form"):
                        yield Label("Apply PMS Specifications", classes="info-section")
                        yield Static("─" * 30)
                        yield Label(f"PMS file: {pms_path}")
                        yield RichLog(id="pms-results", wrap=True)
                        with Horizontal(id="pms-buttons"):
                            yield Button("Apply", variant="primary", id="btn-apply")
                            yield Button("Back", variant="default", id="btn-back")
                
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

    def action_go_back(self) -> None:
        self.app.pop_screen()

    @on(Button.Pressed, "#btn-back")
    def go_back(self) -> None:
        self.app.pop_screen()

    @on(Button.Pressed, "#btn-apply")
    def apply(self) -> None:
        self._run_apply()

    @work(thread=True)
    def _run_apply(self) -> None:
        from pykorf.use_case.tui.app import UseCaseTUI
        from pykorf.use_case.tui.screens.save_confirm import SaveConfirmScreen

        results = self.query_one("#pms-results", RichLog)

        self.app.call_from_thread(results.clear)

        # Get PMS path from configuration
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

        try:
            from pykorf.use_case import apply_pms

            app = self.app
            assert isinstance(app, UseCaseTUI)
            model = app.model
            assert model is not None

            # Check if file has been modified externally and reload if needed
            if model.is_file_modified():
                self.app.call_from_thread(
                    lambda: log_info(results, "File modified externally, reloading...")
                )
                model.reload()

            updated = apply_pms(str(pms_path), model, save=False)

            # Fetch WARNING/ERROR logs from use_case.pms and display them
            log_file = get_log_file()
            if log_file:
                entries = get_log_entries(
                    log_file,
                    levels={"WARNING", "ERROR", "CRITICAL"},
                    logger_filter="pykorf.use_case.pms",
                )
                if entries:
                    self.app.call_from_thread(
                        lambda: log_warning(results, "Warnings/Errors during PMS processing:")
                    )
                    for _ts, _name, level, message in entries:
                        if level == "WARNING":
                            self.app.call_from_thread(
                                lambda m=message: log_warning(results, f"  ⚠ {m}")
                            )
                        else:
                            self.app.call_from_thread(
                                lambda m=message: log_error(results, f"  ✗ {m}")
                            )

            self.app.call_from_thread(
                lambda: log_success(results, f"Applied PMS specs to {len(updated)} pipes."),
            )

            for name in updated:
                self.app.call_from_thread(lambda n=name: log_info(results, f"  - {n}"))
            self.app.call_from_thread(self.app.push_screen, SaveConfirmScreen(model))
        except Exception as exc:
            self.app.call_from_thread(lambda e=exc: log_error(results, f"Error: {e}"))
