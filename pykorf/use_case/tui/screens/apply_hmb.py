"""Apply HMB screen."""

from __future__ import annotations

from pathlib import Path

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Input, Label, RichLog, Static

from pykorf.log import get_log_file
from pykorf.use_case.tui.logging import (
    get_log_entries,
    log_error,
    log_info,
    log_success,
    log_warning,
)


class ApplyHmbScreen(Screen):
    """Screen for applying HMB fluid properties to pipes."""

    BINDINGS = [("escape", "go_back", "Back")]

    CSS = """
    ApplyHmbScreen {
        align: center middle;
    }
    #hmb-container {
        width: 100%;
        height: 100%;
    }
    #hmb-form {
        padding: 0 1;
    }
    #hmb-form Label {
        margin-bottom: 0;
        height: 1;
    }
    #hmb-form Input {
        margin-bottom: 0;
        height: 3;
    }
    #hmb-buttons {
        height: auto;
        margin-top: 1;
    }
    #hmb-buttons Button {
        margin-right: 1;
        height: 3;
        padding: 0 1;
    }
    #hmb-results {
        width: 100%;
        height: 1fr;
        border: round $surface;
        margin-top: 1;
        overflow-x: hidden;
    }
    #hmb-results RichLog {
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
        with Vertical(id="hmb-container"), Horizontal():
            with Vertical(id="left-panel"), Vertical(id="hmb-form"):
                yield Label("Apply HMB Fluid Properties", classes="info-section")
                yield Static("─" * 30)
                yield Label("HMB JSON file path:")
                yield Input(
                    placeholder="C:\\path\\to\\hmb.json",
                    id="hmb-path-input",
                )
                yield RichLog(id="hmb-results", wrap=True)
                with Horizontal(id="hmb-buttons"):
                    yield Button("Apply", variant="primary", id="btn-apply")
                    yield Button("Back", variant="default", id="btn-back")

            with Vertical(id="right-panel"):
                with Vertical(classes="info-section"):
                    yield Label("About HMB")
                    yield Static("─" * 15)
                    yield Static("HMB contains fluid")
                    yield Static("properties for streams.")
                    yield Static("")
                    yield Static("Applies fluid data to")
                    yield Static("pipes based on stream")
                    yield Static("assignments.")

                with Vertical(classes="info-section"):
                    yield Label("Format")
                    yield Static("─" * 15)
                    yield Static("JSON file with stream")
                    yield Static("names and fluid props:")
                    yield Static("  - Density")
                    yield Static("  - Viscosity")
                    yield Static("  - Temperature")
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

        results = self.query_one("#hmb-results", RichLog)
        raw_path = self.query_one("#hmb-path-input", Input).value.strip().strip('"').strip("'")

        self.app.call_from_thread(results.clear)

        if not raw_path:
            self.app.call_from_thread(lambda: log_error(results, "Please enter an HMB file path."))
            return

        path = Path(raw_path)
        if not path.exists():
            self.app.call_from_thread(lambda: log_error(results, f"File not found: {path}"))
            return

        self.app.call_from_thread(lambda: log_info(results, "Applying HMB fluid properties..."))

        try:
            from pykorf.use_case import apply_hmb

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

            updated = apply_hmb(str(path), model, save=False)

            # Fetch WARNING/ERROR logs from use_case.hmb and display them
            log_file = get_log_file()
            if log_file:
                entries = get_log_entries(
                    log_file,
                    levels={"WARNING", "ERROR", "CRITICAL"},
                    logger_filter="pykorf.use_case.hmb",
                )
                if entries:
                    self.app.call_from_thread(
                        lambda: log_warning(results, "Warnings/Errors during HMB processing:")
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
                lambda: log_success(results, f"Applied HMB properties to {len(updated)} pipes."),
            )
            for name in updated:
                self.app.call_from_thread(lambda n=name: log_info(results, f"  - {n}"))
            self.app.call_from_thread(self.app.push_screen, SaveConfirmScreen(model))
        except Exception as exc:
            self.app.call_from_thread(lambda e=exc: log_error(results, f"Error: {e}"))
