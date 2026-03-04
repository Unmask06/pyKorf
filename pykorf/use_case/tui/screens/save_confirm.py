"""Save confirmation screen."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Label, RichLog

if TYPE_CHECKING:
    from pykorf.model import Model


class SaveConfirmScreen(Screen):
    """Modal screen asking the user whether to save changes."""

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

    def __init__(self, model: "Model") -> None:
        super().__init__()
        self._model = model

    def compose(self) -> ComposeResult:
        with Vertical(id="save-box"):
            yield Label("[bold]Save Changes?[/bold]")
            log = RichLog(id="file-path", wrap=True)
            log.write(f"File: {self._model._parser.path}")
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
            print(f"DEBUG: Saving model to: {save_path}")
            print(f"DEBUG: Model has {self._model.num_pipes} pipes")
            self._model.save()
            print(f"DEBUG: Save completed")
            status.update(f"Saved successfully to: {save_path}")
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
