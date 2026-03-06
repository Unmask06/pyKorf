"""Apply HMB screen."""

from __future__ import annotations

from pathlib import Path

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, RichLog, Static

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
    #hmb-box {
        width: 80;
        height: auto;
        max-height: 40;
        border: round $accent;
        padding: 1 2;
    }
    #hmb-box Label {
        margin-bottom: 1;
    }
    #hmb-box Input {
        margin-bottom: 1;
    }
    #hmb-buttons {
        height: 3;
        align: center middle;
    }
    #hmb-buttons Button {
        margin: 0 1;
    }
    #hmb-results {
        height: 12;
        border: round $surface;
        margin-top: 1;
        overflow-x: hidden;
    }
    #hmb-results RichLog {
        overflow-x: hidden;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="hmb-box"):
            yield Label("Apply HMB Fluid Properties")
            yield Static("---")
            yield Label("HMB JSON file path:")
            yield Input(
                placeholder="C:\\path\\to\\hmb.json",
                id="hmb-path-input",
            )
            yield RichLog(id="hmb-results", wrap=True)
            with Horizontal(id="hmb-buttons"):
                yield Button("Apply", variant="primary", id="btn-apply")
                yield Button("Back", variant="default", id="btn-back")
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
