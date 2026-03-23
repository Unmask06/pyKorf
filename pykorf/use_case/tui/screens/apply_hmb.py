"""Apply HMB screen."""

from __future__ import annotations

from pathlib import Path

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Input, Label, LoadingIndicator, RichLog, Static

from pykorf.log import get_log_file
from pykorf.use_case.config import get_last_hmb_path, set_last_hmb_path
from pykorf.use_case.tui.screens import normalize_path_input
from pykorf.use_case.tui.logging import (
    display_log_entries,
    log_error,
    log_info,
    log_success,
    reload_if_modified,
)


class ApplyHmbScreen(Screen):
    """Screen for applying HMB fluid properties to pipes."""

    CSS_PATH = []

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
                    yield LoadingIndicator(id="apply-loading")

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

    def on_mount(self) -> None:
        last_path = get_last_hmb_path()
        if last_path:
            self.query_one("#hmb-path-input", Input).value = last_path

    @on(Button.Pressed, "#btn-apply")
    def apply(self) -> None:
        self.query_one("#btn-apply", Button).disabled = True
        self.query_one("#apply-loading").add_class("active")
        self._run_apply()

    @work(thread=True)
    def _run_apply(self) -> None:
        from pykorf.use_case.tui.app import UseCaseTUI
        from pykorf.use_case.tui.screens.save_confirm import SaveConfirmScreen

        results = self.query_one("#hmb-results", RichLog)
        try:
            raw_path = normalize_path_input(self.query_one("#hmb-path-input", Input).value)
            self.app.call_from_thread(results.clear)

            if not raw_path:
                self.app.call_from_thread(
                    lambda: log_error(results, "Please enter an HMB file path.")
                )
                return

            path = Path(raw_path)
            if not path.exists():
                self.app.call_from_thread(lambda: log_error(results, f"File not found: {path}"))
                return

            set_last_hmb_path(raw_path)

            self.app.call_from_thread(
                lambda: log_info(results, "Applying HMB fluid properties...")
            )

            from pykorf.use_case import apply_hmb

            app = self.app
            assert isinstance(app, UseCaseTUI)
            model = app.model
            assert model is not None

            reload_if_modified(model, self.app.call_from_thread, results)

            updated = apply_hmb(str(path), model, save=False)

            display_log_entries(
                self.app.call_from_thread,
                results,
                get_log_file(),
                "pykorf.use_case.hmb",
                "Warnings/Errors during HMB processing:",
            )

            self.app.call_from_thread(
                lambda: log_success(results, f"Applied HMB properties to {len(updated)} pipes."),
            )
            for name in updated:
                self.app.call_from_thread(lambda n=name: log_info(results, f"  - {n}"))

            app = self.app
            self.app.call_from_thread(
                app.show_notification, f"✅ Applied HMB to {len(updated)} pipes."
            )
            self.app.call_from_thread(self.app.push_screen, SaveConfirmScreen(model))
        except Exception as exc:
            self.app.call_from_thread(lambda e=exc: log_error(results, f"Error: {e}"))
        finally:
            def _finish_hmb():
                self.query_one("#btn-apply", Button).disabled = False
                self.query_one("#apply-loading").remove_class("active")
            self.app.call_from_thread(_finish_hmb)
