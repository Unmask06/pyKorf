"""Main Textual application for pyKorf use case TUI."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.app import App, ComposeResult

if TYPE_CHECKING:
    from pykorf.model import Model


class UseCaseTUI(App):
    """pyKorf Use Case TUI - Textual application."""

    TITLE = "pyKorf Use Case Tool"
    SUB_TITLE = "Bulk operations on KDF files"

    CSS = """
    Screen {
        background: $surface;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    model: Model | None = None

    def on_mount(self) -> None:
        from pykorf.use_case.tui.screens.file_picker import FilePickerScreen

        self.push_screen(FilePickerScreen())


def run_tui() -> None:
    """Launch the Textual TUI application."""
    app = UseCaseTUI()
    app.run()


if __name__ == "__main__":
    run_tui()
