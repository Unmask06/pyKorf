"""Bulk copy fluids screen."""

from __future__ import annotations

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Button,
    Checkbox,
    Footer,
    Header,
    Input,
    Label,
    RichLog,
    Static,
)

from pykorf.use_case.tui.logging import log_error, log_info, log_success


class BulkCopyFluidsScreen(Screen):
    """Screen for copying fluid properties from one pipe to others."""

    BINDINGS = [("escape", "go_back", "Back")]

    CSS = """
    BulkCopyFluidsScreen {
        align: center middle;
    }
    #copy-box {
        width: 80;
        height: auto;
        max-height: 50;
        border: round $accent;
        padding: 1 2;
    }
    #copy-box Label {
        margin-bottom: 1;
    }
    #copy-box Input {
        margin-bottom: 1;
    }
    #copy-buttons {
        height: 3;
        align: center middle;
    }
    #copy-buttons Button {
        margin: 0 1;
    }
    #copy-results {
        height: 12;
        border: round $surface;
        margin-top: 1;
        overflow-x: hidden;
    }
    #copy-results RichLog {
        overflow-x: hidden;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="copy-box"):
            yield Label("Bulk Copy Fluids")
            yield Static("---")
            yield Label("Reference pipe (copy FROM):")
            yield Input(placeholder="e.g. L1", id="ref-pipe-input")
            yield Label("Target pipes (comma-separated, leave empty for ALL):")
            yield Input(
                placeholder="e.g. L2, L3, L4 (or empty for all)",
                id="target-pipes-input",
            )
            yield Checkbox(
                "Exclude mode (copy to all EXCEPT listed targets)",
                id="exclude-checkbox",
            )
            yield RichLog(id="copy-results", wrap=True)
            with Horizontal(id="copy-buttons"):
                yield Button("Execute", variant="primary", id="btn-execute")
                yield Button("Copy Log", variant="default", id="btn-copy-log")
                yield Button("Back", variant="default", id="btn-back")
        yield Footer()

    def action_go_back(self) -> None:
        self.app.pop_screen()

    @on(Button.Pressed, "#btn-back")
    def go_back(self) -> None:
        self.app.pop_screen()

    @on(Button.Pressed, "#btn-copy-log")
    def copy_log(self) -> None:
        """Copy RichLog content to clipboard."""
        import pyperclip

        results = self.query_one("#copy-results", RichLog)
        lines: list[str] = []
        for line in results.lines:
            lines.append(str(line))
        text = "\n".join(lines)
        pyperclip.copy(text)
        log_info(results, "Log copied to clipboard.")

    @on(Button.Pressed, "#btn-execute")
    def execute(self) -> None:
        self._run_copy()

    @work(thread=True)
    def _run_copy(self) -> None:
        from pykorf.use_case.tui.app import UseCaseTUI
        from pykorf.use_case.tui.screens.save_confirm import SaveConfirmScreen

        results = self.query_one("#copy-results", RichLog)
        ref_input = self.query_one("#ref-pipe-input", Input).value.strip()
        target_input = self.query_one("#target-pipes-input", Input).value.strip()
        exclude = self.query_one("#exclude-checkbox", Checkbox).value

        self.app.call_from_thread(results.clear)

        if not ref_input:
            self.app.call_from_thread(lambda: log_error(results, "Please enter a reference pipe."))
            return

        target_lines: list[str] | None = None
        if target_input:
            target_lines = [t.strip() for t in target_input.split(",") if t.strip()]

        self.app.call_from_thread(lambda: log_info(results, "Copying fluids..."))

        try:
            from pykorf.use_case import copy_fluids

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

            updated = copy_fluids(model, ref_input, target_lines, exclude)

            self.app.call_from_thread(
                lambda: log_success(results, f"Updated {len(updated)} pipes.")
            )
            if updated:
                for name in updated:
                    self.app.call_from_thread(lambda n=name: log_info(results, f"  - {n}"))

            self.app.call_from_thread(self.app.push_screen, SaveConfirmScreen(model))
        except Exception as exc:
            error_msg = str(exc)
            self.app.call_from_thread(lambda: log_error(results, f"Error: {error_msg}"))
