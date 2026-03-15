"""Bulk copy fluids screen."""

from __future__ import annotations

from typing import Any

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Button,
    Checkbox,
    Footer,
    Input,
    Label,
    RichLog,
    Static,
)

from pykorf.use_case.tui.logging import log_error, log_info, log_success


class BulkCopyFluidsScreen(Screen):
    """Screen for copying fluid properties from one pipe to others."""

    CSS_PATH = []

    CSS = """
    BulkCopyFluidsScreen {
        align: center middle;
    }
    #copy-container {
        width: 100%;
        height: 100%;
    }
    #main-content {
        width: 100%;
        height: 100%;
    }
    #left-panel {
        width: 70%;
        height: 100%;
        overflow-y: auto;
    }
    #right-panel {
        width: 30%;
        height: 100%;
    }
    #pipe-list-section {
        height: auto;
        max-height: 40%;
        border: round $surface;
        padding: 0 1;
        margin-bottom: 1;
    }
    #pipe-list-content {
        height: auto;
        overflow-y: auto;
    }
    #copy-form {
        padding: 0 1;
    }
    #copy-form Label {
        margin-bottom: 0;
        height: 1;
    }
    #copy-form Input {
        margin-bottom: 0;
        height: 3;
    }
    #copy-form Checkbox {
        margin-bottom: 1;
        height: 3;
    }
    #copy-buttons {
        height: auto;
        margin-top: 1;
        dock: bottom;
    }
    #copy-buttons Button {
        margin-right: 1;
        height: 3;
        padding: 0 1;
    }
    #copy-results {
        width: 100%;
        height: 1fr;
        border: round $surface;
        margin-top: 1;
        overflow-x: hidden;
    }
    #copy-results RichLog {
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
        with Vertical(id="copy-container"), Horizontal(id="main-content"):
            with Vertical(id="left-panel"), Vertical(id="copy-form"):
                yield Label("Bulk Copy Fluids", classes="info-section")
                yield Static("─" * 30)
                yield Label("Reference pipe (copy FROM):")
                yield Input(placeholder="e.g. L1", id="ref-pipe-input")
                yield Label("Target pipes (comma-sep, empty for ALL):")
                yield Input(
                    placeholder="e.g. L2, L3, L4",
                    id="target-pipes-input",
                )
                yield Checkbox(
                    "Exclude mode",
                    id="exclude-checkbox",
                )
                with Horizontal(id="copy-buttons"):
                    yield Button("Execute", variant="primary", id="btn-execute")
                    yield Button("Copy Log", variant="default", id="btn-copy-log")
                yield RichLog(id="copy-results", wrap=True)

            with Vertical(id="right-panel"):
                with Vertical(id="pipe-list-section"):
                    yield Label("Available Pipes")
                    yield Static("─" * 15)
                    yield Static("Loading pipes...", id="pipe-list-content")

                with Vertical(classes="info-section"):
                    yield Label("How to Use")
                    yield Static("─" * 15)
                    yield Static("1. Enter reference pipe name")
                    yield Static("2. Enter target pipes (optional)")
                    yield Static("3. Check exclude for inverse")
                    yield Static("4. Click Execute")

                with Vertical(classes="info-section"):
                    yield Label("Examples")
                    yield Static("─" * 15)
                    yield Static("Ref: L1, Targets: L2,L3")
                    yield Static("  → Copy L1 fluid to L2,L3")
                    yield Static("")
                    yield Static("Ref: L1, Targets: (empty)")
                    yield Static("  → Copy L1 fluid to ALL")
                    yield Static("")
                    yield Static("Ref: L1, Targets: L2, Exclude: ✓")
                    yield Static("  → Copy to all EXCEPT L2")
        yield Footer()

    def on_mount(self) -> None:
        """Populate the pipe list when screen mounts."""
        self.call_after_refresh(self._populate_pipe_list)

    def _populate_pipe_list(self) -> None:
        """Load and display pipe names sorted by index."""
        from typing import cast

        from pykorf.use_case.tui.app import UseCaseTUI

        app = self.app
        if not isinstance(app, UseCaseTUI):
            return
        model = app.model
        if model is None:
            return

        pipe_list = self.query_one("#pipe-list-content", Static)

        # Get pipes sorted by index (skip index 0 which is template)
        pipes_dict = cast(dict[int, Any], model.pipes)
        pipes = sorted(
            [(idx, pipe) for idx, pipe in pipes_dict.items() if idx > 0], key=lambda x: x[0]
        )

        if not pipes:
            pipe_list.update("No pipes found in model.")
            return

        # Format pipe names only (no index), comma-separated for easy copy/paste
        pipe_names = [pipe.name for _, pipe in pipes]
        display_text = ", ".join(pipe_names)

        pipe_list.update(display_text)

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
