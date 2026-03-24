"""Bulk copy fluids screen."""

from __future__ import annotations

from typing import Any

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.containers import VerticalScroll
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
    .pipe-select-btn {
        width: 1fr;
        height: 1;
        margin: 0;
        background: $surface;
        border: none;
        text-align: left;
        color: $text;
    }
    .pipe-select-btn:hover {
        background: $accent 30%;
    }
    .pipe-select-btn.selected-for-target {
        background: $primary 50%;
        color: $text;
    }
    #selection-mode-toggle {
        height: auto;
        margin-bottom: 1;
    }
    #selection-mode-toggle Button {
        width: 1fr;
        height: auto;
        min-height: 2;
        margin-right: 0;
        padding: 0 1;
        content-align: center middle;
    }
    #selection-mode-toggle Button.mode-active {
        background: $primary;
        color: $text;
    }
    #selection-mode-toggle Button.mode-inactive {
        background: $surface;
        color: $text;
    }
    #clear-targets-btn {
        width: auto;
        height: 3;
        margin-left: 1;
    }
    .small-btn {
        width: auto;
        height: 3;
        padding: 0 1;
        margin-left: 1;
    }
    #target-label {
        height: 3;
        content-align: left middle;
    }
    #target-actions {
        height: auto;
        margin-top: 1;
    }
    #target-actions .target-label {
        height: 3;
        content-align: left middle;
        color: $text-muted;
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

    def __init__(self) -> None:
        super().__init__()
        self._fill_mode = "ref"
        self._pipe_names: list[str] = []

    def compose(self) -> ComposeResult:
        with Vertical(id="copy-container"), Horizontal(id="main-content"):
            with Vertical(id="left-panel"), Vertical(id="copy-form"):
                yield Label("Bulk Copy Fluids", classes="info-section")
                yield Static("─" * 30)
                yield Label("Reference pipe (copy FROM):")
                yield Input(placeholder="e.g. L1", id="ref-pipe-input")
                with Horizontal():
                    yield Label("Target pipes (comma-sep, empty for ALL):", id="target-label")
                    yield Button(
                        "Clear", variant="default", id="btn-clear-targets", classes="small-btn"
                    )
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
                    with Horizontal(id="selection-mode-toggle"):
                        yield Button("Select for Reference", variant="primary", id="btn-mode-ref")
                        yield Button("Select for Targets", variant="default", id="btn-mode-target")
                    with VerticalScroll(id="pipe-list-content"):
                        yield Static("Loading pipes...")
                    with Horizontal(id="target-actions"):
                        yield Label("Click pipes to add to:", classes="target-label")
                        yield Button("Clear Targets", variant="default", id="clear-targets-btn")

                with Vertical(classes="info-section"):
                    yield Label("How to Use")
                    yield Static("─" * 15)
                    yield Static("1. Select mode: Reference or Targets")
                    yield Static("2. Click pipe names to auto-fill")
                    yield Static("3. Or type manually in inputs")
                    yield Static("4. Check exclude for inverse")
                    yield Static("5. Click Execute")

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
        self.call_after_refresh(self._update_mode_buttons)

    def _populate_pipe_list(self) -> None:
        """Load and display pipe names as clickable buttons sorted by index."""
        from typing import cast

        from pykorf.use_case.tui.app import UseCaseTUI

        app = self.app
        if not isinstance(app, UseCaseTUI):
            return
        model = app.model
        if model is None:
            return

        pipe_list = self.query_one("#pipe-list-content", VerticalScroll)
        pipe_list.remove_children()

        # Get pipes sorted by index (skip index 0 which is template)
        pipes_dict = cast(dict[int, Any], model.pipes)
        pipes = sorted(
            [(idx, pipe) for idx, pipe in pipes_dict.items() if idx > 0], key=lambda x: x[0]
        )

        if not pipes:
            pipe_list.mount(Static("No pipes found in model."))
            return

        for i, (_, pipe) in enumerate(pipes):
            btn = Button(pipe.name, classes="pipe-select-btn", id=f"pipe-btn-{i}")
            pipe_list.mount(btn)

    def _update_mode_buttons(self) -> None:
        """Update button styles to reflect current selection mode."""
        try:
            btn_ref = self.query_one("#btn-mode-ref", Button)
            btn_target = self.query_one("#btn-mode-target", Button)
            if self._fill_mode == "ref":
                btn_ref.variant = "primary"
                btn_target.variant = "default"
            else:
                btn_ref.variant = "default"
                btn_target.variant = "primary"
        except Exception:
            pass

    def _update_pipe_button_styles(self) -> None:
        """Update pipe button styles to show which are selected for targets."""
        try:
            target_input = self.query_one("#target-pipes-input", Input).value.strip()
            target_names = {x.strip() for x in target_input.split(",") if x.strip()}
            for btn in self.query(".pipe-select-btn"):
                if isinstance(btn, Button):
                    pipe_name = str(btn.label)
                    if pipe_name in target_names and self._fill_mode == "target":
                        btn.add_class("selected-for-target")
                    else:
                        btn.remove_class("selected-for-target")
        except Exception:
            pass

    @on(Button.Pressed, "#btn-mode-ref")
    def set_mode_reference(self) -> None:
        """Switch to reference pipe selection mode."""
        self._fill_mode = "ref"
        self._update_mode_buttons()
        self._update_pipe_button_styles()

    @on(Button.Pressed, "#btn-mode-target")
    def set_mode_targets(self) -> None:
        """Switch to target pipes selection mode."""
        self._fill_mode = "target"
        self._update_mode_buttons()
        self._update_pipe_button_styles()

    @on(Button.Pressed, "#btn-clear-targets")
    @on(Button.Pressed, "#clear-targets-btn")
    def clear_targets(self) -> None:
        """Clear the target pipes input."""
        self.query_one("#target-pipes-input", Input).value = ""
        self._update_pipe_button_styles()

    @on(Button.Pressed, ".pipe-select-btn")
    def select_pipe(self, event: Button.Pressed) -> None:
        """Fill reference or append to target based on current fill mode."""
        name = str(event.button.label)
        if self._fill_mode == "ref":
            self.query_one("#ref-pipe-input", Input).value = name
        else:
            current = self.query_one("#target-pipes-input", Input).value.strip()
            names = [x.strip() for x in current.split(",") if x.strip()]
            if name not in names:
                names.append(name)
            self.query_one("#target-pipes-input", Input).value = ", ".join(names)
            self._update_pipe_button_styles()

    @on(Input.Changed, "#target-pipes-input")
    def on_target_input_changed(self) -> None:
        """Update pipe button styles when target input is manually edited."""
        self._update_pipe_button_styles()

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
