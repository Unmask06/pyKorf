"""Save confirmation screen."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Label, RichLog

from pykorf.log import get_log_file
from pykorf.use_case.tui.logging import has_warnings_or_errors

if TYPE_CHECKING:
    from pykorf.model import Model
    from pykorf.use_case.tui.app import UseCaseTUI


class SaveConfirmScreen(Screen):
    """Modal screen asking the user whether to save changes."""

    CSS_PATH = []

    CSS = """
    SaveConfirmScreen {
        align: center middle;
    }
    #save-box {
        width: 60;
        height: auto;
        max-height: 20;
        border: round $accent;
        padding: 1 2;
    }
    #save-box Label {
        margin-bottom: 1;
    }
    #save-box #file-path {
        width: 100%;
        height: auto;
        max-height: 5;
        text-style: dim;
        overflow-x: hidden;
    }
    #save-box #file-path RichLog {
        overflow-x: hidden;
    }
    #save-buttons {
        height: 3;
        align: center middle;
    }
    #save-buttons Button {
        margin: 0 1;
    }
    #save-status {
        height: auto;
        margin-top: 1;
    }
    """

    def __init__(self, model: Model) -> None:
        super().__init__()
        self._model = model

    def compose(self) -> ComposeResult:
        with Vertical(id="save-box"):
            yield Label("Save Changes?")
            log = RichLog(id="file-path", wrap=True)
            from pathlib import Path

            log.write(f"File: {Path(self._model._parser.path).name}")
            yield log
            yield Label("", id="save-status")
            with Horizontal(id="save-buttons"):
                yield Button("Save", variant="primary", id="btn-save")
                yield Button("Discard", variant="warning", id="btn-discard")

    @on(Button.Pressed, "#btn-save")
    def save(self) -> None:
        status = self.query_one("#save-status", Label)
        try:
            save_path = self._model._parser.path
            self._model.save()
            status.update(f"Saved successfully to: {save_path}")

            # Flush all logging handlers to ensure file is up to date
            import logging

            for handler in logging.getLogger("pykorf").handlers:
                if hasattr(handler, "flush"):
                    handler.flush()

            # DEBUG: Check log file
            log_file = get_log_file()
            print(f"DEBUG: log_file = {log_file}")
            if log_file:
                from pathlib import Path

                log_path = Path(log_file)
                print(f"DEBUG: log_path exists = {log_path.exists()}")
                if log_path.exists():
                    print(f"DEBUG: log file size = {log_path.stat().st_size} bytes")
                    # Read first few lines for debugging
                    with open(log_path) as f:
                        lines = f.readlines()[:5]
                        for i, line in enumerate(lines):
                            print(f"DEBUG: line {i}: {line.strip()[:80]}")
                has_warnings = has_warnings_or_errors(log_file)
                print(f"DEBUG: has_warnings = {has_warnings}")
                if has_warnings:
                    log_name = log_path.name
                    print(f"DEBUG: Showing notification for {log_name}")
                    app = cast("UseCaseTUI", self.app)
                    app.show_notification(
                        f"\u26a0\ufe0f Warnings/errors detected. Please review {log_name} and update the KDF file accordingly."
                    )
            else:
                print("DEBUG: log_file is None")

            self.set_timer(1.0, self._dismiss)
        except Exception as exc:
            import traceback

            print(f"DEBUG: Error saving: {exc}")
            print(traceback.format_exc())
            status.update(f"Error saving: {exc}")

    @on(Button.Pressed, "#btn-discard")
    def discard(self) -> None:
        self.app.pop_screen()

    def _dismiss(self) -> None:
        self.app.pop_screen()
